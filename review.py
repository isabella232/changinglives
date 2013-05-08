#!/usr/bin/env python

import csv
from glob import glob
import re

from flask import Flask, render_template

import app_config
from render_utils import make_context

CSV_HEADERS = ['svg_url', 'status', 'tumblr_url']

app = Flask(app_config.PROJECT_NAME)

svg_map = {}
mapped_svg_urls = list()
unmapped_svg_urls = list()
mapped_tumblr_urls = list()
unmapped_tumblr_urls = list()

def setup():
    with open('data/review.csv') as f:
        reader = csv.DictReader(f, fieldnames=CSV_HEADERS)

        for row in reader:
            svg_map[row['svg_url']] = (row['status'], row['tumblr_url'])

            if row['tumblr_url']:
                mapped_svg_urls.append(row['svg_url'])
                mapped_tumblr_urls.append(row['tumblr_url'])
            else:
                unmapped_svg_urls.append(row['svg_url'])

    for svg_path in glob('/var/www/uploads/%s/*.svg' % app_config.PROJECT_SLUG):
        svg_url = svg_path.replace('/var/www', 'http://%s' % app_config.SERVERS[0])

        if svg_url in mapped_svg_urls:
            pass
        elif svg_url in  unmapped_svg_urls:
            pass
        else:
            svg_map[svg_url] = (False, '')
            unmapped_svg_urls.append(svg_url)

    with open(app_config.LOG_PATH) as f:
        log = list(f)

    for line in log:
        match = re.search('200 (http.*) reader', line)

        if not match:
            error_match = re.search('(http.*) reader', line)

            if not error_match:
                continue

            svg_url = error_match.group(1)
            svg_map[svg_url] = (True, '')

            try:
                unmapped_svg_urls.remove(svg_url)
            except:
                pass

            continue

        tumblr_url = match.group(1)

        unmapped_tumblr_urls.append(tumblr_url)

@app.route('/')
def review():
    tumblr_url = unmapped_tumblr_urls[0]
    svg_url = unmapped_svg_urls[0]

    context = make_context()
    context['tumblr_url'] = tumblr_url
    context['svg_url'] = svg_url

    return render_template('review.html', **context)

if __name__ == '__main__':
    setup()
    app.run(host='0.0.0.0', port=8002, debug=app_config.DEBUG)
