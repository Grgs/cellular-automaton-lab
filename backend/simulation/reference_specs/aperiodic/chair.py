from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    CHAIR_GEOMETRY,
    CHAIR_KIND,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    CHAIR_GEOMETRY: ReferenceFamilySpec(
        geometry=CHAIR_GEOMETRY,
        display_name=_reference_label(CHAIR_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/chair/",),
        root_seed_policy="two-chair rectangular representative seed",
        allowed_public_cell_kinds=_public_cell_kinds(CHAIR_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=CHAIR_KIND,
                fields=("orientation_token",),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=2,
                expected_orientation_token_counts=(("0", 1), ("2", 1)),
                required_kinds=(CHAIR_KIND,),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=8,
                expected_orientation_token_counts=(("0", 2), ("1", 2), ("2", 2), ("3", 2)),
                required_adjacency_pairs=((CHAIR_KIND, CHAIR_KIND),),
                min_unique_orientation_tokens=4,
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=32,
                expected_orientation_token_counts=(("0", 8), ("1", 8), ("2", 8), ("3", 8)),
                min_unique_orientation_tokens=4,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=128,
                expected_orientation_token_counts=(("0", 32), ("1", 32), ("2", 32), ("3", 32)),
                min_unique_orientation_tokens=4,
            ),
        },
        notes=(
            "The representative patch is a true chair substitution over four orientation classes.",
            "It starts from two chairs arranged as a 3x2 rectangle so the default view fills the canvas better.",
            "Patch depth counts substitution rounds, not the earlier nested-corner hierarchy.",
        ),
    ),
}
