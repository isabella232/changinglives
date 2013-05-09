#!/usr/bin/env python

import csv
import re

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

    if not tumblr_url:
	row.append('')
	row.append('')
        continue

    post_id = tumblr_url.split('/')[-1]

    try:
        print post_id
        post = t.get('posts', blog_url=app_config.TUMBLR_URL, params={ 'id': post_id })
    except TumblpyError, e:
        print 'GET error %s: %s %s' % (post_id, e.error_code, e.msg)
        row.append('')
        row.append('')
	continue

    caption = post['posts'][0]['caption']

    attribution = re.search('<p class=\"signature-name\">(.*)<\/p>', caption)

    details = attribution.group(1) 

    if ',' in details:
        name, location = details.split(',', 1)
    else:
        name = details
        location = ''

    name = name.strip()
    location = location.strip()

    print name
    print location

    row.append(name)
    row.append(location)

with open('data/review_plus.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerows(rows)
            
