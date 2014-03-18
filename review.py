#!/usr/bin/env python

import csv
from glob import glob
import os
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

bad_tumblr_urls = list()
bad_svg_urls = list()

next_tumblr = 0

def setup():
    if os.path.exists('data/review.csv'):
        with open('data/review.csv') as f:
            reader = csv.DictReader(f, fieldnames=CSV_HEADERS)

            for row in reader:
                svg_map[row['svg_url']] = (row['status'], row['tumblr_url'])

                if row['tumblr_url']:
                    mapped_svg_urls.append(row['svg_url'])
                    mapped_tumblr_urls.append(row['tumblr_url'])
                else:
                    unmapped_svg_urls.append(row['svg_url'])

    for svg_path in sorted(glob('/var/www/uploads/%s/*.svg' % app_config.PROJECT_SLUG)):
        svg_url = svg_path.replace('/var/www', 'http://%s' % app_config.SERVERS[0])

        if svg_url in mapped_svg_urls:
            pass
        elif svg_url in unmapped_svg_urls:
            pass
        else:
            svg_map[svg_url] = (False, '')
            unmapped_svg_urls.append(svg_url)

    with open(app_config.LOG_PATH) as f:
        log = [l.strip() for l in f]

    for line in log:
        match = re.search('200 (http.*) reader', line)

        if not match:
            error_match = re.search('(http.*) reader', line)

            if not error_match:
                continue

            svg_url = error_match.group(1)
            svg_map[svg_url] = (True, '')

            if svg_url not in mapped_svg_urls:
                mapped_svg_urls.append(svg_url)
            
            if svg_url in unmapped_svg_urls:
                unmapped_svg_urls.remove(svg_url)

            continue

        tumblr_url = match.group(1)

	if tumblr_url not in mapped_tumblr_urls:
            unmapped_tumblr_urls.append(tumblr_url)

    global bad_tumblr_urls

    if os.path.exists('data/bad_tumblr_urls.csv'):
        with open('data/bad_tumblr_urls.csv') as f:
            bad_tumblr_urls = [l.strip() for l in f]	
        
	for url in bad_tumblr_urls:
            if url in unmapped_tumblr_urls:
                unmapped_tumblr_urls.remove(url)

    global bad_svg_urls

    if os.path.exists('data/bad_svg_urls.csv'):
        with open('data/bad_svg_urls.csv') as f:
            bad_svg_urls = [l.strip() for l in f]

        for url in bad_svg_urls:
            if url in unmapped_svg_urls:
                unmapped_svg_urls.remove(url)

    print 'Mapped SVG urls: %i' % len(mapped_svg_urls)
    print 'Unmapped SVG urls: %i' % len(unmapped_svg_urls)
    print 'Mapped Tumblr urls: %i' % len(mapped_tumblr_urls)
    print 'Unmapped Tumblr urls: %i' % len(unmapped_tumblr_urls)
    print 'Bad Tumblr urls: %i' % len(bad_tumblr_urls)
    print 'Bad SVG urls: %i' % len(bad_svg_urls)

def write_csv():
    with open('data/review.csv', 'w') as f:
        writer = csv.writer(f)

        for svg_url in mapped_svg_urls:
            writer.writerow([svg_url, svg_map[svg_url][0], svg_map[svg_url][1]])

        for svg_url in unmapped_svg_urls:
            writer.writerow([svg_url, False, ''])

def write_bad_tumblr_urls():
    global bad_tumblr_urls

    with open('data/bad_tumblr_urls.csv', 'w') as f:
        f.write('\n'.join(bad_tumblr_urls))
            
def write_bad_svg_urls():
    global bad_svg_urls

    with open('data/bad_svg_urls.csv', 'w') as f:
        f.write('\n'.join(bad_svg_urls))
 
@app.route('/')
def review():
    from flask import request

    global next_tumblr

    if request.args.get('match', None):
        svg_url = unmapped_svg_urls.pop(0)
        tumblr_url = unmapped_tumblr_urls.pop(next_tumblr)

        svg_map[svg_url] = (True, tumblr_url)

        mapped_svg_urls.append(svg_url)
        mapped_tumblr_urls.append(tumblr_url)

        write_csv()

        next_tumblr = 0
    elif request.args.get('next', None):
        next_tumblr += 1
    elif request.args.get('bad_tumblr', None):
        bad_tumblr_urls.append(unmapped_tumblr_urls.pop(next_tumblr))
        write_bad_tumblr_urls()
    elif request.args.get('bad_svg', None):
        bad_svg_urls.append(unmapped_svg_urls.pop(0))
        write_bad_svg_urls()

        next_tumblr = 0

    tumblr_url = unmapped_tumblr_urls[next_tumblr]
    svg_url = unmapped_svg_urls[0]

    context = make_context()
    context['tumblr_url'] = tumblr_url
    context['svg_url'] = svg_url

    return render_template('review.html', **context)

if __name__ == '__main__':
    setup()
    app.run(host='0.0.0.0', port=8002, debug=True)
