from __future__ import annotations

from backend.simulation.topology_catalog_types import TopologyVariantDefinition
from backend.simulation.topology_family_manifest import (
    GEOMETRY_MINIMUM_GRID_DIMENSIONS,
    PICKER_GROUP_ORDER,
    TOPOLOGY_FAMILY_MANIFEST,
)


TOPOLOGY_SIZING_POLICIES = {
    tiling_family: definition.sizing_policy
    for tiling_family, definition in TOPOLOGY_FAMILY_MANIFEST.items()
}

TOPOLOGY_VARIANTS: tuple[TopologyVariantDefinition, ...] = tuple(
    TopologyVariantDefinition(
        geometry_key=variant.geometry_key,
        tiling_family=definition.tiling_family,
        adjacency_mode=variant.adjacency_mode,
        label=definition.label,
        picker_group=definition.picker_group,
        picker_order=definition.picker_order,
        default_rule=variant.default_rule,
        sizing_mode=definition.sizing_mode,
        family=definition.family,
        viewport_sync_mode=definition.viewport_sync_mode,
    )
    for definition in sorted(
        TOPOLOGY_FAMILY_MANIFEST.values(),
        key=lambda entry: (
            PICKER_GROUP_ORDER.get(entry.picker_group, 99),
            entry.picker_order,
            entry.label.lower(),
        ),
    )
    for variant in definition.variants
)

LOW_MINIMUM_MIXED_GEOMETRIES = frozenset(
    geometry_key
    for geometry_key, minimum_dimension in GEOMETRY_MINIMUM_GRID_DIMENSIONS.items()
    if minimum_dimension == 1
)


__all__ = [
    "LOW_MINIMUM_MIXED_GEOMETRIES",
    "TOPOLOGY_SIZING_POLICIES",
    "TOPOLOGY_VARIANTS",
]
