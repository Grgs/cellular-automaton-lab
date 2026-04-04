from __future__ import annotations

import math

from backend.simulation.aperiodic_substitution import (
    SubstitutionChild,
    SubstitutionLeafTemplate,
    build_substitution_patch,
)
from backend.simulation.aperiodic_support import (
    AFFINE_IDENTITY,
    AFFINE_REFLECT_X,
    Affine,
    AperiodicPatch,
    Vec,
    affine_multiply,
    rotation,
    scale,
    translation,
)


_SQRT3_OVER_2 = math.sqrt(3) / 2
_SPHINX_BASE_VERTICES = (
    Vec(-0.5, _SQRT3_OVER_2),
    Vec(0.5, _SQRT3_OVER_2),
    Vec(1.5, _SQRT3_OVER_2),
    Vec(2.5, _SQRT3_OVER_2),
    Vec(2.0, 0.0),
    Vec(1.0, 0.0),
    Vec(0.5, -_SQRT3_OVER_2),
    Vec(0.0, 0.0),
)


def _placement_transform(
    *,
    reflected: bool,
    rotation_turns: int,
    tx: float,
    ty: float,
) -> Affine:
    orientation = AFFINE_REFLECT_X if reflected else AFFINE_IDENTITY
    return affine_multiply(
        translation(tx, ty),
        affine_multiply(rotation(rotation_turns * (math.pi / 3)), orientation),
    )


_SPHINX_CHILD_TRANSFORMS = (
    affine_multiply(
        scale(0.5),
        _placement_transform(reflected=True, rotation_turns=0, tx=4.5, ty=_SQRT3_OVER_2),
    ),
    affine_multiply(
        scale(0.5),
        _placement_transform(reflected=True, rotation_turns=3, tx=1.5, ty=_SQRT3_OVER_2),
    ),
    affine_multiply(
        scale(0.5),
        _placement_transform(reflected=True, rotation_turns=0, tx=1.5, ty=_SQRT3_OVER_2),
    ),
    affine_multiply(
        scale(0.5),
        _placement_transform(reflected=False, rotation_turns=2, tx=1.5, ty=-_SQRT3_OVER_2),
    ),
)


def _sphinx_children(node: SubstitutionChild, depth: int) -> tuple[SubstitutionChild, ...]:
    del node, depth
    return tuple(SubstitutionChild("sphinx", transform) for transform in _SPHINX_CHILD_TRANSFORMS)


def _sphinx_leaf_templates(node: SubstitutionChild) -> tuple[SubstitutionLeafTemplate, ...]:
    del node
    return (
        SubstitutionLeafTemplate(
            kind="sphinx",
            id_prefix="sphinx",
            vertices=_SPHINX_BASE_VERTICES,
        ),
    )


def build_sphinx_patch(patch_depth: int) -> AperiodicPatch:
    return build_substitution_patch(
        patch_depth,
        root_items=(SubstitutionChild("sphinx", scale(2 ** int(patch_depth))),),
        expand_children=_sphinx_children,
        leaf_templates_for_label=_sphinx_leaf_templates,
    )
