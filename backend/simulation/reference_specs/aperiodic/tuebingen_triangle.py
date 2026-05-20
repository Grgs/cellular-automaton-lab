from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    TUEBINGEN_THICK_KIND,
    TUEBINGEN_THIN_KIND,
    TUEBINGEN_TRIANGLE_GEOMETRY,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    TUEBINGEN_TRIANGLE_GEOMETRY: ReferenceFamilySpec(
        geometry=TUEBINGEN_TRIANGLE_GEOMETRY,
        display_name=_reference_label(TUEBINGEN_TRIANGLE_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/tuebingen-triangle/",),
        canonical_root_seed_policy="handed Robinson-triangle substitution patch",
        allowed_public_cell_kinds=_public_cell_kinds(TUEBINGEN_TRIANGLE_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=TUEBINGEN_THICK_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
            MetadataRequirement(
                kind=TUEBINGEN_THIN_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            1: ReferenceDepthExpectation(
                required_kinds=(TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                required_adjacency_pairs=(
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THICK_KIND),
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                ),
                min_unique_chirality_tokens=2,
                canonical_patch_fixture_key="exact-depth-1",
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=210,
                expected_kind_counts=(
                    (TUEBINGEN_THICK_KIND, 130),
                    (TUEBINGEN_THIN_KIND, 80),
                ),
                required_kinds=(TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                required_adjacency_pairs=(
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THICK_KIND),
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                ),
                min_unique_chirality_tokens=2,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
        notes=(
            "The Tuebingen triangle substitution distinguishes left- and right-handed Robinson triangles.",
        ),
    ),
}
