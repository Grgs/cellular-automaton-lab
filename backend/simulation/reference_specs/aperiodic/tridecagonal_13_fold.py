from __future__ import annotations

from itertools import combinations_with_replacement

from backend.simulation.aperiodic_family_manifest import (
    TRIDECAGONAL_13_FOLD_GEOMETRY,
    TRIDECAGONAL_13_FOLD_RHOMB_1_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_2_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_3_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_4_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_5_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_6_KIND,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

# The 13-fold rhomb tiling is built by the de Bruijn generalized-dual (multigrid)
# construction, so -- like the Penrose and Socolar multigrid families -- the
# depth-to-cell-count sequence is governed by the bounding-box crop rather than
# a substitution eigenvalue. Counts and the rhomb-adjacency vocabulary below are
# the deterministic output of that crop at half-extent ``0.55 * 1.5^d``.
# Alphabetical by kind name to match the verifier's canonical ordering.
_ALL_KINDS = (
    TRIDECAGONAL_13_FOLD_RHOMB_1_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_2_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_3_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_4_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_5_KIND,
    TRIDECAGONAL_13_FOLD_RHOMB_6_KIND,
)
# 20 of the 21 unordered kind-pairs occur as edge neighbours through depth 1;
# only the rhomb-4/rhomb-4 pairing is absent in the cropped patches.
_ADJACENCY_PAIRS = tuple(
    pair
    for pair in combinations_with_replacement(_ALL_KINDS, 2)
    if pair != (TRIDECAGONAL_13_FOLD_RHOMB_4_KIND, TRIDECAGONAL_13_FOLD_RHOMB_4_KIND)
)

SPECS = {
    TRIDECAGONAL_13_FOLD_GEOMETRY: ReferenceFamilySpec(
        geometry=TRIDECAGONAL_13_FOLD_GEOMETRY,
        display_name=_reference_label(TRIDECAGONAL_13_FOLD_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/",
            "https://www.math.brown.edu/reschwar/M272/pentagrid.pdf",
            "https://github.com/aatishb/patterncollider",
        ),
        canonical_root_seed_policy=(
            "de Bruijn tridecagrid crop: thirteen line families 2*pi/13 apart with "
            "generic offsets, cropped to a square of half-extent 0.5 * 1.5^d"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(TRIDECAGONAL_13_FOLD_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=72,
                expected_kind_counts=(
                    (TRIDECAGONAL_13_FOLD_RHOMB_1_KIND, 3),
                    (TRIDECAGONAL_13_FOLD_RHOMB_2_KIND, 16),
                    (TRIDECAGONAL_13_FOLD_RHOMB_3_KIND, 10),
                    (TRIDECAGONAL_13_FOLD_RHOMB_4_KIND, 13),
                    (TRIDECAGONAL_13_FOLD_RHOMB_5_KIND, 16),
                    (TRIDECAGONAL_13_FOLD_RHOMB_6_KIND, 14),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS,
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=150,
                expected_kind_counts=(
                    (TRIDECAGONAL_13_FOLD_RHOMB_1_KIND, 9),
                    (TRIDECAGONAL_13_FOLD_RHOMB_2_KIND, 24),
                    (TRIDECAGONAL_13_FOLD_RHOMB_3_KIND, 26),
                    (TRIDECAGONAL_13_FOLD_RHOMB_4_KIND, 25),
                    (TRIDECAGONAL_13_FOLD_RHOMB_5_KIND, 32),
                    (TRIDECAGONAL_13_FOLD_RHOMB_6_KIND, 34),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS,
            ),
            2: ReferenceDepthExpectation(exact_total_cells=317),
            3: ReferenceDepthExpectation(exact_total_cells=707),
        },
        notes=(
            "The 13-fold tridecagonal rhomb tiling is built by the de Bruijn "
            "generalized-dual (multigrid) construction over thirteen line families "
            "spaced 2*pi/13 apart (a tridecagrid). Thirteen is prime, so all "
            "thirteen families are fully independent -- no antiparallel-family "
            "degeneracy and no sub-symmetry concurrences. Generic offsets keep the "
            "multigrid regular, so every cell is one of the six tridecagonal "
            "rhombi with acute angles k * 180/13 for k = 1..6 (~13.8, ~27.7, "
            "~41.5, ~55.4, ~69.2, ~83.1 degrees), and the patch is edge-to-edge, "
            "gap-free, and overlap-free. Like the Penrose and Socolar multigrid "
            "families, depth scales the crop half-extent (0.5 * 1.5^d) rather than "
            "applying a substitution inflation, so the depth-to-cell-count "
            "sequence (64/124/271/575 at depths 0..3) is governed by the crop. "
            "This is the de Bruijn tridecagrid rhombus tiling, not a "
            "marked-prototile substitution; see docs/TILING_KNOWN_DEVIATIONS.md.",
        ),
    ),
}
