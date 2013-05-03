#!/usr/bin/env python

import datetime
import logging
import os
import re
import shlex
import subprocess
import time
import urllib

from flask import Flask, redirect, render_template
import Image
import ImageDraw
import ImageFont
from jinja2.filters import do_mark_safe
from tumblpy import Tumblpy
from tumblpy import TumblpyError
from werkzeug import secure_filename

import app_config

app = Flask(app_config.PROJECT_NAME)
app.config['PROPAGATE_EXCEPTIONS'] = True

os.environ['TZ'] = 'US/Eastern'
time.tzset()

logger = logging.getLogger('tumblr')
file_handler = logging.FileHandler('/var/log/%s.log' % app_config.PROJECT_SLUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


@app.route('/%s/errors/' % app_config.PROJECT_SLUG, methods=['GET'])
def _errors():
    """
    Parses the log for errors.
    Returns them to the page.
    """
    context = {}
    context['errors'] = []
    with open('/var/log/%s.log' % app_config.PROJECT_SLUG) as logfile:
        for line in logfile:
            if 'ERROR' in line:
                line_dict = {}
                try:
                    total_items = len(line.split())
                    line_dict['date'] = line.split()[0]
                    line_dict['time'] = line.split()[1]
                    line_dict['type'] = '%s %s' % (line.split()[2], line.split()[3])
                    line_dict['message'] = ''
                    current_item = 4
                    for item in line.split():
                        if current_item <= total_items:
                            line_dict['message'] += '%s ' % item
                            current_item += 1
                    line_dict['message'] = line_dict['message'].strip()
                    context['errors'].append(line_dict)
                except:
                    pass

    context['errors'] = sorted(context['errors'], key=lambda item: item['date'], reverse=True)
    return render_template('error.html', **context)


@app.route('/%s/test/' % app_config.PROJECT_SLUG, methods=['GET'])
def _test():
    """
    Returns the time. Proves the app server is running.
    """
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@app.route('/%s/' % app_config.PROJECT_SLUG, methods=['POST'])
def _post_to_tumblr():
    """
    Handles the POST to Tumblr.
    """
    def strip_html(value):
        """
        Strips HTML from a string.
        """
        try:
            return re.compile(r'</?\S([^=]*=(\s*"[^"]*"|\s*\'[^\']*\'|\S*)|[^>])*?>', re.IGNORECASE).sub('', value)
        except TypeError:
            return None

    def strip_breaks(value):
        """
        Converts newlines, returns and other breaks to <br/>.
        """
        value = re.sub(r'\r\n|\r|\n', '\n', value)
        return value.replace('\n', do_mark_safe('<br/>'))

    # Request is a global. Import it down here where we need it.
    from flask import request

    name = strip_html(request.form.get('signed_name', None))
    location = strip_html(request.form.get('location', None))

    svg = request.form.get('image', None)
    svg = re.sub('(height|width)=\"[0-9]+\"', '', svg, 2)

    # Fix for duplicate namespaces in IE...
    if svg.count('xmlns="http://www.w3.org/2000/svg"') > 1:
        svg = svg.replace('xmlns="http://www.w3.org/2000/svg"', '', 1)

    file_path = '/uploads/%s/%s_%s' % (
        app_config.PROJECT_SLUG,
        str(time.mktime(datetime.datetime.now().timetuple())).replace('.', ''),
        secure_filename(name.replace(' ', '-'))
    )

    svg_path = file_path + '.svg'
    png_path = file_path + '.png'

    with open('/var/www%s' % svg_path, 'wb') as f:
        f.write(svg.encode('utf-8'))

    if app_config.DEPLOYMENT_TARGET == 'development':
        command = 'cairosvg /var/www/%s -f png -o /var/www%s' % (svg_path, png_path)
    else:
        command = '/home/ubuntu/apps/changing-lives/virtualenv/bin/cairosvg /var/www%s -f png -o /var/www%s' % (svg_path, png_path)

    args = shlex.split(command)

    try:
        # When used with check_output(), subprocess will return errors to a "CalledProcessError."
        # This is nice. I'm also piping stderr to stdout so we can see a trace if we want.
        # I am not logging the trace because we need the log to be single lines for continuity.
        subprocess.check_output(args, stderr=subprocess.STDOUT)

    except subprocess.CalledProcessError, e:
        # If we encounter a CalledProcessError, log the output.
        logger.error('%s %s %s http://%s%s reader(%s) (times in EST)' % (
            'ERROR', '500', e, app_config.SERVERS[0], svg_path, name))

        # These bits build a nicer error page that has the real stack trace on it.
        context = {}
        context['title'] = 'CairoSVG is unhappy.'
        context['message'] = e.output
        return render_template('500.html', **context)

    zazzle_png_path = zazzlify_png(png_path, name, location)

    image_url = 'http://%s%s' % (app_config.SERVERS[0], zazzle_png_path)
    zazzle_url = app_config.ZAZZLE_URL % urllib.quote(image_url)

    context = {
        'name': name,
        'location': location,
        'zazzle_url': zazzle_url
    }

    caption = render_template('caption.html', **context)

    secrets = app_config.get_secrets()

    t = Tumblpy(
        app_key=secrets['TUMBLR_APP_KEY'],
        app_secret=secrets['TUMBLR_APP_SECRET'],
        oauth_token=secrets['TUMBLR_OAUTH_TOKEN'],
        oauth_token_secret=secrets['TUMBLR_OAUTH_TOKEN_SECRET'])

    params = {
        "type": "photo",
        "caption": caption,
        "tags": app_config.TUMBLR_TAGS,
        "source": "http://%s%s" % (app_config.SERVERS[0], png_path)
    }

    try:
        tumblr_post = t.post('post', blog_url=app_config.TUMBLR_URL, params=params)
        tumblr_url = u"http://%s/%s" % (app_config.TUMBLR_URL, tumblr_post['id'])
        logger.info('200 %s reader(%s) (times in EST)' % (tumblr_url, name))

        return redirect(tumblr_url, code=301)

    except TumblpyError, e:
        logger.error('%s %s http://%s%s reader(%s) (times in EST)' % (
            e.error_code, e.msg, app_config.SERVERS[0], svg_path, name))
        context = {}
        context['title'] = 'Tumblr error'
        context['message'] = '%s\n%s' % (e.error_code, e.msg)
        return render_template('500.html', **context)

    return redirect('%s#posts' % tumblr_url, code=301)


def zazzlify_png(png_path, name, location):
    """
    Add a footer and border to the PNG for Zazzle.
    """
    path, filename = os.path.split(png_path)
    zazzle_path = '%s/zazzle_%s' % (path, filename)

    border = 128
    size = 2048

    png = Image.open('/var/www/%s' % png_path)
    zazzle_png = Image.new('RGBA', (size + border * 2, size + border * 2), (0, 0, 0, 0))
    zazzle_png.paste(png, (border, border))

    draw = ImageDraw.Draw(zazzle_png)
    font = ImageFont.truetype('NotoSerif-Regular.ttf', 50)
    draw.rectangle((border, size + border, border + size, size + border * 2), fill='rgb(0,0,0)')

    draw.text((border, border + size), '%s, %s' % (name, location), (255, 255, 255), font=font)
    draw.text((border, border + size + 64), 'she-works.tumblr.com', (255, 255, 255), font=font)

    zazzle_png.show()
    zazzle_png.save('/var/www/%s' % zazzle_path)

    print '/var/www/%s' % zazzle_path

    return zazzle_path


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=app_config.DEBUG)
