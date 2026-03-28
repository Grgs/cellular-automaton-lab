from __future__ import annotations

from dataclasses import dataclass

from backend.payload_types import (
    SizingPolicyPayload,
    TopologyCatalogEntryPayload,
    TopologySpecPayload,
    TopologyVariantPayload,
)

DEFAULT_SQUARE_RULE = "conway"
DEFAULT_MIN_GRID_SIZE = 3
DEFAULT_TOPOLOGY_PATCH_DEPTH = 4


EDGE_ADJACENCY = "edge"
VERTEX_ADJACENCY = "vertex"

SQUARE_GEOMETRY = "square"
HEX_GEOMETRY = "hex"
TRIANGLE_GEOMETRY = "triangle"
ARCHIMEDEAN_488_GEOMETRY = "archimedean-4-8-8"
ARCHIMEDEAN_31212_GEOMETRY = "archimedean-3-12-12"
ARCHIMEDEAN_3464_GEOMETRY = "archimedean-3-4-6-4"
ARCHIMEDEAN_4612_GEOMETRY = "archimedean-4-6-12"
ARCHIMEDEAN_33434_GEOMETRY = "archimedean-3-3-4-3-4"
ARCHIMEDEAN_33344_GEOMETRY = "archimedean-3-3-3-4-4"
ARCHIMEDEAN_33336_GEOMETRY = "archimedean-3-3-3-3-6"
KAGOME_GEOMETRY = "trihexagonal-3-6-3-6"
CAIRO_GEOMETRY = "cairo-pentagonal"
PENROSE_GEOMETRY = "penrose-p3-rhombs"
PENROSE_VERTEX_GEOMETRY = "penrose-p3-rhombs-vertex"
PENROSE_P2_GEOMETRY = "penrose-p2-kite-dart"
AMMANN_BEENKER_GEOMETRY = "ammann-beenker"

PICKER_GROUP_ORDER = {
    "Classic": 0,
    "Periodic Mixed": 1,
    "Aperiodic": 2,
}


@dataclass(frozen=True)
class TopologyVariantDefinition:
    geometry_key: str
    tiling_family: str
    adjacency_mode: str
    label: str
    picker_group: str
    picker_order: int
    default_rule: str
    sizing_mode: str
    family: str
    viewport_sync_mode: str

    @property
    def id(self) -> str:
        return self.geometry_key

    def to_dict(self) -> TopologyVariantPayload:
        return {
            "id": self.geometry_key,
            "geometry_key": self.geometry_key,
            "tiling_family": self.tiling_family,
            "adjacency_mode": self.adjacency_mode,
            "label": self.label,
            "picker_group": self.picker_group,
            "picker_order": self.picker_order,
            "default_rule": self.default_rule,
            "sizing_mode": self.sizing_mode,
            "family": self.family,
            "viewport_sync_mode": self.viewport_sync_mode,
        }


@dataclass(frozen=True)
class SizingPolicyDefinition:
    control: str
    default: int
    minimum: int
    maximum: int

    def to_dict(self) -> SizingPolicyPayload:
        return {
            "control": self.control,
            "default": self.default,
            "min": self.minimum,
            "max": self.maximum,
        }


@dataclass(frozen=True)
class TopologyDefinition:
    tiling_family: str
    label: str
    picker_group: str
    picker_order: int
    sizing_mode: str
    family: str
    viewport_sync_mode: str
    supported_adjacency_modes: tuple[str, ...]
    default_adjacency_mode: str
    default_rules: dict[str, str]
    geometry_keys: dict[str, str]
    sizing_policy: SizingPolicyDefinition

    def to_dict(self) -> TopologyCatalogEntryPayload:
        return {
            "tiling_family": self.tiling_family,
            "label": self.label,
            "picker_group": self.picker_group,
            "picker_order": self.picker_order,
            "sizing_mode": self.sizing_mode,
            "family": self.family,
            "viewport_sync_mode": self.viewport_sync_mode,
            "supported_adjacency_modes": list(self.supported_adjacency_modes),
            "default_adjacency_mode": self.default_adjacency_mode,
            "default_rules": dict(self.default_rules),
            "geometry_keys": dict(self.geometry_keys),
            "sizing_policy": self.sizing_policy.to_dict(),
        }


CELL_SIZE_CONTROL = "cell_size"
PATCH_DEPTH_CONTROL = "patch_depth"

TOPOLOGY_SIZING_POLICIES = {
    SQUARE_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 24),
    HEX_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 16, 10, 24),
    TRIANGLE_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 20, 12, 24),
    ARCHIMEDEAN_488_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 24),
    KAGOME_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 24),
    ARCHIMEDEAN_31212_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 20),
    ARCHIMEDEAN_3464_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 14, 10, 20),
    ARCHIMEDEAN_4612_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 20),
    ARCHIMEDEAN_33434_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 18, 12, 20),
    ARCHIMEDEAN_33344_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 18, 12, 20),
    ARCHIMEDEAN_33336_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 16, 14, 20),
    CAIRO_GEOMETRY: SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 20),
    PENROSE_GEOMETRY: SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 6),
    PENROSE_P2_GEOMETRY: SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 6),
    AMMANN_BEENKER_GEOMETRY: SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 4),
}


TOPOLOGY_VARIANTS: tuple[TopologyVariantDefinition, ...] = (
    TopologyVariantDefinition(
        geometry_key=SQUARE_GEOMETRY,
        tiling_family=SQUARE_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Square",
        picker_group="Classic",
        picker_order=10,
        default_rule=DEFAULT_SQUARE_RULE,
        sizing_mode="grid",
        family="regular",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=HEX_GEOMETRY,
        tiling_family=HEX_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Hexagonal",
        picker_group="Classic",
        picker_order=20,
        default_rule="hexlife",
        sizing_mode="grid",
        family="regular",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=TRIANGLE_GEOMETRY,
        tiling_family=TRIANGLE_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Triangular",
        picker_group="Classic",
        picker_order=30,
        default_rule="trilife",
        sizing_mode="grid",
        family="regular",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=ARCHIMEDEAN_488_GEOMETRY,
        tiling_family=ARCHIMEDEAN_488_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Square-Octagon (4.8.8)",
        picker_group="Periodic Mixed",
        picker_order=110,
        default_rule="archlife488",
        sizing_mode="grid",
        family="mixed",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=ARCHIMEDEAN_31212_GEOMETRY,
        tiling_family=ARCHIMEDEAN_31212_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Truncated Hexagonal (3.12.12)",
        picker_group="Periodic Mixed",
        picker_order=130,
        default_rule="archlife-3-12-12",
        sizing_mode="grid",
        family="mixed",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=ARCHIMEDEAN_3464_GEOMETRY,
        tiling_family=ARCHIMEDEAN_3464_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Rhombitrihexagonal (3.4.6.4)",
        picker_group="Periodic Mixed",
        picker_order=140,
        default_rule="archlife-3-4-6-4",
        sizing_mode="grid",
        family="mixed",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=ARCHIMEDEAN_4612_GEOMETRY,
        tiling_family=ARCHIMEDEAN_4612_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Truncated Trihexagonal (4.6.12)",
        picker_group="Periodic Mixed",
        picker_order=150,
        default_rule="archlife-4-6-12",
        sizing_mode="grid",
        family="mixed",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=ARCHIMEDEAN_33434_GEOMETRY,
        tiling_family=ARCHIMEDEAN_33434_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Snub Square (3.3.4.3.4)",
        picker_group="Periodic Mixed",
        picker_order=160,
        default_rule="archlife-3-3-4-3-4",
        sizing_mode="grid",
        family="mixed",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=ARCHIMEDEAN_33344_GEOMETRY,
        tiling_family=ARCHIMEDEAN_33344_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Elongated Triangular (3.3.3.4.4)",
        picker_group="Periodic Mixed",
        picker_order=170,
        default_rule="archlife-3-3-3-4-4",
        sizing_mode="grid",
        family="mixed",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=ARCHIMEDEAN_33336_GEOMETRY,
        tiling_family=ARCHIMEDEAN_33336_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Snub Trihexagonal (3.3.3.3.6)",
        picker_group="Periodic Mixed",
        picker_order=180,
        default_rule="archlife-3-3-3-3-6",
        sizing_mode="grid",
        family="mixed",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=KAGOME_GEOMETRY,
        tiling_family=KAGOME_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Kagome / Trihexagonal (3.6.3.6)",
        picker_group="Periodic Mixed",
        picker_order=120,
        default_rule="kagome-life",
        sizing_mode="grid",
        family="mixed",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=CAIRO_GEOMETRY,
        tiling_family=CAIRO_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Cairo Pentagonal",
        picker_group="Periodic Mixed",
        picker_order=190,
        default_rule="life-b2-s23",
        sizing_mode="grid",
        family="mixed",
        viewport_sync_mode="backend-sync",
    ),
    TopologyVariantDefinition(
        geometry_key=PENROSE_GEOMETRY,
        tiling_family=PENROSE_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Penrose P3 Rhombs",
        picker_group="Aperiodic",
        picker_order=220,
        default_rule="life-b2-s23",
        sizing_mode="patch_depth",
        family="aperiodic",
        viewport_sync_mode="presentation-only",
    ),
    TopologyVariantDefinition(
        geometry_key=PENROSE_VERTEX_GEOMETRY,
        tiling_family=PENROSE_GEOMETRY,
        adjacency_mode=VERTEX_ADJACENCY,
        label="Penrose P3 Rhombs",
        picker_group="Aperiodic",
        picker_order=220,
        default_rule="conway",
        sizing_mode="patch_depth",
        family="aperiodic",
        viewport_sync_mode="presentation-only",
    ),
    TopologyVariantDefinition(
        geometry_key=PENROSE_P2_GEOMETRY,
        tiling_family=PENROSE_P2_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Penrose P2 Kite-Dart",
        picker_group="Aperiodic",
        picker_order=210,
        default_rule="life-b2-s23",
        sizing_mode="patch_depth",
        family="aperiodic",
        viewport_sync_mode="presentation-only",
    ),
    TopologyVariantDefinition(
        geometry_key=AMMANN_BEENKER_GEOMETRY,
        tiling_family=AMMANN_BEENKER_GEOMETRY,
        adjacency_mode=EDGE_ADJACENCY,
        label="Ammann-Beenker",
        picker_group="Aperiodic",
        picker_order=230,
        default_rule="life-b2-s23",
        sizing_mode="patch_depth",
        family="aperiodic",
        viewport_sync_mode="presentation-only",
    ),
)

TOPOLOGY_VARIANT_BY_GEOMETRY = {
    variant.geometry_key: variant
    for variant in TOPOLOGY_VARIANTS
}


def _build_topology_catalog() -> tuple[TopologyDefinition, ...]:
    grouped: dict[str, list[TopologyVariantDefinition]] = {}
    for variant in TOPOLOGY_VARIANTS:
        grouped.setdefault(variant.tiling_family, []).append(variant)

    catalog: list[TopologyDefinition] = []
    for tiling_family, variants in grouped.items():
        variants.sort(key=lambda entry: (entry.adjacency_mode != EDGE_ADJACENCY, entry.adjacency_mode))
        first = variants[0]
        catalog.append(
            TopologyDefinition(
                tiling_family=tiling_family,
                label=first.label,
                picker_group=first.picker_group,
                picker_order=first.picker_order,
                sizing_mode=first.sizing_mode,
                family=first.family,
                viewport_sync_mode=first.viewport_sync_mode,
                supported_adjacency_modes=tuple(variant.adjacency_mode for variant in variants),
                default_adjacency_mode=variants[0].adjacency_mode,
                default_rules={
                    variant.adjacency_mode: variant.default_rule
                    for variant in variants
                },
                geometry_keys={
                    variant.adjacency_mode: variant.geometry_key
                    for variant in variants
                },
                sizing_policy=TOPOLOGY_SIZING_POLICIES[tiling_family],
            )
        )
    catalog.sort(
        key=lambda definition: (
            PICKER_GROUP_ORDER.get(definition.picker_group, 99),
            definition.picker_order,
            definition.label.lower(),
        )
    )
    return tuple(catalog)


TOPOLOGY_CATALOG = _build_topology_catalog()
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
    return [definition.to_dict() for definition in TOPOLOGY_CATALOG]


def describe_topology_variants() -> list[TopologyVariantPayload]:
    return [variant.to_dict() for variant in TOPOLOGY_VARIANTS]


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
    payload: TopologySpecPayload = {
        "tiling_family": variant.tiling_family,
        "adjacency_mode": variant.adjacency_mode,
        "sizing_mode": definition.sizing_mode,
        "width": width,
        "height": height,
        "patch_depth": DEFAULT_TOPOLOGY_PATCH_DEPTH if patch_depth is None else patch_depth,
    }
    return payload


def geometry_uses_patch_depth(geometry_key: str) -> bool:
    return get_topology_variant_for_geometry(geometry_key).sizing_mode == "patch_depth"


def geometry_uses_backend_viewport_sync(geometry_key: str) -> bool:
    return get_topology_variant_for_geometry(geometry_key).viewport_sync_mode == "backend-sync"


def is_penrose_geometry(geometry_key: str) -> bool:
    return get_topology_variant_for_geometry(geometry_key).tiling_family == PENROSE_GEOMETRY


def is_aperiodic_geometry(geometry_key: str) -> bool:
    return get_topology_variant_for_geometry(geometry_key).family == "aperiodic"


_LOW_MINIMUM_MIXED_GEOMETRIES = frozenset(
    {
        ARCHIMEDEAN_31212_GEOMETRY,
        ARCHIMEDEAN_3464_GEOMETRY,
        ARCHIMEDEAN_4612_GEOMETRY,
        ARCHIMEDEAN_33434_GEOMETRY,
        ARCHIMEDEAN_33344_GEOMETRY,
        ARCHIMEDEAN_33336_GEOMETRY,
        CAIRO_GEOMETRY,
    }
)


def minimum_grid_dimension_for_geometry(geometry_key: str) -> int:
    if geometry_key in _LOW_MINIMUM_MIXED_GEOMETRIES:
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
