var BITMAPS = {
    BIRD_OF_PREY: [
    [0,0,0,0,0,0,0,0,0],
    [0,0,1,1,1,1,1,1,0],
    [0,1,0,1,0,0,0,0,0],
    [0,1,1,1,0,0,0,0,0],
    [0,1,0,0,1,0,0,0,0],
    [0,1,0,0,0,1,1,1,0],
    [0,1,0,0,0,1,1,1,0],
    [0,1,0,0,0,1,1,0,0],
    [0,0,0,0,0,0,0,0,0]
]};


var GLYPH_SETS = {
    'no-border': [],
    'flower-corner': [{ 
        bitmap: BITMAPS.BIRD_OF_PREY,
        align: 'left',
        valign: 'top',
        grid_offset: 1,
        invert: false,
        vinvert: false
    }, {
        bitmap: BITMAPS.BIRD_OF_PREY,
        align: 'right',
        valign: 'top',
        grid_offset: 1,
        invert: true,
        vinvert: false
    }],
    'swash-border': [],
    'triangle-border': []
}
