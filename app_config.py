#!/usr/bin/env python

"""
Project-wide application configuration.

DO NOT STORE SECRETS, PASSWORDS, ETC. IN THIS FILE.
They will be exposed to users. Use environment variables instead.
"""

import os

PROJECT_NAME = 'She Works: Her Money'
PROJECT_SLUG = 'changing-lives'
REPOSITORY_NAME = 'changinglives'
CONFIG_NAME = PROJECT_SLUG.replace('-', '').upper()

PROJECT_CREDITS = 'Jeremy Bowers, Danny DeBelius, Kitty Eisele, Christopher Groskopf, Alyson Hurt and Selena Simmons-Duffin / NPR'
PROJECT_SHORTLINK = 'npr.org/sheworks'

PRODUCTION_S3_BUCKETS = ['apps.npr.org', 'apps2.npr.org']
PRODUCTION_SERVERS = ['54.214.20.225']

STAGING_S3_BUCKETS = ['stage-apps.npr.org']
STAGING_SERVERS = ['54.214.20.232']

S3_BUCKETS = []
SERVERS = []
DEBUG = True

NUMBER_OF_AGGREGATES = 15

PROJECT_DESCRIPTION = 'Financial wisdom you can print! Create a motivational poster and hang it somewhere with NPR\'s She Works project.'
SHARE_URL = 'http://%s/%s/' % (PRODUCTION_S3_BUCKETS[0], PROJECT_SLUG)

COPY_GOOGLE_DOC_KEY = '0AlXMOHKxzQVRdHZuX1UycXplRlBfLVB0UVNldHJYZmc'

TWITTER = {
    'TEXT': PROJECT_NAME,
    'URL': SHARE_URL
}

FACEBOOK = {
    'TITLE': PROJECT_NAME,
    'URL': SHARE_URL,
    'DESCRIPTION': PROJECT_DESCRIPTION,
    'IMAGE_URL': '',
    'APP_ID': '138837436154588'
}

NPR_DFP = {
    'STORY_ID': '171421875',
    'TARGET': '\/news_politics;storyid=171421875'
}

GOOGLE_ANALYTICS_ID = 'UA-5828686-4'

TUMBLR_TAGS = 'women, advice, image'
TUMBLR_FILENAME = 'www/live-data/%s-data.json' % PROJECT_SLUG
TUMBLR_POST_LIMIT = 150

ADMIN_EMAILS = ['sheworks@npr.org']

LOG_PATH = '/var/log/%s.log' % PROJECT_SLUG

def get_secrets():
    """
    A method for accessing our secrets.
    """
    secrets = [
        '%s_TUMBLR_APP_KEY' % CONFIG_NAME,
        '%s_TUMBLR_OAUTH_TOKEN' % CONFIG_NAME,
        '%s_TUMBLR_OAUTH_TOKEN_SECRET' % CONFIG_NAME,
        '%s_TUMBLR_APP_SECRET' % CONFIG_NAME,
    ]

    secrets_dict = {}

    for secret in secrets:
        # Saves the secret with the old name.
        secrets_dict[secret.replace('%s_' % CONFIG_NAME, '')] = os.environ.get(secret, None)

    return secrets_dict

def configure_targets(deployment_target):
    """
    Configure deployment targets. Abstracted so this can be
    overriden for rendering before deployment.
    """
    global S3_BUCKETS
    global SERVERS
    global DEBUG
    global TUMBLR_URL
    global TUMBLR_BLOG_ID

    if deployment_target == 'production':
        S3_BUCKETS = PRODUCTION_S3_BUCKETS
        SERVERS = PRODUCTION_SERVERS
        DEBUG = False
        TUMBLR_URL = 'she-works.tumblr.com'
        TUMBLR_BLOG_ID = 'she-works'

    elif deployment_target == 'staging':
        S3_BUCKETS = STAGING_S3_BUCKETS
        SERVERS = STAGING_SERVERS
        DEBUG = True
        TUMBLR_URL = 'staging-%s.tumblr.com' % PROJECT_SLUG
        TUMBLR_BLOG_ID = 'staging-%s' % PROJECT_SLUG

    else:
        blog_id = os.environ.get('DEVELOPMENT_BLOG_ID', 'staging-%s' % PROJECT_SLUG)
        S3_BUCKETS = ['127.0.0.1:8000']
        SERVERS = ['127.0.0.1:8001']
        DEBUG = True
        TUMBLR_URL = '%s.tumblr.com' % blog_id
        TUMBLR_BLOG_ID = blog_id

DEPLOYMENT_TARGET = os.environ.get('DEPLOYMENT_TARGET', None)

configure_targets(DEPLOYMENT_TARGET)
