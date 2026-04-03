from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from backend.simulation.aperiodic_support import (
    AFFINE_IDENTITY,
    Affine,
    AperiodicPatch,
    PatchRecord,
    Vec,
    affine_apply,
    affine_multiply,
    id_from_transform,
    patch_from_records,
    polygon_centroid,
    rounded_point,
)


@dataclass(frozen=True)
class SubstitutionChild:
    label: str
    transform: Affine


@dataclass(frozen=True)
class SubstitutionLeafTemplate:
    kind: str
    id_prefix: str
    vertices: tuple[Vec, ...]
    transform: Affine = AFFINE_IDENTITY
    orientation_token: str | None = None
    chirality_token: str | None = None


LeafTemplatesForLabel = Callable[[str], Iterable[SubstitutionLeafTemplate]]
ExpandChildren = Callable[[str, int], Iterable[SubstitutionChild]]


def _leaf_record_prefix(template: SubstitutionLeafTemplate) -> str:
    tokens = [template.id_prefix]
    if template.chirality_token:
        tokens.append(f"chirality-{template.chirality_token}")
    if template.orientation_token:
        tokens.append(f"orientation-{template.orientation_token}")
    return ":".join(tokens)


def _records_for_leaf_templates(
    templates: Iterable[SubstitutionLeafTemplate],
    transform: Affine,
) -> list[PatchRecord]:
    records: list[PatchRecord] = []
    for template in templates:
        resolved_transform = affine_multiply(transform, template.transform)
        vertices = tuple(affine_apply(resolved_transform, vertex) for vertex in template.vertices)
        records.append(
            {
                "id": id_from_transform(_leaf_record_prefix(template), resolved_transform),
                "kind": template.kind,
                "center": rounded_point(polygon_centroid(vertices)),
                "vertices": tuple(rounded_point(vertex) for vertex in vertices),
            }
        )
    return records


def build_substitution_patch(
    patch_depth: int,
    *,
    root_items: Iterable[SubstitutionChild],
    expand_children: ExpandChildren,
    leaf_templates_for_label: LeafTemplatesForLabel,
) -> AperiodicPatch:
    records: list[PatchRecord] = []

    def collect(label: str, remaining_depth: int, transform: Affine) -> None:
        if remaining_depth <= 0:
            records.extend(_records_for_leaf_templates(leaf_templates_for_label(label), transform))
            return
        for child in expand_children(label, remaining_depth):
            collect(
                child.label,
                remaining_depth - 1,
                affine_multiply(transform, child.transform),
            )

    resolved_depth = int(patch_depth)
    for item in root_items:
        collect(item.label, resolved_depth, item.transform)

    return patch_from_records(resolved_depth, records)
