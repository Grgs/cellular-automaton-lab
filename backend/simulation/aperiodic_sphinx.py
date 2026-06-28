from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import SPHINX_KIND
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
    affine_chirality_token,
    affine_multiply,
    affine_orientation_token,
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

_SPHINX_ROOT_TRANSFORM = _placement_transform(
    reflected=False,
    rotation_turns=2,
    tx=1.0,
    ty=-math.sqrt(3),
)

_SPHINX_COMPACT_PAIR_ROOT_TRANSFORMS = (
    _placement_transform(
        reflected=False,
        rotation_turns=2,
        tx=1.0,
        ty=0.0,
    ),
    _placement_transform(
        reflected=True,
        rotation_turns=5,
        tx=-0.5,
        ty=-math.sqrt(3) / 2,
    ),
)

_SPHINX_WIDE_PAIR_ROOT_TRANSFORM = _placement_transform(
    reflected=True,
    rotation_turns=1,
    tx=0.0,
    ty=0.0,
)


def _sphinx_root_items(patch_depth: int) -> tuple[SubstitutionChild, ...]:
    root_scale = scale(2 ** int(patch_depth))
    return (
        SubstitutionChild("sphinx", root_scale),
        SubstitutionChild("sphinx", affine_multiply(root_scale, _SPHINX_ROOT_TRANSFORM)),
    )


def _sphinx_compact_pair_root_items(patch_depth: int) -> tuple[SubstitutionChild, ...]:
    root_scale = scale(2 ** int(patch_depth))
    return tuple(
        SubstitutionChild("sphinx", affine_multiply(root_scale, transform))
        for transform in _SPHINX_COMPACT_PAIR_ROOT_TRANSFORMS
    )


def _sphinx_wide_pair_root_items(patch_depth: int) -> tuple[SubstitutionChild, ...]:
    root_scale = scale(2 ** int(patch_depth))
    return (
        SubstitutionChild("sphinx", root_scale),
        SubstitutionChild(
            "sphinx",
            affine_multiply(root_scale, _SPHINX_WIDE_PAIR_ROOT_TRANSFORM),
        ),
    )


def _canonical_sphinx_root_items(patch_depth: int) -> tuple[SubstitutionChild, ...]:
    return (SubstitutionChild("sphinx", scale(2 ** int(patch_depth))),)


def _sphinx_children(node: SubstitutionChild, depth: int) -> tuple[SubstitutionChild, ...]:
    del node, depth
    return tuple(SubstitutionChild("sphinx", transform) for transform in _SPHINX_CHILD_TRANSFORMS)


def _sphinx_leaf_templates(node: SubstitutionChild) -> tuple[SubstitutionLeafTemplate, ...]:
    # Sphinx tiles are placed at integer multiples of 60° rotation, optionally
    # reflected. Both axes carry visible structure: chirality flips the whole
    # tile shape, and rotation places the same shape at six possible
    # orientations. Setting both tokens from the resolved transform lets the
    # family-dead palette express the structure when cells are dead.
    return (
        SubstitutionLeafTemplate(
            kind=SPHINX_KIND,
            id_prefix="sphinx",
            vertices=_SPHINX_BASE_VERTICES,
            chirality_token=affine_chirality_token(node.transform),
            orientation_token=affine_orientation_token(
                node.transform,
                angle_step_degrees=60.0,
            ),
        ),
    )


def build_sphinx_patch(patch_depth: int) -> AperiodicPatch:
    return build_substitution_patch(
        patch_depth,
        root_items=_sphinx_root_items(patch_depth),
        expand_children=_sphinx_children,
        leaf_templates_for_label=_sphinx_leaf_templates,
    )


def build_sphinx_compact_pair_patch(patch_depth: int) -> AperiodicPatch:
    return build_substitution_patch(
        patch_depth,
        root_items=_sphinx_compact_pair_root_items(patch_depth),
        expand_children=_sphinx_children,
        leaf_templates_for_label=_sphinx_leaf_templates,
    )


def build_sphinx_wide_pair_patch(patch_depth: int) -> AperiodicPatch:
    return build_substitution_patch(
        patch_depth,
        root_items=_sphinx_wide_pair_root_items(patch_depth),
        expand_children=_sphinx_children,
        leaf_templates_for_label=_sphinx_leaf_templates,
    )


def _build_canonical_sphinx_patch(patch_depth: int) -> AperiodicPatch:
    return build_substitution_patch(
        patch_depth,
        root_items=_canonical_sphinx_root_items(patch_depth),
        expand_children=_sphinx_children,
        leaf_templates_for_label=_sphinx_leaf_templates,
    )
