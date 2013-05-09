#!/usr/bin/env python

import csv
import os

import app_config
from public_app import zazzlify_png

with open('data/review_plus.csv') as f:
    rows = list(csv.reader(f))

for row in rows:
    svg_url, status, tumblr_url, name, location = row

    svg_path = svg_url.replace('http://%s/' % app_config.SERVERS[0], '')
    png_path = svg_path.replace('svg', 'png')
    path, filename = os.path.split(png_path)
    zazzle_path = os.path.join(path, 'zazzle_' + filename)

    print zazzle_path

    zazzlify_png(png_path, name, location)
