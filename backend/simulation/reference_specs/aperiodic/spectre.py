from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    SPECTRE_GEOMETRY,
    SPECTRE_KIND,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    SPECTRE_GEOMETRY: ReferenceFamilySpec(
        geometry=SPECTRE_GEOMETRY,
        display_name=_reference_label(SPECTRE_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/spectre/",
            "https://doi.org/10.5070/C64264241",
        ),
        canonical_root_seed_policy="delta supertile seed",
        allowed_public_cell_kinds=_public_cell_kinds(SPECTRE_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(exact_total_cells=1, required_kinds=(SPECTRE_KIND,)),
            1: ReferenceDepthExpectation(
                exact_total_cells=9,
                required_adjacency_pairs=((SPECTRE_KIND, SPECTRE_KIND),),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=71),
            3: ReferenceDepthExpectation(
                exact_total_cells=559,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
}
