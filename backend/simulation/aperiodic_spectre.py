from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

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
    affine_apply,
    affine_multiply,
    rotation,
    translation,
    translation_to,
)


@dataclass(frozen=True)
class _SpectreTemplate:
    quad: tuple[Vec, Vec, Vec, Vec]
    children: tuple[tuple[str, Affine], ...]


_SPECTRE_LABELS = (
    "Gamma",
    "Delta",
    "Theta",
    "Lambda",
    "Xi",
    "Pi",
    "Sigma",
    "Phi",
    "Psi",
)
_SPECTRE_ROOT_LABEL = "Delta"
_SPECTRE_BASE_VERTICES = (
    Vec(0.0, 0.0),
    Vec(1.0, 0.0),
    Vec(1.5, -0.8660254037844386),
    Vec(2.366025403784439, -0.36602540378443865),
    Vec(2.366025403784439, 0.6339745962155614),
    Vec(3.366025403784439, 0.6339745962155614),
    Vec(3.866025403784439, 1.5),
    Vec(3.0, 2.0),
    Vec(2.133974596215561, 1.5),
    Vec(1.6339745962155614, 2.3660254037844393),
    Vec(0.6339745962155614, 2.3660254037844393),
    Vec(-0.3660254037844386, 2.3660254037844393),
    Vec(-0.866025403784439, 1.5),
    Vec(0.0, 1.0),
)
_SPECTRE_BASE_QUAD = (
    _SPECTRE_BASE_VERTICES[3],
    _SPECTRE_BASE_VERTICES[5],
    _SPECTRE_BASE_VERTICES[7],
    _SPECTRE_BASE_VERTICES[11],
)
_SPECTRE_GAMMA_SECONDARY_TRANSFORM = affine_multiply(
    translation(_SPECTRE_BASE_VERTICES[8].x, _SPECTRE_BASE_VERTICES[8].y),
    rotation(math.pi / 6),
)
_SPECTRE_SUBSTITUTION_RULES: dict[str, tuple[str | None, ...]] = {
    "Gamma": ("Pi", "Delta", None, "Theta", "Sigma", "Xi", "Phi", "Gamma"),
    "Delta": ("Xi", "Delta", "Xi", "Phi", "Sigma", "Pi", "Phi", "Gamma"),
    "Theta": ("Psi", "Delta", "Pi", "Phi", "Sigma", "Pi", "Phi", "Gamma"),
    "Lambda": ("Psi", "Delta", "Xi", "Phi", "Sigma", "Pi", "Phi", "Gamma"),
    "Xi": ("Psi", "Delta", "Pi", "Phi", "Sigma", "Psi", "Phi", "Gamma"),
    "Pi": ("Psi", "Delta", "Xi", "Phi", "Sigma", "Psi", "Phi", "Gamma"),
    "Sigma": ("Xi", "Delta", "Xi", "Phi", "Sigma", "Pi", "Lambda", "Gamma"),
    "Phi": ("Psi", "Delta", "Psi", "Phi", "Sigma", "Pi", "Phi", "Gamma"),
    "Psi": ("Psi", "Delta", "Psi", "Phi", "Sigma", "Psi", "Phi", "Gamma"),
}


def _build_spectre_supertile_child_transforms(quad: tuple[Vec, Vec, Vec, Vec]) -> tuple[Affine, ...]:
    transition_rules = (
        (60, 3, 1),
        (0, 2, 0),
        (60, 3, 1),
        (60, 3, 1),
        (0, 2, 0),
        (60, 3, 1),
        (-120, 3, 3),
    )
    transforms: list[Affine] = [AFFINE_IDENTITY]
    total_angle = 0.0
    rotation_transform = AFFINE_IDENTITY
    transformed_quad = list(quad)
    for angle, from_index, to_index in transition_rules:
        total_angle += angle
        if angle != 0:
            rotation_transform = rotation(math.radians(total_angle))
            transformed_quad = [
                affine_apply(rotation_transform, point)
                for point in quad
            ]
        translation_transform = translation_to(
            transformed_quad[to_index],
            affine_apply(transforms[-1], quad[from_index]),
        )
        transforms.append(affine_multiply(translation_transform, rotation_transform))
    return tuple(
        affine_multiply(AFFINE_REFLECT_X, transform)
        for transform in transforms
    )


_SPECTRE_BASE_TEMPLATES = {
    label: _SpectreTemplate(
        quad=_SPECTRE_BASE_QUAD,
        children=(
            (label, AFFINE_IDENTITY),
            (label, _SPECTRE_GAMMA_SECONDARY_TRANSFORM),
        )
        if label == "Gamma"
        else ((label, AFFINE_IDENTITY),),
    )
    for label in _SPECTRE_LABELS
}


def _spectre_supertile_quad(
    quad: tuple[Vec, Vec, Vec, Vec],
    child_transforms: tuple[Affine, ...],
) -> tuple[Vec, Vec, Vec, Vec]:
    return (
        affine_apply(child_transforms[6], quad[2]),
        affine_apply(child_transforms[5], quad[1]),
        affine_apply(child_transforms[3], quad[2]),
        affine_apply(child_transforms[0], quad[1]),
    )


@lru_cache(maxsize=None)
def _spectre_template_for_depth(label: str, depth: int) -> _SpectreTemplate:
    if depth <= 0:
        return _SPECTRE_BASE_TEMPLATES[label]

    prior_delta = _spectre_template_for_depth(_SPECTRE_ROOT_LABEL, depth - 1)
    child_transforms = _build_spectre_supertile_child_transforms(prior_delta.quad)
    return _SpectreTemplate(
        quad=_spectre_supertile_quad(prior_delta.quad, child_transforms),
        children=tuple(
            (child_label, child_transforms[index])
            for index, child_label in enumerate(_SPECTRE_SUBSTITUTION_RULES[label])
            if child_label is not None
        ),
    )


def _spectre_expand_children(node: SubstitutionChild, depth: int) -> tuple[SubstitutionChild, ...]:
    return tuple(
        SubstitutionChild(child_label, child_transform)
        for child_label, child_transform in _spectre_template_for_depth(node.label, depth).children
    )


def _spectre_leaf_templates(node: SubstitutionChild) -> tuple[SubstitutionLeafTemplate, ...]:
    return tuple(
        SubstitutionLeafTemplate(
            kind="spectre",
            id_prefix="spectre",
            vertices=_SPECTRE_BASE_VERTICES,
            transform=child_transform,
        )
        for _, child_transform in _SPECTRE_BASE_TEMPLATES[node.label].children
    )


def build_spectre_patch(patch_depth: int) -> AperiodicPatch:
    return build_substitution_patch(
        patch_depth,
        root_items=(SubstitutionChild(_SPECTRE_ROOT_LABEL, AFFINE_IDENTITY),),
        expand_children=_spectre_expand_children,
        leaf_templates_for_label=_spectre_leaf_templates,
    )
