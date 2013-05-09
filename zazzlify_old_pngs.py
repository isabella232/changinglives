#!/usr/bin/env python

import csv
import os

import app_config
from zazzle import zazzlify_png

with open('data/review_plus.csv') as f:
    rows = list(csv.reader(f))

for i, row in enumerate(rows):
    svg_url, status, tumblr_url, name, location = row

    if not tumblr_url:
        continue

    tumblr_id = tumblr_url.split('/')[-1] 

    svg_path = svg_url.replace('http://%s/' % app_config.SERVERS[0], '')
    png_path = svg_path.replace('svg', 'png')
    
    path, filename = os.path.split(png_path)
    zazzle_path = os.path.join(path, tumblr_id + '.png')

    print i, png_path
    print zazzle_path

    if os.path.exists('/var/www/' + zazzle_path):
        print 'Skipping'
        continue

    print zazzlify_png(png_path, tumblr_id, name, location)
