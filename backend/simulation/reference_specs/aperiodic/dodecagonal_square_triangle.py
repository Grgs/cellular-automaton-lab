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
        canonical_root_seed_policy=(
            "decorated 3.12.12 Archimedean tiling: hexagonal lattice of regular "
            "dodecagonal supercells decomposed into six unit squares plus twelve "
            "unit equilateral triangles, with two bridging triangles per supercell "
            "from the underlying 3.12.12 Archimedean layout"
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
                min_unique_chirality_tokens=2,
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
                min_unique_orientation_tokens=8,
                min_unique_chirality_tokens=3,
                canonical_patch_fixture_key="dense-depth-3",
            ),
        },
        notes=(
            "The runtime is a periodic decorated 3.12.12 Archimedean tiling. Each "
            "regular-dodecagonal supercell is decomposed into the canonical six unit "
            "squares plus twelve unit equilateral triangles (a 6-fold-symmetric layout), "
            "and the bridging triangles between supercells are partitioned so that "
            "each plane triangle is owned by exactly one supercell.",
            "The result is locally 12-fold flavoured inside every former-dodecagon "
            "region, has both kinds in the expected 7:3 triangle/square asymptotic "
            "ratio, and tiles the plane exactly without any vendored data dependency. "
            "It is not the canonical Schlottmann quasi-periodic square-triangle tiling.",
        ),
    ),
}
