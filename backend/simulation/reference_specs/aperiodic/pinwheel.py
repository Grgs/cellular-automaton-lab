from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import (
    PINWHEEL_GEOMETRY,
    PINWHEEL_TRIANGLE_KIND,
)
from backend.simulation.reference_specs.types import (
    BuilderSignalExpectation,
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

_PINWHEEL_SIDE_RATIOS = (1.0, 2.0, math.sqrt(5))

SPECS = {
    PINWHEEL_GEOMETRY: ReferenceFamilySpec(
        geometry=PINWHEEL_GEOMETRY,
        display_name=_reference_label(PINWHEEL_GEOMETRY),
        source_urls=(
            "https://annals.math.princeton.edu/1994/139-3/p05",
            "https://tilings.math.uni-bielefeld.de/substitution/pinwheel/",
        ),
        root_seed_policy="paired right triangles forming a rectangle",
        allowed_public_cell_kinds=_public_cell_kinds(PINWHEEL_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=PINWHEEL_TRIANGLE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                expected_triangle_side_ratios=_PINWHEEL_SIDE_RATIOS,
                exact_total_cells=2,
                required_kinds=(PINWHEEL_TRIANGLE_KIND,),
                required_adjacency_pairs=((PINWHEEL_TRIANGLE_KIND, PINWHEEL_TRIANGLE_KIND),),
                # Both root triangles are listed in (small-angle, right-angle,
                # large-angle) order so the subdivision is a similarity
                # transform; this makes both seed triangles ``left`` chirality.
                # Chirality variety emerges at depth 1+ where the pinwheel
                # subdivision rule produces 3 right + 2 left children per
                # left parent.
                min_unique_chirality_tokens=1,
            ),
            1: ReferenceDepthExpectation(
                expected_triangle_side_ratios=_PINWHEEL_SIDE_RATIOS,
                exact_total_cells=10,
                min_unique_orientation_tokens=4,
                min_bounds_longest_span=3.0,
                canonical_patch_fixture_key="exact-depth-1",
                canonical_patch_include_id=True,
            ),
            2: ReferenceDepthExpectation(
                expected_triangle_side_ratios=_PINWHEEL_SIDE_RATIOS,
                exact_total_cells=50,
                min_unique_orientation_tokens=10,
                min_bounds_longest_span=6.0,
            ),
            3: ReferenceDepthExpectation(
                expected_triangle_side_ratios=_PINWHEEL_SIDE_RATIOS,
                exact_total_cells=250,
                # The similarity-preserving subdivision grows hypotenuse
                # directions linearly (2 + 4d per depth for the two-root
                # rectangle seed): 2, 6, 10, 14 at depths 0..3. The previous
                # minimum of 30 was calibrated against the sheared pre-fix
                # geometry, whose distorted triangles inflated the count.
                min_unique_orientation_tokens=14,
                min_bounds_longest_span=12.0,
                canonical_patch_fixture_key="exact-depth-3",
                canonical_patch_include_id=True,
            ),
        },
        builder_signals=(
            BuilderSignalExpectation(
                module="backend.simulation.aperiodic_pinwheel",
                attribute="USES_EXACT_REFERENCE_PATH",
                expected_value=True,
            ),
        ),
        exact_reference_mode="pinwheel_exact",
        notes=(
            "Pinwheel verification uses the exact-affine path instead of rounded-edge reconstruction.",
            "The representative literature patch starts from two right triangles forming a rectangle.",
        ),
    ),
}
