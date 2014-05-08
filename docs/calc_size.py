#! /usr/bin/python

from math import ceil

THUMBNAIL_SIZE = 8902
TILE_SIZE = 8029
TILE_SIDE = 256
ZOOM_LEVELS = [0, 0.25, 0.5, 0.75, 1]

def get_size(original_size, width, height):
    T = original_size + THUMBNAIL_SIZE
    n = 0
    for z in ZOOM_LEVELS:
        n = n + (ceil(width * z / TILE_SIDE) * ceil(height * z / TILE_SIDE))
    T = T + n * TILE_SIZE
    print "Original size:", original_size, 'bytes'
    print "Resolution:", str(width) + 'x' + str(height)
    print "Total size:", T, 'bytes'
    print "Percentage extra:", (T - original_size) * 100 / T

types=[
    {"type": "DCM", "size": 4196978, "width": 2048, "height": 1024},
    {"type": "BMP", "size": 2180154, "width": 2048, "height": 1064},
    {"type": "TIFF", "size": 1622273, "width": 1920, "height": 1168}

]

for t in types:
    get_size(t["size"], t["width"], t["height"])
    print "-" * 70

