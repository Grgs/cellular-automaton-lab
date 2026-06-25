from __future__ import annotations

from itertools import combinations_with_replacement

from backend.simulation.aperiodic_family_manifest import (
    HENDECAGONAL_11_FOLD_GEOMETRY,
    HENDECAGONAL_11_FOLD_RHOMB_1_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_2_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_3_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_4_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_5_KIND,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

# The 11-fold rhomb tiling is built by the de Bruijn generalized-dual (multigrid)
# construction, so -- like the Penrose and Socolar multigrid families -- the
# depth-to-cell-count sequence is governed by the bounding-box crop rather than
# a substitution eigenvalue. Counts and the rhomb-adjacency vocabulary below are
# the deterministic output of that crop at half-extent ``0.6 * 1.5^d``.
# Alphabetical by kind name to match the verifier's canonical ordering.
_ALL_KINDS = (
    HENDECAGONAL_11_FOLD_RHOMB_1_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_2_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_3_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_4_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_5_KIND,
)
# All fifteen unordered kind-pairs occur as edge neighbours, already at depth 0.
_ADJACENCY_PAIRS = tuple(combinations_with_replacement(_ALL_KINDS, 2))

SPECS = {
    HENDECAGONAL_11_FOLD_GEOMETRY: ReferenceFamilySpec(
        geometry=HENDECAGONAL_11_FOLD_GEOMETRY,
        display_name=_reference_label(HENDECAGONAL_11_FOLD_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/",
            "https://www.math.brown.edu/reschwar/M272/pentagrid.pdf",
            "https://github.com/aatishb/patterncollider",
        ),
        canonical_root_seed_policy=(
            "de Bruijn hendecagrid crop: eleven line families 2*pi/11 apart with "
            "generic offsets, cropped to a square of half-extent 0.6 * 1.5^d"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(HENDECAGONAL_11_FOLD_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=57,
                expected_kind_counts=(
                    (HENDECAGONAL_11_FOLD_RHOMB_1_KIND, 4),
                    (HENDECAGONAL_11_FOLD_RHOMB_2_KIND, 14),
                    (HENDECAGONAL_11_FOLD_RHOMB_3_KIND, 11),
                    (HENDECAGONAL_11_FOLD_RHOMB_4_KIND, 13),
                    (HENDECAGONAL_11_FOLD_RHOMB_5_KIND, 15),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS,
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=127,
                expected_kind_counts=(
                    (HENDECAGONAL_11_FOLD_RHOMB_1_KIND, 12),
                    (HENDECAGONAL_11_FOLD_RHOMB_2_KIND, 20),
                    (HENDECAGONAL_11_FOLD_RHOMB_3_KIND, 30),
                    (HENDECAGONAL_11_FOLD_RHOMB_4_KIND, 32),
                    (HENDECAGONAL_11_FOLD_RHOMB_5_KIND, 33),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS,
            ),
            2: ReferenceDepthExpectation(exact_total_cells=268),
            3: ReferenceDepthExpectation(exact_total_cells=634),
        },
        notes=(
            "The 11-fold hendecagonal rhomb tiling is built by the de Bruijn "
            "generalized-dual (multigrid) construction over eleven line families "
            "spaced 2*pi/11 apart (a hendecagrid). Eleven is prime, so all eleven "
            "families are fully independent -- no antiparallel-family degeneracy "
            "and no sub-symmetry concurrences. Generic offsets keep the multigrid "
            "regular, so every cell is one of the five hendecagonal rhombi with "
            "acute angles k * 180/11 for k = 1..5 (~16.4, ~32.7, ~49.1, ~65.5, "
            "~81.8 degrees), and the patch is edge-to-edge, gap-free, and "
            "overlap-free. Like the Penrose and Socolar multigrid families, depth "
            "scales the crop half-extent (0.6 * 1.5^d) rather than applying a "
            "substitution inflation, so the depth-to-cell-count sequence "
            "(57/127/268/634 at depths 0..3) is governed by the crop. This is the "
            "de Bruijn hendecagrid rhombus tiling, not a marked-prototile "
            "substitution; see docs/TILING_KNOWN_DEVIATIONS.md.",
        ),
    ),
}
