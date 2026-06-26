from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    L_TETROMINO_GEOMETRY,
    L_TETROMINO_KIND,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    L_TETROMINO_GEOMETRY: ReferenceFamilySpec(
        geometry=L_TETROMINO_GEOMETRY,
        display_name=_reference_label(L_TETROMINO_GEOMETRY),
        source_urls=("https://en.wikipedia.org/wiki/Rep-tile",),
        canonical_root_seed_policy="single L-tetromino rep-4 substitution seed",
        allowed_public_cell_kinds=_public_cell_kinds(L_TETROMINO_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=L_TETROMINO_KIND,
                fields=("orientation_token",),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=1,
                expected_orientation_token_counts=(("0", 1),),
                required_kinds=(L_TETROMINO_KIND,),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=4,
                expected_orientation_token_counts=(("0", 1), ("1", 1), ("2", 1), ("3", 1)),
                required_adjacency_pairs=((L_TETROMINO_KIND, L_TETROMINO_KIND),),
                min_unique_orientation_tokens=4,
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=16,
                expected_orientation_token_counts=(("0", 4), ("1", 4), ("2", 4), ("3", 4)),
                min_unique_orientation_tokens=4,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=64,
                expected_orientation_token_counts=(("0", 16), ("1", 16), ("2", 16), ("3", 16)),
                min_unique_orientation_tokens=4,
            ),
        },
        notes=(
            "The L-tetromino is a rep-4 rep-tile; the representative patch is its exact "
            "self-similar substitution over four orientation classes (the Klein four-group).",
            "Every tile yields one child of each orientation, so tokens are evenly split "
            "at every depth >= 1. Patch depth counts substitution rounds (4**depth cells).",
        ),
    ),
}
