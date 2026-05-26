from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)
from backend.simulation.reference_specs.helpers import (
    _alphabetic_slots,
)

SPECS = {
    "archimedean-4-8-8": ReferenceFamilySpec(
        geometry="archimedean-4-8-8",
        display_name="Square-Octagon (4.8.8)",
        source_urls=("https://en.wikipedia.org/wiki/Truncated_square_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("octagon", "square"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=25,
                expected_kind_counts=(("octagon", 9), ("square", 16)),
                expected_adjacency_pairs=(("octagon", "octagon"), ("octagon", "square")),
                expected_degree_histogram=((1, 4), (2, 8), (4, 4), (6, 4), (7, 4), (8, 1)),
                expected_signature="17bcb9c29121",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=2,
            slot_vocabulary=("octagon", "square"),
            id_pattern="{prefix}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(("octagon", "octagon", "square"),),
            expected_interior_vertex_configuration_frequencies=(
                (("octagon", "octagon", "square"), 24),
            ),
            expected_dual_geometry="tetrakis-square",
        ),
    ),
    "archimedean-3-12-12": ReferenceFamilySpec(
        geometry="archimedean-3-12-12",
        display_name="Truncated Hexagonal (3.12.12)",
        source_urls=("https://en.wikipedia.org/wiki/Truncated_hexagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("dodecagon", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=162,
                expected_kind_counts=(("dodecagon", 54), ("triangle", 108)),
                expected_adjacency_pairs=(("dodecagon", "dodecagon"), ("dodecagon", "triangle")),
                expected_degree_histogram=(
                    (1, 10),
                    (2, 18),
                    (3, 80),
                    (4, 1),
                    (6, 2),
                    (7, 11),
                    (9, 1),
                    (10, 7),
                    (11, 4),
                    (12, 28),
                ),
                expected_signature="06279aa8cb8f",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=18,
            slot_vocabulary=_alphabetic_slots(18),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(("dodecagon", "dodecagon", "triangle"),),
            expected_interior_vertex_configuration_frequencies=(
                (("dodecagon", "dodecagon", "triangle"), 258),
            ),
            expected_dual_geometry="triakis-triangular",
        ),
    ),
    "archimedean-3-4-6-4": ReferenceFamilySpec(
        geometry="archimedean-3-4-6-4",
        display_name="Rhombitrihexagonal (3.4.6.4)",
        source_urls=("https://en.wikipedia.org/wiki/Rhombitrihexagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("hexagon", "square", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("hexagon", 18), ("square", 54), ("triangle", 36)),
                expected_adjacency_pairs=(("hexagon", "square"), ("square", "triangle")),
                expected_degree_histogram=((1, 2), (2, 13), (3, 44), (4, 37), (5, 2), (6, 10)),
                expected_signature="e116b6803eec",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=12,
            slot_vocabulary=_alphabetic_slots(12),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(("hexagon", "square", "triangle", "square"),),
            expected_interior_vertex_configuration_frequencies=(
                (("hexagon", "square", "triangle", "square"), 82),
            ),
            expected_dual_candidate_geometries=(
                "deltoidal-hexagonal",
                "deltoidal-trihexagonal",
            ),
            expected_dual_structure_signature=((4, 82),),
        ),
    ),
    "archimedean-4-6-12": ReferenceFamilySpec(
        geometry="archimedean-4-6-12",
        display_name="Truncated Trihexagonal (4.6.12)",
        source_urls=("https://en.wikipedia.org/wiki/Truncated_trihexagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("dodecagon", "hexagon", "square"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("dodecagon", 18), ("hexagon", 36), ("square", 54)),
                expected_adjacency_pairs=(
                    ("dodecagon", "hexagon"),
                    ("dodecagon", "square"),
                    ("hexagon", "square"),
                ),
                expected_degree_histogram=(
                    (1, 1),
                    (2, 7),
                    (3, 14),
                    (4, 41),
                    (5, 8),
                    (6, 20),
                    (7, 5),
                    (9, 2),
                    (12, 10),
                ),
                expected_signature="f9d9986097c7",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=12,
            slot_vocabulary=_alphabetic_slots(12),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(("dodecagon", "hexagon", "square"),),
            expected_interior_vertex_configuration_frequencies=(
                (("dodecagon", "hexagon", "square"), 170),
            ),
            expected_dual_geometry="kisrhombille",
        ),
    ),
    "archimedean-3-3-4-3-4": ReferenceFamilySpec(
        geometry="archimedean-3-3-4-3-4",
        display_name="Snub Square (3.3.4.3.4)",
        source_urls=("https://en.wikipedia.org/wiki/Snub_square_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("square", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("square", 36), ("triangle", 72)),
                expected_adjacency_pairs=(("square", "triangle"), ("triangle", "triangle")),
                expected_degree_histogram=((1, 6), (2, 17), (3, 60), (4, 25)),
                expected_signature="d68bc0cacc26",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=12,
            slot_vocabulary=_alphabetic_slots(12),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("square", "triangle", "square", "triangle", "triangle"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("square", "triangle", "square", "triangle", "triangle"), 53),
            ),
            expected_dual_candidate_geometries=(
                "basketweave",
                "cairo-pentagonal",
                "prismatic-pentagonal",
                "snub-square-dual",
                "type-7-pentagonal",
            ),
            expected_dual_structure_signature=((5, 53),),
        ),
    ),
    "archimedean-3-3-3-4-4": ReferenceFamilySpec(
        geometry="archimedean-3-3-3-4-4",
        display_name="Elongated Triangular (3.3.3.4.4)",
        source_urls=("https://en.wikipedia.org/wiki/Elongated_triangular_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("square", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("square", 36), ("triangle", 72)),
                expected_adjacency_pairs=(
                    ("square", "square"),
                    ("square", "triangle"),
                    ("triangle", "triangle"),
                ),
                expected_degree_histogram=((1, 1), (2, 18), (3, 69), (4, 20)),
                expected_signature="5a6ddd8b8e23",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=12,
            slot_vocabulary=_alphabetic_slots(12),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("square", "square", "triangle", "triangle", "triangle"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("square", "square", "triangle", "triangle", "triangle"), 55),
            ),
            expected_dual_candidate_geometries=(
                "basketweave",
                "cairo-pentagonal",
                "prismatic-pentagonal",
                "snub-square-dual",
                "type-7-pentagonal",
            ),
            expected_dual_structure_signature=((5, 55),),
        ),
    ),
    "archimedean-3-3-3-3-6": ReferenceFamilySpec(
        geometry="archimedean-3-3-3-3-6",
        display_name="Snub Trihexagonal (3.3.3.3.6)",
        source_urls=("https://en.wikipedia.org/wiki/Snub_trihexagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("hexagon", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=1134,
                expected_kind_counts=(("hexagon", 126), ("triangle", 1008)),
                expected_adjacency_pairs=(("hexagon", "triangle"), ("triangle", "triangle")),
                expected_degree_histogram=((1, 3), (2, 87), (3, 921), (4, 12), (5, 6), (6, 105)),
                expected_signature="65f0ec0732f0",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=126,
            slot_vocabulary=_alphabetic_slots(126),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("hexagon", "triangle", "triangle", "triangle", "triangle"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("hexagon", "triangle", "triangle", "triangle", "triangle"), 691),
            ),
            expected_dual_geometry="floret-pentagonal",
        ),
    ),
}
