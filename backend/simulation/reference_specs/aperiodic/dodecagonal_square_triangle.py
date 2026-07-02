from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY: ReferenceFamilySpec(
        geometry=DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        display_name=_reference_label(DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY),
        source_urls=("https://tilings.math.uni-bielefeld.de/substitution/square-triangle/",),
        root_seed_policy=(
            "Schlottmann marked square-triangle pseudo substitution (inflation "
            "factor 2 + sqrt(3), five marked prototiles: red/yellow/blue "
            "triangles plus plain/marked squares); the runtime iterates the "
            "blue triangle's interior identity self-slot so patches converge "
            "around a fixed anchor tile, then BFS-crops from the square "
            "nearest the anchor"
        ),
        allowed_public_cell_kinds=_public_cell_kinds(DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind=DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            1: ReferenceDepthExpectation(
                exact_total_cells=5,
                expected_kind_counts=(
                    (DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND, 1),
                    (DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND, 4),
                ),
                expected_tile_family_counts=((DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 5),),
                required_kinds=(
                    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                ),
                required_adjacency_pairs=(
                    (
                        DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                        DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                    ),
                ),
                expected_degree_histogram=((1, 4), (4, 1)),
                min_unique_orientation_tokens=3,
                min_unique_chirality_tokens=3,
                canonical_patch_fixture_key="dense-depth-1",
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=25,
                expected_kind_counts=(
                    (DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND, 7),
                    (DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND, 18),
                ),
                expected_tile_family_counts=((DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 25),),
                required_kinds=(
                    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                ),
                expected_adjacency_pairs=(
                    (
                        DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                        DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                    ),
                    (
                        DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                        DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                    ),
                ),
                expected_degree_histogram=((1, 6), (2, 6), (3, 8), (4, 5)),
                min_unique_orientation_tokens=4,
                min_unique_chirality_tokens=3,
                canonical_patch_fixture_key="dense-depth-3",
            ),
        },
        notes=(
            "The runtime is the Schlottmann quasi-periodic square-triangle "
            "pseudo substitution with inflation factor 2 + sqrt(3): five marked "
            "prototiles (three marked unit triangles exposed as red/yellow/blue "
            "chirality tokens plus two marked unit squares collapsed to the "
            "public square kind). Supertiles interlock, so boundary children "
            "are emitted by both adjacent supertiles and deduplicated by exact "
            "Z[zeta12]-module geometry.",
            "The child placements were extracted from the Tilings Encyclopedia "
            "substitution-rule figure and verified against the encyclopedia's "
            "4999-cell literature patch: a two-level supertile decomposition "
            "pins every child pose, re-expanding the decomposed coarse "
            "configuration reproduces the literature patch tile-for-tile "
            "(marking colors included), sigma^2 supertile patches are gap- and "
            "overlap-free, and the triangle:square census converges to the "
            "canonical 4/sqrt(3).",
        ),
    ),
}
