from __future__ import annotations

from backend.simulation.topology_catalog_types import SizingPolicyDefinition, TopologyVariantDefinition

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

LOW_MINIMUM_MIXED_GEOMETRIES = frozenset(
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
