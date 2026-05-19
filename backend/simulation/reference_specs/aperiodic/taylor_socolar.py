from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    TAYLOR_HALF_HEX_KIND,
    TAYLOR_SOCOLAR_GEOMETRY,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    TAYLOR_SOCOLAR_GEOMETRY: ReferenceFamilySpec(
        geometry=TAYLOR_SOCOLAR_GEOMETRY,
        display_name=_reference_label(TAYLOR_SOCOLAR_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/half-hex/",
            "https://www.mdpi.com/2073-8994/5/1/1",
        ),
        canonical_root_seed_policy="paired half-hex seed",
        allowed_public_cell_kinds=_public_cell_kinds(TAYLOR_SOCOLAR_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=2,
                required_kinds=(TAYLOR_HALF_HEX_KIND,),
                required_adjacency_pairs=((TAYLOR_HALF_HEX_KIND, TAYLOR_HALF_HEX_KIND),),
            ),
            1: ReferenceDepthExpectation(exact_total_cells=8),
            2: ReferenceDepthExpectation(exact_total_cells=32),
            3: ReferenceDepthExpectation(
                exact_total_cells=128,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
}
