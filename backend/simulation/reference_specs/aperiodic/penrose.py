from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    DART_HALF_OBTUSE_KIND,
    DART_KIND,
    KITE_KIND,
    P1_BOAT_KIND,
    P1_DIAMOND_KIND,
    P1_PENTAGON_CLUSTER_KIND,
    P1_PENTAGON_KIND,
    P1_STAR_KIND,
    PENROSE_GEOMETRY,
    PENROSE_P1_DISTRIBUTED_GEOMETRY,
    PENROSE_P1_GEOMETRY,
    PENROSE_P1_PBS_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    THICK_RHOMB_KIND,
    THIN_RHOMB_KIND,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    PENROSE_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_GEOMETRY,
        display_name=_reference_label(PENROSE_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/",),
        root_seed_policy="de Bruijn pentagrid crop at half-extent 0.85 * phi^d",
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
        root_seed_policy=(
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
    PENROSE_P1_DISTRIBUTED_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_P1_DISTRIBUTED_GEOMETRY,
        display_name="Penrose P1 Distributed",
        source_urls=(
            "https://en.wikipedia.org/wiki/Penrose_tiling#Original_pentagonal_Penrose_tiling_(P1)",
            "https://www.math.brown.edu/reschwar/M272/pentagrid.pdf",
            "https://github.com/aatishb/patterncollider",
        ),
        root_seed_policy=(
            "non-uniform pentagrid offsets (0.3, 0.4, 0.5, 0.6, 0.7) with "
            "vertex-merge post-pass: scattered sun, star, and boat vertices "
            "in the underlying P3 rhomb tiling are collapsed into Penrose's "
            "P1 pentagon, pentagram star, and hexagonal boat prototiles, "
            "producing a tiling with no concentrated central singularity"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(PENROSE_P1_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=42,
                expected_kind_counts=(
                    (P1_BOAT_KIND, 11),
                    (P1_DIAMOND_KIND, 13),
                    (P1_PENTAGON_KIND, 15),
                    (P1_PENTAGON_CLUSTER_KIND, 3),
                ),
                required_kinds=(
                    P1_PENTAGON_KIND,
                    P1_PENTAGON_CLUSTER_KIND,
                    P1_DIAMOND_KIND,
                    P1_BOAT_KIND,
                ),
                required_adjacency_pairs=(
                    (P1_BOAT_KIND, P1_DIAMOND_KIND),
                    (P1_BOAT_KIND, P1_PENTAGON_KIND),
                    (P1_DIAMOND_KIND, P1_PENTAGON_KIND),
                    (P1_PENTAGON_KIND, P1_PENTAGON_KIND),
                    (P1_PENTAGON_CLUSTER_KIND, P1_PENTAGON_KIND),
                ),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=107,
                expected_kind_counts=(
                    (P1_BOAT_KIND, 24),
                    (P1_DIAMOND_KIND, 29),
                    (P1_PENTAGON_KIND, 43),
                    (P1_PENTAGON_CLUSTER_KIND, 10),
                    (P1_STAR_KIND, 1),
                ),
                required_kinds=(
                    P1_PENTAGON_KIND,
                    P1_PENTAGON_CLUSTER_KIND,
                    P1_DIAMOND_KIND,
                    P1_BOAT_KIND,
                    P1_STAR_KIND,
                ),
                required_adjacency_pairs=(
                    (P1_BOAT_KIND, P1_DIAMOND_KIND),
                    (P1_BOAT_KIND, P1_PENTAGON_KIND),
                    (P1_BOAT_KIND, P1_PENTAGON_CLUSTER_KIND),
                    (P1_DIAMOND_KIND, P1_PENTAGON_KIND),
                    (P1_DIAMOND_KIND, P1_PENTAGON_CLUSTER_KIND),
                    (P1_PENTAGON_KIND, P1_PENTAGON_KIND),
                    (P1_PENTAGON_KIND, P1_PENTAGON_CLUSTER_KIND),
                    (P1_PENTAGON_KIND, P1_STAR_KIND),
                    (P1_PENTAGON_CLUSTER_KIND, P1_STAR_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=272),
            3: ReferenceDepthExpectation(exact_total_cells=723),
        },
        notes=(
            "Penrose P1 is built in two stages. Stage 1 runs the de Bruijn "
            "pentagrid construction (de Bruijn 1981; Pattern Collider by "
            "Aatish Bhatia) with non-uniform offsets ``(0.3, 0.4, 0.5, 0.6, "
            "0.7)`` that produce a regular P3 rhomb tiling without a "
            "concentrated central singularity. Stage 2 (``apply_p1_vertex_"
            "merge``) walks every rhomb-vertex and identifies the four "
            "canonical Penrose vertex configurations: sun (5 thick rhombs "
            "at 72-degree apex), star (10 thin rhombs at 36-degree apex), "
            "and two 3-rhomb boat configurations (one thin + two thick at "
            "144/108/108 degrees, or two thin + one thick at 144/144/72 "
            "degrees). Each cluster collapses into the corresponding P1 "
            "prototile cell (sun -> 10-vertex ``p1-pentagon-cluster``, "
            "star -> 20-vertex ``p1-star``, boat -> 6-vertex ``p1-boat``). "
            "Unmerged thick rhombs that don't participate in any cluster "
            "keep the ``p1-pentagon`` label (rhomb-region MLD "
            "representative of the pentagonal P1 prototile). Pentagon "
            "clusters, boats, and stars are distributed throughout the "
            "patch rather than concentrated at a single special centre; "
            "every cell renders as a complete polygon and the tiling is "
            "hole-free, edge-matched, and connected at every depth.",
        ),
    ),
    PENROSE_P1_PBS_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_P1_PBS_GEOMETRY,
        display_name="Penrose Pentagon Boat Star",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/penrose-pentagon-boat-star/",
            "https://www.math.brown.edu/reschwar/M272/pentagrid.pdf",
        ),
        root_seed_policy=(
            "singular pentagrid crop with all-zero offsets and half-extent 1.6 * phi^d"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(PENROSE_P1_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=29,
                expected_kind_counts=(
                    (P1_BOAT_KIND, 14),
                    (P1_PENTAGON_KIND, 14),
                    (P1_STAR_KIND, 1),
                ),
                required_kinds=(P1_BOAT_KIND, P1_PENTAGON_KIND, P1_STAR_KIND),
                required_adjacency_pairs=(
                    (P1_BOAT_KIND, P1_BOAT_KIND),
                    (P1_BOAT_KIND, P1_PENTAGON_KIND),
                    (P1_BOAT_KIND, P1_STAR_KIND),
                ),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=127,
                expected_kind_counts=(
                    (P1_BOAT_KIND, 34),
                    (P1_DIAMOND_KIND, 24),
                    (P1_PENTAGON_KIND, 68),
                    (P1_STAR_KIND, 1),
                ),
                required_kinds=(
                    P1_BOAT_KIND,
                    P1_DIAMOND_KIND,
                    P1_PENTAGON_KIND,
                    P1_STAR_KIND,
                ),
                required_adjacency_pairs=(
                    (P1_BOAT_KIND, P1_BOAT_KIND),
                    (P1_BOAT_KIND, P1_DIAMOND_KIND),
                    (P1_BOAT_KIND, P1_PENTAGON_KIND),
                    (P1_BOAT_KIND, P1_STAR_KIND),
                    (P1_DIAMOND_KIND, P1_PENTAGON_KIND),
                    (P1_PENTAGON_KIND, P1_PENTAGON_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=411),
            3: ReferenceDepthExpectation(exact_total_cells=1161),
        },
        notes=(
            "This family uses the singular de Bruijn pentagrid dual directly: "
            "all five line-family offsets are zero, so the patch is centered "
            "on one 5-line coincidence whose dual polygon becomes the central "
            "P1 star. Three-line coincidences emit boats directly, while "
            "generic 2-line cells yield the diamond and pentagon "
            "representatives. The result is a deterministic, hole-free, "
            "connected canonical patch with the full P1 cell vocabulary "
            "present from depth 1 onward.",
        ),
    ),
    PENROSE_P2_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_P2_GEOMETRY,
        display_name=_reference_label(PENROSE_P2_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/penrose-kite-dart/",),
        root_seed_policy="five-kite sun seed",
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
}
