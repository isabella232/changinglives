var GRID_BG_COLOR = '#787878';
var GRID_DOT_COLOR = '#444';
var GLYPH_COLOR = '#fff';
var FONT_NAME = 'Quicksand';
var FONT_COLOR = '#fff';
var FONT_SIZE = 120;
var LINE_HEIGHT = 110;
var X_DOTS = 64;
var GLYPH_RECT_MARGIN = 1 / 8;

var X_OFFSET = 16;
var Y_OFFSET = 36;

var GLYPH = [
    [0,0,0,0,0,0,0,0,0],
    [0,0,1,1,1,1,1,1,0],
    [0,1,0,1,0,0,0,0,0],
    [0,1,1,1,0,0,0,0,0],
    [0,1,0,0,1,0,0,0,0],
    [0,1,0,0,0,1,1,1,0],
    [0,1,0,0,0,1,1,1,0],
    [0,1,0,0,0,1,1,0,0],
    [0,0,0,0,0,0,0,0,0]
];

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
var font;
var grid_bg = null;
var grid_dots = [];
var glyph_rects = [];
var text_paths = [];

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

function render_grid() {
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
    grid_bg.attr({ fill: GRID_BG_COLOR, 'stroke-width': 0 });

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

function render_glyphs() {
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

    for (var y = 0; y < GLYPH.length; y++) {
        for (var x = 0; x < GLYPH[0].length; x++) {
            if (GLYPH[y][x]) {
                var lx = ((x + 1) * x_pitch) + x_margin;
                var ly = ((y + 1) * y_pitch) + y_margin;
                var lw = x_pitch - (x_margin * 2);
                var lh = y_pitch - (y_margin * 2);

                glyph_rects.push(preview.rect(lx, ly, lw, lh).attr({ fill: GLYPH_COLOR, 'stroke-width': 0 }));
            }
        }
    }
}

function render_text(text) {
    /*
     * Render the SVG text.
     */
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
        font = preview.getFont(FONT_NAME);
        
        render_grid();
        render_glyphs();
        render_text('');

        $('textarea[name="string"]').keyup(function(e) {
            render_text($(this).val());    
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
});
