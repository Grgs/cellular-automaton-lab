from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    ENNEAGONAL_9_FOLD_GEOMETRY,
    ENNEAGONAL_9_FOLD_RHOMB_20_KIND,
    ENNEAGONAL_9_FOLD_RHOMB_40_KIND,
    ENNEAGONAL_9_FOLD_RHOMB_60_KIND,
    ENNEAGONAL_9_FOLD_RHOMB_80_KIND,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

# The 9-fold rhomb tiling is built by the de Bruijn generalized-dual (multigrid)
# construction, so -- like the Penrose and Socolar multigrid families -- the
# depth-to-cell-count sequence is governed by the bounding-box crop rather than
# a substitution eigenvalue. Counts and the rhomb-adjacency vocabulary below are
# the deterministic output of that crop at half-extent ``0.75 * 1.5^d``.
#
# All ten unordered kind-pairs occur as edge neighbours in the interior. The
# small depth-0 crop is not yet large enough to contain a 20-rhomb/20-rhomb edge
# contact (the rarest pairing), so depth 0 requires only the nine pairs it
# actually realises; depth 1 onward realises all ten.
_ADJACENCY_PAIRS_ALL = (
    (ENNEAGONAL_9_FOLD_RHOMB_20_KIND, ENNEAGONAL_9_FOLD_RHOMB_20_KIND),
    (ENNEAGONAL_9_FOLD_RHOMB_20_KIND, ENNEAGONAL_9_FOLD_RHOMB_40_KIND),
    (ENNEAGONAL_9_FOLD_RHOMB_20_KIND, ENNEAGONAL_9_FOLD_RHOMB_60_KIND),
    (ENNEAGONAL_9_FOLD_RHOMB_20_KIND, ENNEAGONAL_9_FOLD_RHOMB_80_KIND),
    (ENNEAGONAL_9_FOLD_RHOMB_40_KIND, ENNEAGONAL_9_FOLD_RHOMB_40_KIND),
    (ENNEAGONAL_9_FOLD_RHOMB_40_KIND, ENNEAGONAL_9_FOLD_RHOMB_60_KIND),
    (ENNEAGONAL_9_FOLD_RHOMB_40_KIND, ENNEAGONAL_9_FOLD_RHOMB_80_KIND),
    (ENNEAGONAL_9_FOLD_RHOMB_60_KIND, ENNEAGONAL_9_FOLD_RHOMB_60_KIND),
    (ENNEAGONAL_9_FOLD_RHOMB_60_KIND, ENNEAGONAL_9_FOLD_RHOMB_80_KIND),
    (ENNEAGONAL_9_FOLD_RHOMB_80_KIND, ENNEAGONAL_9_FOLD_RHOMB_80_KIND),
)
_ADJACENCY_PAIRS_D0 = tuple(
    pair
    for pair in _ADJACENCY_PAIRS_ALL
    if pair != (ENNEAGONAL_9_FOLD_RHOMB_20_KIND, ENNEAGONAL_9_FOLD_RHOMB_20_KIND)
)
# Alphabetical by kind name to match the verifier's canonical ordering.
_ALL_KINDS = (
    ENNEAGONAL_9_FOLD_RHOMB_20_KIND,
    ENNEAGONAL_9_FOLD_RHOMB_40_KIND,
    ENNEAGONAL_9_FOLD_RHOMB_60_KIND,
    ENNEAGONAL_9_FOLD_RHOMB_80_KIND,
)

SPECS = {
    ENNEAGONAL_9_FOLD_GEOMETRY: ReferenceFamilySpec(
        geometry=ENNEAGONAL_9_FOLD_GEOMETRY,
        display_name=_reference_label(ENNEAGONAL_9_FOLD_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/",
            "https://www.math.brown.edu/reschwar/M272/pentagrid.pdf",
            "https://github.com/aatishb/patterncollider",
        ),
        root_seed_policy=(
            "de Bruijn enneagrid crop: nine line families 2*pi/9 (20 deg) apart "
            "with generic offsets, cropped to a square of half-extent 0.75 * 1.5^d"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(ENNEAGONAL_9_FOLD_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=62,
                expected_kind_counts=(
                    (ENNEAGONAL_9_FOLD_RHOMB_20_KIND, 7),
                    (ENNEAGONAL_9_FOLD_RHOMB_40_KIND, 14),
                    (ENNEAGONAL_9_FOLD_RHOMB_60_KIND, 20),
                    (ENNEAGONAL_9_FOLD_RHOMB_80_KIND, 21),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS_D0,
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=137,
                expected_kind_counts=(
                    (ENNEAGONAL_9_FOLD_RHOMB_20_KIND, 15),
                    (ENNEAGONAL_9_FOLD_RHOMB_40_KIND, 27),
                    (ENNEAGONAL_9_FOLD_RHOMB_60_KIND, 44),
                    (ENNEAGONAL_9_FOLD_RHOMB_80_KIND, 51),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS_ALL,
            ),
            2: ReferenceDepthExpectation(exact_total_cells=292),
            3: ReferenceDepthExpectation(exact_total_cells=641),
        },
        notes=(
            "The 9-fold enneagonal rhomb tiling is built by the de Bruijn "
            "generalized-dual (multigrid) construction over nine line families "
            "spaced 2*pi/9 (20 degrees) apart (an enneagrid). Nine is odd, so "
            "all nine families are used directly with no antiparallel-family "
            "degeneracy. Generic offsets keep the multigrid regular, so every "
            "cell is one of the four enneagonal rhombi with acute angles 20, 40, "
            "60, and 80 degrees, and the patch is edge-to-edge, gap-free, and "
            "overlap-free. Like the Penrose and Socolar multigrid families, "
            "depth scales the crop half-extent (0.75 * 1.5^d) rather than "
            "applying a substitution inflation, so the depth-to-cell-count "
            "sequence (62/137/292/641 at depths 0..3) is governed by the crop. "
            "This is the de Bruijn enneagrid rhombus tiling, not a Danzer-style "
            "9-fold marked-prototile substitution; see "
            "docs/TILING_KNOWN_DEVIATIONS.md.",
        ),
    ),
}
