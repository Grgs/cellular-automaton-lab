from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    HEPTAGONAL_7_FOLD_GEOMETRY,
    HEPTAGONAL_7_FOLD_MEDIUM_KIND,
    HEPTAGONAL_7_FOLD_THIN_KIND,
    HEPTAGONAL_7_FOLD_WIDE_KIND,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

# The 7-fold rhomb tiling is built by the de Bruijn generalized-dual (multigrid)
# construction, so -- like the Penrose and Socolar multigrid families -- the
# depth-to-cell-count sequence is governed by the bounding-box crop rather than
# a substitution eigenvalue. Counts and the rhomb-adjacency vocabulary below are
# the deterministic output of that crop at half-extent ``1.0 * 1.5^d``.
# All six unordered kind-pairs occur as edge neighbours in the interior of the
# tiling. The small depth-0 crop is not yet large enough to contain a
# thin-rhomb/thin-rhomb edge contact (the rarest pairing), so depth 0 requires
# only the five pairs it actually realises; depth 1 onward realises all six.
_ADJACENCY_PAIRS_ALL = (
    (HEPTAGONAL_7_FOLD_MEDIUM_KIND, HEPTAGONAL_7_FOLD_MEDIUM_KIND),
    (HEPTAGONAL_7_FOLD_MEDIUM_KIND, HEPTAGONAL_7_FOLD_THIN_KIND),
    (HEPTAGONAL_7_FOLD_MEDIUM_KIND, HEPTAGONAL_7_FOLD_WIDE_KIND),
    (HEPTAGONAL_7_FOLD_THIN_KIND, HEPTAGONAL_7_FOLD_THIN_KIND),
    (HEPTAGONAL_7_FOLD_THIN_KIND, HEPTAGONAL_7_FOLD_WIDE_KIND),
    (HEPTAGONAL_7_FOLD_WIDE_KIND, HEPTAGONAL_7_FOLD_WIDE_KIND),
)
_ADJACENCY_PAIRS_D0 = tuple(
    pair
    for pair in _ADJACENCY_PAIRS_ALL
    if pair != (HEPTAGONAL_7_FOLD_THIN_KIND, HEPTAGONAL_7_FOLD_THIN_KIND)
)
# Alphabetical by kind name to match the verifier's canonical ordering.
_ALL_KINDS = (
    HEPTAGONAL_7_FOLD_MEDIUM_KIND,
    HEPTAGONAL_7_FOLD_THIN_KIND,
    HEPTAGONAL_7_FOLD_WIDE_KIND,
)

SPECS = {
    HEPTAGONAL_7_FOLD_GEOMETRY: ReferenceFamilySpec(
        geometry=HEPTAGONAL_7_FOLD_GEOMETRY,
        display_name=_reference_label(HEPTAGONAL_7_FOLD_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/goodman-strauss-7-fold-rhomb/",
            "https://en.wikipedia.org/wiki/De_Bruijn%27s_theorem",
            "https://www.math.brown.edu/reschwar/M272/pentagrid.pdf",
            "https://github.com/aatishb/patterncollider",
        ),
        root_seed_policy=(
            "de Bruijn heptagrid crop: seven line families 2*pi/7 apart with "
            "generic offsets, cropped to a square of half-extent 1.0 * 1.5^d"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(HEPTAGONAL_7_FOLD_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=62,
                expected_kind_counts=(
                    (HEPTAGONAL_7_FOLD_MEDIUM_KIND, 23),
                    (HEPTAGONAL_7_FOLD_THIN_KIND, 11),
                    (HEPTAGONAL_7_FOLD_WIDE_KIND, 28),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS_D0,
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=139,
                expected_kind_counts=(
                    (HEPTAGONAL_7_FOLD_MEDIUM_KIND, 49),
                    (HEPTAGONAL_7_FOLD_THIN_KIND, 29),
                    (HEPTAGONAL_7_FOLD_WIDE_KIND, 61),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS_ALL,
            ),
            2: ReferenceDepthExpectation(exact_total_cells=317),
            3: ReferenceDepthExpectation(exact_total_cells=707),
        },
        notes=(
            "The 7-fold heptagonal rhomb tiling is built by the de Bruijn "
            "generalized-dual (multigrid) construction over seven line families "
            "spaced 2*pi/7 apart (a heptagrid). Seven is odd, so all seven "
            "families are used directly with no antiparallel-family degeneracy. "
            "Generic offsets keep the multigrid regular, so every cell is one of "
            "the three heptagonal rhombi -- thin (acute angle pi/7), medium "
            "(2*pi/7), and wide (3*pi/7) -- and the patch is edge-to-edge, "
            "gap-free, and overlap-free. Like the Penrose and Socolar multigrid "
            "families, depth scales the crop half-extent (1.0 * 1.5^d) rather "
            "than applying a substitution inflation, so the depth-to-cell-count "
            "sequence (62/139/317/707 at depths 0..3) is governed by the crop. "
            "This is the de Bruijn heptagrid rhombus tiling, not the "
            "Goodman-Strauss 7-fold marked-prototile substitution; see "
            "docs/TILING_KNOWN_DEVIATIONS.md.",
        ),
    ),
}
