"""Sketch for 2-uniform #16 variant 1 [3^3.4^2; 3^2.4.3.4].

Reference:
https://commons.wikimedia.org/wiki/File:2-uniform_n16.svg

The reference SVG uses relative path commands for most faces. The unit below
is a square repeat window from the canonical diagram, with minimal extra
right/top repeats for faces that straddle the finite patch boundary.
"""

from typing import Any

GEOMETRY = "uniform-2-16-v1-33344-33434"
LABEL = "2-uniform #16 variant 1 (3^3.4^2; 3^2.4.3.4)"
BASE_EDGE = 42.75
CELL_WIDTH = 202.295
CELL_HEIGHT = 202.295

FACES: list[dict[str, Any]] = [
    {
        "slot": "t00",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((180.92, 165.272), (202.295, 202.295), (159.545, 202.295)),
    },
    {
        "slot": "t01",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((143.897, 143.897), (180.92, 122.522), (180.92, 165.272)),
    },
    {
        "slot": "t02",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((101.147, 143.897), (143.897, 143.897), (122.522, 180.92)),
    },
    {
        "slot": "t03",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((143.897, 101.147), (180.92, 79.772), (180.92, 122.522)),
    },
    {
        "slot": "t04",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((58.398, 143.897), (101.147, 143.897), (79.772, 180.92)),
    },
    {
        "slot": "t05",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((21.375, 165.272), (42.75, 202.295), (0.0, 202.295)),
    },
    {
        "slot": "t06",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((159.545, 42.75), (202.295, 42.75), (180.92, 79.772)),
    },
    {
        "slot": "t07",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((122.522, 64.125), (143.897, 101.147), (101.147, 101.147)),
    },
    {
        "slot": "t08",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((21.375, 122.522), (58.398, 143.897), (21.375, 165.272)),
    },
    {
        "slot": "t09",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((79.772, 64.125), (101.147, 101.147), (58.398, 101.147)),
    },
    {
        "slot": "t10",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((122.522, 21.375), (159.545, 42.75), (122.522, 64.125)),
    },
    {
        "slot": "t11",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((21.375, 79.772), (58.398, 101.147), (21.375, 122.522)),
    },
    {
        "slot": "t12",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((42.75, 42.75), (79.772, 21.375), (79.772, 64.125)),
    },
    {
        "slot": "t13",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((122.522, -21.375), (159.545, 0.0), (122.522, 21.375)),
        "repeat_y_extra": 1,
    },
    {
        "slot": "t14",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((0.0, 42.75), (42.75, 42.75), (21.375, 79.772)),
    },
    {
        "slot": "t15",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((42.75, 0.0), (79.772, -21.375), (79.772, 21.375)),
        "repeat_y_extra": 1,
    },
    {
        "slot": "t16",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((101.147, 143.897), (122.522, 180.92), (79.772, 180.92)),
    },
    {
        "slot": "t17",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((143.897, 101.147), (180.92, 122.522), (143.897, 143.897)),
    },
    {
        "slot": "t18",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((21.375, 122.522), (58.398, 101.147), (58.398, 143.897)),
    },
    {
        "slot": "t19",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((79.772, 64.125), (122.522, 64.125), (101.147, 101.147)),
    },
    {
        "slot": "t20",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((-21.375, 165.272), (21.375, 165.272), (0.0, 202.295)),
        "repeat_x_extra": 1,
    },
    {
        "slot": "t21",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((122.522, 21.375), (159.545, 0.0), (159.545, 42.75)),
    },
    {
        "slot": "t22",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((0.0, 42.75), (21.375, 79.772), (-21.375, 79.772)),
        "repeat_x_extra": 1,
    },
    {
        "slot": "t23",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((42.75, 0.0), (79.772, 21.375), (42.75, 42.75)),
    },
    {
        "slot": "s24",
        "kind": "square",
        "prefix": "s",
        "vertices": (
            (101.147, 101.147),
            (143.897, 101.147),
            (143.897, 143.897),
            (101.147, 143.897),
        ),
    },
    {
        "slot": "s25",
        "kind": "square",
        "prefix": "s",
        "vertices": ((58.398, 101.147), (101.147, 101.147), (101.147, 143.897), (58.398, 143.897)),
    },
    {
        "slot": "s26",
        "kind": "square",
        "prefix": "s",
        "vertices": ((159.545, 0.0), (202.295, 0.0), (202.295, 42.75), (159.545, 42.75)),
    },
    {
        "slot": "s27",
        "kind": "square",
        "prefix": "s",
        "vertices": ((-21.375, 122.522), (21.375, 122.522), (21.375, 165.272), (-21.375, 165.272)),
        "repeat_x_extra": 1,
    },
    {
        "slot": "s28",
        "kind": "square",
        "prefix": "s",
        "vertices": ((79.772, 21.375), (122.522, 21.375), (122.522, 64.125), (79.772, 64.125)),
    },
    {
        "slot": "s29",
        "kind": "square",
        "prefix": "s",
        "vertices": ((-21.375, 79.772), (21.375, 79.772), (21.375, 122.522), (-21.375, 122.522)),
        "repeat_x_extra": 1,
    },
    {
        "slot": "s30",
        "kind": "square",
        "prefix": "s",
        "vertices": ((79.772, -21.375), (122.522, -21.375), (122.522, 21.375), (79.772, 21.375)),
        "repeat_y_extra": 1,
    },
    {
        "slot": "s31",
        "kind": "square",
        "prefix": "s",
        "vertices": ((0.0, 0.0), (42.75, 0.0), (42.75, 42.75), (0.0, 42.75)),
    },
    {
        "slot": "s32",
        "kind": "square",
        "prefix": "s",
        "vertices": ((143.897, 143.897), (180.92, 165.272), (159.545, 202.295), (122.522, 180.92)),
    },
    {
        "slot": "s33",
        "kind": "square",
        "prefix": "s",
        "vertices": ((21.375, 165.272), (58.398, 143.897), (79.772, 180.92), (42.75, 202.295)),
    },
    {
        "slot": "s34",
        "kind": "square",
        "prefix": "s",
        "vertices": ((122.522, 64.125), (159.545, 42.75), (180.92, 79.772), (143.897, 101.147)),
    },
    {
        "slot": "s35",
        "kind": "square",
        "prefix": "s",
        "vertices": ((42.75, 42.75), (79.772, 64.125), (58.398, 101.147), (21.375, 79.772)),
    },
]
