from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    ROBINSON_THICK_KIND,
    ROBINSON_THIN_KIND,
    ROBINSON_TRIANGLES_GEOMETRY,
)
from backend.simulation.reference_specs.types import (
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    ROBINSON_TRIANGLES_GEOMETRY: ReferenceFamilySpec(
        geometry=ROBINSON_TRIANGLES_GEOMETRY,
        display_name=_reference_label(ROBINSON_TRIANGLES_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/robinson-triangle/",),
        root_seed_policy="five-kite sun seed (10 acute Robinson halves)",
        allowed_public_cell_kinds=_public_cell_kinds(ROBINSON_TRIANGLES_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=10,
                expected_kind_counts=((ROBINSON_THICK_KIND, 10),),
                required_kinds=(ROBINSON_THICK_KIND,),
                required_adjacency_pairs=((ROBINSON_THICK_KIND, ROBINSON_THICK_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=30,
                expected_kind_counts=(
                    (ROBINSON_THICK_KIND, 20),
                    (ROBINSON_THIN_KIND, 10),
                ),
                required_kinds=(ROBINSON_THICK_KIND, ROBINSON_THIN_KIND),
                required_adjacency_pairs=(
                    (ROBINSON_THICK_KIND, ROBINSON_THICK_KIND),
                    (ROBINSON_THICK_KIND, ROBINSON_THIN_KIND),
                ),
                canonical_patch_fixture_key="exact-depth-1",
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=80,
                expected_kind_counts=(
                    (ROBINSON_THICK_KIND, 50),
                    (ROBINSON_THIN_KIND, 30),
                ),
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=210,
                expected_kind_counts=(
                    (ROBINSON_THICK_KIND, 130),
                    (ROBINSON_THIN_KIND, 80),
                ),
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
        notes=(
            "Built from the canonical Robinson half-tile substitution (matrix [[2,1],[1,1]], "
            "leading eigenvalue phi^2 ~ 2.618) seeded with the 5-kite sun (10 acute halves). "
            "All half-tiles are emitted directly without pairing into full kites/darts; the "
            "depth-d cell counts (10, 30, 80, 210, ...) follow the Bielefeld substitution at "
            "https://tilings.math.uni-bielefeld.de/substitution/robinson-triangle/.",
        ),
    ),
}
