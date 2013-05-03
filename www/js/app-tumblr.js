var SVG_WIDTH = 2048;
var SVG_HEIGHT = 2048;

var GRID_X_TICKS = 64;
var GRID_Y_TICKS = GRID_X_TICKS * (SVG_HEIGHT / SVG_WIDTH)
var GRID_X_PITCH = SVG_WIDTH / GRID_X_TICKS;
var GRID_Y_PITCH = SVG_HEIGHT / GRID_Y_TICKS;
var GRID_DOT_COLOR = '#000';
var GRID_DOT_OPACITY = 0.15;

var GLYPH_COLOR = '#fff';
var GLYPH_RECT_MARGIN = 1 / 8;
var GLYPH_X_MARGIN = GRID_X_PITCH * GLYPH_RECT_MARGIN;
var GLYPH_Y_MARGIN = GRID_Y_PITCH * GLYPH_RECT_MARGIN;

var FONT_NAMES = ['Roboto Condensed', 'Snippet', 'Noto Serif', 'Quicksand'];
var FONT_COLOR = '#fff';
var FONT_SIZE = 220;
var LINE_HEIGHT = FONT_SIZE;

var X_OFFSET = {
    'Roboto Condensed': 20,
    'Snippet': 25,
    'Noto Serif': 0,
    'Quicksand': 30
};
var Y_OFFSET = {
    'Roboto Condensed': 150,
    'Snippet': 150,
    'Noto Serif': 150,
    'Quicksand': 150
};

var $b;
var $form;
var $modal_bg;
var $modal_btn;
var $project_hdr;
var $project_wrap;
var $project_iframe;
var $tumblr_form;
var $preview;
var preview_div;
var preview;

var fonts = [];
var grid_bg = null;
var grid_dots = [];
var glyph_rects = [];
var text_paths = [];

var current_grid = '#17807e';
var current_glyphs = 'flower-corner';
var current_font = 'Roboto Condensed';
var current_text = 'Your\nadvice\nhere';

function trimMessages(){
    $("body.index-page .post .message").each(function(i,v){
        var message = $(v);
        message.text(message.text().substring(0,80) + "...");
    });
}

function toggle_header() {
    $b.toggleClass('modal-open');
    resize_window();
}

function resize_window() {
    var new_height = $form.height() - $project_hdr.height();
    $project_wrap.height(new_height);

    var width = $preview.width();
    var height = width;

    $preview.height(height);

    if(typeof(preview) !== 'undefined'){
        preview.setSize(width, height);
    }
}

function render_grid(color) {
    /*
     * Render the SVG background grid.
     */
    if (grid_bg) {
        grid_bg.attr({ fill: color });
    } else {
        grid_bg = preview.rect(0, 0, SVG_WIDTH, SVG_HEIGHT);
        grid_bg.attr({ fill: color, 'stroke-width': 0 });

        grid_dots = [];

        for (var x = 1; x < GRID_X_TICKS; x++) {
            for (var y = 1; y < GRID_Y_TICKS; y++) {
                grid_dots.push(preview.circle(x * GRID_X_PITCH, y * GRID_Y_PITCH, 5).attr({ fill: GRID_DOT_COLOR, 'fill-opacity': GRID_DOT_OPACITY, 'stroke-width': 0 }));
            }
        }
    }
}

function render_glyphs(glyph_set) {
    /*
     * Render the SVG ornament glyphs.
     */
    for (var i = 0; i < glyph_rects.length; i++) {
        glyph_rects[i].remove();
    }

    glyph_rects = [];

    var glyphs = GLYPH_SETS[glyph_set];

    for (var i = 0; i < glyphs.length; i++) {
        var glyph = glyphs[i];
        var bitmap = glyph.bitmap;
        var w = bitmap[0].length;
        var h = bitmap.length;

        if (glyph.align == 'left') {
            var x_base = glyph.grid_offset_x;
        } else if (glyph.align == 'right') {
            var x_base = (GRID_X_TICKS - glyph.grid_offset_x) - w;
        } else if (glyph.align == 'center') {
            var x_base = ((GRID_X_TICKS / 2) + glyph.grid_offset_x) - (w / 2);
        }

        if (glyph.valign == 'top') {
            var y_base = glyph.grid_offset_y;
        } else if (glyph.valign == 'bottom') {
            var y_base = (GRID_Y_TICKS - glyph.grid_offset_y) - h;
        } else if (glyph.valign == 'middle') {
            var y_base = ((GRID_Y_TICKS / 2) + glyph.grid_offset_y) - (h / 2);
        }

        for (var y = 0; y < h; y++) {
            for (var x = 0; x < w; x++) {
                if (glyph.invert) {
                    var x2 = w - (x + 1);
                } else {
                    var x2 = x;
                }

                if (glyph.vinvert) {
                    var y2 = h - (y + 1);
                } else {
                    var y2 = y;
                }

                if (bitmap[y2][x2]) {
                    var lx = ((x + x_base) * GRID_X_PITCH) + GLYPH_X_MARGIN;
                    var ly = ((y + y_base) * GRID_Y_PITCH) + GLYPH_Y_MARGIN;
                    var lw = GRID_X_PITCH - (GLYPH_X_MARGIN * 2);
                    var lh = GRID_Y_PITCH - (GLYPH_Y_MARGIN * 2);

                    glyph_rects.push(preview.rect(lx, ly, lw, lh).attr({ fill: GLYPH_COLOR, 'stroke-width': 0 }));
                }
            }
        }
    }
}

function render_text(font_name, text) {
    /*
     * Render the SVG text.
     */
    var font = fonts[font_name];

    for (var i = 0; i < text_paths.length; i++) {
        text_paths[i].remove();
    }

    text_paths = [];

    var lines = text.split('\n');
    var lines_height = LINE_HEIGHT * lines.length;
    var base_width = (SVG_WIDTH / 2) - X_OFFSET[font_name];

    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];

        var text_path = preview.print(0, 0, line, font, FONT_SIZE, 'middle');

        var bbox = text_path.getBBox();
        text_path.translate(base_width - (bbox.width / 2), 0);

        text_paths.push(text_path);
    }

    var base_height = (SVG_HEIGHT / 2) - (lines_height / 2 - Y_OFFSET[font_name]);

    for (var i = 0; i < text_paths.length; i++) {
        var text_path = text_paths[i];

        text_path.translate(0, base_height + LINE_HEIGHT * i);
        text_path.attr({ fill: FONT_COLOR });
    }
}

$(function() {
    // jQuery refs
    $b = $('body');
    $form = $('#project-form');
    $modal_bg = $('.modal-bg');
    $modal_btn = $('#modal-btn');
    $project_hdr = $form.find('.hdr');
    $project_wrap = $form.find('.project-iframe-wrapper');
    $project_iframe = $form.find('iframe');
    $tumblr_form = $("#tumblr-form");
    $preview = $('#preview');
    preview_div = $preview[0];

    // Setup Raphael
    if (!Raphael.svg) {
        $svg_warning = $('<div class="svg-warning"><h2>We\'re sorry, you can\'t make a sign using this web browser.<br /> Try using Google Chrome or Mozilla Firefox. <br><span class="close btn">Okay</span></h2></div>');
        $form.find('.tumblr-form-wrap')
            .addClass('opaque')
            .before($svg_warning);
        $svg_warning.on('click', function(){
            $b.removeClass('modal-open');
        });
        $form.find('input, button').each(function(){
            $(this).attr("disabled", "disabled");
        });
    } else {
        var width = $preview.width();
        var height = $preview.height();

        preview = new Raphael(preview_div, width, height);
        preview.setViewBox(0, 0, SVG_WIDTH, SVG_HEIGHT);

        for (var i = 0; i < FONT_NAMES.length; i++) {
            fonts[FONT_NAMES[i]] = preview.getFont(FONT_NAMES[i]);
        }

        render_grid(current_grid);
        render_glyphs(current_glyphs);
        render_text(current_font, current_text);

        $('textarea[name="string"]').keyup(function(e) {
            current_text = $(this).val();
            render_text(current_font, current_text);
        });

        $('input[name="color"]').change(function(e) {
            var val = $(this).val();
            var label = $('label[for="' + $(this).attr('id') + '"]');

            $('.form-color label').removeClass('active');
            label.addClass('active');
            current_grid = label.find('span').css('background-color');

            render_grid(current_grid);
            render_glyphs(current_glyphs);
            render_text(current_font, current_text);
        });

        $('input[name="typeface"]').change(function(e) {
            var val = $(this).val();
            var label = $('label[for="' + $(this).attr('id') + '"]');

            $('.form-typeface label').removeClass('active');
            label.addClass('active');
            current_font = val;

            render_glyphs(current_glyphs);
            render_text(current_font, current_text);
        });

        $('input[name="ornament"]').change(function(e) {
            var val = $(this).val();
            var label = $('label[for="' + $(this).attr('id') + '"]');

            $('.form-ornament label').removeClass('active');
            label.addClass('active');
            current_glyphs = val;

            render_grid(current_grid);
            render_glyphs(current_glyphs);
            render_text(current_font, current_text);
        });

        $tumblr_form.submit(function(e) {
            var btn = $('.form-submit button');

            btn.addClass('loading')
               .text('Sending, please wait...')
               .attr('disabled', 'disabled');

            $('input[name="image"]').val($preview.html());

            return true;
        });

        $tumblr_form.find('input').keypress(function(e) {
            if (e.which == 13) {
                return false;
            }
        });
    }

    // Event handlers
    $modal_btn.on('click', function() {
        toggle_header();
    });

    $project_hdr.on('click', function() {
        toggle_header();
    });

    $modal_bg.on('click', function() {
        toggle_header();
    });

    $(document).keyup(function(e) {
      if (e.keyCode == 27) { $b.removeClass('modal-open'); }
    });

    // Startup
    trimMessages();

    $(window).resize(resize_window);
    resize_window();

    if (/iP(hone|od|ad)/.test(navigator.platform)) {
        var v = (navigator.appVersion).match(/OS (\d+)_(\d+)_?(\d+)?/);
        var version = parseInt(v[1]);

        if (version < 6) {
            $('.tumblr-form').html('<p>Sorry, iOS versions older than 6 are not supported.');
        }
    }
    $('#posts, #post-wrap h2').hide();

    $.ajax({
        url: "http://" + APP_CONFIG.S3_BUCKETS[0] + "/" + APP_CONFIG.PROJECT_SLUG + "/live-data/aggregates.json",
        context: document.body,
        jsonp: false,
        dataType: 'jsonp',
        crossDomain: true,
        jsonpCallback: "aggregateCallback"
    }).done(function(data) {
        if ($b.hasClass('index-page')){
            $container = $('#post-wrap h2');
        } else {
            $container = $('#footer');
        }
        $popular = $('<div id="popular"></div>');
        $popular.html(data.popular).insertBefore($container).prepend('<h2>Popular Advice</h2>');


        $popular.find(".post").fadeTo(0,0);

        var delay = 0;
        $popular.show();
        $popular.find(".post").each(function(i) {
          delay = (i + 1) * 350;
          $(this).delay(delay).fadeTo(750,1);
        });
        $('#posts, #post-wrap h2').show();
    });
});

