from __future__ import annotations

from .helpers import REGULAR_TILING_SOURCES, _alphabetic_slots, _prefixed_slots
from .types import (
    BuilderSignalExpectation,
    MetadataRequirement,
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)


REGULAR_REFERENCE_FAMILY_SPECS: dict[str, ReferenceFamilySpec] = {
    "square": ReferenceFamilySpec(
        geometry="square",
        display_name="Square",
        source_urls=(
            "https://en.wikipedia.org/wiki/Square_tiling",
            *REGULAR_TILING_SOURCES,
        ),
        canonical_root_seed_policy="open-boundary 3x3 square grid sample",
        allowed_public_cell_kinds=("cell",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=9,
                expected_kind_counts=(("cell", 9),),
                required_kinds=("cell",),
                expected_adjacency_pairs=(("cell", "cell"),),
                expected_degree_histogram=((3, 4), (5, 4), (8, 1)),
                expected_signature="5e7404005b58",  # pragma: allowlist secret
            ),
        },
    ),
    "hex": ReferenceFamilySpec(
        geometry="hex",
        display_name="Hexagonal",
        source_urls=(
            "https://en.wikipedia.org/wiki/Hexagonal_tiling",
            *REGULAR_TILING_SOURCES,
        ),
        canonical_root_seed_policy="open-boundary 3x3 hex grid sample",
        allowed_public_cell_kinds=("cell",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=9,
                expected_kind_counts=(("cell", 9),),
                required_kinds=("cell",),
                expected_adjacency_pairs=(("cell", "cell"),),
                expected_degree_histogram=((2, 2), (3, 3), (4, 2), (5, 1), (6, 1)),
                expected_signature="16ed3df93bd2",  # pragma: allowlist secret
            ),
        },
    ),
    "triangle": ReferenceFamilySpec(
        geometry="triangle",
        display_name="Triangular",
        source_urls=(
            "https://en.wikipedia.org/wiki/Triangular_tiling",
            *REGULAR_TILING_SOURCES,
        ),
        canonical_root_seed_policy="open-boundary 3x3 triangular grid sample",
        allowed_public_cell_kinds=("cell",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=9,
                expected_kind_counts=(("cell", 9),),
                required_kinds=("cell",),
                expected_adjacency_pairs=(("cell", "cell"),),
                expected_degree_histogram=((4, 2), (5, 4), (7, 2), (8, 1)),
                expected_signature="bb712107397f",  # pragma: allowlist secret
            ),
        },
    ),
}
