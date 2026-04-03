from __future__ import annotations

import math

from backend.simulation.aperiodic_support import (
    Affine,
    AperiodicPatch,
    PatchRecord,
    Vec,
    affine_apply,
    affine_multiply,
    id_from_transform,
    patch_from_records,
    polygon_centroid,
    rotation,
    rounded_point,
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


def _collect_half_hex_leaf_transforms(
    depth: int,
    transform: Affine,
    leaves: list[Affine],
) -> None:
    if depth <= 0:
        leaves.append(transform)
        return
    for child_transform in _HALF_HEX_CHILD_TRANSFORMS:
        _collect_half_hex_leaf_transforms(
            depth - 1,
            affine_multiply(transform, child_transform),
            leaves,
        )


def build_taylor_socolar_patch(patch_depth: int) -> AperiodicPatch:
    root_scale = 2 ** int(patch_depth)
    root_transforms = (
        scale(root_scale),
        affine_multiply(rotation(math.pi), scale(root_scale)),
    )
    leaf_transforms: list[Affine] = []
    for root_transform in root_transforms:
        _collect_half_hex_leaf_transforms(int(patch_depth), root_transform, leaf_transforms)

    records: list[PatchRecord] = []
    for transform in leaf_transforms:
        vertices = tuple(affine_apply(transform, vertex) for vertex in _HALF_HEX_BASE_VERTICES)
        records.append(
            {
                "id": id_from_transform("taylor", transform),
                "kind": "taylor-half-hex",
                "center": rounded_point(polygon_centroid(vertices)),
                "vertices": tuple(rounded_point(vertex) for vertex in vertices),
            }
        )
    return patch_from_records(patch_depth, records)
