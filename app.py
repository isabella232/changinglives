#!/usr/bin/env python

import datetime
import json
from mimetypes import guess_type
import os
import urllib

from dateutil.parser import *
import envoy
from flask import Flask, Markup, abort, render_template
import pytz

import app_config
from render_utils import flatten_app_config, make_context
import tumblr_utils

app = Flask(app_config.PROJECT_NAME)

@app.route('/email.html')
def _email():
    context = make_context()

    post_list = tumblr_utils.fetch_posts()

    if app_config.DEPLOYMENT_TARGET in ['staging', 'production']:
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    else:
        yesterday = datetime.datetime(2013, 5, 3, 12, 18, 20)

    yesterdate = datetime.date(yesterday.year, yesterday.month, yesterday.day)

    eastern = pytz.timezone('US/Eastern')

    reset = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0) + datetime.timedelta(days=1)
    time_left = reset - yesterday

    today_posts = []

    for post in post_list:
        parsed_post_date = parse(post['date'])
        eastern_transformed_post_date = parsed_post_date.astimezone(eastern)
        post_date = datetime.date(
            eastern_transformed_post_date.year,
            eastern_transformed_post_date.month,
            eastern_transformed_post_date.day)

        if post_date == yesterdate:
            post['date'] = eastern_transformed_post_date
            today_posts.append(post)

    print "Posts since last reset: %s" % len(today_posts)
    print "Posts remaining until next reset: %s" % (app_config.TUMBLR_POST_LIMIT - len(today_posts))
    print "Time left until next reset: %s" % time_left

    context['posts'] = today_posts
    context['yesterday'] = (datetime.datetime.now() - datetime.timedelta(days=1))

    return render_template('email.html', **context)

# Example application views
@app.route('/tumblr-form.html')
def test_widget():
    """
    Example page displaying widget at different embed sizes.
    """
    return render_template('tumblr-form.html', **make_context())

@app.route('/test-signs.html')
def test_signs():
    """
    Example page displaying potential sign designs.
    """
    return render_template('test-signs.html', **make_context())

# Render LESS files on-demand
@app.route('/less/<string:filename>')
def _less(filename):
    try:
        with open('less/%s' % filename) as f:
            less = f.read()
    except IOError:
        abort(404)

    if os.path.exists('node_modules/.bin/lessc'):
        r = envoy.run('node_modules/.bin/lessc -', data=less)

    else:
        r = envoy.run('node_modules/bin/lessc -', data=less)

    return r.std_out, 200, { 'Content-Type': 'text/css' }

# Render JST templates on-demand
@app.route('/js/templates.js')
def _templates_js():
    r = envoy.run('node_modules/.bin/jst --template underscore jst')

    return r.std_out, 200, { 'Content-Type': 'application/javascript' }

# Render application configuration
@app.route('/js/app_config.js')
def _app_config_js():
    config = flatten_app_config()
    js = 'window.APP_CONFIG = ' + json.dumps(config)

    return js, 200, { 'Content-Type': 'application/javascript' }

# Server arbitrary static files on-demand
@app.route('/%s/<path:path>' % app_config.PROJECT_SLUG)
def _static(path):
    try:
        with open('www/%s' % path) as f:
            return f.read(), 200, { 'Content-Type': guess_type(path)[0] }
    except IOError:
        abort(404)

# Server arbitrary static files on-demand
@app.route('/<path:path>')
def _static(path):
    try:
        with open('www/%s' % path) as f:
            return f.read(), 200, { 'Content-Type': guess_type(path)[0] }
    except IOError:
        abort(404)

@app.template_filter('urlencode')
def urlencode_filter(s):
    """
    Filter to urlencode strings.
    """
    if type(s) == 'Markup':
        s = s.unescape()

    s = s.encode('utf8')
    s = urllib.quote_plus(s)

    return Markup(s)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=app_config.DEBUG)
