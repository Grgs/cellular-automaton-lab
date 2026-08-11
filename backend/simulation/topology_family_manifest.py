from __future__ import annotations

from dataclasses import dataclass, field

from backend.simulation.aperiodic_family_manifest import (
    AMMANN_BEENKER_GEOMETRY,
    APERIODIC_FAMILY_MANIFEST,
    CHAIR_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    ENNEAGONAL_9_FOLD_GEOMETRY,
    HAT_MONOTILE_GEOMETRY,
    HENDECAGONAL_11_FOLD_GEOMETRY,
    HEPTAGONAL_7_FOLD_GEOMETRY,
    L_TETROMINO_GEOMETRY,
    P_PENTOMINO_GEOMETRY,
    PENROSE_GEOMETRY,
    PENROSE_P1_DISTRIBUTED_GEOMETRY,
    PENROSE_P1_GEOMETRY,
    PENROSE_P1_PBS_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PINWHEEL_2_1_GEOMETRY,
    PINWHEEL_GEOMETRY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SOCOLAR_12_FOLD_GEOMETRY,
    SOCOLAR_HEXAGONAL_GEOMETRY,
    SPECTRE_GEOMETRY,
    SPHINX_COMPACT_PAIR_GEOMETRY,
    SPHINX_GEOMETRY,
    SPHINX_WIDE_PAIR_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TRIDECAGONAL_13_FOLD_GEOMETRY,
    TUEBINGEN_TRIANGLE_GEOMETRY,
    TURTLE_MONOTILE_GEOMETRY,
)
from backend.simulation.periodic_face_catalog_data import load_periodic_face_catalog
from backend.simulation.topology_catalog_types import SizingPolicyDefinition

DEFAULT_SQUARE_RULE = "conway"
DEFAULT_MIN_GRID_SIZE = 3
DEFAULT_TOPOLOGY_PATCH_DEPTH = 4

EDGE_ADJACENCY = "edge"
VERTEX_ADJACENCY = "vertex"
PENROSE_P1_DISTRIBUTED_MODE = "distributed"
PENROSE_P1_BOAT_STAR_MODE = "boat-star"
COMPACT_SEED = "compact"
WIDE_SEED = "wide"

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
RHOMBILLE_GEOMETRY = "rhombille"
DELTOIDAL_HEXAGONAL_GEOMETRY = "deltoidal-hexagonal"
TETRAKIS_SQUARE_GEOMETRY = "tetrakis-square"
# Square-grid split into congruent 45-45-90 triangles. This is intentionally
# distinct from the equilateral triangular lattice and gives users a simple
# non-regular triangle topology with anisotropic diagonal structure.
RIGHT_TRIANGLE_GEOMETRY = "right-triangle"
TRIAKIS_TRIANGULAR_GEOMETRY = "triakis-triangular"
DELTOIDAL_TRIHEXAGONAL_GEOMETRY = "deltoidal-trihexagonal"
PRISMATIC_PENTAGONAL_GEOMETRY = "prismatic-pentagonal"
FLORET_PENTAGONAL_GEOMETRY = "floret-pentagonal"
SNUB_SQUARE_DUAL_GEOMETRY = "snub-square-dual"
# 2-uniform tiling #10 [3^6; 3^2.6^2]: hexagons share three alternating
# edges in a honeycomb arrangement, leaving pure triangular-lattice gaps.
UNIFORM_2_10_GEOMETRY = "uniform-2-10-36-3262"
# 2-uniform tiling #18 [3^6; 3^2.4.3.4]: regular triangles and squares
# arranged with both pure-triangular and snub-square vertex orbits.
UNIFORM_2_18_GEOMETRY = "uniform-2-18-36-33434"
# 2-uniform tiling #13 [3^6; 3^2.4.12]: regular triangles, squares, and
# dodecagons arranged with pure-triangular and mixed vertex orbits.
UNIFORM_2_13_GEOMETRY = "uniform-2-13-36-32412"
# 2-uniform tiling #12 [3^2.6^2; 3^4.6]: alternating rows of regular
# hexagons with equilateral triangles filling the inter-row gaps.
UNIFORM_2_12_GEOMETRY = "uniform-2-12-3262-346"
# Demiregular tiling combining the 3.4.6.4 and 4.6.12 vertex orbits.
# Its regular triangle, square, hexagon, and dodecagon faces make it the
# catalog's first periodic tiling with four polygon kinds in one topology.
UNIFORM_34612_GEOMETRY = "uniform-3-4-6-12"


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
    mode_type: str = "adjacency"
    mode_label: str = "Mode"
    mode_labels: dict[str, str] = field(default_factory=dict)
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
    mode_type: str = "adjacency",
    mode_label: str = "Mode",
    mode_labels: dict[str, str] | None = None,
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
        mode_type=mode_type,
        mode_label=mode_label,
        mode_labels=mode_labels or {},
    )


def _periodic_face_families() -> dict[str, TopologyFamilyManifestEntry]:
    families: dict[str, TopologyFamilyManifestEntry] = {}
    for metadata in load_periodic_face_catalog():
        geometry = str(metadata["geometry"])
        sizing = metadata["sizing_policy"]
        families[geometry] = _single_variant_family(
            tiling_family=geometry,
            label=str(metadata["label"]),
            picker_group=str(metadata["picker_group"]),
            picker_order=int(metadata["picker_order"]),
            family=str(metadata["family"]),
            viewport_sync_mode=str(metadata["viewport_sync_mode"]),
            sizing_policy=SizingPolicyDefinition(
                str(sizing["control"]),
                int(sizing["default"]),
                int(sizing["min"]),
                int(sizing["max"]),
                int(sizing["unsafe_max"]) if "unsafe_max" in sizing else None,
            ),
            default_rule=str(metadata["default_rule"]),
            minimum_grid_dimension=int(metadata["minimum_grid_dimension"]),
        )
    return families


UNIFORM_2_19_V1_36_346_GEOMETRY = "uniform-2-19-v1-36-346"

UNIFORM_2_2_3122_34312_GEOMETRY = "uniform-2-2-3122-34312"

UNIFORM_3_4_36_3262_63_GEOMETRY = "uniform-3-4-36-3262-63"

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
    PENROSE_P1_GEOMETRY: _translated_aperiodic_family(
        PENROSE_P1_GEOMETRY,
        # The de Bruijn pentagrid construction is approximately linear in
        # cell count: 29 / 127 / 411 / 1161 / 3247 / 8995 / 24277 cells at
        # depths 0..6, with build times of <0.01s through ~1s respectively.
        # Same depth range as P3 since both use a pentagrid bounded by
        # ``half_extent = base * phi^d``.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 6),
        variants=(
            _variant(
                PENROSE_P1_DISTRIBUTED_GEOMETRY,
                PENROSE_P1_DISTRIBUTED_MODE,
                APERIODIC_FAMILY_MANIFEST[PENROSE_P1_GEOMETRY].default_rule,
            ),
            _variant(
                PENROSE_P1_PBS_GEOMETRY,
                PENROSE_P1_BOAT_STAR_MODE,
                APERIODIC_FAMILY_MANIFEST[PENROSE_P1_GEOMETRY].default_rule,
            ),
        ),
        mode_type="construction",
        mode_label="Construction",
        mode_labels={
            PENROSE_P1_DISTRIBUTED_MODE: "Distributed",
            PENROSE_P1_BOAT_STAR_MODE: "Boat-Star",
        },
    ),
    PENROSE_P2_GEOMETRY: _translated_aperiodic_family(
        PENROSE_P2_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 6),
    ),
    PENROSE_GEOMETRY: _translated_aperiodic_family(
        PENROSE_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 6),
        variants=(
            _variant(
                PENROSE_GEOMETRY,
                EDGE_ADJACENCY,
                APERIODIC_FAMILY_MANIFEST[PENROSE_GEOMETRY].default_rule,
            ),
            _variant(PENROSE_VERTEX_GEOMETRY, VERTEX_ADJACENCY, DEFAULT_SQUARE_RULE),
        ),
        mode_label="Adjacency",
        mode_labels={
            EDGE_ADJACENCY: "Edge adjacency",
            VERTEX_ADJACENCY: "Vertex adjacency",
        },
    ),
    AMMANN_BEENKER_GEOMETRY: _translated_aperiodic_family(
        AMMANN_BEENKER_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 4),
    ),
    SPECTRE_GEOMETRY: _translated_aperiodic_family(
        SPECTRE_GEOMETRY,
        # Depth 4 is the first showcase-sized Spectre patch whose interior
        # reads as a continuous field at the default viewport.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 4),
    ),
    HAT_MONOTILE_GEOMETRY: _translated_aperiodic_family(
        HAT_MONOTILE_GEOMETRY,
        # The H8 seed needs one additional substitution for the default patch
        # to use the canvas as a showcase instead of leaving sparse arms.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 3),
    ),
    TURTLE_MONOTILE_GEOMETRY: _translated_aperiodic_family(
        TURTLE_MONOTILE_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 2, 0, 3),
    ),
    CHAIR_GEOMETRY: _translated_aperiodic_family(
        CHAIR_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    L_TETROMINO_GEOMETRY: _translated_aperiodic_family(
        L_TETROMINO_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    P_PENTOMINO_GEOMETRY: _translated_aperiodic_family(
        P_PENTOMINO_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    TAYLOR_SOCOLAR_GEOMETRY: _translated_aperiodic_family(
        TAYLOR_SOCOLAR_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    SPHINX_GEOMETRY: _translated_aperiodic_family(
        SPHINX_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
        variants=(
            _variant(
                SPHINX_GEOMETRY,
                EDGE_ADJACENCY,
                APERIODIC_FAMILY_MANIFEST[SPHINX_GEOMETRY].default_rule,
            ),
            _variant(
                SPHINX_COMPACT_PAIR_GEOMETRY,
                COMPACT_SEED,
                APERIODIC_FAMILY_MANIFEST[SPHINX_GEOMETRY].default_rule,
            ),
            _variant(
                SPHINX_WIDE_PAIR_GEOMETRY,
                WIDE_SEED,
                APERIODIC_FAMILY_MANIFEST[SPHINX_GEOMETRY].default_rule,
            ),
        ),
        mode_type="seed",
        mode_label="Seed",
        mode_labels={
            EDGE_ADJACENCY: "Balanced seed",
            COMPACT_SEED: "Compact seed",
            WIDE_SEED: "Wide seed",
        },
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
        SizingPolicyDefinition(
            PATCH_DEPTH_CONTROL,
            default=3,
            minimum=0,
            maximum=6,
            unsafe_maximum=60,
        ),
    ),
    SHIELD_GEOMETRY: _translated_aperiodic_family(
        SHIELD_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 5),
    ),
    PINWHEEL_GEOMETRY: _translated_aperiodic_family(
        PINWHEEL_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 4),
    ),
    PINWHEEL_2_1_GEOMETRY: _translated_aperiodic_family(
        PINWHEEL_2_1_GEOMETRY,
        # Pinwheel 2-1 produces 5^d cells per root (vs Conway-Radin's
        # 2 * 5^d). Depth 4 = 625 cells; same effective ceiling as the
        # original pinwheel.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 4),
    ),
    HEPTAGONAL_7_FOLD_GEOMETRY: _translated_aperiodic_family(
        HEPTAGONAL_7_FOLD_GEOMETRY,
        # Multigrid crop half-extent 1.0 * 1.5^d gives ~62/139/317/707 cells at
        # depths 0..3. Default 2 is a snappy starting view; cap at 4.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 2, 0, 4),
    ),
    TRIDECAGONAL_13_FOLD_GEOMETRY: _translated_aperiodic_family(
        TRIDECAGONAL_13_FOLD_GEOMETRY,
        # Multigrid crop half-extent 0.5 * 1.5^d gives ~64/124/271/575 cells at
        # depths 0..3. Default 2 is a snappy starting view; cap at 4.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 2, 0, 4),
    ),
    **_periodic_face_families(),
    SOCOLAR_12_FOLD_GEOMETRY: _translated_aperiodic_family(
        SOCOLAR_12_FOLD_GEOMETRY,
        # Multigrid crop half-extent 1.0 * 1.55^d gives ~44/102/250/623/1450
        # cells at depths 0..4. Default 2 is a snappy starting view; cap at 4.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 2, 0, 4),
    ),
    ENNEAGONAL_9_FOLD_GEOMETRY: _translated_aperiodic_family(
        ENNEAGONAL_9_FOLD_GEOMETRY,
        # Multigrid crop half-extent 0.75 * 1.5^d gives ~62/137/292/641 cells at
        # depths 0..3. Default 2 is a snappy starting view; cap at 4.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 2, 0, 4),
    ),
    HENDECAGONAL_11_FOLD_GEOMETRY: _translated_aperiodic_family(
        HENDECAGONAL_11_FOLD_GEOMETRY,
        # Multigrid crop half-extent 0.6 * 1.5^d gives ~57/127/268/634 cells at
        # depths 0..3. Default 2 is a snappy starting view; cap at 4.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 2, 0, 4),
    ),
    SOCOLAR_HEXAGONAL_GEOMETRY: _translated_aperiodic_family(
        SOCOLAR_HEXAGONAL_GEOMETRY,
        # Cut-and-project ball radius 4 + 0.75*d gives linear cell growth
        # (~41/108/275 cells at depths 0/3/8). Depth 60 is ~6.3k cells and
        # builds in a few seconds, so the unsafe ceiling matches the
        # dodecagonal family's.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 3, 0, 8, unsafe_maximum=60),
    ),
}

GEOMETRY_MINIMUM_GRID_DIMENSIONS = {
    variant.geometry_key: family.minimum_grid_dimension
    for family in TOPOLOGY_FAMILY_MANIFEST.values()
    for variant in family.variants
}


def _is_module_export(name: str, value: object) -> bool:
    if name.startswith("_"):
        return False
    value_module = getattr(value, "__module__", None)
    if value_module is None:
        return True
    if value_module == __name__:
        return True
    if type(value).__module__ in {"typing", "typing_extensions"}:
        return True
    return False


# Auto-derive __all__ so adding a new geometry constant or family entry
# doesn't require touching a hand-maintained list. See the matching
# helper in aperiodic_family_manifest.py.
__all__ = sorted(name for name, value in globals().items() if _is_module_export(name, value))
