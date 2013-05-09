#!/usr/bin/env python

import csv
import os

from tumblpy import Tumblpy, TumblpyError

import app_config

secrets = app_config.get_secrets()

t = Tumblpy(
    app_key=secrets['TUMBLR_APP_KEY'],
    app_secret=secrets['TUMBLR_APP_SECRET'],
    oauth_token=secrets['TUMBLR_OAUTH_TOKEN'],
    oauth_token_secret=secrets['TUMBLR_OAUTH_TOKEN_SECRET'])

with open('data/review.csv') as f:
    rows = list(csv.reader(f))

for row in rows:
    svg_url, status, tumblr_url = row

    if tumblr_url:
        post_id = tumblr_url.split('/')[-1]

        try:
            post = t.get('posts', blog_url=app_config.TUMBLR_URL, params={ 'id': post_id })
        except TumblpyError, e:
            print 'Error %s: %s %s' % (post_id, e.error_code, e.msg)
            continue

        caption = post['posts'][0]['caption']

        if 'zazzle_url' in caption:
            print 'Skipping %s because it already has a Zazzle URL' % post_id 

            continue

        path, filename = os.path.split(svg_url)
        zazzle_url = os.path.join(path, 'zazzle_' + filename.replace('svg', 'png'))

        caption += '\n<input id="zazzle_url" type="hidden" value="%s">' % zazzle_url

        print caption

