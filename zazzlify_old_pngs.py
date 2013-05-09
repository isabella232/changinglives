#!/usr/bin/env python

import csv

import app_config
from public_app import zazzlify_png

with open('data/review_plus.csv') as f:
    rows = list(csv.reader(f))

for row in rows:
    svg_url, status, tumblr_url, name, location = row

    tumblr_id = tumblr_url.split('/')[-1] 

    svg_path = svg_url.replace('http://%s/' % app_config.SERVERS[0], '')
    png_path = svg_path.replace('svg', 'png')

    zazzlify_png(png_path, tumblr_id, name, location)
