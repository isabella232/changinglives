#!/usr/bin/env python

import csv
import os

import app_config
from public_app import zazzlify_png

with open('data/review_plus.csv') as f:
    rows = list(csv.reader(f))

for row in rows:
    svg_url, status, tumblr_url, name, location = row

    svg_path = svg_url.replace('http://%s' % app_config.SERVERS[0], '/var/www/uploads')
    path, filename = os.path.split(svg_path)
    zazzle_path = os.path.join(path, 'zazzle_' + filename.replace('svg', 'png'))

    print svg_path
    print zazzle_path

    if os.path.exists(zazzle_path):
        print 'Skipping'
        continue

        #zazzlify_png(png_path, name, location)
