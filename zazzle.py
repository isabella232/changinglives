#!/usr/bin/env python

import os

import Image
import ImageDraw
import ImageFont

import app_config

def zazzlify_png(png_path, tumblr_id, name, location):
    """
    Add a footer and border to the PNG for Zazzle.
    """
    path, filename = os.path.split(png_path)
    zazzle_path = '%s/%s.png' % (path, tumblr_id)

    border = 128
    size = 2048
    text_color = (120, 120, 120)
    logo_height = 92
    logo_width = 274
    disclaimer = 'This design was created for the project She Works: Note To Self and printed in support of NPR. Create your own at: npr.org/sheworks'

    png = Image.open('/var/www/%s' % png_path)
    zazzle_png = Image.new('RGBA', (size + border * 2, size + border * 2), (0, 0, 0, 0))
    zazzle_png.paste(png, (border, border))

    draw = ImageDraw.Draw(zazzle_png)
    font_big = ImageFont.truetype('Knockout-29.otf', 50)
    font_small = ImageFont.truetype('Knockout-29.otf', 40)

    if name and location:
        attribution = 'By %s, %s' % (name, location)
    elif name:
        attribution = 'By %s' % name
    elif location:
        attribution = 'By Anonymous, %s' % location
    else:
        attribution = 'By Anonymous'

    attribution = attribution.upper()

    draw.text((border, border + size + 15), attribution, text_color, font=font_big)
    draw.text((border, border + size + 70), disclaimer, text_color, font=font_small)

    logo = Image.open('www/img/nprlogo-transparent.png')
    zazzle_png.paste(logo, (size + border - logo_width + 13, size + border + (border - logo_height) / 2))

    if app_config.DEPLOYMENT_TARGET == 'development':
        zazzle_png.show()
        print '/var/www/%s' % zazzle_path

    zazzle_png.save('/var/www/%s' % zazzle_path)


