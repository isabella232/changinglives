#!/usr/bin/env python
import datetime
import gzip
import json
import os
from random import choice
from sets import *
import urlparse

import boto
from jinja2 import Template
import oauth2 as oauth
import requests
from tumblpy import Tumblpy

import app_config


def generate_new_oauth_tokens():
    """
    Script to generate new OAuth tokens.
    Code from this gist: https://gist.github.com/4219558
    """
    consumer_key = os.environ['%s_TUMBLR_APP_KEY' % app_config.CONFIG_NAME]
    consumer_secret = os.environ['%s_TUMBLR_APP_SECRET' % app_config.CONFIG_NAME]

    request_token_url = 'http://www.tumblr.com/oauth/request_token'
    access_token_url = 'http://www.tumblr.com/oauth/access_token'
    authorize_url = 'http://www.tumblr.com/oauth/authorize'

    consumer = oauth.Consumer(consumer_key, consumer_secret)
    client = oauth.Client(consumer)

    # Step 1: Get a request token. This is a temporary token that is used for
    # having the user authorize an access token and to sign the request to obtain
    # said access token.

    resp, content = client.request(request_token_url, "POST")
    if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])

    request_token = dict(urlparse.parse_qsl(content))

    print "Request Token:"
    print "    - oauth_token        = %s" % request_token['oauth_token']
    print "    - oauth_token_secret = %s" % request_token['oauth_token_secret']
    print

    # Step 2: Redirect to the provider. Since this is a CLI script we do not
    # redirect. In a web application you would redirect the user to the URL
    # below.

    print "Go to the following link in your browser:"
    print "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
    print

    # After the user has granted access to you, the consumer, the provider will
    # redirect you to whatever URL you have told them to redirect to. You can
    # usually define this in the oauth_callback argument as well.
    accepted = 'n'
    while accepted.lower() == 'n':
            accepted = raw_input('Have you authorized me? (y/n) ')
            oauth_verifier = raw_input('What is the OAuth Verifier? ')

    # Step 3: Once the consumer has redirected the user back to the oauth_callback
    # URL you can request the access token the user has approved. You use the
    # request token to sign this request. After this is done you throw away the
    # request token and use the access token returned. You should store this
    # access token somewhere safe, like a database, for future use.
    token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
    token.set_verifier(oauth_verifier)
    client = oauth.Client(consumer, token)

    resp, content = client.request(access_token_url, "POST")
    access_token = dict(urlparse.parse_qsl(content))

    print "Access Token:"
    print "    - oauth_token        = %s" % access_token['oauth_token']
    print "    - oauth_token_secret = %s" % access_token['oauth_token_secret']
    print
    print "You may now access protected resources using the access tokens above."
    print


def dump_tumblr_json():
    secrets = app_config.get_secrets()

    t = Tumblpy(
        app_key=secrets['TUMBLR_APP_KEY'],
        app_secret=secrets['TUMBLR_APP_SECRET'],
        oauth_token=secrets['TUMBLR_OAUTH_TOKEN'],
        oauth_token_secret=secrets['TUMBLR_OAUTH_TOKEN_SECRET'])

    limit = 10
    pages = range(0, 20)

    for page in pages:
        offset = page * limit
        posts = t.get('posts', blog_url=app_config.TUMBLR_URL, params={'limit': limit, 'offset': offset})

        with open('data/backups/tumblr_prod_%s.json' % page, 'w') as f:
            f.write(json.dumps(posts))


def fetch_posts():
    """
    Returns a list of all tumblr posts, unsorted.
    """
    print "Starting."

    # Set constants
    secrets = app_config.get_secrets()
    base_url = 'http://api.tumblr.com/v2/blog/%s.tumblr.com/posts/photo' % app_config.TUMBLR_BLOG_ID
    key_param = '?api_key=%s' % secrets['TUMBLR_APP_KEY']
    limit_param = '&limit=20'
    limit = 20
    new_limit = limit
    post_list = []

    print base_url + key_param

    # Figure out the total number of posts.
    r = requests.get(base_url + key_param)
    total_count = int(json.loads(r.content)['response']['total_posts'])
    print "%s total posts available." % total_count

    # Do the pagination math.
    pages_count = (total_count / limit)
    pages_remainder = (total_count % limit)
    if pages_remainder > 0:
        pages_count += 1
    pages = range(0, pages_count)
    print "%s pages required." % len(pages)

    # Start requesting pages.
    # Note: Maximum of 20 posts per page.
    print "Requesting pages."
    for page in pages:

        # Update all of the pagination shenanigans.
        start_number = new_limit - limit
        end_number = new_limit
        if end_number > total_count:
            end_number = total_count
        new_limit = new_limit + limit
        page_param = '&offset=%s' % start_number
        page_url = base_url + key_param + limit_param + page_param

        # Actually fetch the page URL.
        r = requests.get(page_url)
        posts = json.loads(r.content)

        for post in posts['response']['posts']:
            try:
                if 'NSFW' in post['tags']:
                    pass
                elif 'nsfw' in post['tags']:
                    pass
                else:
                    post_list.append(post)
            except KeyError:
                pass

    return post_list


def _deploy_file(s3_buckets, local_path, s3_path):
    """
    Generic function for deploying a file to arbitrary S3 buckets.
    """
    file_name = os.path.split(local_path)[1]

    with open(local_path, 'r') as html_output:
        with gzip.open(file_name + '.gz', 'wb') as f:
            f.write(html_output.read())

    for bucket in s3_buckets:
        conn = boto.connect_s3()
        bucket = conn.get_bucket(bucket)
        key = boto.s3.key.Key(bucket)
        key.key = '%s/%s' % (app_config.PROJECT_SLUG, s3_path)
        key.set_contents_from_filename(
            file_name + '.gz',
            policy='public-read',
            headers={
                'Cache-Control': 'max-age=5 no-cache no-store must-revalidate',
                'Content-Encoding': 'gzip'
            }
        )

    os.remove(file_name + '.gz')


def _format_post(post):
    default_photo_url = post['photos'][0]['original_size']['url']

    simple_post = {
        'id': post['id'],
        'url': post['post_url'],
        'text': post['caption'],
        'timestamp': post['timestamp'],
        'note_count': post['note_count'],
        'photo_url': default_photo_url,
        'photo_url_100': default_photo_url,
        'photo_url_250': default_photo_url,
        'photo_url_500': default_photo_url,
        'photo_url_1280': default_photo_url
    }

    # Handle the new photo assignment.
    for photo in post['photos'][0]['alt_sizes']:
        if int(photo['width']) == 100:
            simple_post['photo_url_100'] = photo['url']
        if int(photo['width']) == 250:
            simple_post['photo_url_250'] = photo['url']
        if int(photo['width']) == 500:
            simple_post['photo_url_500'] = photo['url']
        if int(photo['width']) == 1280:
            simple_post['photo_url_1280'] = photo['url']

    return simple_post


def _render_output_template(posts, input_template, output_file):
    """
    Renders the output templates.
    """
    context = {}
    context['posts'] = posts
    with open(input_template,  'r') as read_template:
        payload = Template(read_template.read())
        return payload.render(**context)


def write_aggregates():
    """
    Most popular posts as defined by Tumblr notes.
    """

    # Call function to fetch posts.
    post_list = fetch_posts()

    return_obj = {}
    return_obj['popular'] = None
    return_obj['featured'] = None

    popular_list = sorted(post_list, key=lambda post: post['note_count'], reverse=True)

    popular_output = []
    # Render the sorted list, but slice to just 24 objects per bb.
    for post in popular_list[0:app_config.NUMBER_OF_AGGREGATES]:
        if u'featured' not in post['tags']:
            simple_post = _format_post(post)
            popular_output.append(simple_post)

    popular_output = sorted(popular_output, key=lambda post: post['note_count'], reverse=True)

    # Call funtion to write file.
    return_obj['popular'] = _render_output_template(popular_output, 'templates/_post_list.html', 'www/live-data/aggregates_popular.html')

    featured_list = sorted(post_list, key=lambda post: post['timestamp'], reverse=True)

    featured_output = []
    for post in featured_list:
        is_featured = False
        for tag in post['tags']:
            if tag == u'featured':
                is_featured = True

        if is_featured is True:
            featured_output.append(_format_post(post))

    featured_output = sorted(featured_output, key=lambda post: post['timestamp'], reverse=True)

    # Call funtion to write file.
    return_obj['featured'] = _render_output_template(featured_output[0:app_config.NUMBER_OF_AGGREGATES], 'templates/_featured_post_list.html', 'www/live-data/aggregates_featured.html')

    with open('www/live-data/aggregates.json', 'wb') as json_file:
        json_file.write("aggregateCallback(%s)" % json.dumps(return_obj))


def deploy_aggregates(s3_buckets):
    """
    Control function for deploying the aggregate files.
    """
    file_name = 'aggregates.json'
    file_path = 'www/live-data/%s' % file_name
    _deploy_file(s3_buckets, file_path, 'live-data/%s' % file_name)


def write_test_posts():
    """
    Writes test posts to our test blog as defined by app_config.py
    """

    # This is how many posts will be written.
    TOTAL_NUMBER = 9

    secrets = app_config.get_secrets()

    t = Tumblpy(
        app_key=secrets['TUMBLR_APP_KEY'],
        app_secret=secrets['TUMBLR_APP_SECRET'],
        oauth_token=secrets['TUMBLR_OAUTH_TOKEN'],
        oauth_token_secret=secrets['TUMBLR_OAUTH_TOKEN_SECRET'])

    tags = ['featured', '']

    images = [
        'http://media.npr.org/assets/img/2013/04/24/habitablezones_custom-fa87578c6e6a97788b92a0ecac956b9098607aa6-s40.jpg',
        'http://media.npr.org/assets/img/2013/04/24/ocpack-32260770b4090f86ddeb7502175a631d50c3b4a1-s51.jpg',
        'http://media.npr.org/assets/img/2013/04/24/dalrymple-c-karoki-lewis-4c9bd790639c870d51c670cbecbca4b802b82b1a-s51.jpg',
        'http://media.npr.org/assets/img/2013/04/24/ap111231019469-46289d097a45801ed2ca3464da14b13be40e5adb-s51.jpg'
    ]

    n = 0
    while n < TOTAL_NUMBER:
        image = choice(images)
        tag = choice(tags)
        caption = u"<p class='intro'>Introduction,</p><p class='message'>This is a test post.</p><p class='signature-name'>Sincerely,<br/>Test from Test, Test</p>"
        tumblr_post = t.post('post', blog_url=app_config.TUMBLR_URL, params={
            'type': 'photo',
            'caption': caption,
            'tags': tag,
            'source': image
        })

        print n, tumblr_post['id']

        n += 1
