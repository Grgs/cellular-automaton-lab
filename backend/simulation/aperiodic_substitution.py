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
class SubstitutionNode:
    label: str
    transform: Affine
    variant: str | None = None
    orientation_token: str | None = None
    chirality_token: str | None = None
    tile_family: str | None = None
    decoration_tokens: tuple[str, ...] | None = None


SubstitutionChild = SubstitutionNode


@dataclass(frozen=True)
class SubstitutionLeafTemplate:
    kind: str
    id_prefix: str
    vertices: tuple[Vec, ...]
    transform: Affine = AFFINE_IDENTITY
    variant: str | None = None
    orientation_token: str | None = None
    chirality_token: str | None = None
    tile_family: str | None = None
    decoration_tokens: tuple[str, ...] | None = None


LeafTemplatesForLabel = Callable[[SubstitutionNode], Iterable[SubstitutionLeafTemplate]]
ExpandChildren = Callable[[SubstitutionNode, int], Iterable[SubstitutionNode]]


def _combined_decoration_tokens(
    parent: tuple[str, ...] | None,
    child: tuple[str, ...] | None,
) -> tuple[str, ...] | None:
    tokens: list[str] = []
    for source in (parent, child):
        if not source:
            continue
        for token in source:
            if token not in tokens:
                tokens.append(token)
    return tuple(tokens) if tokens else None


def _leaf_record_prefix(
    node: SubstitutionNode,
    template: SubstitutionLeafTemplate,
) -> str:
    tokens = [template.id_prefix]
    variant = template.variant if template.variant is not None else node.variant
    chirality_token = (
        template.chirality_token if template.chirality_token is not None else node.chirality_token
    )
    orientation_token = (
        template.orientation_token
        if template.orientation_token is not None
        else node.orientation_token
    )
    tile_family = template.tile_family if template.tile_family is not None else node.tile_family
    if tile_family:
        tokens.append(f"family-{tile_family}")
    if variant:
        tokens.append(f"variant-{variant}")
    if chirality_token:
        tokens.append(f"chirality-{chirality_token}")
    if orientation_token:
        tokens.append(f"orientation-{orientation_token}")
    return ":".join(tokens)


def _records_for_leaf_templates(
    templates: Iterable[SubstitutionLeafTemplate],
    node: SubstitutionNode,
) -> list[PatchRecord]:
    records: list[PatchRecord] = []
    for template in templates:
        resolved_transform = affine_multiply(node.transform, template.transform)
        vertices = tuple(affine_apply(resolved_transform, vertex) for vertex in template.vertices)
        tile_family = template.tile_family if template.tile_family is not None else node.tile_family
        orientation_token = (
            template.orientation_token
            if template.orientation_token is not None
            else node.orientation_token
        )
        chirality_token = (
            template.chirality_token
            if template.chirality_token is not None
            else node.chirality_token
        )
        decoration_tokens = _combined_decoration_tokens(
            node.decoration_tokens,
            template.decoration_tokens,
        )
        records.append(
            {
                "id": id_from_transform(_leaf_record_prefix(node, template), resolved_transform),
                "kind": template.kind,
                "center": rounded_point(polygon_centroid(vertices)),
                "vertices": tuple(rounded_point(vertex) for vertex in vertices),
                "tile_family": tile_family,
                "orientation_token": orientation_token,
                "chirality_token": chirality_token,
                "decoration_tokens": decoration_tokens,
            }
        )
    return records


def _compose_child_node(
    parent: SubstitutionNode,
    child: SubstitutionNode,
) -> SubstitutionNode:
    return SubstitutionNode(
        label=child.label,
        transform=affine_multiply(parent.transform, child.transform),
        variant=child.variant if child.variant is not None else parent.variant,
        orientation_token=(
            child.orientation_token
            if child.orientation_token is not None
            else parent.orientation_token
        ),
        chirality_token=(
            child.chirality_token if child.chirality_token is not None else parent.chirality_token
        ),
        tile_family=child.tile_family if child.tile_family is not None else parent.tile_family,
        decoration_tokens=_combined_decoration_tokens(
            parent.decoration_tokens,
            child.decoration_tokens,
        ),
    )


def build_substitution_patch(
    patch_depth: int,
    *,
    root_items: Iterable[SubstitutionNode],
    expand_children: ExpandChildren,
    leaf_templates_for_label: LeafTemplatesForLabel,
) -> AperiodicPatch:
    records: list[PatchRecord] = []

    def collect(node: SubstitutionNode, remaining_depth: int) -> None:
        if remaining_depth <= 0:
            records.extend(_records_for_leaf_templates(leaf_templates_for_label(node), node))
            return
        for child in expand_children(node, remaining_depth):
            collect(_compose_child_node(node, child), remaining_depth - 1)

    resolved_depth = int(patch_depth)
    for item in root_items:
        collect(item, resolved_depth)

    return patch_from_records(resolved_depth, records)
