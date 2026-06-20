from __future__ import annotations

from dataclasses import dataclass

from backend.simulation.aperiodic_family_manifest import (
    AMMANN_BEENKER_GEOMETRY,
    APERIODIC_FAMILY_MANIFEST,
    CHAIR_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    HAT_MONOTILE_GEOMETRY,
    PENROSE_GEOMETRY,
    PENROSE_P1_GEOMETRY,
    PENROSE_P1_PBS_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PINWHEEL_2_1_GEOMETRY,
    PINWHEEL_GEOMETRY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SPECTRE_GEOMETRY,
    SPHINX_GEOMETRY,
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
# Square-grid split into congruent 45-45-90 triangles. This is intentionally
# distinct from the equilateral triangular lattice and gives users a simple
# non-regular triangle topology with anisotropic diagonal structure.
RIGHT_TRIANGLE_GEOMETRY = "right-triangle"
TRIAKIS_TRIANGULAR_GEOMETRY = "triakis-triangular"
DELTOIDAL_TRIHEXAGONAL_GEOMETRY = "deltoidal-trihexagonal"
PRISMATIC_PENTAGONAL_GEOMETRY = "prismatic-pentagonal"
FLORET_PENTAGONAL_GEOMETRY = "floret-pentagonal"
TYPE_7_PENTAGONAL_GEOMETRY = "type-7-pentagonal"
SNUB_SQUARE_DUAL_GEOMETRY = "snub-square-dual"
KISRHOMBILLE_GEOMETRY = "kisrhombille"
# Tiltwork is a non-canonical periodic tiling invented for this catalog:
# a unit square with a center diamond (rotated square) inset and four
# right-isosceles triangles in the corners. Vertex configurations are
# (triangle, triangle, diamond, triangle, triangle, diamond) at edge
# midpoints and (triangle, triangle, triangle, triangle) at corners.
TILTWORK_GEOMETRY = "tiltwork"
# Pythagorean tiling: classic two-prototile tiling by two square sizes (here
# 1:2 ratio). Non-edge-to-edge: every long-edge midpoint is a T-junction
# where a small square's vertex meets the middle of a big square's edge.
# To make every edge match exactly, big squares are modeled as 8-vertex
# polygons (four corners plus four collinear mid-edge vertices).
PYTHAGOREAN_GEOMETRY = "pythagorean"
# Herringbone tiling: 2:1 bricks in two orientations (horizontal and
# vertical). Rows of horizontal bricks alternate with rows of vertical
# bricks; each horizontal brick's long edge is met by the short edges
# of two perpendicular vertical bricks at its midpoint (T-junctions).
# To make adjacency match, horizontal bricks are modeled as 6-vertex
# polygons (four corners plus two collinear mid-long-edge vertices).
HERRINGBONE_GEOMETRY = "herringbone"
# Basketweave tiling: 2:1 bricks in two orientations arranged so that
# pairs of parallel bricks form 50x50 blocks, which then alternate
# orientation in a checkerboard pattern. Non-edge-to-edge: every brick
# has exactly one long edge whose midpoint hosts a T-junction with a
# perpendicular brick. Each brick is modeled as a 5-vertex polygon
# (four corners plus a single mid-edge vertex on that long edge).
BASKETWEAVE_GEOMETRY = "basketweave"
# Type-4 pentagonal cross motif: four congruent pentagons meet in a p4
# cross-shaped cluster, giving the periodic catalog a visually distinct
# pentagonal option without leaning on triangle/square subdivisions.
PENTAGON_CROSSES_GEOMETRY = "pentagon-crosses"
# 2-uniform tiling [3^6; 3^3.4^2]: combines pure-triangular and
# elongated-triangular vertex types. Constructed by alternating wide
# strips of pure triangular tiling (2 triangle rows tall, height
# sqrt(3) at unit edge) with a single row of squares (height 1).
# Interior vertices of the triangle strip have 6 triangles meeting
# (3^6); vertices on the triangle/square boundary have 3 triangles
# plus 2 squares (3^3.4^2). It's the smallest 2-uniform tiling that
# uses only regular polygons and only two prototile shapes.
TRIANGULAR_SQUARE_2UNIFORM_GEOMETRY = "triangular-square-2uniform"
# 2-uniform tiling [3.6.3.6; 3^2.6^2]: combines trihexagonal vertex types
# with "elongated trihex" vertices. Constructed from rows of pointy-top
# hexagons that share vertical edges within each row (creating (3^2.6^2)
# vertices at the shared corners), with diamond gaps between rows filled
# by pairs of equilateral triangles. The vertices where adjacent rows of
# hexes meet end-on-end are (3.6.3.6) vertices (THTH order). Edge-to-edge;
# no T-junctions. Uses only triangles + hexagons (complements the
# triangle+square 2-uniform).
TRIHEX_2UNIFORM_3636_3366_GEOMETRY = "trihex-2uniform-3636-3366"
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
# Stein-14 pentagonal: the 14th of the 15 known monohedral convex pentagonal
# tilings, discovered by Rolf Stein (1985). Has completely determined tile
# proportions (no degrees of freedom): 2a=2c=d=e with A=90 deg and angle B
# satisfying sin(B) = (sqrt(57) - 3) / 8 (B obtuse ~145.34 deg). The 6-tile
# primitive unit has p2 symmetry and is 3-isohedral (3 orbit classes of tiles
# under p2). Genuinely SKEW LATTICE: the two translation basis vectors do
# not span an axis-aligned rectangle, requiring the periodic_face system's
# cumulative-skew lattice_skew_x mode (every row shifted by k*skew, not the
# alternating-row brick semantic).
STEIN_14_PENTAGONAL_GEOMETRY = "stein-14-pentagonal"


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
        default_rule="kagome-life",
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
    KISRHOMBILLE_GEOMETRY: _single_variant_family(
        tiling_family=KISRHOMBILLE_GEOMETRY,
        label="Kisrhombille",
        picker_group="Periodic Mixed",
        picker_order=225,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    PENROSE_P1_GEOMETRY: _translated_aperiodic_family(
        PENROSE_P1_GEOMETRY,
        # The de Bruijn pentagrid construction is approximately linear in
        # cell count: 29 / 127 / 411 / 1161 / 3247 / 8995 / 24277 cells at
        # depths 0..6, with build times of <0.01s through ~1s respectively.
        # Same depth range as P3 since both use a pentagrid bounded by
        # ``half_extent = base * phi^d``.
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 6),
    ),
    PENROSE_P1_PBS_GEOMETRY: _translated_aperiodic_family(
        PENROSE_P1_PBS_GEOMETRY,
        SizingPolicyDefinition(PATCH_DEPTH_CONTROL, 4, 0, 6),
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
    RIGHT_TRIANGLE_GEOMETRY: _single_variant_family(
        tiling_family=RIGHT_TRIANGLE_GEOMETRY,
        label="Right-Triangle",
        picker_group="Periodic Mixed",
        picker_order=232,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    TILTWORK_GEOMETRY: _single_variant_family(
        tiling_family=TILTWORK_GEOMETRY,
        label="Tiltwork",
        picker_group="Periodic Mixed",
        picker_order=235,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    PYTHAGOREAN_GEOMETRY: _single_variant_family(
        tiling_family=PYTHAGOREAN_GEOMETRY,
        label="Pythagorean",
        picker_group="Periodic Mixed",
        picker_order=237,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    HERRINGBONE_GEOMETRY: _single_variant_family(
        tiling_family=HERRINGBONE_GEOMETRY,
        label="Herringbone",
        picker_group="Periodic Mixed",
        picker_order=238,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    TRIANGULAR_SQUARE_2UNIFORM_GEOMETRY: _single_variant_family(
        tiling_family=TRIANGULAR_SQUARE_2UNIFORM_GEOMETRY,
        label="2-uniform Triangle+Square (3^6; 3^3.4^2)",
        picker_group="Periodic Mixed",
        picker_order=239,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
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
    BASKETWEAVE_GEOMETRY: _single_variant_family(
        tiling_family=BASKETWEAVE_GEOMETRY,
        label="Basketweave",
        picker_group="Periodic Mixed",
        picker_order=242,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    PENTAGON_CROSSES_GEOMETRY: _single_variant_family(
        tiling_family=PENTAGON_CROSSES_GEOMETRY,
        label="Pentagon Crosses",
        picker_group="Periodic Mixed",
        picker_order=243,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    TRIHEX_2UNIFORM_3636_3366_GEOMETRY: _single_variant_family(
        tiling_family=TRIHEX_2UNIFORM_3636_3366_GEOMETRY,
        label="2-uniform Trihex (3.6.3.6; 3^2.6^2)",
        picker_group="Periodic Mixed",
        picker_order=244,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    UNIFORM_2_10_GEOMETRY: _single_variant_family(
        tiling_family=UNIFORM_2_10_GEOMETRY,
        label="2-uniform #10 (3^6; 3^2.6^2)",
        picker_group="Periodic Mixed",
        picker_order=249,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 18),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    UNIFORM_2_18_GEOMETRY: _single_variant_family(
        tiling_family=UNIFORM_2_18_GEOMETRY,
        label="2-uniform #18 (3^6; 3^2.4.3.4)",
        picker_group="Periodic Mixed",
        picker_order=246,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    UNIFORM_34612_GEOMETRY: _single_variant_family(
        tiling_family=UNIFORM_34612_GEOMETRY,
        label="2-uniform 3-4-6-12",
        picker_group="Periodic Mixed",
        picker_order=247,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 18),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    UNIFORM_2_13_GEOMETRY: _single_variant_family(
        tiling_family=UNIFORM_2_13_GEOMETRY,
        label="2-uniform #13 (3^6; 3^2.4.12)",
        picker_group="Periodic Mixed",
        picker_order=248,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 10, 8, 18),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    UNIFORM_2_12_GEOMETRY: _single_variant_family(
        tiling_family=UNIFORM_2_12_GEOMETRY,
        label="2-uniform #12 (3^2.6^2; 3^4.6)",
        picker_group="Periodic Mixed",
        picker_order=249,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 12, 8, 20),
        default_rule="life-b2-s23",
        minimum_grid_dimension=1,
    ),
    STEIN_14_PENTAGONAL_GEOMETRY: _single_variant_family(
        tiling_family=STEIN_14_PENTAGONAL_GEOMETRY,
        label="Stein 14 Pentagonal",
        picker_group="Periodic Mixed",
        picker_order=245,
        family="mixed",
        viewport_sync_mode="backend-sync",
        sizing_policy=SizingPolicyDefinition(CELL_SIZE_CONTROL, 8, 6, 14),
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
    TYPE_7_PENTAGONAL_GEOMETRY: _single_variant_family(
        tiling_family=TYPE_7_PENTAGONAL_GEOMETRY,
        label="Type 7 Pentagonal",
        picker_group="Periodic Mixed",
        picker_order=265,
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
