from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    TURTLE_KIND,
    TURTLE_MONOTILE_GEOMETRY,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

# The Turtle is the Tile(sqrt(3), 1) member of the hat continuum and is built
# as the exact per-edge-class deformation of the verified Hat tiling
# (Tile(1, sqrt(3))). The two tilings are combinatorially identical, so the
# Turtle inherits the Hat's per-depth cell counts, chirality pairing, and the
# characteristic three-opposite-chirality-neighbour local pattern.
SPECS = {
    TURTLE_MONOTILE_GEOMETRY: ReferenceFamilySpec(
        geometry=TURTLE_MONOTILE_GEOMETRY,
        display_name=_reference_label(TURTLE_MONOTILE_GEOMETRY),
        source_urls=(
            "https://arxiv.org/abs/2303.10798",
            "https://tilings.math.uni-bielefeld.de/substitution/hat-metatiles/",
        ),
        canonical_root_seed_policy="H8 metatile root seed (Tile(sqrt(3), 1) deformation)",
        allowed_public_cell_kinds=_public_cell_kinds(TURTLE_MONOTILE_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=TURTLE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=8,
                required_kinds=(TURTLE_KIND,),
                min_unique_chirality_tokens=2,
                required_chirality_adjacency_pairs=(("left", "right"),),
            ),
            1: ReferenceDepthExpectation(
                min_unique_chirality_tokens=2,
                required_adjacency_pairs=((TURTLE_KIND, TURTLE_KIND),),
                required_chirality_adjacency_pairs=(("left", "right"),),
            ),
            2: ReferenceDepthExpectation(
                min_three_opposite_chirality_neighbor_cells=1,
            ),
        },
        notes=(
            "The Turtle and the Hat are two members of the Tile(a, b) continuum "
            "(Smith, Myers, Kaplan, Goodman-Strauss 2023); the Turtle is "
            "Tile(sqrt(3), 1).",
            "It is built as the exact per-edge-class deformation of the verified "
            "Hat tiling, so it shares the Hat's metatile substitution structure.",
            "Representative patches include reflected copies that participate in the "
            "characteristic three-neighbour local pattern of the hat metatiles.",
        ),
    ),
}
