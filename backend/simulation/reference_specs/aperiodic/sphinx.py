from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    SPHINX_GEOMETRY,
    SPHINX_KIND,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    SPHINX_GEOMETRY: ReferenceFamilySpec(
        geometry=SPHINX_GEOMETRY,
        display_name=_reference_label(SPHINX_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/sphinx/",),
        canonical_root_seed_policy="two-sphinx compact representative seed",
        allowed_public_cell_kinds=_public_cell_kinds(SPHINX_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(exact_total_cells=2, required_kinds=(SPHINX_KIND,)),
            1: ReferenceDepthExpectation(
                exact_total_cells=8,
                required_adjacency_pairs=((SPHINX_KIND, SPHINX_KIND),),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=32),
            3: ReferenceDepthExpectation(
                exact_total_cells=128,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
}
