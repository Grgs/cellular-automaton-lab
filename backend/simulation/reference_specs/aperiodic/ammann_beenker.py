from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    AMMANN_BEENKER_GEOMETRY,
    AMMANN_RHOMB_KIND,
    AMMANN_SQUARE_KIND,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    AMMANN_BEENKER_GEOMETRY: ReferenceFamilySpec(
        geometry=AMMANN_BEENKER_GEOMETRY,
        display_name=_reference_label(AMMANN_BEENKER_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/ammann-beenker/",),
        canonical_root_seed_policy="eight-rhomb star seed",
        allowed_public_cell_kinds=_public_cell_kinds(AMMANN_BEENKER_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=8,
                required_kinds=(AMMANN_RHOMB_KIND,),
                required_adjacency_pairs=((AMMANN_RHOMB_KIND, AMMANN_RHOMB_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=24,
                required_kinds=(AMMANN_RHOMB_KIND, AMMANN_SQUARE_KIND),
                required_adjacency_pairs=(
                    (AMMANN_RHOMB_KIND, AMMANN_RHOMB_KIND),
                    (AMMANN_RHOMB_KIND, AMMANN_SQUARE_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=208),
            3: ReferenceDepthExpectation(exact_total_cells=1304),
        },
    ),
}
