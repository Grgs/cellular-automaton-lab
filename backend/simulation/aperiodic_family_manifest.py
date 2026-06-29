from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AperiodicBuilderKind = Literal["compatibility_patch", "substitution_recipe"]
AperiodicImplementationStatus = Literal[
    "true_substitution",
    "exact_affine",
    "canonical_patch",
    "known_deviation",
]
AperiodicPickerGroup = Literal["Aperiodic", "Experimental"]


PENROSE_GEOMETRY = "penrose-p3-rhombs"
PENROSE_VERTEX_GEOMETRY = "penrose-p3-rhombs-vertex"
PENROSE_P2_GEOMETRY = "penrose-p2-kite-dart"
PENROSE_P1_GEOMETRY = "penrose-p1"
PENROSE_P1_DISTRIBUTED_GEOMETRY = "penrose-p1-pentagon-diamond"
PENROSE_P1_PBS_GEOMETRY = "penrose-p1-pentagon-boat-star"
AMMANN_BEENKER_GEOMETRY = "ammann-beenker"
SPECTRE_GEOMETRY = "spectre"
TAYLOR_SOCOLAR_GEOMETRY = "taylor-socolar"
SPHINX_GEOMETRY = "sphinx"
SPHINX_COMPACT_PAIR_GEOMETRY = "sphinx-compact-pair"
SPHINX_WIDE_PAIR_GEOMETRY = "sphinx-wide-pair"
HAT_MONOTILE_GEOMETRY = "hat-monotile"
TURTLE_MONOTILE_GEOMETRY = "turtle-monotile"
CHAIR_GEOMETRY = "chair"
L_TETROMINO_GEOMETRY = "l-tetromino"
P_PENTOMINO_GEOMETRY = "p-pentomino"
ROBINSON_TRIANGLES_GEOMETRY = "robinson-triangles"
TUEBINGEN_TRIANGLE_GEOMETRY = "tuebingen-triangle"
DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY = "dodecagonal-square-triangle"
SHIELD_GEOMETRY = "shield"
PINWHEEL_GEOMETRY = "pinwheel"
PINWHEEL_2_1_GEOMETRY = "pinwheel-2-1"
SOCOLAR_12_FOLD_GEOMETRY = "socolar-12-fold"
ENNEAGONAL_9_FOLD_GEOMETRY = "enneagonal-9-fold"
HEPTAGONAL_7_FOLD_GEOMETRY = "heptagonal-7-fold"
HENDECAGONAL_11_FOLD_GEOMETRY = "hendecagonal-11-fold"
TRIDECAGONAL_13_FOLD_GEOMETRY = "tridecagonal-13-fold"

THICK_RHOMB_KIND = "thick-rhomb"
THIN_RHOMB_KIND = "thin-rhomb"
KITE_KIND = "kite"
DART_KIND = "dart"
KITE_HALF_ACUTE_KIND = "kite-half-acute"
DART_HALF_OBTUSE_KIND = "dart-half-obtuse"
P1_PENTAGON_KIND = "p1-pentagon"
P1_PENTAGON_CLUSTER_KIND = "p1-pentagon-cluster"
P1_DIAMOND_KIND = "p1-diamond"
P1_BOAT_KIND = "p1-boat"
P1_STAR_KIND = "p1-star"
AMMANN_RHOMB_KIND = "rhomb"
AMMANN_SQUARE_KIND = "square"
SPECTRE_KIND = "spectre"
TAYLOR_HALF_HEX_LEFT_KIND = "taylor-half-hex-left"
TAYLOR_HALF_HEX_RIGHT_KIND = "taylor-half-hex-right"
SPHINX_KIND = "sphinx"
HAT_KIND = "hat"
TURTLE_KIND = "turtle"
CHAIR_KIND = "chair"
L_TETROMINO_KIND = "l-tetromino"
P_PENTOMINO_KIND = "p-pentomino"
ROBINSON_THICK_KIND = "robinson-thick"
ROBINSON_THIN_KIND = "robinson-thin"
TUEBINGEN_THICK_KIND = "tuebingen-thick"
TUEBINGEN_THIN_KIND = "tuebingen-thin"
DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND = "dodecagonal-square-triangle-square"
DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND = "dodecagonal-square-triangle-triangle"
SHIELD_SHIELD_KIND = "shield-shield"
SHIELD_SQUARE_KIND = "shield-square"
SHIELD_TRIANGLE_KIND = "shield-triangle"
PINWHEEL_TRIANGLE_KIND = "pinwheel-triangle"
PINWHEEL_2_1_SMALL_KIND = "pinwheel-2-1-small-triangle"
PINWHEEL_2_1_LARGE_KIND = "pinwheel-2-1-large-triangle"
SOCOLAR_12_FOLD_RHOMB_30_KIND = "socolar-12-fold-rhomb-30"
SOCOLAR_12_FOLD_RHOMB_60_KIND = "socolar-12-fold-rhomb-60"
SOCOLAR_12_FOLD_SQUARE_KIND = "socolar-12-fold-square"
# The four enneagonal-grid rhombi, named by their acute interior angle:
# 20 / 40 / 60 / 80 degrees (k * 180/9 for k = 1..4).
ENNEAGONAL_9_FOLD_RHOMB_20_KIND = "enneagonal-9-fold-rhomb-20"
ENNEAGONAL_9_FOLD_RHOMB_40_KIND = "enneagonal-9-fold-rhomb-40"
ENNEAGONAL_9_FOLD_RHOMB_60_KIND = "enneagonal-9-fold-rhomb-60"
ENNEAGONAL_9_FOLD_RHOMB_80_KIND = "enneagonal-9-fold-rhomb-80"
# The three heptagonal-grid rhombi, named by their acute interior angle:
# thin = pi/7 (~25.7 deg), medium = 2*pi/7 (~51.4 deg), wide = 3*pi/7 (~77.1 deg).
HEPTAGONAL_7_FOLD_THIN_KIND = "heptagonal-7-fold-thin"
HEPTAGONAL_7_FOLD_MEDIUM_KIND = "heptagonal-7-fold-medium"
HEPTAGONAL_7_FOLD_WIDE_KIND = "heptagonal-7-fold-wide"
# The five hendecagonal-grid rhombi, named by acute-angle index k (k = 1..5),
# whose acute interior angle is k * 180/11 degrees: rhomb-1 ~ 16.4 deg,
# rhomb-2 ~ 32.7 deg, rhomb-3 ~ 49.1 deg, rhomb-4 ~ 65.5 deg, rhomb-5 ~ 81.8 deg.
# (The angles are not integers, so an index label is clearer than a degree label.)
HENDECAGONAL_11_FOLD_RHOMB_1_KIND = "hendecagonal-11-fold-rhomb-1"
HENDECAGONAL_11_FOLD_RHOMB_2_KIND = "hendecagonal-11-fold-rhomb-2"
HENDECAGONAL_11_FOLD_RHOMB_3_KIND = "hendecagonal-11-fold-rhomb-3"
HENDECAGONAL_11_FOLD_RHOMB_4_KIND = "hendecagonal-11-fold-rhomb-4"
HENDECAGONAL_11_FOLD_RHOMB_5_KIND = "hendecagonal-11-fold-rhomb-5"
# The six tridecagonal-grid rhombi, named by acute-angle index k (k = 1..6),
# whose acute interior angle is k * 180/13 degrees (~13.8, ~27.7, ~41.5, ~55.4,
# ~69.2, ~83.1 deg). The angles are not integers, so an index label is clearer.
TRIDECAGONAL_13_FOLD_RHOMB_1_KIND = "tridecagonal-13-fold-rhomb-1"
TRIDECAGONAL_13_FOLD_RHOMB_2_KIND = "tridecagonal-13-fold-rhomb-2"
TRIDECAGONAL_13_FOLD_RHOMB_3_KIND = "tridecagonal-13-fold-rhomb-3"
TRIDECAGONAL_13_FOLD_RHOMB_4_KIND = "tridecagonal-13-fold-rhomb-4"
TRIDECAGONAL_13_FOLD_RHOMB_5_KIND = "tridecagonal-13-fold-rhomb-5"
TRIDECAGONAL_13_FOLD_RHOMB_6_KIND = "tridecagonal-13-fold-rhomb-6"

PENROSE_P1_TILE_FAMILY = "penrose-p1"
ROBINSON_TILE_FAMILY = "robinson"
TUEBINGEN_TILE_FAMILY = "tuebingen"
HAT_TILE_FAMILY = "hat"
TURTLE_TILE_FAMILY = "turtle"
DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY = DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY
SHIELD_TILE_FAMILY = "shield"
PINWHEEL_TILE_FAMILY = "pinwheel"
PINWHEEL_2_1_TILE_FAMILY = "pinwheel-2-1"
SOCOLAR_12_FOLD_TILE_FAMILY = "socolar-12-fold"
ENNEAGONAL_9_FOLD_TILE_FAMILY = "enneagonal-9-fold"
HEPTAGONAL_7_FOLD_TILE_FAMILY = "heptagonal-7-fold"
HENDECAGONAL_11_FOLD_TILE_FAMILY = "hendecagonal-11-fold"
TRIDECAGONAL_13_FOLD_TILE_FAMILY = "tridecagonal-13-fold"
L_TETROMINO_TILE_FAMILY = "l-tetromino"
P_PENTOMINO_TILE_FAMILY = "p-pentomino"


@dataclass(frozen=True)
class AperiodicFamilyManifestEntry:
    geometry: str
    catalog_label: str
    reference_label: str
    picker_group: AperiodicPickerGroup
    picker_order: int
    default_rule: str
    builder_kind: AperiodicBuilderKind
    implementation_status: AperiodicImplementationStatus
    public_cell_kinds: tuple[str, ...]
    promotion_blocker: str | None = None
    # Label used by ``aperiodic_contracts._depth_semantics``. The default
    # "substitution patch depth" covers most families; exact-affine
    # pinwheel-family families use "exact affine substitution depth" so
    # consumers can tell that the depth counter is a similarity inflation
    # count rather than a generic substitution round.
    depth_semantics_label: str = "substitution patch depth"
    # Whether the polygon-union surface-component check in
    # ``topology_validation.validate_topology`` applies to this family.
    # Disabled for families whose substitution inherently produces
    # T-junctions and point-only cell contacts (currently only
    # pinwheel-2-1, where the cell-adjacency graph stays connected but
    # Shapely's polygon union sees depth-specific near-disconnections).
    polygon_surface_check: bool = True

    @property
    def experimental(self) -> bool:
        return self.picker_group == "Experimental"


APERIODIC_FAMILY_MANIFEST: dict[str, AperiodicFamilyManifestEntry] = {
    PENROSE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=PENROSE_GEOMETRY,
        catalog_label="Penrose P3 Rhombs",
        reference_label="Penrose Rhombs",
        picker_group="Aperiodic",
        picker_order=220,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        # Built by the de Bruijn pentagrid construction in
        # ``backend/simulation/penrose.py`` -- mathematically equivalent to the
        # canonical Penrose substitution but produced by a bounding-box crop
        # over five intersecting strip families rather than by iterating
        # ``[[2,1],[1,1]]`` from a seed. Cells are valid Penrose thick / thin
        # rhombs with correct adjacency; the depth-to-cell-count sequence
        # (5/10/24/66 at depths 0..3) is governed by the half-extent
        # ``0.85 * phi^d`` rather than the substitution eigenvalue.
        implementation_status="canonical_patch",
        public_cell_kinds=(THICK_RHOMB_KIND, THIN_RHOMB_KIND),
    ),
    PENROSE_P1_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=PENROSE_P1_GEOMETRY,
        catalog_label="Penrose P1",
        reference_label="Penrose P1",
        picker_group="Aperiodic",
        picker_order=205,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        # Built by the de Bruijn multigrid construction in
        # ``backend/simulation/aperiodic_penrose_multigrid.py`` followed by a
        # P3 -> P1 vertex-merge pass over a non-singular pentagrid with
        # offsets ``(0.3, 0.4, 0.5, 0.6, 0.7)``. The vertex-merge pass detects
        # canonical Penrose vertex configurations (sun, star, two boat
        # variants) and collapses each into the corresponding P1 prototile,
        # giving a patch that distributes pentagons, diamonds, boats, and
        # stars across the crop without the centered singular ring present
        # in the all-zero pentagrid manifestation. The
        # ``p1-pentagon-cluster`` kind is the 10-vertex decagonal cell
        # emitted at each sun-vertex merge (canonical P1 pentagon
        # position); ``p1-pentagon`` is reserved for unmerged thick
        # rhombs that don't participate in any cluster (rhomb-region MLD
        # representatives of the pentagonal P1 prototile).
        implementation_status="canonical_patch",
        public_cell_kinds=(
            P1_PENTAGON_KIND,
            P1_PENTAGON_CLUSTER_KIND,
            P1_DIAMOND_KIND,
            P1_BOAT_KIND,
            P1_STAR_KIND,
        ),
    ),
    PENROSE_P2_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=PENROSE_P2_GEOMETRY,
        catalog_label="Penrose P2 Kite-Dart",
        reference_label="Penrose Kite-Dart",
        picker_group="Aperiodic",
        picker_order=210,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        # The 5-kite sun seed is geometrically asymmetric under the canonical
        # Robinson substitution: every acute half always finds a long-edge kite
        # partner, but obtuse halves on the patch perimeter can be left without
        # a short-edge partner and are emitted as ``dart-half-obtuse`` cells.
        # Acute halves are therefore never exposed as ``kite-half-acute`` from
        # this seed; the kind is declared on the half-tile constants but is
        # not part of P2's reachable surface.
        public_cell_kinds=(KITE_KIND, DART_KIND, DART_HALF_OBTUSE_KIND),
    ),
    AMMANN_BEENKER_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=AMMANN_BEENKER_GEOMETRY,
        catalog_label="Ammann-Beenker",
        reference_label="Ammann-Beenker",
        picker_group="Aperiodic",
        picker_order=230,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        implementation_status="true_substitution",
        public_cell_kinds=(AMMANN_RHOMB_KIND, AMMANN_SQUARE_KIND),
    ),
    SPECTRE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=SPECTRE_GEOMETRY,
        catalog_label="Spectre",
        reference_label="Spectre",
        picker_group="Aperiodic",
        picker_order=240,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(SPECTRE_KIND,),
    ),
    HAT_MONOTILE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=HAT_MONOTILE_GEOMETRY,
        catalog_label="Hat",
        reference_label="Hat",
        picker_group="Aperiodic",
        picker_order=250,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(HAT_KIND,),
    ),
    TURTLE_MONOTILE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=TURTLE_MONOTILE_GEOMETRY,
        catalog_label="Turtle",
        reference_label="Turtle",
        picker_group="Aperiodic",
        picker_order=255,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        # The Turtle is the Tile(sqrt(3), 1) member of the hat continuum and is
        # realised as the exact per-edge-class deformation of the verified Hat
        # tiling (Tile(1, sqrt(3))). It therefore inherits the Hat's true
        # metatile substitution structure and adjacency at every depth.
        implementation_status="true_substitution",
        public_cell_kinds=(TURTLE_KIND,),
    ),
    TAYLOR_SOCOLAR_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=TAYLOR_SOCOLAR_GEOMETRY,
        catalog_label="Taylor-Socolar",
        reference_label="Taylor-Socolar",
        picker_group="Aperiodic",
        picker_order=270,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(TAYLOR_HALF_HEX_LEFT_KIND, TAYLOR_HALF_HEX_RIGHT_KIND),
    ),
    SPHINX_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=SPHINX_GEOMETRY,
        catalog_label="Sphinx",
        reference_label="Sphinx",
        picker_group="Aperiodic",
        picker_order=280,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(SPHINX_KIND,),
    ),
    CHAIR_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=CHAIR_GEOMETRY,
        catalog_label="Chair",
        reference_label="Chair",
        picker_group="Aperiodic",
        picker_order=290,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(CHAIR_KIND,),
    ),
    L_TETROMINO_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=L_TETROMINO_GEOMETRY,
        catalog_label="L-Tetromino",
        reference_label="L-Tetromino",
        picker_group="Aperiodic",
        picker_order=295,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        # The L-tetromino is a rep-4 rep-tile: four half-scale copies tile a
        # double-scale copy. Iterating that exact integer-lattice dissection in
        # ``backend/simulation/aperiodic_l_tetromino.py`` gives a self-similar
        # (limit-periodic) substitution tiling, the tetromino analogue of the
        # L-tromino ``chair``. The substitution closes over four orientations
        # (the Klein four-group) with one child of each per tile.
        implementation_status="true_substitution",
        public_cell_kinds=(L_TETROMINO_KIND,),
    ),
    P_PENTOMINO_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=P_PENTOMINO_GEOMETRY,
        catalog_label="P-Pentomino",
        reference_label="P-Pentomino",
        picker_group="Aperiodic",
        picker_order=297,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        # The P-pentomino is the unique rep-4 pentomino: four half-scale copies
        # tile a double-scale copy (verified by exhaustive exact cover; all other
        # pentominoes fail). Iterating that exact integer-lattice dissection in
        # ``backend/simulation/aperiodic_p_pentomino.py`` gives a self-similar
        # (limit-periodic) substitution tiling, the pentomino member of the
        # rep-4 polyomino series alongside the L-tromino ``chair`` and
        # ``l-tetromino``. Being chiral, its substitution closes over all eight
        # dihedral (D4) orientations rather than a four-element subgroup.
        implementation_status="true_substitution",
        public_cell_kinds=(P_PENTOMINO_KIND,),
    ),
    ROBINSON_TRIANGLES_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=ROBINSON_TRIANGLES_GEOMETRY,
        catalog_label="Robinson Triangles",
        reference_label="Robinson Triangles",
        picker_group="Aperiodic",
        picker_order=300,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(ROBINSON_THICK_KIND, ROBINSON_THIN_KIND),
    ),
    TUEBINGEN_TRIANGLE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=TUEBINGEN_TRIANGLE_GEOMETRY,
        catalog_label="Tuebingen Triangle",
        reference_label="Tuebingen Triangle",
        picker_group="Aperiodic",
        picker_order=310,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
    ),
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        catalog_label="Dodecagonal Square-Triangle",
        reference_label="Dodecagonal Square-Triangle",
        picker_group="Experimental",
        picker_order=320,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        implementation_status="canonical_patch",
        public_cell_kinds=(
            DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
            DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
        ),
        promotion_blocker=(
            "Experimental until a recursive marked substitution replaces the finite Bielefeld crop; "
            "strict topology validation is currently proven through depth 11."
        ),
    ),
    SHIELD_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=SHIELD_GEOMETRY,
        catalog_label="Shield",
        reference_label="Shield",
        picker_group="Aperiodic",
        picker_order=330,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="true_substitution",
        public_cell_kinds=(SHIELD_SHIELD_KIND, SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
    ),
    PINWHEEL_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=PINWHEEL_GEOMETRY,
        catalog_label="Pinwheel",
        reference_label="Pinwheel",
        picker_group="Aperiodic",
        picker_order=340,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        implementation_status="exact_affine",
        public_cell_kinds=(PINWHEEL_TRIANGLE_KIND,),
        depth_semantics_label="exact affine substitution depth",
        # The similarity-correct pinwheel subdivision is not edge-to-edge:
        # hypotenuse midpoints meet neighbor vertices at T-junctions, and the
        # float conversion of the exact rational coordinates leaves hairline
        # gaps that split Shapely's polygon-union surface (4 components at
        # depth 3; a 1e-9 buffer reunifies it to one). The cell-adjacency
        # graph is connected, overlap-free, and hole-free at every depth, so
        # only the union surface-component check is waived -- the same waiver
        # pinwheel-2-1 carries for the same reason.
        polygon_surface_check=False,
    ),
    PINWHEEL_2_1_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=PINWHEEL_2_1_GEOMETRY,
        catalog_label="Pinwheel 2-1",
        reference_label="Pinwheel 2-1",
        picker_group="Aperiodic",
        picker_order=345,
        default_rule="life-b2-s23",
        builder_kind="substitution_recipe",
        # Two-prototile pinwheel variant from the Bielefeld Tilings
        # Encyclopedia (``pinwheel-2-1``): 1:4:sqrt(17) right triangle
        # subdividing into one small child (scale 1/sqrt(17)) at the
        # right-angle corner plus four large children (scale 2/sqrt(17))
        # filling the rest. Construction is exact in Fractions
        # (foot-of-altitude + midpoints all yield rational coordinates).
        implementation_status="exact_affine",
        public_cell_kinds=(PINWHEEL_2_1_SMALL_KIND, PINWHEEL_2_1_LARGE_KIND),
        depth_semantics_label="exact affine substitution depth",
        # pinwheel-2-1's substitution inherently produces T-junctions and
        # point-only cell contacts; the cell-adjacency graph is connected
        # at every depth but Shapely's polygon-union surface check sees
        # near-disconnected pieces at depth 3 specifically. See
        # docs/TILING_KNOWN_DEVIATIONS.md for the full rationale.
        polygon_surface_check=False,
    ),
    SOCOLAR_12_FOLD_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=SOCOLAR_12_FOLD_GEOMETRY,
        catalog_label="Socolar 12-fold (rhombs)",
        reference_label="Socolar 12-fold (rhombs)",
        picker_group="Aperiodic",
        picker_order=235,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        # Built by the de Bruijn generalized-dual (multigrid) construction in
        # ``backend/simulation/aperiodic_socolar_12_fold.py`` over six line
        # families spaced 30 degrees apart (a dodecagrid). The dual of that
        # multigrid is the 12-fold dodecagonal rhomb tiling -- the rhombus
        # variant of the Socolar tiling (Socolar 1989), which is mutually
        # locally derivable from the already-shipped ``shield`` tiling. Cells
        # are the three dodecagonal rhombi (30-degree, 60-degree, and the
        # 90-degree square); like the Penrose multigrid families this is a
        # bounding-box crop, so the depth-to-cell-count sequence is governed
        # by the half-extent rather than a substitution eigenvalue. This is the
        # dodecagonal *rhombus* tiling: the canonical Socolar tiling proper uses
        # a different prototile set {30-degree rhomb, square, hexagon} (no
        # 60-degree rhomb) with inflation factor 2 + sqrt(3) and an oriented
        # center-inclusion substitution, which is not reproduced here. See
        # docs/TILING_KNOWN_DEVIATIONS.md.
        implementation_status="canonical_patch",
        public_cell_kinds=(
            SOCOLAR_12_FOLD_RHOMB_30_KIND,
            SOCOLAR_12_FOLD_RHOMB_60_KIND,
            SOCOLAR_12_FOLD_SQUARE_KIND,
        ),
    ),
    ENNEAGONAL_9_FOLD_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=ENNEAGONAL_9_FOLD_GEOMETRY,
        catalog_label="Enneagonal 9-fold (rhombs)",
        reference_label="Enneagonal 9-fold (rhombs)",
        picker_group="Aperiodic",
        picker_order=238,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        # Built by the de Bruijn generalized-dual (multigrid) construction in
        # ``backend/simulation/aperiodic_enneagonal_9_fold.py`` over nine line
        # families spaced 2*pi/9 (20 degrees) apart (an enneagrid). Nine is odd,
        # so all nine families are used directly with no antiparallel-family
        # degeneracy. The dual of that multigrid is the 9-fold rhomb tiling:
        # every cell is one of the four enneagonal rhombi whose acute angles are
        # 20, 40, 60, and 80 degrees (k * 180/9 for k = 1..4). Like the Penrose
        # and Socolar multigrid families this is a bounding-box crop, so the
        # depth-to-cell-count sequence is governed by the half-extent rather
        # than a substitution eigenvalue. This is the de Bruijn enneagrid
        # rhombus tiling; it is not the Danzer-style 9-fold *substitution*
        # tiling (a different, marked-prototile construction). See
        # docs/TILING_KNOWN_DEVIATIONS.md.
        implementation_status="canonical_patch",
        public_cell_kinds=(
            ENNEAGONAL_9_FOLD_RHOMB_20_KIND,
            ENNEAGONAL_9_FOLD_RHOMB_40_KIND,
            ENNEAGONAL_9_FOLD_RHOMB_60_KIND,
            ENNEAGONAL_9_FOLD_RHOMB_80_KIND,
        ),
    ),
    HEPTAGONAL_7_FOLD_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=HEPTAGONAL_7_FOLD_GEOMETRY,
        catalog_label="Heptagonal 7-fold (rhombs)",
        reference_label="Heptagonal 7-fold (rhombs)",
        picker_group="Aperiodic",
        picker_order=236,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        # Built by the de Bruijn generalized-dual (multigrid) construction in
        # ``backend/simulation/aperiodic_heptagonal_7_fold.py`` over seven line
        # families spaced 2*pi/7 apart (a heptagrid). Seven is odd, so all
        # seven families are used directly with no antiparallel-family
        # degeneracy. The dual of that multigrid is the 7-fold rhomb tiling:
        # every cell is one of the three heptagonal rhombi whose acute angles
        # are pi/7 (thin), 2*pi/7 (medium), and 3*pi/7 (wide). Like the Penrose
        # and Socolar multigrid families this is a bounding-box crop, so the
        # depth-to-cell-count sequence is governed by the half-extent rather
        # than a substitution eigenvalue. This is the de Bruijn heptagrid
        # rhombus tiling; it is not the Goodman-Strauss 7-fold *substitution*
        # tiling (a different, marked-prototile construction). See
        # docs/TILING_KNOWN_DEVIATIONS.md.
        implementation_status="canonical_patch",
        public_cell_kinds=(
            HEPTAGONAL_7_FOLD_THIN_KIND,
            HEPTAGONAL_7_FOLD_MEDIUM_KIND,
            HEPTAGONAL_7_FOLD_WIDE_KIND,
        ),
    ),
    HENDECAGONAL_11_FOLD_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=HENDECAGONAL_11_FOLD_GEOMETRY,
        catalog_label="Hendecagonal 11-fold (rhombs)",
        reference_label="Hendecagonal 11-fold (rhombs)",
        picker_group="Aperiodic",
        picker_order=239,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        # Built by the de Bruijn generalized-dual (multigrid) construction in
        # ``backend/simulation/aperiodic_hendecagonal_11_fold.py`` over eleven
        # line families spaced 2*pi/11 apart (a hendecagrid). Eleven is prime
        # (and odd), so all eleven families are used directly with no
        # antiparallel-family degeneracy and no sub-symmetry concurrences. The
        # dual of that multigrid is the 11-fold rhomb tiling: every cell is one
        # of the five hendecagonal rhombi whose acute angles are k * 180/11 for
        # k = 1..5 (~16.4, ~32.7, ~49.1, ~65.5, ~81.8 degrees). Like the Penrose
        # and Socolar multigrid families this is a bounding-box crop, so the
        # depth-to-cell-count sequence is governed by the half-extent rather
        # than a substitution eigenvalue. This is the de Bruijn hendecagrid
        # rhombus tiling; it is not a marked-prototile *substitution* tiling.
        # See docs/TILING_KNOWN_DEVIATIONS.md.
        implementation_status="canonical_patch",
        public_cell_kinds=(
            HENDECAGONAL_11_FOLD_RHOMB_1_KIND,
            HENDECAGONAL_11_FOLD_RHOMB_2_KIND,
            HENDECAGONAL_11_FOLD_RHOMB_3_KIND,
            HENDECAGONAL_11_FOLD_RHOMB_4_KIND,
            HENDECAGONAL_11_FOLD_RHOMB_5_KIND,
        ),
    ),
    TRIDECAGONAL_13_FOLD_GEOMETRY: AperiodicFamilyManifestEntry(
        geometry=TRIDECAGONAL_13_FOLD_GEOMETRY,
        catalog_label="Tridecagonal 13-fold (rhombs)",
        reference_label="Tridecagonal 13-fold (rhombs)",
        picker_group="Aperiodic",
        picker_order=237,
        default_rule="life-b2-s23",
        builder_kind="compatibility_patch",
        # Built by the de Bruijn generalized-dual (multigrid) construction in
        # ``backend/simulation/aperiodic_tridecagonal_13_fold.py`` over thirteen
        # line families spaced 2*pi/13 apart (a tridecagrid). Thirteen is prime
        # (and odd), so all thirteen families are fully independent -- no
        # antiparallel-family degeneracy and no sub-symmetry concurrences. The
        # dual of that multigrid is the 13-fold rhomb tiling: every cell is one
        # of the six tridecagonal rhombi whose acute angles are k * 180/13 for
        # k = 1..6 (~13.8, ~27.7, ~41.5, ~55.4, ~69.2, ~83.1 degrees). Like the
        # Penrose and Socolar multigrid families this is a bounding-box crop, so
        # the depth-to-cell-count sequence is governed by the half-extent rather
        # than a substitution eigenvalue. This is the de Bruijn tridecagrid
        # rhombus tiling; it is not a marked-prototile *substitution* tiling.
        # See docs/TILING_KNOWN_DEVIATIONS.md.
        implementation_status="canonical_patch",
        public_cell_kinds=(
            TRIDECAGONAL_13_FOLD_RHOMB_1_KIND,
            TRIDECAGONAL_13_FOLD_RHOMB_2_KIND,
            TRIDECAGONAL_13_FOLD_RHOMB_3_KIND,
            TRIDECAGONAL_13_FOLD_RHOMB_4_KIND,
            TRIDECAGONAL_13_FOLD_RHOMB_5_KIND,
            TRIDECAGONAL_13_FOLD_RHOMB_6_KIND,
        ),
    ),
}

APERIODIC_FAMILY_IDS: tuple[str, ...] = tuple(
    geometry
    for geometry, _entry in sorted(
        APERIODIC_FAMILY_MANIFEST.items(),
        key=lambda item: item[1].picker_order,
    )
)
EXPERIMENTAL_APERIODIC_FAMILY_IDS: tuple[str, ...] = tuple(
    geometry
    for geometry in APERIODIC_FAMILY_IDS
    if APERIODIC_FAMILY_MANIFEST[geometry].experimental
)


# Variant geometries render a distinct seed or construction of a base catalog
# family and therefore share that family's manifest entry (builder kind, public
# cell kinds, picker metadata). Map each variant back to the owning family.
_VARIANT_GEOMETRY_FAMILY: dict[str, str] = {
    PENROSE_VERTEX_GEOMETRY: PENROSE_GEOMETRY,
    PENROSE_P1_DISTRIBUTED_GEOMETRY: PENROSE_P1_GEOMETRY,
    PENROSE_P1_PBS_GEOMETRY: PENROSE_P1_GEOMETRY,
    SPHINX_COMPACT_PAIR_GEOMETRY: SPHINX_GEOMETRY,
    SPHINX_WIDE_PAIR_GEOMETRY: SPHINX_GEOMETRY,
}


def manifest_family_geometry(geometry: str) -> str:
    """Return the catalog family geometry that owns ``geometry``'s manifest entry.

    Most geometries own their own entry and map to themselves. Seed/construction
    variant geometries (e.g. the Sphinx pair seeds, the Penrose P1 sub-modes)
    map back to the base family that carries the shared manifest metadata.
    """
    return _VARIANT_GEOMETRY_FAMILY.get(geometry, geometry)


def get_aperiodic_family_manifest_entry(geometry: str) -> AperiodicFamilyManifestEntry:
    try:
        return APERIODIC_FAMILY_MANIFEST[geometry]
    except KeyError as error:
        raise ValueError(f"Unsupported aperiodic family {geometry!r}.") from error


def _is_module_export(name: str, value: object) -> bool:
    if name.startswith("_"):
        return False
    # Re-exported imports like ``Literal`` carry their original ``__module__``;
    # exclude them while still admitting locally-defined classes / functions
    # and ``Literal[...]`` type aliases (whose value's *type* lives in typing).
    value_module = getattr(value, "__module__", None)
    if value_module is None:
        return True  # plain constants (strings, dicts, tuples, ...)
    if value_module == __name__:
        return True
    if type(value).__module__ in {"typing", "typing_extensions"}:
        return True
    return False


# Auto-derive __all__ so adding a new GEOMETRY / KIND / TILE_FAMILY
# constant or manifest entry doesn't require touching a hand-maintained
# list (which has accidentally been the source of "forgot to export"
# CI failures more than once).
__all__ = sorted(name for name, value in globals().items() if _is_module_export(name, value))
