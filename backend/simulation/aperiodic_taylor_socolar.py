"""Half-hex substitution that underlies the Taylor-Socolar monotile.

What this generator produces
----------------------------
The 1-into-4 half-hex substitution from the Bielefeld Tilings Encyclopedia
(``/substitution/half-hex/``), attributed by Bielefeld to Grünbaum &
Shephard 1987 / Frettlöh 2002. Each prototile is an isosceles trapezoid
(half of a regular hexagon); each parent substitutes into 4 smaller
half-hexes (one in-place + three rotated by 120°, 180°, 240°). Two
half-hexes pair into one full regular hexagon, giving the limit-periodic
hexagonal hierarchy that underlies the published Taylor-Socolar tile.

What this generator does NOT produce
------------------------------------
The published Socolar-Taylor monotile (Socolar & Taylor 2011,
arXiv:1009.1419) is a regular hexagon decorated with R1 stripes + R2
flags + chirality coloring; the decorations and matching rules are
what force aperiodicity. Without those decorations the bare half-hex
substitution can be assembled periodically. This implementation
generates the underlying half-hex hierarchy but does NOT compute or
render the R1/R2 markings or per-hex chirality from the paper. The
``decoration_tokens`` stamped on each cell carry the substitution
hierarchy (parent-pair id, which-half) needed by a future renderer to
attach the R1/R2 decorations, but the markings themselves are not
materialized.

See ``docs/TILING_KNOWN_DEVIATIONS.md`` for the gap statement.
"""

from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import TAYLOR_HALF_HEX_KIND
from backend.simulation.aperiodic_substitution import (
    SubstitutionChild,
    SubstitutionLeafTemplate,
    build_substitution_patch,
)
from backend.simulation.aperiodic_support import (
    Affine,
    AperiodicPatch,
    Vec,
    affine_multiply,
    affine_orientation_token,
    rotation,
    scale,
    translation,
)


_SQRT3 = math.sqrt(3)
_HALF_HEX_BASE_VERTICES = (
    Vec(-1.0, 0.0),
    Vec(-0.5, _SQRT3 / 2),
    Vec(0.5, _SQRT3 / 2),
    Vec(1.0, 0.0),
)

# Per-child decoration tokens. Each child of a half-hex covers a specific
# position inside its parent: one stays in-place (``substitution-role:in-place``),
# one is paired across the long edge (``substitution-role:paired``), and two
# sit on the parent's outer corners (``substitution-role:outer-left`` and
# ``substitution-role:outer-right``). The corresponding rotations are
# 0°, 180°, 240°, 120°. These tokens accumulate from parent to child via
# the substitution machinery, so a depth-d cell carries a path-length-d
# trail describing how it was reached. That trail is the substitution-tree
# address a future renderer would need to attach the canonical Socolar-
# Taylor R1/R2 decorations.
_HALF_HEX_CHILDREN: tuple[tuple[Affine, str], ...] = (
    (scale(0.5), "in-place"),
    (
        affine_multiply(
            translation(0.0, _SQRT3 / 2), affine_multiply(rotation(math.pi), scale(0.5))
        ),
        "paired",
    ),
    (
        affine_multiply(
            translation(-0.75, _SQRT3 / 4),
            affine_multiply(rotation((4 * math.pi) / 3), scale(0.5)),
        ),
        "outer-left",
    ),
    (
        affine_multiply(
            translation(0.75, _SQRT3 / 4),
            affine_multiply(rotation((2 * math.pi) / 3), scale(0.5)),
        ),
        "outer-right",
    ),
)


def _half_hex_children(node: SubstitutionChild, depth: int) -> tuple[SubstitutionChild, ...]:
    del node, depth
    return tuple(
        SubstitutionChild(
            "half-hex",
            transform,
            decoration_tokens=(f"substitution-role:{role}",),
        )
        for transform, role in _HALF_HEX_CHILDREN
    )


def _half_hex_leaf_templates(node: SubstitutionChild) -> tuple[SubstitutionLeafTemplate, ...]:
    # The bare half-hex prototile is reflection-symmetric, so the cell's
    # geometric shape carries no intrinsic chirality. The published
    # Taylor-Socolar tile (which is the pair of half-hexes forming a
    # regular hexagon, decorated with R1 stripes + R2 flags) IS chiral,
    # but that chirality lives in the decorations we don't yet
    # materialize. ``orientation_token`` groups cells by visual rotation
    # so the family-dead palette can colour rotationally-related
    # half-hexes the same way.
    return (
        SubstitutionLeafTemplate(
            kind=TAYLOR_HALF_HEX_KIND,
            id_prefix="taylor",
            vertices=_HALF_HEX_BASE_VERTICES,
            orientation_token=affine_orientation_token(
                node.transform,
                angle_step_degrees=60.0,
            ),
        ),
    )


def build_taylor_socolar_patch(patch_depth: int) -> AperiodicPatch:
    # The two roots form one full hexagon at the patch centre: the
    # upper half (no rotation) + the lower half (rotated by π). They
    # carry the ``hex-half`` decoration token so descendants know
    # which side of the pair they descended from.
    root_scale = 2 ** int(patch_depth)
    return build_substitution_patch(
        patch_depth,
        root_items=(
            SubstitutionChild(
                "half-hex",
                scale(root_scale),
                decoration_tokens=("hex-half:upper",),
            ),
            SubstitutionChild(
                "half-hex",
                affine_multiply(rotation(math.pi), scale(root_scale)),
                decoration_tokens=("hex-half:lower",),
            ),
        ),
        expand_children=_half_hex_children,
        leaf_templates_for_label=_half_hex_leaf_templates,
    )
