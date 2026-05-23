"""Half-hex substitution underlying the Socolar-Taylor monotile, with
binary chirality propagation.

What this generator produces
----------------------------
The 1-into-4 half-hex substitution from the Bielefeld Tilings Encyclopedia
(``/substitution/half-hex/``), attributed by Bielefeld to Grünbaum &
Shephard 1987 / Frettlöh 2002. Each prototile is an isosceles trapezoid
(half of a regular hexagon); each parent substitutes into 4 smaller
half-hexes (one in-place + three rotated by 120°, 180°, 240°).

Per Baake-Gähler-Grimm 2012 (arXiv:1210.3967), the bare half-hex
substitution is a topological factor of the Socolar-Taylor LI class:
the underlying geometric substitution is identical, with the full
Taylor tiling adding a 14-prototile labelling (7 hex colours A-G × 2
chiralities) on top. This generator carries the **chirality** layer
of that labelling — the binary L/R split — by flipping chirality on
the one substitution child that is geometrically reflected. Specifically:

- 3 of the 4 children (``in-place``, ``outer-left``, ``outer-right``)
  inherit the parent's chirality.
- 1 child (``paired`` — the one translated up and rotated by π) flips
  chirality. This child is the geometrically reflected one in the
  classical half-hex picture (Grünbaum-Shephard 1987 Fig. 10.1.7;
  Baake-Gähler-Grimm Fig. 1).

Both roots seed with the same chirality (``left``) so the central pair
forms one full chiral hexagon. The resulting depth-d cell counts
balance toward 50/50 L/R as the substitution iterates.

What this generator does NOT produce
------------------------------------
The full 14-state Taylor substitution (Socolar-Taylor 2011 Fig. 9 /
Baake-Gähler-Grimm 2012 Fig. 7) carries 7 hex colours alongside the
chirality bit; the colour transitions determine the exact R1 stripe
and R2 flag positions per hex. This generator implements **only** the
chirality bit. The 7-colour labelling and the per-hex R1/R2 marking
positions are not computed.

See ``docs/TILING_KNOWN_DEVIATIONS.md`` for the remaining gap.
"""

from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import (
    TAYLOR_HALF_HEX_LEFT_KIND,
    TAYLOR_HALF_HEX_RIGHT_KIND,
)
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

# Substitution children, with their roles. Roles:
#   - ``in-place``: scale 0.5, no rotation. Lower-centre of parent.
#   - ``paired``:   scale 0.5, rotated π, translated up. Upper of parent.
#                   This is the **reflected** child whose chirality is
#                   flipped relative to the parent.
#   - ``outer-left``:  scale 0.5, rotated 240°, translated left wing.
#   - ``outer-right``: scale 0.5, rotated 120°, translated right wing.
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

_CHIRALITY_FLIPPING_ROLES: frozenset[str] = frozenset({"paired"})


def _opposite_chirality(chirality: str) -> str:
    return "right" if chirality == "left" else "left"


def _kind_for_chirality(chirality: str) -> str:
    return TAYLOR_HALF_HEX_LEFT_KIND if chirality == "left" else TAYLOR_HALF_HEX_RIGHT_KIND


def _half_hex_children(node: SubstitutionChild, depth: int) -> tuple[SubstitutionChild, ...]:
    del depth
    # Default the parent's chirality to "left" so roots without an
    # explicit chirality_token still produce a deterministic subtree.
    parent_chirality = node.chirality_token or "left"
    children: list[SubstitutionChild] = []
    for transform, role in _HALF_HEX_CHILDREN:
        child_chirality = (
            _opposite_chirality(parent_chirality)
            if role in _CHIRALITY_FLIPPING_ROLES
            else parent_chirality
        )
        children.append(
            SubstitutionChild(
                "half-hex",
                transform,
                chirality_token=child_chirality,
                decoration_tokens=(f"substitution-role:{role}",),
            )
        )
    return tuple(children)


def _half_hex_leaf_templates(node: SubstitutionChild) -> tuple[SubstitutionLeafTemplate, ...]:
    chirality = node.chirality_token or "left"
    return (
        SubstitutionLeafTemplate(
            kind=_kind_for_chirality(chirality),
            id_prefix="taylor",
            vertices=_HALF_HEX_BASE_VERTICES,
            orientation_token=affine_orientation_token(
                node.transform,
                angle_step_degrees=60.0,
            ),
            chirality_token=chirality,
        ),
    )


def build_taylor_socolar_patch(patch_depth: int) -> AperiodicPatch:
    # The two roots together form one full hexagon at the patch centre,
    # so they share a single chirality (``left``). After substitution,
    # the ``paired`` child rule introduces ``right`` cells from depth 1
    # onward; cell counts balance toward 50/50 by depth ~5.
    root_scale = 2 ** int(patch_depth)
    return build_substitution_patch(
        patch_depth,
        root_items=(
            SubstitutionChild(
                "half-hex",
                scale(root_scale),
                chirality_token="left",
                decoration_tokens=("hex-half:upper",),
            ),
            SubstitutionChild(
                "half-hex",
                affine_multiply(rotation(math.pi), scale(root_scale)),
                chirality_token="left",
                decoration_tokens=("hex-half:lower",),
            ),
        ),
        expand_children=_half_hex_children,
        leaf_templates_for_label=_half_hex_leaf_templates,
    )
