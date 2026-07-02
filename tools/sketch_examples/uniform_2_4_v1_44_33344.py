"""Sketch for 2-uniform #4 variant 1 [4^4; 3^3.4^2].

Reference:
https://commons.wikimedia.org/wiki/File:2-uniform_n4.svg

The Wikimedia diagram is skew-periodic. This sketch uses a 2-cell-wide
package of the primitive skew repeat so the rendered board is not a narrow
strip while preserving the exact #4 variant geometry.
"""

from typing import Any

GEOMETRY = "uniform-2-4-v1-44-33344"
LABEL = "2-uniform #4 variant 1 (4^4; 3^3.4^2)"
BASE_EDGE = 43.048
CELL_WIDTH = 86.096
CELL_HEIGHT = 123.376
LATTICE_SKEW_X = 21.524

FACES: list[dict[str, Any]] = [
    {
        "slot": "t00",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((86.096, 43.048), (107.62, 80.328), (64.572, 80.328)),
    },
    {
        "slot": "t01",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((43.048, 43.048), (64.572, 80.328), (21.524, 80.328)),
    },
    {
        "slot": "t02",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((43.048, 43.048), (86.096, 43.048), (64.572, 80.328)),
    },
    {
        "slot": "t03",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((0.0, 43.048), (43.048, 43.048), (21.524, 80.328)),
    },
    {
        "slot": "s04",
        "kind": "square",
        "prefix": "s",
        "vertices": (
            (64.572, 80.328),
            (107.62, 80.328),
            (107.62, 123.376),
            (64.572, 123.376),
        ),
    },
    {
        "slot": "s05",
        "kind": "square",
        "prefix": "s",
        "vertices": (
            (21.524, 80.328),
            (64.572, 80.328),
            (64.572, 123.376),
            (21.524, 123.376),
        ),
    },
    {
        "slot": "s06",
        "kind": "square",
        "prefix": "s",
        "vertices": (
            (43.048, 0.0),
            (86.096, 0.0),
            (86.096, 43.048),
            (43.048, 43.048),
        ),
    },
    {
        "slot": "s07",
        "kind": "square",
        "prefix": "s",
        "vertices": ((0.0, 0.0), (43.048, 0.0), (43.048, 43.048), (0.0, 43.048)),
    },
]
