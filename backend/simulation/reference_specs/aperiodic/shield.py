from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    SHIELD_GEOMETRY,
    SHIELD_SHIELD_KIND,
    SHIELD_SQUARE_KIND,
    SHIELD_TRIANGLE_KIND,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    SHIELD_GEOMETRY: ReferenceFamilySpec(
        geometry=SHIELD_GEOMETRY,
        display_name=_reference_label(SHIELD_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/shield/",
            "https://www.math.uni-bielefeld.de/~gaehler/tilings/sh.ps",
        ),
        root_seed_policy="single right-shield seed from Gahler's marked recursive PostScript rule",
        allowed_public_cell_kinds=_public_cell_kinds(SHIELD_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=SHIELD_SHIELD_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
            MetadataRequirement(
                kind=SHIELD_SQUARE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
            MetadataRequirement(
                kind=SHIELD_TRIANGLE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=1,
                required_kinds=(SHIELD_SHIELD_KIND,),
                min_unique_orientation_tokens=1,
                min_unique_chirality_tokens=1,
                max_bounds_aspect_ratio=1.1,
                expected_signature="ced78e983b2d",  # pragma: allowlist secret
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=13,
                required_kinds=(SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                required_adjacency_pairs=(
                    (SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_TRIANGLE_KIND, SHIELD_TRIANGLE_KIND),
                ),
                min_unique_orientation_tokens=10,
                min_unique_chirality_tokens=2,
                expected_signature="e707a58ed144",  # pragma: allowlist secret
                canonical_patch_fixture_key="dense-depth-1",
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=151,
                required_kinds=(SHIELD_SHIELD_KIND, SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                required_adjacency_pairs=(
                    (SHIELD_SHIELD_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_TRIANGLE_KIND, SHIELD_TRIANGLE_KIND),
                ),
                min_unique_orientation_tokens=12,
                min_unique_chirality_tokens=2,
                expected_signature="bf43dadeef7c",  # pragma: allowlist secret
                canonical_patch_fixture_key="dense-depth-3",
            ),
        },
        notes=(
            "The backend now translates Gahler's exact marked recursive PostScript rule instead of tracing a rendered patch image.",
            "The public runtime still collapses the marked internal prototiles to public square / triangle / shield kinds while preserving orientation and chirality metadata.",
            "Shield now uses exact substitution patch depth with strict edge-sharing validation.",
        ),
    ),
}
