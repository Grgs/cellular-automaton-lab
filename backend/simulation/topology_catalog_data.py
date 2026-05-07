from __future__ import annotations

from backend.simulation.topology_catalog_types import TopologyVariantDefinition
from backend.simulation.topology_family_manifest import (
    AMMANN_BEENKER_GEOMETRY,
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_488_GEOMETRY,
    CAIRO_GEOMETRY,
    CELL_SIZE_CONTROL,
    CHAIR_GEOMETRY,
    DEFAULT_MIN_GRID_SIZE,
    DEFAULT_SQUARE_RULE,
    DEFAULT_TOPOLOGY_PATCH_DEPTH,
    DELTOIDAL_HEXAGONAL_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    EDGE_ADJACENCY,
    FLORET_PENTAGONAL_GEOMETRY,
    GEOMETRY_MINIMUM_GRID_DIMENSIONS,
    HAT_MONOTILE_GEOMETRY,
    HEX_GEOMETRY,
    KAGOME_GEOMETRY,
    KISRHOMBILLE_GEOMETRY,
    PATCH_DEPTH_CONTROL,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PICKER_GROUP_ORDER,
    PINWHEEL_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
    SPHINX_GEOMETRY,
    SPECTRE_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    SQUARE_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TOPOLOGY_FAMILY_MANIFEST,
    TRIANGLE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
    TUEBINGEN_TRIANGLE_GEOMETRY,
    VERTEX_ADJACENCY,
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
    "AMMANN_BEENKER_GEOMETRY",
    "ARCHIMEDEAN_31212_GEOMETRY",
    "ARCHIMEDEAN_33336_GEOMETRY",
    "ARCHIMEDEAN_33344_GEOMETRY",
    "ARCHIMEDEAN_33434_GEOMETRY",
    "ARCHIMEDEAN_3464_GEOMETRY",
    "ARCHIMEDEAN_4612_GEOMETRY",
    "ARCHIMEDEAN_488_GEOMETRY",
    "CAIRO_GEOMETRY",
    "CELL_SIZE_CONTROL",
    "CHAIR_GEOMETRY",
    "DEFAULT_MIN_GRID_SIZE",
    "DEFAULT_SQUARE_RULE",
    "DEFAULT_TOPOLOGY_PATCH_DEPTH",
    "DELTOIDAL_HEXAGONAL_GEOMETRY",
    "DELTOIDAL_TRIHEXAGONAL_GEOMETRY",
    "EDGE_ADJACENCY",
    "FLORET_PENTAGONAL_GEOMETRY",
    "HAT_MONOTILE_GEOMETRY",
    "HEX_GEOMETRY",
    "KAGOME_GEOMETRY",
    "KISRHOMBILLE_GEOMETRY",
    "LOW_MINIMUM_MIXED_GEOMETRIES",
    "PATCH_DEPTH_CONTROL",
    "PENROSE_GEOMETRY",
    "PENROSE_P2_GEOMETRY",
    "PENROSE_VERTEX_GEOMETRY",
    "PICKER_GROUP_ORDER",
    "PINWHEEL_GEOMETRY",
    "PRISMATIC_PENTAGONAL_GEOMETRY",
    "RHOMBILLE_GEOMETRY",
    "ROBINSON_TRIANGLES_GEOMETRY",
    "SHIELD_GEOMETRY",
    "SNUB_SQUARE_DUAL_GEOMETRY",
    "SPHINX_GEOMETRY",
    "SPECTRE_GEOMETRY",
    "DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY",
    "SQUARE_GEOMETRY",
    "TAYLOR_SOCOLAR_GEOMETRY",
    "TETRAKIS_SQUARE_GEOMETRY",
    "TOPOLOGY_SIZING_POLICIES",
    "TOPOLOGY_VARIANTS",
    "TRIANGLE_GEOMETRY",
    "TRIAKIS_TRIANGULAR_GEOMETRY",
    "TUEBINGEN_TRIANGLE_GEOMETRY",
    "VERTEX_ADJACENCY",
]
