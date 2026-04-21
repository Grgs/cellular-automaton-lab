from __future__ import annotations

from dataclasses import dataclass

from backend.simulation.aperiodic_family_manifest import (
    AMMANN_BEENKER_GEOMETRY,
    APERIODIC_FAMILY_MANIFEST,
    CHAIR_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    HAT_MONOTILE_GEOMETRY,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PINWHEEL_GEOMETRY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SPHINX_GEOMETRY,
    SPECTRE_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TUEBINGEN_TRIANGLE_GEOMETRY,
)
from backend.simulation.topology_catalog_types import SizingPolicyDefinition


DEFAULT_SQUARE_RULE = "conway"
DEFAULT_MIN_GRID_SIZE = 3
DEFAULT_TOPOLOGY_PATCH_DEPTH = 4

EDGE_ADJACENCY = "edge"
VERTEX_ADJACENCY = "vertex"

CELL_SIZE_CONTROL = "cell_size"
PATCH_DEPTH_CONTROL = "patch_depth"

PICKER_GROUP_ORDER = {
    "Classic": 0,
    "Periodic Mixed": 1,
    "Aperiodic": 2,
    "Experimental": 3,
}

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
RHOMBILLE_GEOMETRY = "rhombille"
DELTOIDAL_HEXAGONAL_GEOMETRY = "deltoidal-hexagonal"
TETRAKIS_SQUARE_GEOMETRY = "tetrakis-square"
TRIAKIS_TRIANGULAR_GEOMETRY = "triakis-triangular"
DELTOIDAL_TRIHEXAGONAL_GEOMETRY = "deltoidal-trihexagonal"
PRISMATIC_PENTAGONAL_GEOMETRY = "prismatic-pentagonal"
FLORET_PENTAGONAL_GEOMETRY = "floret-pentagonal"
SNUB_SQUARE_DUAL_GEOMETRY = "snub-square-dual"


@dataclass(frozen=True)
class TopologyFamilyVariantManifestEntry:
    geometry_key: str
    adjacency_mode: str
    default_rule: str


@dataclass(frozen=True)
class TopologyFamilyManifestEntry:
    tiling_family: str
    label: str
    picker_group: str
    picker_order: int
    family: str
    sizing_mode: str
    viewport_sync_mode: str
    sizing_policy: SizingPolicyDefinition
    variants: tuple[TopologyFamilyVariantManifestEntry, ...]
    minimum_grid_dimension: int = DEFAULT_MIN_GRID_SIZE


def _variant(
    geometry_key: str,
    adjacency_mode: str,
    default_rule: str,
) -> TopologyFamilyVariantManifestEntry:
    return TopologyFamilyVariantManifestEntry(
        geometry_key=geometry_key,
        adjacency_mode=adjacency_mode,
        default_rule=default_rule,
    )


def _single_variant_family(
    *,
    tiling_family: str,
    label: str,
    picker_group: str,
    picker_order: int,
    family: str,
    viewport_sync_mode: str,
    sizing_policy: SizingPolicyDefinition,
    default_rule: str,
    minimum_grid_dimension: int = DEFAULT_MIN_GRID_SIZE,
) -> TopologyFamilyManifestEntry:
    return TopologyFamilyManifestEntry(
        tiling_family=tiling_family,
        label=label,
        picker_group=picker_group,
        picker_order=picker_order,
        family=family,
        sizing_mode="patch_depth" if sizing_policy.control == PATCH_DEPTH_CONTROL else "grid",
        viewport_sync_mode=viewport_sync_mode,
        sizing_policy=sizing_policy,
        variants=(_variant(tiling_family, EDGE_ADJACENCY, default_rule),),
        minimum_grid_dimension=minimum_grid_dimension,
    )


def _translated_aperiodic_family(
    tiling_family: str,
    sizing_policy: SizingPolicyDefinition,
    *,
    variants: tuple[TopologyFamilyVariantManifestEntry, ...] | None = None,
) -> TopologyFamilyManifestEntry:
    metadata = APERIODIC_FAMILY_MANIFEST[tiling_family]
    return TopologyFamilyManifestEntry(
        tiling_family=tiling_family,
        label=metadata.catalog_label,
        picker_group=metadata.picker_group,
        picker_order=metadata.picker_order,
        family="aperiodic",
        sizing_mode="patch_depth",
        viewport_sync_mode="presentation-only",
        sizing_policy=sizing_policy,
        variants=variants or (_variant(tiling_family, EDGE_ADJACENCY, metadata.default_rule),),
    )


TOPOLOGY_FAMILY_MANIFEST: dict[str, TopologyFamilyManifestEntry] = {
    SQUARE_GEOMETRY: _single_variant_family(
        tiling_family=SQUARE_GEOMETRY,
        label="Square",
        picker_group="Classic",
        picker_order=10,
        family="regular",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 24),
        default_rule=DEFAULT_SQUARE_RULE,
    ),
    HEX_GEOMETRY: _single_variant_family(
        tiling_family=HEX_GEOMETRY,
        label="Hexagonal",
        picker_group="Classic",
        picker_order=20,
        family="regular",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 16, 10, 24),
        default_rule="hexlife",
    ),
    TRIANGLE_GEOMETRY: _single_variant_family(
        tiling_family=TRIANGLE_GEOMETRY,
        label="Triangular",
        picker_group="Classic",
        picker_order=30,
        family="regular",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 20, 12, 24),
        default_rule="trilife",
    ),
    ARCHIMEDEAN_488_GEOMETRY: _single_variant_family(
        tiling_family=ARCHIMEDEAN_488_GEOMETRY,
        label="Square-Octagon (4.8.8)",
        picker_group="Periodic Mixed",
        picker_order=110,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 24),
        default_rule="archlife488",
    ),
    KAGOME_GEOMETRY: _single_variant_family(
        tiling_family=KAGOME_GEOMETRY,
        label="Kagome / Trihexagonal (3.6.3.6)",
        picker_group="Periodic Mixed",
        picker_order=120,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 24),
        default_rule="kagome-life",
    ),
    ARCHIMEDEAN_31212_GEOMETRY: _single_variant_family(
        tiling_family=ARCHIMEDEAN_31212_GEOMETRY,
        label="Truncated Hexagonal (3.12.12)",
        picker_group="Periodic Mixed",
        picker_order=130,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 20),
        default_rule="archlife-3-12-12",
        minimum_grid_dimension=1,
    ),
    ARCHIMEDEAN_3464_GEOMETRY: _single_variant_family(
        tiling_family=ARCHIMEDEAN_3464_GEOMETRY,
        label="Rhombitrihexagonal (3.4.6.4)",
        picker_group="Periodic Mixed",
        picker_order=140,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 14, 10, 20),
        default_rule="archlife-3-4-6-4",
        minimum_grid_dimension=1,
    ),
    ARCHIMEDEAN_4612_GEOMETRY: _single_variant_family(
        tiling_family=ARCHIMEDEAN_4612_GEOMETRY,
        label="Truncated Trihexagonal (4.6.12)",
        picker_group="Periodic Mixed",
        picker_order=150,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 20),
        default_rule="archlife-4-6-12",
        minimum_grid_dimension=1,
    ),
    ARCHIMEDEAN_33434_GEOMETRY: _single_variant_family(
        tiling_family=ARCHIMEDEAN_33434_GEOMETRY,
        label="Snub Square (3.3.4.3.4)",
        picker_group="Periodic Mixed",
        picker_order=160,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 18, 12, 20),
        default_rule="archlife-3-3-4-3-4",
        minimum_grid_dimension=1,
    ),
    ARCHIMEDEAN_33344_GEOMETRY: _single_variant_family(
        tiling_family=ARCHIMEDEAN_33344_GEOMETRY,
        label="Elongated Triangular (3.3.3.4.4)",
        picker_group="Periodic Mixed",
        picker_order=170,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 18, 12, 20),
        default_rule="archlife-3-3-3-4-4",
        minimum_grid_dimension=1,
    ),
    ARCHIMEDEAN_33336_GEOMETRY: _single_variant_family(
        tiling_family=ARCHIMEDEAN_33336_GEOMETRY,
        label="Snub Trihexagonal (3.3.3.3.6)",
        picker_group="Periodic Mixed",
        picker_order=180,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 16, 14, 20),
        default_rule="archlife-3-3-3-3-6",
        minimum_grid_dimension=1,
    ),
    CAIRO_GEOMETRY: _single_variant_family(
        tiling_family=CAIRO_GEOMETRY,
        label="Cairo Pentagonal",
        picker_group="Periodic Mixed",
        picker_order=190,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    RHOMBILLE_GEOMETRY: _single_variant_family(
        tiling_family=RHOMBILLE_GEOMETRY,
        label="Rhombille",
        picker_group="Periodic Mixed",
        picker_order=200,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
    ),
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY: _single_variant_family(
        tiling_family=DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
        label="Deltoidal Trihexagonal",
        picker_group="Periodic Mixed",
        picker_order=210,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    DELTOIDAL_HEXAGONAL_GEOMETRY: _single_variant_family(
        tiling_family=DELTOIDAL_HEXAGONAL_GEOMETRY,
        label="Deltoidal Hexagonal",
        picker_group="Periodic Mixed",
        picker_order=215,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    SNUB_SQUARE_DUAL_GEOMETRY: _single_variant_family(
        tiling_family=SNUB_SQUARE_DUAL_GEOMETRY,
        label="Snub Square Dual",
        picker_group="Periodic Mixed",
        picker_order=220,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 18),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    PENROSE_P2_GEOMETRY: _translated_aperiodic_family(
        PENROSE_P2_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 6),
    ),
    PENROSE_GEOMETRY: _translated_aperiodic_family(
        PENROSE_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 6),
        variants=(
            _variant(PENROSE_GEOMETRY, EDGE_ADJACENCY, APERIODIC_FAMILY_MANIFEST[PENROSE_GEOMETRY].default_rule),
            _variant(PENROSE_VERTEX_GEOMETRY, VERTEX_ADJACENCY, DEFAULT_SQUARE_RULE),
        ),
    ),
    AMMANN_BEENKER_GEOMETRY: _translated_aperiodic_family(
        AMMANN_BEENKER_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 4),
    ),
    TETRAKIS_SQUARE_GEOMETRY: _single_variant_family(
        tiling_family=TETRAKIS_SQUARE_GEOMETRY,
        label="Tetrakis Square",
        picker_group="Periodic Mixed",
        picker_order=230,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
    ),
    SPECTRE_GEOMETRY: _translated_aperiodic_family(
        SPECTRE_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 3),
    ),
    TRIAKIS_TRIANGULAR_GEOMETRY: _single_variant_family(
        tiling_family=TRIAKIS_TRIANGULAR_GEOMETRY,
        label="Triakis Triangular",
        picker_group="Periodic Mixed",
        picker_order=240,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    HAT_MONOTILE_GEOMETRY: _translated_aperiodic_family(
        HAT_MONOTILE_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 2, 0, 3),
    ),
    PRISMATIC_PENTAGONAL_GEOMETRY: _single_variant_family(
        tiling_family=PRISMATIC_PENTAGONAL_GEOMETRY,
        label="Prismatic Pentagonal",
        picker_group="Periodic Mixed",
        picker_order=250,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 18),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    CHAIR_GEOMETRY: _translated_aperiodic_family(
        CHAIR_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    FLORET_PENTAGONAL_GEOMETRY: _single_variant_family(
        tiling_family=FLORET_PENTAGONAL_GEOMETRY,
        label="Floret Pentagonal",
        picker_group="Periodic Mixed",
        picker_order=260,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 18),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    TAYLOR_SOCOLAR_GEOMETRY: _translated_aperiodic_family(
        TAYLOR_SOCOLAR_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    SPHINX_GEOMETRY: _translated_aperiodic_family(
        SPHINX_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    ROBINSON_TRIANGLES_GEOMETRY: _translated_aperiodic_family(
        ROBINSON_TRIANGLES_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    TUEBINGEN_TRIANGLE_GEOMETRY: _translated_aperiodic_family(
        TUEBINGEN_TRIANGLE_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY: _translated_aperiodic_family(
        DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 7),
    ),
    SHIELD_GEOMETRY: _translated_aperiodic_family(
        SHIELD_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    PINWHEEL_GEOMETRY: _translated_aperiodic_family(
        PINWHEEL_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 4),
    ),
}

GEOMETRY_MINIMUM_GRID_DIMENSIONS = {
    variant.geometry_key: family.minimum_grid_dimension
    for family in TOPOLOGY_FAMILY_MANIFEST.values()
    for variant in family.variants
}


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
    "GEOMETRY_MINIMUM_GRID_DIMENSIONS",
    "HAT_MONOTILE_GEOMETRY",
    "HEX_GEOMETRY",
    "KAGOME_GEOMETRY",
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
    "TOPOLOGY_FAMILY_MANIFEST",
    "TopologyFamilyManifestEntry",
    "TopologyFamilyVariantManifestEntry",
    "TRIAKIS_TRIANGULAR_GEOMETRY",
    "TRIANGLE_GEOMETRY",
    "TUEBINGEN_TRIANGLE_GEOMETRY",
    "VERTEX_ADJACENCY",
]
