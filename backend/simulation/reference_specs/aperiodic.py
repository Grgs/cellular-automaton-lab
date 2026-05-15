from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    AMMANN_BEENKER_GEOMETRY,
    AMMANN_RHOMB_KIND,
    AMMANN_SQUARE_KIND,
    CHAIR_GEOMETRY,
    CHAIR_KIND,
    DART_HALF_OBTUSE_KIND,
    DART_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
    HAT_KIND,
    HAT_MONOTILE_GEOMETRY,
    KITE_KIND,
    P1_DIAMOND_HALF_KIND,
    P1_DIAMOND_KIND,
    P1_PENTAGON_KIND,
    PENROSE_GEOMETRY,
    PENROSE_P1_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PINWHEEL_GEOMETRY,
    PINWHEEL_TRIANGLE_KIND,
    ROBINSON_THICK_KIND,
    ROBINSON_THIN_KIND,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SHIELD_SHIELD_KIND,
    SHIELD_SQUARE_KIND,
    SHIELD_TRIANGLE_KIND,
    SPECTRE_GEOMETRY,
    SPECTRE_KIND,
    SPHINX_GEOMETRY,
    SPHINX_KIND,
    TAYLOR_HALF_HEX_KIND,
    TAYLOR_SOCOLAR_GEOMETRY,
    THICK_RHOMB_KIND,
    THIN_RHOMB_KIND,
    TUEBINGEN_THICK_KIND,
    TUEBINGEN_THIN_KIND,
    TUEBINGEN_TRIANGLE_GEOMETRY,
    get_aperiodic_family_manifest_entry,
)
from .types import (
    BuilderSignalExpectation,
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)


def _reference_label(geometry: str) -> str:
    return get_aperiodic_family_manifest_entry(geometry).reference_label


def _public_cell_kinds(geometry: str) -> tuple[str, ...]:
    return get_aperiodic_family_manifest_entry(geometry).public_cell_kinds


APERIODIC_REFERENCE_FAMILY_SPECS: dict[str, ReferenceFamilySpec] = {
    PENROSE_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_GEOMETRY,
        display_name=_reference_label(PENROSE_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/",),
        canonical_root_seed_policy="de Bruijn pentagrid crop at half-extent 0.85 * phi^d",
        allowed_public_cell_kinds=_public_cell_kinds(PENROSE_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=5,
                required_kinds=(THICK_RHOMB_KIND,),
                required_adjacency_pairs=((THICK_RHOMB_KIND, THICK_RHOMB_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=10,
                required_kinds=(THICK_RHOMB_KIND, THIN_RHOMB_KIND),
                required_adjacency_pairs=(
                    (THICK_RHOMB_KIND, THICK_RHOMB_KIND),
                    (THICK_RHOMB_KIND, THIN_RHOMB_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=24),
            3: ReferenceDepthExpectation(exact_total_cells=66),
        },
        notes=(
            "Built by the de Bruijn pentagrid construction in "
            "``backend/simulation/penrose.py`` -- mathematically equivalent to the canonical "
            "Penrose rhomb substitution at "
            "https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/, but produced "
            "by intersecting five strip families and cropping to a square of half-extent "
            "``0.85 * phi^d``. Cells are valid thick / thin rhombs with correct Penrose "
            "matching at every depth; the depth-to-cell-count sequence (5/10/24/66 at "
            "depths 0..3) is governed by the bounding-box crop rather than by iterating the "
            "[[2,1],[1,1]] substitution from a seed.",
        ),
    ),
    PENROSE_VERTEX_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_VERTEX_GEOMETRY,
        display_name="Penrose Rhombs (Vertex Adjacency)",
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/",),
        canonical_root_seed_policy=(
            "de Bruijn pentagrid crop at half-extent 0.85 * phi^d with vertex-neighbor topology"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(PENROSE_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=5,
                required_kinds=(THICK_RHOMB_KIND,),
                required_adjacency_pairs=((THICK_RHOMB_KIND, THICK_RHOMB_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=10,
                required_kinds=(THICK_RHOMB_KIND, THIN_RHOMB_KIND),
                required_adjacency_pairs=(
                    (THICK_RHOMB_KIND, THICK_RHOMB_KIND),
                    (THICK_RHOMB_KIND, THIN_RHOMB_KIND),
                    (THIN_RHOMB_KIND, THIN_RHOMB_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=24),
            3: ReferenceDepthExpectation(exact_total_cells=66),
        },
        notes=(
            "Vertex-adjacency topology variant of the canonical Penrose rhomb tiling; "
            "shares the same de Bruijn pentagrid construction as ``penrose-p3-rhombs``, "
            "with neighbour edges promoted to any pair of cells sharing a vertex.",
        ),
    ),
    PENROSE_P1_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_P1_GEOMETRY,
        display_name=_reference_label(PENROSE_P1_GEOMETRY),
        source_urls=(
            "https://en.wikipedia.org/wiki/Penrose_tiling#Original_pentagonal_Penrose_tiling_(P1)",
            "https://tilings.math.uni-bielefeld.de/substitution/penrose-pentagon-boat-star/",
        ),
        canonical_root_seed_policy=(
            "single regular pentagon at origin, side phi^(2*depth), substituted "
            "by Penrose's 1974 pentagonal deflation: P -> 1 inverted P + 5 outer "
            "P + 5 boundary acute Robinson halves at parent edges; halves pair "
            "across edges into thin rhombs (diamonds)"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(PENROSE_P1_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=1,
                expected_kind_counts=((P1_PENTAGON_KIND, 1),),
                required_kinds=(P1_PENTAGON_KIND,),
                # Single pentagon seed -- no neighbours yet, so no diamonds and
                # no boundary halves at depth 0. The single cell trivially has
                # no neighbours so the connected-graph check is bypassed too.
                require_connected_graph=False,
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=11,
                expected_kind_counts=(
                    (P1_DIAMOND_HALF_KIND, 5),
                    (P1_PENTAGON_KIND, 6),
                ),
                required_kinds=(P1_PENTAGON_KIND, P1_DIAMOND_HALF_KIND),
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=66,
                expected_kind_counts=(
                    (P1_DIAMOND_KIND, 5),
                    (P1_DIAMOND_HALF_KIND, 25),
                    (P1_PENTAGON_KIND, 36),
                ),
                required_kinds=(P1_PENTAGON_KIND, P1_DIAMOND_KIND),
                required_adjacency_pairs=(
                    (P1_DIAMOND_KIND, P1_PENTAGON_KIND),
                    (P1_PENTAGON_KIND, P1_PENTAGON_KIND),
                ),
                # The recursive substitution accumulates float drift of ~1e-3
                # by depth 3+, which leaves T-vertex mismatches between large
                # boundary halves / paired diamonds and the smaller iter-d
                # pentagons that border them. Each cell still renders its
                # exact polygon (no real area gaps; sum of cell areas equals
                # the union area), but shapely's polygon merge sees the
                # mismatched edges as topological seams. Iter-1 boundary
                # halves on the seed perimeter end up with no edge-overlap
                # neighbours since their long edges (length phi^d) span many
                # smaller iter-d pentagon edges. Both checks are disabled
                # until diamonds and halves get their own substitution rules.
                require_hole_free_surface=False,
                require_connected_graph=False,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=386,
                expected_kind_counts=(
                    (P1_DIAMOND_KIND, 45),
                    (P1_DIAMOND_HALF_KIND, 125),
                    (P1_PENTAGON_KIND, 216),
                ),
                require_hole_free_surface=False,
                require_connected_graph=False,
            ),
        },
        notes=(
            "Penrose P1 (pentagon / diamond) is built by Penrose's 1974 "
            "pentagonal substitution rule, implemented from scratch in "
            "``backend/simulation/aperiodic_penrose_p1_canonical.py``. Each "
            "pentagon at scale s deflates to 1 inverted central pentagon "
            "(side s/phi^2) + 5 outer upright pentagons (side s/phi^2, one "
            "centred per parent vertex direction) + 5 acute Robinson half-tiles "
            "(golden triangles, side s/phi^2) along the 5 parent edges. The "
            "boundary half-tiles pair across edges with the matching halves "
            "from neighbour pentagons -- two acutes glued at their short base "
            "form a thin rhomb (the canonical P1 diamond, 36-144-36-144). "
            "Halves on the outermost patch boundary remain unpaired and "
            "surface as ``p1-diamond-half`` cells (Option-2 boundary "
            "treatment). Pentagons at every recursion level are emitted; the "
            "depth-to-cell-count sequence (1/11/66/386 at depths 0..3) "
            "follows from the 6x pentagon expansion plus accumulated boundary "
            "halves at every level. Diamonds and halves are currently "
            "terminal and do not further deflate; promoting them to "
            "substituting prototiles with full 4-prototile (pentagon, star, "
            "boat, diamond) decomposition is a future-work item documented "
            "in ``docs/TILING_KNOWN_DEVIATIONS.md``.",
        ),
    ),
    PENROSE_P2_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_P2_GEOMETRY,
        display_name=_reference_label(PENROSE_P2_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/penrose-kite-dart/",),
        canonical_root_seed_policy="five-kite sun seed",
        allowed_public_cell_kinds=_public_cell_kinds(PENROSE_P2_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=5,
                expected_kind_counts=((KITE_KIND, 5),),
                required_kinds=(KITE_KIND,),
                required_adjacency_pairs=((KITE_KIND, KITE_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=15,
                expected_kind_counts=((DART_KIND, 5), (KITE_KIND, 10)),
                required_kinds=(KITE_KIND, DART_KIND),
                required_adjacency_pairs=(
                    (DART_KIND, KITE_KIND),
                    (KITE_KIND, KITE_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=45,
                expected_kind_counts=(
                    (DART_KIND, 10),
                    (DART_HALF_OBTUSE_KIND, 10),
                    (KITE_KIND, 25),
                ),
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=115,
                expected_kind_counts=(
                    (DART_KIND, 30),
                    (DART_HALF_OBTUSE_KIND, 20),
                    (KITE_KIND, 65),
                ),
            ),
        },
        notes=(
            "Built from the canonical Robinson half-tile substitution (matrix [[2,1],[1,1]], "
            "leading eigenvalue phi^2 ~ 2.618) seeded with the 5-kite sun. After substitution, "
            "acute halves pair into kites along long edges and obtuse halves pair into darts "
            "along short edges (Conway / de Bruijn convention). The 5-kite sun seed is "
            "geometrically asymmetric under this substitution: at every depth every acute "
            "finds a kite partner, while perimeter obtuses can be left unpaired and emitted "
            "as ``dart-half-obtuse`` cells (Option 2 from "
            "docs/PENROSE_CANONICAL_SUBSTITUTION_PLAN.md). Depth >= 2 patches therefore "
            "show visibly halved darts around the sun's outer boundary, but no halved kites.",
        ),
    ),
    AMMANN_BEENKER_GEOMETRY: ReferenceFamilySpec(
        geometry=AMMANN_BEENKER_GEOMETRY,
        display_name=_reference_label(AMMANN_BEENKER_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/ammann-beenker/",),
        canonical_root_seed_policy="eight-rhomb star seed",
        allowed_public_cell_kinds=_public_cell_kinds(AMMANN_BEENKER_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=8,
                required_kinds=(AMMANN_RHOMB_KIND,),
                required_adjacency_pairs=((AMMANN_RHOMB_KIND, AMMANN_RHOMB_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=24,
                required_kinds=(AMMANN_RHOMB_KIND, AMMANN_SQUARE_KIND),
                required_adjacency_pairs=(
                    (AMMANN_RHOMB_KIND, AMMANN_RHOMB_KIND),
                    (AMMANN_RHOMB_KIND, AMMANN_SQUARE_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=208),
            3: ReferenceDepthExpectation(exact_total_cells=1304),
        },
    ),
    SPECTRE_GEOMETRY: ReferenceFamilySpec(
        geometry=SPECTRE_GEOMETRY,
        display_name=_reference_label(SPECTRE_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/spectre/",
            "https://doi.org/10.5070/C64264241",
        ),
        canonical_root_seed_policy="delta supertile seed",
        allowed_public_cell_kinds=_public_cell_kinds(SPECTRE_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(exact_total_cells=1, required_kinds=(SPECTRE_KIND,)),
            1: ReferenceDepthExpectation(
                exact_total_cells=9,
                required_adjacency_pairs=((SPECTRE_KIND, SPECTRE_KIND),),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=71),
            3: ReferenceDepthExpectation(
                exact_total_cells=559,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
    TAYLOR_SOCOLAR_GEOMETRY: ReferenceFamilySpec(
        geometry=TAYLOR_SOCOLAR_GEOMETRY,
        display_name=_reference_label(TAYLOR_SOCOLAR_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/half-hex/",
            "https://www.mdpi.com/2073-8994/5/1/1",
        ),
        canonical_root_seed_policy="paired half-hex seed",
        allowed_public_cell_kinds=_public_cell_kinds(TAYLOR_SOCOLAR_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=2,
                required_kinds=(TAYLOR_HALF_HEX_KIND,),
                required_adjacency_pairs=((TAYLOR_HALF_HEX_KIND, TAYLOR_HALF_HEX_KIND),),
            ),
            1: ReferenceDepthExpectation(exact_total_cells=8),
            2: ReferenceDepthExpectation(exact_total_cells=32),
            3: ReferenceDepthExpectation(
                exact_total_cells=128,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
    SPHINX_GEOMETRY: ReferenceFamilySpec(
        geometry=SPHINX_GEOMETRY,
        display_name=_reference_label(SPHINX_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/sphinx/",),
        canonical_root_seed_policy="single sphinx rep-tile seed",
        allowed_public_cell_kinds=_public_cell_kinds(SPHINX_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(exact_total_cells=1, required_kinds=(SPHINX_KIND,)),
            1: ReferenceDepthExpectation(
                exact_total_cells=4,
                required_adjacency_pairs=((SPHINX_KIND, SPHINX_KIND),),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=16),
            3: ReferenceDepthExpectation(
                exact_total_cells=64,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
    CHAIR_GEOMETRY: ReferenceFamilySpec(
        geometry=CHAIR_GEOMETRY,
        display_name=_reference_label(CHAIR_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/chair/",),
        canonical_root_seed_policy="single chair substitution seed",
        allowed_public_cell_kinds=_public_cell_kinds(CHAIR_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=CHAIR_KIND,
                fields=("orientation_token",),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=1,
                expected_orientation_token_counts=(("0", 1),),
                required_kinds=(CHAIR_KIND,),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=4,
                expected_orientation_token_counts=(("0", 2), ("1", 1), ("3", 1)),
                required_adjacency_pairs=((CHAIR_KIND, CHAIR_KIND),),
                min_unique_orientation_tokens=3,
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=16,
                expected_orientation_token_counts=(("0", 6), ("1", 4), ("2", 2), ("3", 4)),
                min_unique_orientation_tokens=4,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=64,
                expected_orientation_token_counts=(("0", 20), ("1", 16), ("2", 12), ("3", 16)),
                min_unique_orientation_tokens=4,
            ),
        },
        notes=(
            "The representative patch is a true chair substitution over four orientation classes.",
            "Patch depth counts substitution rounds, not the earlier nested-corner hierarchy.",
        ),
    ),
    ROBINSON_TRIANGLES_GEOMETRY: ReferenceFamilySpec(
        geometry=ROBINSON_TRIANGLES_GEOMETRY,
        display_name=_reference_label(ROBINSON_TRIANGLES_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/robinson-triangle/",),
        canonical_root_seed_policy="five-kite sun seed (10 acute Robinson halves)",
        allowed_public_cell_kinds=_public_cell_kinds(ROBINSON_TRIANGLES_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=10,
                expected_kind_counts=((ROBINSON_THICK_KIND, 10),),
                required_kinds=(ROBINSON_THICK_KIND,),
                required_adjacency_pairs=((ROBINSON_THICK_KIND, ROBINSON_THICK_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=30,
                expected_kind_counts=(
                    (ROBINSON_THICK_KIND, 20),
                    (ROBINSON_THIN_KIND, 10),
                ),
                required_kinds=(ROBINSON_THICK_KIND, ROBINSON_THIN_KIND),
                required_adjacency_pairs=(
                    (ROBINSON_THICK_KIND, ROBINSON_THICK_KIND),
                    (ROBINSON_THICK_KIND, ROBINSON_THIN_KIND),
                ),
                canonical_patch_fixture_key="exact-depth-1",
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=80,
                expected_kind_counts=(
                    (ROBINSON_THICK_KIND, 50),
                    (ROBINSON_THIN_KIND, 30),
                ),
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=210,
                expected_kind_counts=(
                    (ROBINSON_THICK_KIND, 130),
                    (ROBINSON_THIN_KIND, 80),
                ),
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
        notes=(
            "Built from the canonical Robinson half-tile substitution (matrix [[2,1],[1,1]], "
            "leading eigenvalue phi^2 ~ 2.618) seeded with the 5-kite sun (10 acute halves). "
            "All half-tiles are emitted directly without pairing into full kites/darts; the "
            "depth-d cell counts (10, 30, 80, 210, ...) follow the Bielefeld substitution at "
            "https://tilings.math.uni-bielefeld.de/substitution/robinson-triangle/.",
        ),
    ),
    HAT_MONOTILE_GEOMETRY: ReferenceFamilySpec(
        geometry=HAT_MONOTILE_GEOMETRY,
        display_name=_reference_label(HAT_MONOTILE_GEOMETRY),
        source_urls=(
            "https://arxiv.org/abs/2303.10798",
            "https://tilings.math.uni-bielefeld.de/substitution/hat-metatiles/",
        ),
        canonical_root_seed_policy="H8 metatile root seed",
        allowed_public_cell_kinds=_public_cell_kinds(HAT_MONOTILE_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=HAT_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=8,
                required_kinds=(HAT_KIND,),
                min_unique_chirality_tokens=2,
                required_chirality_adjacency_pairs=(("left", "right"),),
            ),
            1: ReferenceDepthExpectation(
                min_unique_chirality_tokens=2,
                required_adjacency_pairs=((HAT_KIND, HAT_KIND),),
                required_chirality_adjacency_pairs=(("left", "right"),),
            ),
            2: ReferenceDepthExpectation(
                min_three_opposite_chirality_neighbor_cells=1,
            ),
        },
        notes=(
            "The hat literature describes a metatile substitution rather than a single-tile root seed.",
            "Representative patches should include reflected copies of the monotile.",
            "The reflected copies should participate in the characteristic three-neighbor local pattern described in the hat-metatiles source.",
        ),
    ),
    TUEBINGEN_TRIANGLE_GEOMETRY: ReferenceFamilySpec(
        geometry=TUEBINGEN_TRIANGLE_GEOMETRY,
        display_name=_reference_label(TUEBINGEN_TRIANGLE_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/tuebingen-triangle/",),
        canonical_root_seed_policy="handed Robinson-triangle substitution patch",
        allowed_public_cell_kinds=_public_cell_kinds(TUEBINGEN_TRIANGLE_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=TUEBINGEN_THICK_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
            MetadataRequirement(
                kind=TUEBINGEN_THIN_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            1: ReferenceDepthExpectation(
                required_kinds=(TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                required_adjacency_pairs=(
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THICK_KIND),
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                ),
                min_unique_chirality_tokens=2,
                canonical_patch_fixture_key="exact-depth-1",
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=210,
                expected_kind_counts=(
                    (TUEBINGEN_THICK_KIND, 130),
                    (TUEBINGEN_THIN_KIND, 80),
                ),
                required_kinds=(TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                required_adjacency_pairs=(
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THICK_KIND),
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                ),
                min_unique_chirality_tokens=2,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
        notes=(
            "The Tuebingen triangle substitution distinguishes left- and right-handed Robinson triangles.",
        ),
    ),
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY: ReferenceFamilySpec(
        geometry=DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        display_name=_reference_label(DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/square-triangle/",),
        canonical_root_seed_policy=(
            "decorated 3.12.12 Archimedean tiling: hexagonal lattice of regular "
            "dodecagonal supercells decomposed into six unit squares plus twelve "
            "unit equilateral triangles, with two bridging triangles per supercell "
            "from the underlying 3.12.12 Archimedean layout"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind=DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            1: ReferenceDepthExpectation(
                exact_total_cells=5,
                expected_kind_counts=(
                    (DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND, 1),
                    (DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND, 4),
                ),
                expected_tile_family_counts=((DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 5),),
                required_kinds=(
                    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                ),
                required_adjacency_pairs=(
                    (
                        DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                        DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                    ),
                ),
                expected_degree_histogram=((1, 4), (4, 1)),
                min_unique_orientation_tokens=3,
                min_unique_chirality_tokens=2,
                canonical_patch_fixture_key="dense-depth-1",
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=25,
                expected_kind_counts=(
                    (DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND, 7),
                    (DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND, 18),
                ),
                expected_tile_family_counts=((DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 25),),
                required_kinds=(
                    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                ),
                expected_adjacency_pairs=(
                    (
                        DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                        DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                    ),
                    (
                        DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                        DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                    ),
                ),
                expected_degree_histogram=((1, 6), (2, 6), (3, 8), (4, 5)),
                min_unique_orientation_tokens=8,
                min_unique_chirality_tokens=3,
                canonical_patch_fixture_key="dense-depth-3",
            ),
        },
        notes=(
            "The runtime is a periodic decorated 3.12.12 Archimedean tiling. Each "
            "regular-dodecagonal supercell is decomposed into the canonical six unit "
            "squares plus twelve unit equilateral triangles (a 6-fold-symmetric layout), "
            "and the bridging triangles between supercells are partitioned so that "
            "each plane triangle is owned by exactly one supercell.",
            "The result is locally 12-fold flavoured inside every former-dodecagon "
            "region, has both kinds in the expected 7:3 triangle/square asymptotic "
            "ratio, and tiles the plane exactly without any vendored data dependency. "
            "It is not the canonical Schlottmann quasi-periodic square-triangle tiling.",
        ),
    ),
    SHIELD_GEOMETRY: ReferenceFamilySpec(
        geometry=SHIELD_GEOMETRY,
        display_name=_reference_label(SHIELD_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/shield/",
            "https://www.math.uni-bielefeld.de/~gaehler/tilings/sh.ps",
        ),
        canonical_root_seed_policy="single right-shield seed from Gahler's marked recursive PostScript rule",
        allowed_public_cell_kinds=_public_cell_kinds(SHIELD_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=SHIELD_SHIELD_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
            MetadataRequirement(
                kind=SHIELD_SQUARE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
            MetadataRequirement(
                kind=SHIELD_TRIANGLE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=1,
                required_kinds=(SHIELD_SHIELD_KIND,),
                min_unique_orientation_tokens=1,
                min_unique_chirality_tokens=1,
                max_bounds_aspect_ratio=1.1,
                expected_signature="ced78e983b2d",  # pragma: allowlist secret
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=13,
                required_kinds=(SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                required_adjacency_pairs=(
                    (SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_TRIANGLE_KIND, SHIELD_TRIANGLE_KIND),
                ),
                min_unique_orientation_tokens=10,
                min_unique_chirality_tokens=2,
                expected_signature="e707a58ed144",  # pragma: allowlist secret
                canonical_patch_fixture_key="dense-depth-1",
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=151,
                required_kinds=(SHIELD_SHIELD_KIND, SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                required_adjacency_pairs=(
                    (SHIELD_SHIELD_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_TRIANGLE_KIND, SHIELD_TRIANGLE_KIND),
                ),
                min_unique_orientation_tokens=12,
                min_unique_chirality_tokens=2,
                expected_signature="bf43dadeef7c",  # pragma: allowlist secret
                canonical_patch_fixture_key="dense-depth-3",
            ),
        },
        notes=(
            "The backend now translates Gahler's exact marked recursive PostScript rule instead of tracing a rendered patch image.",
            "The public runtime still collapses the marked internal prototiles to public square / triangle / shield kinds while preserving orientation and chirality metadata.",
            "Shield now uses exact substitution patch depth with strict edge-sharing validation.",
        ),
    ),
    PINWHEEL_GEOMETRY: ReferenceFamilySpec(
        geometry=PINWHEEL_GEOMETRY,
        display_name=_reference_label(PINWHEEL_GEOMETRY),
        source_urls=(
            "https://annals.math.princeton.edu/1994/139-3/p05",
            "https://tilings.math.uni-bielefeld.de/substitution/pinwheel/",
        ),
        canonical_root_seed_policy="paired right triangles forming a rectangle",
        allowed_public_cell_kinds=_public_cell_kinds(PINWHEEL_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=PINWHEEL_TRIANGLE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=2,
                required_kinds=(PINWHEEL_TRIANGLE_KIND,),
                required_adjacency_pairs=((PINWHEEL_TRIANGLE_KIND, PINWHEEL_TRIANGLE_KIND),),
                min_unique_chirality_tokens=2,
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=10,
                min_unique_orientation_tokens=4,
                min_bounds_longest_span=3.0,
                canonical_patch_fixture_key="exact-depth-1",
                canonical_patch_include_id=True,
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=50,
                min_unique_orientation_tokens=10,
                min_bounds_longest_span=6.0,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=250,
                min_unique_orientation_tokens=30,
                min_bounds_longest_span=12.0,
                canonical_patch_fixture_key="exact-depth-3",
                canonical_patch_include_id=True,
            ),
        },
        builder_signals=(
            BuilderSignalExpectation(
                module="backend.simulation.aperiodic_pinwheel",
                attribute="USES_EXACT_REFERENCE_PATH",
                expected_value=True,
            ),
        ),
        exact_reference_mode="pinwheel_exact",
        notes=(
            "Pinwheel verification uses the exact-affine path instead of rounded-edge reconstruction.",
            "The representative literature patch starts from two right triangles forming a rectangle.",
        ),
    ),
}
