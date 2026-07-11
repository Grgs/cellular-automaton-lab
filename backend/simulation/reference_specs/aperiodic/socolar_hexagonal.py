from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    SOCOLAR_HEXAGONAL_GEOMETRY,
    SOCOLAR_HEXAGONAL_HEXAGON_KIND,
    SOCOLAR_HEXAGONAL_RHOMB_KIND,
    SOCOLAR_HEXAGONAL_SQUARE_KIND,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

# The canonical Socolar tiling's matching rules forbid rhomb-rhomb,
# square-square, and hexagon-hexagon edge contacts; every hexagon ring
# alternates rhomb/square. The adjacency vocabulary is therefore exactly the
# three mixed pairs at every depth.
_ADJACENCY_PAIRS = (
    (SOCOLAR_HEXAGONAL_HEXAGON_KIND, SOCOLAR_HEXAGONAL_RHOMB_KIND),
    (SOCOLAR_HEXAGONAL_HEXAGON_KIND, SOCOLAR_HEXAGONAL_SQUARE_KIND),
    (SOCOLAR_HEXAGONAL_RHOMB_KIND, SOCOLAR_HEXAGONAL_SQUARE_KIND),
)
_ALL_KINDS = (
    SOCOLAR_HEXAGONAL_HEXAGON_KIND,
    SOCOLAR_HEXAGONAL_RHOMB_KIND,
    SOCOLAR_HEXAGONAL_SQUARE_KIND,
)

SPECS = {
    SOCOLAR_HEXAGONAL_GEOMETRY: ReferenceFamilySpec(
        geometry=SOCOLAR_HEXAGONAL_GEOMETRY,
        display_name=_reference_label(SOCOLAR_HEXAGONAL_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/socolar/",
            "https://doi.org/10.1103/PhysRevB.39.10519",
            "https://bendwavy.org/klitzing/quasi/socolar.htm",
            "https://en.wikipedia.org/wiki/Socolar_tiling",
        ),
        root_seed_policy=(
            "cut-and-project ball: all tiles whose centers fall within radius "
            "4 + 0.75*d tile-edge units of the origin of the reference member "
            "(acceptance windows extracted from the Tilings Encyclopedia patch "
            "and verified tile-for-tile against it)"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(SOCOLAR_HEXAGONAL_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=SOCOLAR_HEXAGONAL_HEXAGON_KIND,
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind=SOCOLAR_HEXAGONAL_SQUARE_KIND,
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind=SOCOLAR_HEXAGONAL_RHOMB_KIND,
                fields=("tile_family", "orientation_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=41,
                expected_kind_counts=(
                    (SOCOLAR_HEXAGONAL_HEXAGON_KIND, 10),
                    (SOCOLAR_HEXAGONAL_RHOMB_KIND, 15),
                    (SOCOLAR_HEXAGONAL_SQUARE_KIND, 16),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS,
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=58,
                expected_kind_counts=(
                    (SOCOLAR_HEXAGONAL_HEXAGON_KIND, 16),
                    (SOCOLAR_HEXAGONAL_RHOMB_KIND, 22),
                    (SOCOLAR_HEXAGONAL_SQUARE_KIND, 20),
                ),
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS,
                canonical_patch_fixture_key="window-depth-1",
            ),
            2: ReferenceDepthExpectation(exact_total_cells=81),
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                required_kinds=_ALL_KINDS,
                required_adjacency_pairs=_ADJACENCY_PAIRS,
                canonical_patch_fixture_key="window-depth-3",
            ),
        },
        notes=(
            "Canonical Socolar tiling (Socolar 1989): prototiles {regular hexagon, "
            "square, 30-degree rhomb}, 12-fold quasiperiodic. Implemented as the "
            "cut-and-project construction (Socolar's own scheme; A2xA2 root lattice, "
            "star map zeta -> zeta^5 on Z[zeta12]) with exact Q(sqrt(3)) acceptance "
            "windows: equilateral-triangle windows for the two deep-hole subtypes of "
            "each hexagon orientation family, parallelogram windows for the six rhomb "
            "orientations, square windows for the three square orientations. The "
            "windows were extracted from the Tilings Encyclopedia's published Socolar "
            "patch and verified in exact arithmetic: regenerating the patch region "
            "reproduces the encyclopedia patch tile-for-tile (1876/1876 deep-interior "
            "tiles; every coset point classified correctly), so the generator emits "
            "the same tiling member extended to arbitrary radius. A vendored "
            "literature sample is diffed tile-for-tile by "
            "tests/unit/test_aperiodic_socolar_hexagonal.py. Unlike socolar-12-fold "
            "(the rhombus variant), this family carries the canonical hexagon-bearing "
            "prototile set.",
        ),
    ),
}
