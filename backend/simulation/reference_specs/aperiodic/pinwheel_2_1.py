from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import (
    PINWHEEL_2_1_GEOMETRY,
    PINWHEEL_2_1_LARGE_KIND,
    PINWHEEL_2_1_SMALL_KIND,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

_PINWHEEL_2_1_SIDE_RATIOS = (1.0, 4.0, math.sqrt(17))

SPECS = {
    PINWHEEL_2_1_GEOMETRY: ReferenceFamilySpec(
        geometry=PINWHEEL_2_1_GEOMETRY,
        display_name=_reference_label(PINWHEEL_2_1_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/pinwheel-2-1/",),
        canonical_root_seed_policy="paired right triangles forming a 4:1 rectangle",
        allowed_public_cell_kinds=_public_cell_kinds(PINWHEEL_2_1_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=PINWHEEL_2_1_SMALL_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
            MetadataRequirement(
                kind=PINWHEEL_2_1_LARGE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                expected_triangle_side_ratios=_PINWHEEL_2_1_SIDE_RATIOS,
                exact_total_cells=2,
                expected_kind_counts=((PINWHEEL_2_1_LARGE_KIND, 2),),
                required_kinds=(PINWHEEL_2_1_LARGE_KIND,),
                required_adjacency_pairs=((PINWHEEL_2_1_LARGE_KIND, PINWHEEL_2_1_LARGE_KIND),),
                # Both paired roots are listed in canonical (small, right,
                # large) order so the subdivision is a similarity; this
                # makes both seed triangles ``left`` chirality. Chirality
                # variety emerges at depth 1+ where the substitution rule
                # produces children of both chiralities.
                min_unique_chirality_tokens=1,
                min_unique_orientation_tokens=2,
            ),
            1: ReferenceDepthExpectation(
                expected_triangle_side_ratios=_PINWHEEL_2_1_SIDE_RATIOS,
                exact_total_cells=10,
                # One small + four large per root x two roots = 2 small +
                # 8 large. Entries sorted alphabetically (verifier compares
                # tuples).
                expected_kind_counts=(
                    (PINWHEEL_2_1_LARGE_KIND, 8),
                    (PINWHEEL_2_1_SMALL_KIND, 2),
                ),
                required_kinds=(PINWHEEL_2_1_SMALL_KIND, PINWHEEL_2_1_LARGE_KIND),
                required_adjacency_pairs=((PINWHEEL_2_1_LARGE_KIND, PINWHEEL_2_1_LARGE_KIND),),
                min_unique_orientation_tokens=6,
                canonical_patch_fixture_key="exact-depth-1",
                canonical_patch_include_id=True,
            ),
            2: ReferenceDepthExpectation(
                expected_triangle_side_ratios=_PINWHEEL_2_1_SIDE_RATIOS,
                exact_total_cells=50,
                expected_kind_counts=(
                    (PINWHEEL_2_1_LARGE_KIND, 40),
                    (PINWHEEL_2_1_SMALL_KIND, 10),
                ),
                min_unique_orientation_tokens=10,
            ),
            3: ReferenceDepthExpectation(
                expected_triangle_side_ratios=_PINWHEEL_2_1_SIDE_RATIOS,
                exact_total_cells=250,
                expected_kind_counts=(
                    (PINWHEEL_2_1_LARGE_KIND, 200),
                    (PINWHEEL_2_1_SMALL_KIND, 50),
                ),
                min_unique_orientation_tokens=14,
                canonical_patch_fixture_key="exact-depth-3",
                canonical_patch_include_id=True,
            ),
        },
        notes=(
            "Built from the canonical pinwheel-2-1 substitution from "
            "https://tilings.math.uni-bielefeld.de/substitution/pinwheel-2-1/, "
            "seeded with two 1:4:sqrt(17) right triangles paired into a 4:1 "
            "rectangle (matching the seed convention of the original "
            "Conway-Radin pinwheel). Each parent subdivides into one small "
            "child (scale 1/sqrt(17)) at the right-angle corner plus four "
            "large children (scale 2/sqrt(17)); the depth-d total is "
            "2 * 5^d. Vertex coordinates stay rational under subdivision "
            "(foot of altitude + midpoints), so the generator works in exact "
            "Fraction arithmetic.",
        ),
    ),
}
