"""Canonical Socolar tiling (hexagon / square / 30-degree rhomb).

The Socolar tiling (Socolar, *Simple octagonal and dodecagonal quasicrystals*,
Phys. Rev. B 39, 1989) is the canonical 12-fold quasiperiodic tiling with
prototiles {regular hexagon, square, 30-degree rhomb}. Socolar described both
a decorated substitution and a cut-and-project scheme from the A2xA2 root
lattice; this module implements the cut-and-project construction as exact
acceptance-window tests in the Z[zeta12] module.

Construction. Coordinates are integer 4-tuples ``(a, b, c, d)`` representing
``a + b*zeta + c*zeta**2 + d*zeta**3`` with ``zeta = exp(i*pi/6)`` and
``zeta**4 = zeta**2 - 1``, at x2 scale so every tile center is integral (unit
edge = 2). The Galois star map ``zeta -> zeta**5`` sends a center to internal
space. Tile centers of each of 13 classes (6 rhomb orientations, 3 square
orientations, 2 hexagon orientation families x 2 deep-hole subtypes) live in a
coset of a rank-4 sublattice; a center hosts a tile exactly when its star
image lies in that class's CLOSED convex acceptance window (equilateral
triangles for the hexagon subtypes -- the A2 Delone up/down triangles --
parallelograms for rhombs, squares for squares; all window-edge normals at
multiples of 30 degrees, offsets exact in Q(sqrt(3))).

The window data below was extracted from the Tilings Encyclopedia's own
Socolar patch and verified in exact arithmetic: regenerating the patch region
from these windows reproduces the encyclopedia patch tile-for-tile (1876/1876
deep-interior tiles) and every coset point of the patch is classified
correctly. The translation gauge is the encyclopedia patch's own (singular,
symmetric) gamma; the closed-window convention resolves its singular worm
orbits exactly as the published patch does, so this generator produces the
same tiling member, extended to arbitrary radius.

Sources:
https://tilings.math.uni-bielefeld.de/substitution/socolar/
https://bendwavy.org/klitzing/quasi/socolar.htm
"""

from __future__ import annotations

import math
from collections import deque
from fractions import Fraction
from typing import Any

from backend.simulation.aperiodic_family_manifest import (
    SOCOLAR_HEXAGONAL_HEXAGON_KIND,
    SOCOLAR_HEXAGONAL_RHOMB_KIND,
    SOCOLAR_HEXAGONAL_SQUARE_KIND,
    SOCOLAR_HEXAGONAL_TILE_FAMILY,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    ExactPatchRecord,
    patch_from_exact_records,
)

_SQRT3 = math.sqrt(3.0)
_COS30 = _SQRT3 / 2.0

Module = tuple[int, int, int, int]


def _madd(v: Module, w: Module) -> Module:
    return (v[0] + w[0], v[1] + w[1], v[2] + w[2], v[3] + w[3])


def _msub(v: Module, w: Module) -> Module:
    return (v[0] - w[0], v[1] - w[1], v[2] - w[2], v[3] - w[3])


def _mmulz(v: Module) -> Module:
    a, b, c, d = v
    return (-d, a, b + d, c)


def _mrot(v: Module, k: int) -> Module:
    for _ in range(k % 12):
        v = _mmulz(v)
    return v


def _module_xy(v: Module) -> tuple[float, float]:
    a, b, c, d = v
    return (a + b * _COS30 + c * 0.5, b * 0.5 + c * _COS30 + d)


_UNIT = [_mrot((1, 0, 0, 0), k) for k in range(12)]

# Galois star map zeta -> zeta**5 (linear in the integer coefficients).
_STAR_1 = (1, 0, 0, 0)
_STAR_Z = _mrot((1, 0, 0, 0), 5)
_STAR_Z2 = _mrot((1, 0, 0, 0), 10)
_STAR_Z3 = _mrot((1, 0, 0, 0), 3)


def _star(v: Module) -> Module:
    a, b, c, d = v
    return (
        a * _STAR_1[0] + b * _STAR_Z[0] + c * _STAR_Z2[0] + d * _STAR_Z3[0],
        a * _STAR_1[1] + b * _STAR_Z[1] + c * _STAR_Z2[1] + d * _STAR_Z3[1],
        a * _STAR_1[2] + b * _STAR_Z[2] + c * _STAR_Z2[2] + d * _STAR_Z3[2],
        a * _STAR_1[3] + b * _STAR_Z[3] + c * _STAR_Z2[3] + d * _STAR_Z3[3],
    )


def _dot30_q3_times4(s: Module, k: int) -> tuple[int, int]:
    """4 * <star_xy(s), (cos 30k, sin 30k)> as exact (p, q) meaning p + q*sqrt3.

    star_xy(s) = (a + b*sqrt3/2 + c/2, b/2 + c*sqrt3/2 + d) for s=(a,b,c,d).
    cos/sin of 30-degree multiples lie in {0, +-1/2, +-sqrt3/2, +-1}, so the
    dot product is (p + q*sqrt3)/4 with integers p, q.
    """
    a, b, c, d = s
    # x = (4a + 2c)/4 + (2b)/4 * sqrt3 ; y = (2b + 4d)/4 + (2c)/4 * sqrt3
    xp, xq = 4 * a + 2 * c, 2 * b
    yp, yq = 2 * b + 4 * d, 2 * c
    k %= 12
    # cos(30k), sin(30k) as (p, q, denominator 2): value = (p + q*sqrt3)/2
    cos_pq = [
        (2, 0),
        (0, 1),
        (1, 0),
        (0, 0),
        (-1, 0),
        (0, -1),
        (-2, 0),
        (0, -1),
        (-1, 0),
        (0, 0),
        (1, 0),
        (0, 1),
    ][k]
    sin_pq = [
        (0, 0),
        (1, 0),
        (0, 1),
        (2, 0),
        (0, 1),
        (1, 0),
        (0, 0),
        (-1, 0),
        (0, -1),
        (-2, 0),
        (0, -1),
        (-1, 0),
    ][k]
    cp, cq = cos_pq
    sp, sq = sin_pq
    # (xp + xq*sqrt3)/4 * (cp + cq*sqrt3)/2 + (yp + yq*sqrt3)/4 * (sp + sq*sqrt3)/2
    # = [xp*cp + 3*xq*cq + yp*sp + 3*yq*sq + (xp*cq + xq*cp + yp*sq + yq*sp)*sqrt3]/8
    p8 = xp * cp + 3 * xq * cq + yp * sp + 3 * yq * sq
    q8 = xp * cq + xq * cp + yp * sq + yq * sp
    # result * 4 => divide by 2; parity is even for our inputs, but keep exact:
    if p8 % 2 or q8 % 2:
        # fall back to half-integer representation scaled by 8 (should not
        # happen for module inputs, guarded for safety)
        raise AssertionError("unexpected odd parity in exact dot product")
    return (p8 // 2, q8 // 2)


def _q3_leq(p: int, q: int, rp: int, rq: int) -> bool:
    """Exact test (p + q*sqrt3) <= (rp + rq*sqrt3)."""
    da = p - rp
    db = q - rq
    if da == 0 and db == 0:
        return True
    if da >= 0 and db >= 0:
        return False
    if da <= 0 and db <= 0:
        return True
    if da > 0:  # db < 0: da + db*sqrt3 <= 0  <=>  da*da <= 3*db*db
        return da * da <= 3 * db * db
    # da < 0, db > 0: <= 0  <=>  da*da >= 3*db*db
    return da * da >= 3 * db * db


# ---------------------------------------------------------------------------
# Acceptance-window data (extracted from the Tilings Encyclopedia patch and
# verified exactly; see module docstring). Offsets are 4x the exact values,
# i.e. window test: dot30_q3_times4(star(c), k) <= (p, q).
# ---------------------------------------------------------------------------

_CLASSES: tuple[dict[str, Any], ...] = (
    # hexagons: family 0 (edge parity 0), deep-hole subtypes up/down
    {
        "kind": "hexagon",
        "rot": 0,
        "base": (-18, -4, 32, 28),
        "basis": ((2, 0, 2, 0), (0, -2, 0, 4), (0, 0, 6, 0), (0, 0, 0, -6)),
        "window": {3: (92, -52), 7: (-64, 36), 11: (32, -12)},
    },
    {
        "kind": "hexagon",
        "rot": 0,
        "base": (-36, -26, 32, 40),
        "basis": ((2, 0, 2, 0), (0, -2, 0, 4), (0, 0, 6, 0), (0, 0, 0, -6)),
        "window": {1: (-60, 40), 5: (24, -16), 9: (96, -52)},
    },
    {
        "kind": "hexagon",
        "rot": 1,
        "base": (-36, -26, 30, 38),
        "basis": ((2, 0, -4, 0), (0, -2, 0, 4), (0, 0, -6, 0), (0, 0, 0, 6)),
        "window": {2: (96, -52), 6: (24, -16), 10: (-60, 40)},
    },
    {
        "kind": "hexagon",
        "rot": 1,
        "base": (-28, -18, 30, 34),
        "basis": ((2, 0, -4, 0), (0, -2, 0, 4), (0, 0, -6, 0), (0, 0, 0, 6)),
        "window": {0: (32, -12), 4: (-64, 36), 8: (92, -52)},
    },
    # rhombs: orientation classes by acute-edge direction pair (mod 6)
    {
        "kind": "rhomb",
        "rot": 0,
        "base": (-1, 17, 34, 18),
        "basis": ((-2, 0, -2, 0), (0, -2, 0, -2), (0, 0, 6, 0), (0, 0, 0, 6)),
        "window": {0: (28, -10), 5: (20, -14), 6: (20, -14), 11: (28, -10)},
    },
    {
        "kind": "rhomb",
        "rot": 5,
        "base": (-19, -5, 34, 29),
        "basis": ((-2, 0, -2, 0), (0, -2, 0, -2), (0, 0, -6, 0), (0, 0, 0, 6)),
        "window": {0: (28, -10), 1: (-64, 42), 6: (20, -14), 7: (-68, 38)},
    },
    {
        "kind": "rhomb",
        "rot": 1,
        "base": (-26, -11, 33, 32),
        "basis": ((2, 0, -4, 0), (0, 2, 0, -4), (0, 0, 6, 0), (0, 0, 0, 6)),
        "window": {4: (-68, 38), 5: (20, -14), 10: (-64, 42), 11: (28, -10)},
    },
    {
        "kind": "rhomb",
        "rot": 2,
        "base": (-36, -28, 29, 39),
        "basis": ((2, 0, -4, 0), (0, 2, 0, -4), (0, 0, -6, 0), (0, 0, 0, 6)),
        "window": {3: (88, -50), 4: (-68, 38), 9: (92, -50), 10: (-64, 42)},
    },
    {
        "kind": "rhomb",
        "rot": 3,
        "base": (-15, 0, 29, 25),
        "basis": ((2, 0, -4, 0), (0, -2, 0, -2), (0, 0, -6, 0), (0, 0, 0, 6)),
        "window": {2: (92, -50), 3: (88, -50), 8: (88, -50), 9: (92, -50)},
    },
    {
        "kind": "rhomb",
        "rot": 4,
        "base": (-35, -25, 33, 39),
        "basis": ((2, 0, 2, 0), (0, -2, 0, -2), (0, 0, -6, 0), (0, 0, 0, 6)),
        "window": {1: (-64, 42), 2: (92, -50), 7: (-68, 38), 8: (88, -50)},
    },
    # squares: orientation classes by edge direction mod 3
    {
        "kind": "square",
        "rot": 0,
        "base": (-33, -22, 32, 39),
        "basis": ((2, 0, -4, 0), (0, -2, 0, 4), (0, 0, 6, 0), (0, 0, 0, -6)),
        "window": {0: (28, -8), 3: (88, -48), 6: (20, -12), 9: (92, -48)},
    },
    {
        "kind": "square",
        "rot": 1,
        "base": (-35, -23, 33, 38),
        "basis": ((2, 0, 2, 0), (0, -2, 0, -2), (0, 0, -6, 0), (0, 0, 0, 6)),
        "window": {2: (92, -48), 5: (20, -12), 8: (88, -48), 11: (28, -8)},
    },
    {
        "kind": "square",
        "rot": 2,
        "base": (-26, -13, 33, 33),
        "basis": ((2, 0, 2, 0), (0, -2, 0, -2), (0, 0, -6, 0), (0, 0, 0, 6)),
        "window": {1: (-64, 44), 4: (-68, 40), 7: (-68, 40), 10: (-64, 44)},
    },
)

_PUBLIC_KIND = {
    "hexagon": SOCOLAR_HEXAGONAL_HEXAGON_KIND,
    "square": SOCOLAR_HEXAGONAL_SQUARE_KIND,
    "rhomb": SOCOLAR_HEXAGONAL_RHOMB_KIND,
}
_ID_CODE = {"hexagon": "hx", "square": "sq", "rhomb": "rh"}


# Prototiles centered at the origin at x2 scale (unit edge = 2): vertex
# offsets from the tile center, CCW. Derived from the canonical prototiles
# (rhomb acute vertex at origin with edges zeta^0, zeta^1; square edges
# zeta^0, zeta^3; regular hexagon) by subtracting the center.
def _centered_prototile(kind: str) -> tuple[Module, ...]:
    if kind == "rhomb":
        verts = [(0, 0, 0, 0), _UNIT[0], _madd(_UNIT[0], _UNIT[1]), _UNIT[1]]
    elif kind == "square":
        verts = [(0, 0, 0, 0), _UNIT[0], _madd(_UNIT[0], _UNIT[3]), _UNIT[3]]
    else:
        verts = [(0, 0, 0, 0)]
        for k in (0, 2, 4, 6, 8):
            verts.append(_madd(verts[-1], _UNIT[k]))
    doubled: list[Module] = [(2 * v[0], 2 * v[1], 2 * v[2], 2 * v[3]) for v in verts]
    total = (0, 0, 0, 0)
    for v in doubled:
        total = _madd(total, v)
    n = len(doubled)
    center: Module = (total[0] // n, total[1] // n, total[2] // n, total[3] // n)
    if tuple(x * n for x in center) != total:
        raise AssertionError("prototile center is not integral at x2 scale")
    return tuple(_msub(v, center) for v in doubled)


_CENTERED = {kind: _centered_prototile(kind) for kind in ("rhomb", "square", "hexagon")}

# Physical half-extent of the generated ball, in tile-edge units, per depth.
_BASE_RADIUS = 4.0
_RADIUS_PER_DEPTH = 0.75

# Star-space bound: all windows fit inside |star_xy| <= 5 (x2 units) around
# the origin with margin; used to bound the coset enumeration in 4D.
_STAR_BOUND = 8.0


def _reduced_base(spec: dict[str, Any]) -> Module:
    """A coset point near the origin in physical space whose star image stays
    near the class window (the embedded base is a far-away literature-patch
    center). Solves the real 4x4 system (physical -> 0, star -> star(base))
    over the basis, rounds, and polishes greedily."""
    base = spec["base"]
    basis = spec["basis"]
    sx0, sy0 = _module_xy(_star(base))

    def cost(c: Module) -> float:
        x, y = _module_xy(c)
        sx, sy = _module_xy(_star(c))
        return math.hypot(x, y) + 3.0 * math.hypot(sx - sx0, sy - sy0)

    # linear solve for coefficients n minimizing phys(base + sum n_i b_i) = 0
    # and star displacement = 0 (4 equations, 4 unknowns)
    rows = []
    for b in basis:
        bx, by = _module_xy(b)
        bsx, bsy = _module_xy(_star(b))
        rows.append([bx, by, bsx, bsy])
    bx0, by0 = _module_xy(base)
    target = [-bx0, -by0, 0.0, 0.0]
    # Gaussian elimination on the transposed system A^T n = target
    mat = [[rows[j][i] for j in range(4)] + [target[i]] for i in range(4)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda r: abs(mat[r][col]))
        mat[col], mat[pivot] = mat[pivot], mat[col]
        if abs(mat[col][col]) < 1e-12:
            continue
        for r in range(4):
            if r != col and abs(mat[r][col]) > 0:
                f = mat[r][col] / mat[col][col]
                mat[r] = [a - f * b for a, b in zip(mat[r], mat[col], strict=True)]
    coeffs = [round(mat[i][4] / mat[i][i]) if abs(mat[i][i]) > 1e-12 else 0 for i in range(4)]
    current = base
    for n, b in zip(coeffs, basis, strict=True):
        current = _madd(current, tuple(n * u for u in b))
    # greedy polish
    improved = True
    while improved:
        improved = False
        for b in basis:
            for sign in (1, -1):
                cand = _madd(current, tuple(sign * u for u in b))
                if cost(cand) < cost(current):
                    current = cand
                    improved = True
    return current


def _class_tiles(
    spec: dict[str, Any], radius_units: float
) -> list[tuple[Module, tuple[Module, ...]]]:
    """All accepted centers of one class within the physical radius, with
    exact vertex tuples."""
    window = spec["window"]
    base = spec["reduced_base"]
    basis = spec["basis"]
    r2 = 2.0 * radius_units + 4.0
    seen = {base}
    queue = deque((base,))
    out = []
    proto = tuple(_mrot(v, spec["rot"]) for v in _CENTERED[spec["kind"]])
    while queue:
        c = queue.popleft()
        x, y = _module_xy(c)
        s = _star(c)
        sx, sy = _module_xy(s)
        if math.hypot(x, y) <= r2 and math.hypot(sx, sy) <= _STAR_BOUND:
            accepted = all(_q3_leq(*_dot30_q3_times4(s, k), *pq) for k, pq in window.items())
            if accepted and math.hypot(x, y) <= 2.0 * radius_units:
                out.append((c, tuple(_madd(v, c) for v in proto)))
            for b in basis:
                for sign in (1, -1):
                    n = _madd(c, tuple(sign * u for u in b))
                    if n not in seen:
                        seen.add(n)
                        queue.append(n)
    return out


# Rational stand-in for sqrt(3), accurate to 1e-30. Vertex coordinates are
# (integer + integer * sqrt3) / 4 in tile-edge units; substituting this
# rational keeps the map injective for any realistic patch (a collision would
# need coefficients of order 1e30) while float conversion stays exact to
# double precision. Exact edge identity therefore matches exactly the true
# geometric edge identity.
_SQRT3_RATIONAL = Fraction(1732050807568877293527446341506, 10**30)


def _exact_vertex(v: Module) -> tuple[Fraction, Fraction]:
    """x2-module point -> exact rational plane coordinates at x8 unit scale
    (multiply by float_scale=0.125 for tile-edge units)."""
    a, b, c, d = v
    x = Fraction(2 * (2 * a + c)) + Fraction(2 * b) * _SQRT3_RATIONAL
    y = Fraction(2 * (b + 2 * d)) + Fraction(2 * c) * _SQRT3_RATIONAL
    return (x, y)


def _orientation_token(kind: str, rot: int) -> str:
    if kind == "hexagon":
        return str((rot % 2) * 30)
    if kind == "square":
        return str((rot % 3) * 30)
    return str((rot % 6) * 30)


def socolar_hexagonal_radius(patch_depth: int) -> float:
    return _BASE_RADIUS + _RADIUS_PER_DEPTH * max(0, int(patch_depth))


def build_socolar_hexagonal_patch(patch_depth: int) -> AperiodicPatch:
    """Build the canonical Socolar patch: all tiles whose centers lie within
    the depth-scaled radius of the origin, cut-and-project selected."""
    depth = max(0, int(patch_depth))
    radius = socolar_hexagonal_radius(depth)

    for spec in _CLASSES:
        if "reduced_base" not in spec:
            spec["reduced_base"] = _reduced_base(spec)

    records: list[ExactPatchRecord] = []
    for spec in _CLASSES:
        for center, verts in _class_tiles(spec, radius):
            records.append(
                {
                    "id": (
                        f"sxh:{_ID_CODE[spec['kind']]}:"
                        f"{center[0]}:{center[1]}:{center[2]}:{center[3]}"
                    ),
                    "kind": _PUBLIC_KIND[spec["kind"]],
                    "vertices": tuple(_exact_vertex(v) for v in verts),
                    "tile_family": SOCOLAR_HEXAGONAL_TILE_FAMILY,
                    "orientation_token": _orientation_token(spec["kind"], spec["rot"]),
                    "chirality_token": None,
                    "decoration_tokens": None,
                }
            )
    return patch_from_exact_records(depth, records, float_scale=0.125)
