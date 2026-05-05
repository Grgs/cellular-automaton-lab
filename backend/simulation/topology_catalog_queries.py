from __future__ import annotations

from typing import Protocol

from backend.payload_types import (
    TopologyCatalogEntryPayload,
    TopologySpecPayload,
    TopologyVariantPayload,
)


class _CatalogEntryLike(Protocol):
    @property
    def sizing_mode(self) -> str: ...

    def to_dict(self) -> TopologyCatalogEntryPayload: ...


class _VariantLike(Protocol):
    @property
    def tiling_family(self) -> str: ...

    @property
    def adjacency_mode(self) -> str: ...

    def to_dict(self) -> TopologyVariantPayload: ...


def describe_topologies(
    catalog: tuple[_CatalogEntryLike, ...],
) -> list[TopologyCatalogEntryPayload]:
    return [definition.to_dict() for definition in catalog]


def describe_topology_variants(variants: tuple[_VariantLike, ...]) -> list[TopologyVariantPayload]:
    return [variant.to_dict() for variant in variants]


def topology_spec_payload(
    *,
    variant: _VariantLike,
    definition: _CatalogEntryLike,
    width: int,
    height: int,
    patch_depth: int,
) -> TopologySpecPayload:
    return {
        "tiling_family": variant.tiling_family,
        "adjacency_mode": variant.adjacency_mode,
        "sizing_mode": definition.sizing_mode,
        "width": width,
        "height": height,
        "patch_depth": patch_depth,
    }
