var GRID_DOT_COLOR = '#444';
var GLYPH_COLOR = '#fff';
var GLYPH_RECT_MARGIN = 1 / 8;
var FONT_NAMES = ['Roboto Condensed', 'Snippet', 'Noto Serif', 'Quicksand'];
var FONT_COLOR = '#fff';
var FONT_SIZE = 120;
var LINE_HEIGHT = 110;
var X_DOTS = 64;

var X_OFFSET = 16;
var Y_OFFSET = 36;

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

var width;
var height;
var fonts = [];
var grid_bg = null;
var grid_dots = [];
var glyph_rects = [];
var text_paths = [];

var current_grid = '#787878';
var current_glyphs = 'flower-corner';
var current_font = 'Roboto Condensed';
var current_text = '';

function trimMessages(){
    $("body.index-page .post .message").each(function(i,v){
        var message = $(v);
        message.text(message.text().substring(0,80) + "...");
    });
}

function toggle_header() {
    $b.toggleClass('modal-open');
}

function resize_window() {
    var new_height = $form.height() - $project_hdr.height();
    $project_wrap.height(new_height);
}

function render_grid(color) {
    /*
     * Render the SVG background grid.
     */
    if (grid_bg) {
        grid_bg.remove();
    }

    for (var i = 0; i < grid_dots.length; i++) {
        grid_dots[i].remove();
    }

    grid_bg = preview.rect(0, 0, width, height);
    grid_bg.attr({ fill: color, 'stroke-width': 0 });

    var y_dots = X_DOTS * (height / width)
    var x_pitch = width / X_DOTS;
    var y_pitch = height / y_dots;
    
    grid_dots = [];

    for (var x = 1; x < X_DOTS; x++) {
        for (var y = 1; y < y_dots; y++) {
            grid_dots.push(preview.circle(x * x_pitch, y * y_pitch, 1).attr({ fill: GRID_DOT_COLOR, 'stroke-width': 0 }));
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

    var y_dots = X_DOTS * (height / width)
    var x_pitch = width / X_DOTS;
    var y_pitch = height / y_dots;
    var x_margin = x_pitch * GLYPH_RECT_MARGIN;
    var y_margin = y_pitch * GLYPH_RECT_MARGIN;

    var glyphs = GLYPH_SETS[glyph_set];

    for (var i = 0; i < glyphs.length; i++) {
        var glyph = glyphs[i];
        var bitmap = glyph.bitmap;
        var w = bitmap[0].length;
        var h = bitmap.length;

        if (glyph.align == 'left') {
            var x_base = glyph.grid_offset;
        } else if (glyph.align == 'right') {
           var x_base = (X_DOTS - glyph.grid_offset) - w; 
        }

        if (glyph.valign == 'top') {
            var y_base = glyph.grid_offset;
        } else if (glyph.valign == 'bottom') {
            var y_base = (y_dots - glyph.grid_offset) - h; 
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
                    var lx = ((x + x_base) * x_pitch) + x_margin;
                    var ly = ((y + y_base) * y_pitch) + y_margin;
                    var lw = x_pitch - (x_margin * 2);
                    var lh = y_pitch - (y_margin * 2);

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
    var base_width = (width / 2) - X_OFFSET;

    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];

        var text_path = preview.print(0, 0, line, font, FONT_SIZE, 'middle');
        
        var bbox = text_path.getBBox();
        text_path.translate(base_width - (bbox.width / 2), 0)
        
        text_paths.push(text_path);
    }

    var base_height = (height / 2) - (lines_height / 2 - Y_OFFSET)

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
        alert('Your browser doesn\'t support SVG, so this will be broken.');
    } else {
        preview = new Raphael(preview_div, $preview.width(), $preview.height());

        width = $preview.width();
        height = $preview.height();

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
            current_grid = label.css('background-color');

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

            render_grid(current_grid);
            render_glyphs(current_glyphs);
            render_text(current_font, current_text);
        });

        $('input[name="ornament"]').change(function(e) {
            var val = $(this).val();
            console.log(val);
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

            btn.text('Sending, please wait...');
            // btn.attr('disabled', 'disabled');

            $('input[name="image"]').val($preview.html());

            return true;
        });
    }

    // Event handlers
    $modal_btn.click(function() {
        toggle_header();
    });

    $project_hdr.click(function() {
        toggle_header();
    });

    $modal_bg.click(function() {
        toggle_header();
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

    function render_popular_posts(posts){
        var $popular = $('<div id="popular"></div>');
        var $container = $('.index-page #post-wrap');
        $popular.html(posts);
        $container.prepend($popular).prepend('<h2>Popular Advice</h2>');
    }

    $.ajax({
        //url: "http://stage-apps.npr.org/changing-lives/aggregates.json",
        url: "http://127.0.0.1:8000/js/aggregates.json",
        context: document.body,
        jsonp: false,
        dataType: 'jsonp',
        crossDomain: true,
        jsonpCallback: "aggregateCallback"
    }).done(function(data) {
        render_popular_posts(data.popular);
    });
});

