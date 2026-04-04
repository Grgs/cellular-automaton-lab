from __future__ import annotations

import cmath
import itertools
import math
from dataclasses import dataclass

from backend.simulation.aperiodic_golden_triangles import (
    TUEBINGEN_THICK_KIND,
    TUEBINGEN_THIN_KIND,
    triangle_record,
)
from backend.simulation.aperiodic_support import (
    Affine,
    AperiodicPatch,
    PatchRecord,
    Vec,
    affine_apply,
    affine_inverse,
    affine_multiply,
    id_from_transform,
    patch_from_records,
    rotation,
    scale,
)


PHI = (1 + math.sqrt(5)) / 2
XI = cmath.exp((2j * math.pi) / 5)
CONTRACTION = XI + (XI ** 4)
_EDGE_LENGTH_EPSILON = 1e-12

# Canonical Robinson triangle prototypes in simple local coordinates.
# Thick: two unit edges meeting at a 36 degree apex at the origin.
STANDARD_THICK = (
    0j,
    1 + 0j,
    complex(math.cos(math.radians(36)), math.sin(math.radians(36))),
)
# Thin: long edge on the x-axis, acute apex above the base.
STANDARD_THIN = (
    0j,
    1 + 0j,
    complex(0.5, math.sqrt((1 / (PHI * PHI)) - 0.25)),
)

# Published Tuebingen prototiles from the Penrose dual-IFS construction:
# the thick triangle coordinates are given explicitly in Frettloh 2007.
# The thin triangle has the two listed vertices ξ² and ξ³; the third vertex
# is the unique same-scale Robinson-triangle completion that closes the dual IFS.
PAPER_THICK = (
    1 + (XI ** 2) + (XI ** 4),
    1 + XI + (XI ** 3),
    1 + (XI ** 2) + (XI ** 3),
)
PAPER_THIN = (
    XI ** 2,
    XI ** 3,
    complex(-(1 / (PHI * PHI)), 0.0),
)


@dataclass(frozen=True)
class _TuebingenNode:
    label: str
    chirality: str
    transform: Affine


@dataclass(frozen=True)
class _TuebingenChild:
    label: str
    chirality: str
    transform: Affine


def _complex_affine(scale_rotate: complex, translate: complex) -> Affine:
    return (
        float(scale_rotate.real),
        float(-scale_rotate.imag),
        float(translate.real),
        float(scale_rotate.imag),
        float(scale_rotate.real),
        float(translate.imag),
    )


def _similarity_affine(
    source: tuple[complex, complex, complex],
    target: tuple[complex, complex, complex],
) -> Affine:
    tolerance = 1e-6
    for permutation in itertools.permutations(range(3)):
        left = tuple(source[index] for index in permutation)
        source_first, source_second, source_third = left
        target_first, target_second, target_third = target
        denominator = source_second - source_first
        if abs(denominator) <= tolerance:
            continue
        scale_rotate = (target_second - target_first) / denominator
        translate = target_first - (scale_rotate * source_first)
        if abs((scale_rotate * source_third) + translate - target_third) <= tolerance:
            return _complex_affine(scale_rotate, translate)
    raise ValueError("Unable to resolve similarity transform for Tuebingen triangles.")


def _vecs(points: tuple[complex, complex, complex]) -> tuple[Vec, Vec, Vec]:
    return (
        Vec(float(points[0].real), float(points[0].imag)),
        Vec(float(points[1].real), float(points[1].imag)),
        Vec(float(points[2].real), float(points[2].imag)),
    )


STANDARD_VERTICES = {
    "thick": _vecs(STANDARD_THICK),
    "thin": _vecs(STANDARD_THIN),
}

PAPER_AFFINES = {
    "thick": _similarity_affine(STANDARD_THICK, PAPER_THICK),
    "thin": _similarity_affine(STANDARD_THIN, PAPER_THIN),
}

STANDARD_FROM_PAPER = {
    label: affine_inverse(transform)
    for label, transform in PAPER_AFFINES.items()
}

STANDARD_REFLECTIONS = {
    "thick": _similarity_affine(
        STANDARD_THICK,
        (STANDARD_THICK[0], STANDARD_THICK[2], STANDARD_THICK[1]),
    ),
    "thin": _similarity_affine(
        STANDARD_THIN,
        (STANDARD_THIN[1], STANDARD_THIN[0], STANDARD_THIN[2]),
    ),
}

PAPER_CHILD_TRANSFORMS = {
    "thin": (
        (
            "thin",
            _complex_affine(
                CONTRACTION * (XI ** 3),
                CONTRACTION * ((XI ** 3) + (XI ** 2)),
            ),
        ),
        (
            "thick",
            _complex_affine(
                CONTRACTION * XI,
                CONTRACTION * (-XI + (XI ** 2)),
            ),
        ),
    ),
    "thick": (
        (
            "thin",
            _complex_affine(
                CONTRACTION * (XI ** 2),
                CONTRACTION * (XI + (XI ** 2) + (XI ** 4)),
            ),
        ),
        (
            "thick",
            _complex_affine(
                CONTRACTION * (-XI),
                CONTRACTION * (XI + (XI ** 4)),
            ),
        ),
        (
            "thick",
            _complex_affine(
                CONTRACTION,
                CONTRACTION * (-1 + XI + (XI ** 4)),
            ),
        ),
    ),
}

STANDARD_CHILD_TRANSFORMS = {
    parent_label: tuple(
        (
            child_label,
            affine_multiply(
                STANDARD_FROM_PAPER[parent_label],
                affine_multiply(
                    child_transform,
                    PAPER_AFFINES[child_label],
                ),
            ),
        )
        for child_label, child_transform in child_items
    )
    for parent_label, child_items in PAPER_CHILD_TRANSFORMS.items()
}


def _opposite_chirality(chirality: str) -> str:
    return "right" if chirality == "left" else "left"


def _canonical_short_edge_handedness(
    vertices: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> str:
    chosen_edge: tuple[
        float,
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ] | None = None
    for index, start in enumerate(vertices):
        end = vertices[(index + 1) % len(vertices)]
        opposite = vertices[(index + 2) % len(vertices)]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        edge = (dx * dx + dy * dy, start, end, opposite)
        if chosen_edge is None:
            chosen_edge = edge
            continue
        edge_length, edge_start, edge_end, _ = edge
        chosen_length, chosen_start, chosen_end, _ = chosen_edge
        if edge_length < chosen_length - _EDGE_LENGTH_EPSILON:
            chosen_edge = edge
            continue
        if (
            abs(edge_length - chosen_length) <= _EDGE_LENGTH_EPSILON
            and tuple(sorted((edge_start, edge_end))) < tuple(sorted((chosen_start, chosen_end)))
        ):
            chosen_edge = edge
    if chosen_edge is None:
        raise ValueError("Tuebingen triangles require exactly three vertices.")
    _, start, end, opposite = chosen_edge
    if end < start:
        start, end = end, start
    cross = ((end[0] - start[0]) * (opposite[1] - start[1])) - (
        (end[1] - start[1]) * (opposite[0] - start[0])
    )
    return "left" if cross >= 0 else "right"


def _transformed_triangle_vertices(
    label: str,
    transform: Affine,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    vertex_a, vertex_b, vertex_c = STANDARD_VERTICES[label]
    vertices = (
        affine_apply(transform, vertex_a),
        affine_apply(transform, vertex_b),
        affine_apply(transform, vertex_c),
    )
    return (
        (vertices[0].x, vertices[0].y),
        (vertices[1].x, vertices[1].y),
        (vertices[2].x, vertices[2].y),
    )


def _reflect_child_transform(
    parent_label: str,
    child_label: str,
    transform: Affine,
) -> Affine:
    return affine_multiply(
        STANDARD_REFLECTIONS[parent_label],
        affine_multiply(transform, STANDARD_REFLECTIONS[child_label]),
    )


STANDARD_CHILD_SUBSTITUTIONS = {
    parent_label: {
        "left": tuple(
            _TuebingenChild(
                label=child_label,
                chirality=_canonical_short_edge_handedness(
                    _transformed_triangle_vertices(child_label, child_transform),
                ),
                transform=child_transform,
            )
            for child_label, child_transform in child_items
        ),
        "right": tuple(
            _TuebingenChild(
                label=child_label,
                chirality=_opposite_chirality(
                    _canonical_short_edge_handedness(
                        _transformed_triangle_vertices(child_label, child_transform),
                    ),
                ),
                transform=_reflect_child_transform(parent_label, child_label, child_transform),
            )
            for child_label, child_transform in child_items
        ),
    }
    for parent_label, child_items in STANDARD_CHILD_TRANSFORMS.items()
}


def _record_for_node(node: _TuebingenNode) -> PatchRecord:
    rounded_vertices = _transformed_triangle_vertices(node.label, node.transform)
    return triangle_record(
        cell_id=id_from_transform(f"tuebingen:{node.label}", node.transform),
        kind=(
            TUEBINGEN_THICK_KIND
            if node.label == "thick"
            else TUEBINGEN_THIN_KIND
        ),
        vertices=rounded_vertices,
        tile_family="tuebingen",
        chirality_token=node.chirality,
    )


def _root_star_nodes(root_scale: float) -> tuple[_TuebingenNode, ...]:
    nodes: list[_TuebingenNode] = []
    base_scale = scale(root_scale)
    for index in range(10):
        transform = affine_multiply(
            rotation(math.radians(index * 36)),
            base_scale,
        )
        nodes.append(
            _TuebingenNode(
                label="thick",
                chirality=_canonical_short_edge_handedness(
                    _transformed_triangle_vertices("thick", transform),
                ),
                transform=transform,
            )
        )
    return tuple(nodes)


def build_tuebingen_triangle_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []

    def collect(node: _TuebingenNode, remaining_depth: int) -> None:
        if remaining_depth <= 0:
            records.append(_record_for_node(node))
            return
        for child in STANDARD_CHILD_SUBSTITUTIONS[node.label][node.chirality]:
            collect(
                _TuebingenNode(
                    label=child.label,
                    chirality=child.chirality,
                    transform=affine_multiply(node.transform, child.transform),
                ),
                remaining_depth - 1,
            )

    root_scale = PHI ** resolved_depth
    for node in _root_star_nodes(root_scale):
        collect(node, resolved_depth)

    return patch_from_records(
        resolved_depth,
        records,
        neighbor_mode="segment_overlap",
    )
