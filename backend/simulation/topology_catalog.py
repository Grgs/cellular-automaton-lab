from __future__ import annotations

from backend.payload_types import TopologyCatalogEntryPayload, TopologySpecPayload, TopologyVariantPayload
from backend.simulation.topology_catalog_build import build_topology_catalog
from backend.simulation.topology_catalog_data import (
    AMMANN_BEENKER_GEOMETRY,
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_488_GEOMETRY,
    CAIRO_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    CELL_SIZE_CONTROL,
    DEFAULT_MIN_GRID_SIZE,
    DEFAULT_SQUARE_RULE,
    DEFAULT_TOPOLOGY_PATCH_DEPTH,
    EDGE_ADJACENCY,
    FLORET_PENTAGONAL_GEOMETRY,
    HEX_GEOMETRY,
    KAGOME_GEOMETRY,
    LOW_MINIMUM_MIXED_GEOMETRIES,
    PATCH_DEPTH_CONTROL,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PICKER_GROUP_ORDER,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
    SPECTRE_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    SQUARE_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TOPOLOGY_SIZING_POLICIES,
    TOPOLOGY_VARIANTS,
    TRIAKIS_TRIANGULAR_GEOMETRY,
    TRIANGLE_GEOMETRY,
    VERTEX_ADJACENCY,
)
from backend.simulation.topology_catalog_queries import (
    describe_topologies as describe_topology_entries,
    describe_topology_variants as describe_variant_entries,
    topology_spec_payload as build_topology_spec_payload,
)
from backend.simulation.topology_catalog_types import (
    SizingPolicyDefinition,
    TopologyDefinition,
    TopologyVariantDefinition,
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
    "DELTOIDAL_TRIHEXAGONAL_GEOMETRY",
    "CELL_SIZE_CONTROL",
    "DEFAULT_MIN_GRID_SIZE",
    "DEFAULT_SQUARE_RULE",
    "DEFAULT_TOPOLOGY_PATCH_DEPTH",
    "EDGE_ADJACENCY",
    "FLORET_PENTAGONAL_GEOMETRY",
    "GEOMETRY_DEFAULT_RULES",
    "HEX_GEOMETRY",
    "KAGOME_GEOMETRY",
    "PATCH_DEPTH_CONTROL",
    "PENROSE_GEOMETRY",
    "PENROSE_P2_GEOMETRY",
    "PENROSE_VERTEX_GEOMETRY",
    "PICKER_GROUP_ORDER",
    "PRISMATIC_PENTAGONAL_GEOMETRY",
    "RHOMBILLE_GEOMETRY",
    "SNUB_SQUARE_DUAL_GEOMETRY",
    "SPECTRE_GEOMETRY",
    "TAYLOR_SOCOLAR_GEOMETRY",
    "SUPPORTED_GEOMETRIES",
    "SUPPORTED_TOPOLOGY_FAMILIES",
    "SQUARE_GEOMETRY",
    "TETRAKIS_SQUARE_GEOMETRY",
    "TOPOLOGY_CATALOG",
    "TOPOLOGY_BY_FAMILY",
    "TOPOLOGY_DEFAULT_RULES",
    "TOPOLOGY_SIZING_POLICIES",
    "TOPOLOGY_VARIANTS",
    "TOPOLOGY_VARIANT_BY_GEOMETRY",
    "TRIANGLE_GEOMETRY",
    "VERTEX_ADJACENCY",
    "SizingPolicyDefinition",
    "TopologyDefinition",
    "TopologyVariantDefinition",
    "default_patch_depth_for_tiling_family",
    "describe_topologies",
    "describe_topology_variants",
    "geometry_uses_backend_viewport_sync",
    "geometry_uses_patch_depth",
    "get_topology_definition",
    "get_topology_sizing_policy",
    "get_topology_variant_for_geometry",
    "is_aperiodic_geometry",
    "is_penrose_geometry",
    "is_supported_topology_family",
    "maximum_patch_depth_for_tiling_family",
    "minimum_grid_dimension_for_geometry",
    "minimum_patch_depth_for_tiling_family",
    "normalize_adjacency_mode",
    "resolve_geometry_key",
    "topology_spec_payload",
    "TRIAKIS_TRIANGULAR_GEOMETRY",
]


TOPOLOGY_VARIANT_BY_GEOMETRY = {
    variant.geometry_key: variant
    for variant in TOPOLOGY_VARIANTS
}

TOPOLOGY_CATALOG = build_topology_catalog(
    TOPOLOGY_VARIANTS,
    TOPOLOGY_SIZING_POLICIES,
    PICKER_GROUP_ORDER,
)
TOPOLOGY_BY_FAMILY = {
    definition.tiling_family: definition
    for definition in TOPOLOGY_CATALOG
}
SUPPORTED_TOPOLOGY_FAMILIES = tuple(
    definition.tiling_family
    for definition in TOPOLOGY_CATALOG
)
SUPPORTED_GEOMETRIES = tuple(variant.geometry_key for variant in TOPOLOGY_VARIANTS)
GEOMETRY_DEFAULT_RULES = {
    variant.geometry_key: variant.default_rule
    for variant in TOPOLOGY_VARIANTS
}
TOPOLOGY_DEFAULT_RULES = {
    definition.tiling_family: dict(definition.default_rules)
    for definition in TOPOLOGY_CATALOG
}


def describe_topologies() -> list[TopologyCatalogEntryPayload]:
    return describe_topology_entries(TOPOLOGY_CATALOG)


def describe_topology_variants() -> list[TopologyVariantPayload]:
    return describe_variant_entries(TOPOLOGY_VARIANTS)


def is_supported_topology_family(tiling_family: str) -> bool:
    return tiling_family in TOPOLOGY_BY_FAMILY


def get_topology_definition(tiling_family: str) -> TopologyDefinition:
    return TOPOLOGY_BY_FAMILY[tiling_family]


def get_topology_sizing_policy(tiling_family: str) -> SizingPolicyDefinition:
    return get_topology_definition(tiling_family).sizing_policy


def get_topology_variant_for_geometry(geometry_key: str) -> TopologyVariantDefinition:
    return TOPOLOGY_VARIANT_BY_GEOMETRY[geometry_key]


def normalize_adjacency_mode(tiling_family: str, adjacency_mode: str | None = None) -> str:
    definition = get_topology_definition(tiling_family)
    if adjacency_mode in definition.geometry_keys:
        return adjacency_mode
    return definition.default_adjacency_mode


def resolve_geometry_key(tiling_family: str, adjacency_mode: str | None = None) -> str:
    definition = get_topology_definition(tiling_family)
    resolved_adjacency_mode = normalize_adjacency_mode(tiling_family, adjacency_mode)
    return definition.geometry_keys[resolved_adjacency_mode]


def topology_spec_payload(
    geometry_key: str,
    *,
    width: int,
    height: int,
    patch_depth: int | None = None,
) -> TopologySpecPayload:
    variant = get_topology_variant_for_geometry(geometry_key)
    definition = get_topology_definition(variant.tiling_family)
    return build_topology_spec_payload(
        variant=variant,
        definition=definition,
        width=width,
        height=height,
        patch_depth=DEFAULT_TOPOLOGY_PATCH_DEPTH if patch_depth is None else patch_depth,
    )


def geometry_uses_patch_depth(geometry_key: str) -> bool:
    return get_topology_variant_for_geometry(geometry_key).sizing_mode == "patch_depth"


def geometry_uses_backend_viewport_sync(geometry_key: str) -> bool:
    return get_topology_variant_for_geometry(geometry_key).viewport_sync_mode == "backend-sync"


def is_penrose_geometry(geometry_key: str) -> bool:
    return get_topology_variant_for_geometry(geometry_key).tiling_family == PENROSE_GEOMETRY


def is_aperiodic_geometry(geometry_key: str) -> bool:
    return get_topology_variant_for_geometry(geometry_key).family == "aperiodic"


def minimum_grid_dimension_for_geometry(geometry_key: str) -> int:
    if geometry_key in LOW_MINIMUM_MIXED_GEOMETRIES:
        return 1
    return DEFAULT_MIN_GRID_SIZE


def default_patch_depth_for_tiling_family(tiling_family: str) -> int:
    policy = get_topology_sizing_policy(tiling_family)
    return policy.default if policy.control == PATCH_DEPTH_CONTROL else DEFAULT_TOPOLOGY_PATCH_DEPTH


def minimum_patch_depth_for_tiling_family(tiling_family: str) -> int:
    policy = get_topology_sizing_policy(tiling_family)
    return policy.minimum if policy.control == PATCH_DEPTH_CONTROL else 0


def maximum_patch_depth_for_tiling_family(tiling_family: str) -> int:
    policy = get_topology_sizing_policy(tiling_family)
    return policy.maximum if policy.control == PATCH_DEPTH_CONTROL else DEFAULT_TOPOLOGY_PATCH_DEPTH
