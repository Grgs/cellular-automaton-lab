from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    SOCOLAR_12_FOLD_GEOMETRY,
    SOCOLAR_12_FOLD_RHOMB_30_KIND,
    SOCOLAR_12_FOLD_RHOMB_60_KIND,
    SOCOLAR_12_FOLD_SQUARE_KIND,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

# The dodecagonal rhomb tiling is built by the de Bruijn generalized-dual
# (multigrid) construction, so -- like the Penrose multigrid families -- the
# depth-to-cell-count sequence is governed by the bounding-box crop rather than
# a substitution eigenvalue. Counts and the rhomb-adjacency vocabulary below are
# the deterministic output of that crop at half-extent ``1.0 * 1.55^d``.
_ADJACENCY_PAIRS = (
    (SOCOLAR_12_FOLD_RHOMB_30_KIND, SOCOLAR_12_FOLD_RHOMB_30_KIND),
    (SOCOLAR_12_FOLD_RHOMB_30_KIND, SOCOLAR_12_FOLD_RHOMB_60_KIND),
    (SOCOLAR_12_FOLD_RHOMB_30_KIND, SOCOLAR_12_FOLD_SQUARE_KIND),
    (SOCOLAR_12_FOLD_RHOMB_60_KIND, SOCOLAR_12_FOLD_RHOMB_60_KIND),
    (SOCOLAR_12_FOLD_RHOMB_60_KIND, SOCOLAR_12_FOLD_SQUARE_KIND),
)
_ALL_KINDS = (
    SOCOLAR_12_FOLD_RHOMB_30_KIND,
    SOCOLAR_12_FOLD_RHOMB_60_KIND,
    SOCOLAR_12_FOLD_SQUARE_KIND,
)

SPECS = {
    SOCOLAR_12_FOLD_GEOMETRY: ReferenceFamilySpec(
        geometry=SOCOLAR_12_FOLD_GEOMETRY,
        display_name=_reference_label(SOCOLAR_12_FOLD_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/socolar/",
            "https://doi.org/10.1103/PhysRevB.39.10519",
            "https://en.wikipedia.org/wiki/Socolar_tiling",
            "https://bendwavy.org/klitzing/quasi/socolar.htm",
        ),
        root_seed_policy=(
            "de Bruijn dodecagrid crop: six line families 30 degrees apart with "
            "generic offsets, cropped to a square of half-extent 1.0 * 1.55^d"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(SOCOLAR_12_FOLD_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=44,
                expected_kind_counts=(
                    (SOCOLAR_12_FOLD_RHOMB_30_KIND, 12),
                    (SOCOLAR_12_FOLD_RHOMB_60_KIND, 20),
                    (SOCOLAR_12_FOLD_SQUARE_KIND, 12),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS,
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=102,
                expected_kind_counts=(
                    (SOCOLAR_12_FOLD_RHOMB_30_KIND, 25),
                    (SOCOLAR_12_FOLD_RHOMB_60_KIND, 49),
                    (SOCOLAR_12_FOLD_SQUARE_KIND, 28),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS,
            ),
            2: ReferenceDepthExpectation(exact_total_cells=250),
            3: ReferenceDepthExpectation(exact_total_cells=623),
        },
        notes=(
            "The Socolar tiling (Socolar 1989) is a 12-fold quasiperiodic tiling whose "
            "exact marked substitution is published only as a rule diagram. This family "
            "instead ships the dodecagonal rhomb tiling -- the rhombus variant of the "
            "Socolar tiling, mutually locally derivable from the shield tiling -- built "
            "by the de Bruijn generalized-dual (multigrid) construction over six line "
            "families spaced 30 degrees apart. Generic offsets keep the multigrid regular, "
            "so every cell is one of the three dodecagonal rhombi (30-degree, 60-degree, "
            "and the 90-degree square) and the patch is edge-to-edge, gap-free, and "
            "overlap-free. Like the Penrose multigrid families, depth scales the crop "
            "half-extent (1.0 * 1.55^d) rather than applying a substitution inflation, so "
            "the depth-to-cell-count sequence (44/102/250/623 at depths 0..3) is governed "
            "by the crop. See docs/TILING_KNOWN_DEVIATIONS.md for the substitution caveat.",
        ),
    ),
}
