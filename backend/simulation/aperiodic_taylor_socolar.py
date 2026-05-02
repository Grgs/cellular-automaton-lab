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
_HALF_HEX_CHILD_TRANSFORMS: tuple[Affine, ...] = (
    scale(0.5),
    affine_multiply(translation(0.0, _SQRT3 / 2), affine_multiply(rotation(math.pi), scale(0.5))),
    affine_multiply(translation(-0.75, _SQRT3 / 4), affine_multiply(rotation((4 * math.pi) / 3), scale(0.5))),
    affine_multiply(translation(0.75, _SQRT3 / 4), affine_multiply(rotation((2 * math.pi) / 3), scale(0.5))),
)


def _half_hex_children(node: SubstitutionChild, depth: int) -> tuple[SubstitutionChild, ...]:
    del node, depth
    return tuple(SubstitutionChild("half-hex", transform) for transform in _HALF_HEX_CHILD_TRANSFORMS)


def _half_hex_leaf_templates(node: SubstitutionChild) -> tuple[SubstitutionLeafTemplate, ...]:
    # Taylor-Socolar tiles do not carry chirality (the half-hex shape itself is
    # reflection-symmetric), but the substitution rotates each half-hex by
    # multiples of 60° as it descends. Setting orientation_token from the
    # combined transform groups cells by visual rotation so the family-dead
    # palette can colour rotationally-related half-hexes the same way.
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
    root_scale = 2 ** int(patch_depth)
    return build_substitution_patch(
        patch_depth,
        root_items=(
            SubstitutionChild("half-hex", scale(root_scale)),
            SubstitutionChild("half-hex", affine_multiply(rotation(math.pi), scale(root_scale))),
        ),
        expand_children=_half_hex_children,
        leaf_templates_for_label=_half_hex_leaf_templates,
    )
