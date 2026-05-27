"""Example sketch: Stein 14 monohedral convex pentagonal tiling.

Stein (1985). Completely determined: 2a=2c=d=e, A=90 deg, 2B+C=360,
C+E=180, sin(B) = (sqrt(57) - 3) / 8. p2 symmetry, 6-tile primitive
unit, 3-isohedral, non-edge-to-edge.

Demonstrates the LATTICE_SKEW_X field: Stein-14 sits on a genuine
skewed parallelogram lattice rather than the brick-alternating offset
that ROW_OFFSET_X covers. The sketch tool plumbs LATTICE_SKEW_X through
to the same _pattern_cells builder the backend uses, so the same
geometry that lands in periodic_face_patterns.json can be iterated
here first.

Run with:

    py tools/sketch_tiling.py tools/sketch_examples/stein_14_pentagonal.py

Coordinates are the same ones shipped in
backend/simulation/data/periodic_face_patterns.json (extracted by
porting Rolf Stein's original Java construction algorithm, rounded to
8 decimal places). The sketch validator's strict T-junction check will
flag this geometry because the irrational midpoint relationship can't
be enforced bit-exactly in float64 (~5e-7 drift). The geometry IS valid
in the catalog because topology_validation puts stein-14-pentagonal on
its _NON_EDGE_TO_EDGE_IRRATIONAL_GEOMETRIES allowlist; the sketch tool
doesn't (it's a sanity checker, not a topology validator).
"""

from typing import Any

GEOMETRY = "stein-14-pentagonal"
LABEL = "Stein 14 Pentagonal"
BASE_EDGE = 50.0
CELL_WIDTH = 278.39987995
CELL_HEIGHT = 224.63131168
LATTICE_SKEW_X = -153.02078259


def _tile(slot: str, verts: list[tuple[float, float]]) -> dict[str, Any]:
    return {"slot": slot, "kind": "stein14", "prefix": "p", "vertices": verts}


FACES = [
    _tile(
        "t0",
        [
            (16.02339558, 177.26834336),
            (143.60504845, 134.10611259),
            (191.67523669, 147.86318038),
            (131.98675869, 228.09587693),
            (32.04679263, 224.63131168),
        ],
    ),
    _tile(
        "t1",
        [
            (16.02339558, 177.26834336),
            (143.60504845, 134.10611259),
            (173.44928652, 93.98976433),
            (77.30890808, 66.47562877),
            (0.0, 129.90537503),
        ],
    ),
    _tile(
        "t2",
        [
            (301.03093766, 50.82753357),
            (173.44928652, 93.98976433),
            (143.60504845, 134.10611259),
            (239.74542585, 161.62024817),
            (317.05433405, 98.19050239),
        ],
    ),
    _tile(
        "t3",
        [
            (301.03093766, 50.82753357),
            (173.44928652, 93.98976433),
            (125.37909736, 80.23269654),
            (185.06757536, 0.0),
            (285.00754128, 3.46456525),
        ],
    ),
    _tile(
        "t4",
        [
            (239.74542585, 161.62024817),
            (202.68800557, 291.10694043),
            (164.03355147, 322.82181357),
            (131.98675869, 228.09587693),
            (191.67523669, 147.86318038),
        ],
    ),
    _tile(
        "t5",
        [
            (202.68800557, 291.10694043),
            (239.74542585, 161.62024817),
            (278.39987995, 129.90537503),
            (310.44667272, 224.63131168),
            (250.75819473, 304.86400822),
        ],
    ),
]
