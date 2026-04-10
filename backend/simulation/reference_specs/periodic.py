from __future__ import annotations

from .helpers import REGULAR_TILING_SOURCES, _alphabetic_slots, _prefixed_slots
from .types import (
    BuilderSignalExpectation,
    MetadataRequirement,
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)


PERIODIC_REFERENCE_FAMILY_SPECS: dict[str, ReferenceFamilySpec] = {
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
                expected_degree_histogram=((1, 10), (2, 18), (3, 80), (4, 1), (6, 2), (7, 11), (9, 1), (10, 7), (11, 4), (12, 28)),
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
                expected_degree_histogram=((1, 1), (2, 7), (3, 14), (4, 41), (5, 8), (6, 20), (7, 5), (9, 2), (12, 10)),
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
                "cairo-pentagonal",
                "prismatic-pentagonal",
                "snub-square-dual",
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
                "cairo-pentagonal",
                "prismatic-pentagonal",
                "snub-square-dual",
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
    "trihexagonal-3-6-3-6": ReferenceFamilySpec(
        geometry="trihexagonal-3-6-3-6",
        display_name="Kagome / Trihexagonal (3.6.3.6)",
        source_urls=("https://en.wikipedia.org/wiki/Trihexagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("hexagon", "triangle-down", "triangle-up"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=27,
                expected_kind_counts=(("hexagon", 9), ("triangle-down", 9), ("triangle-up", 9)),
                expected_adjacency_pairs=(("hexagon", "triangle-down"), ("hexagon", "triangle-up")),
                expected_degree_histogram=((1, 5), (2, 6), (3, 11), (5, 2), (6, 3)),
                expected_signature="9e8a5ba64587",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=3,
            slot_vocabulary=("hexagon", "triangle-down", "triangle-up"),
            id_pattern="{prefix}:{x}:{y}",
            row_offset_x=52.0,
            expected_interior_vertex_configurations=(
                ("hexagon", "triangle-down", "hexagon", "triangle-up"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("hexagon", "triangle-down", "hexagon", "triangle-up"), 13),
            ),
            expected_dual_geometry="rhombille",
        ),
    ),
    "cairo-pentagonal": ReferenceFamilySpec(
        geometry="cairo-pentagonal",
        display_name="Cairo Pentagonal",
        source_urls=("https://en.wikipedia.org/wiki/Cairo_pentagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=36,
                expected_kind_counts=(("pentagon", 36),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_degree_histogram=((2, 3), (3, 8), (4, 13), (5, 12)),
                expected_signature="e33351b2ed77",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=4,
            slot_vocabulary=("a", "b", "c", "d"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=71.0,
            expected_interior_vertex_configurations=(
                ("pentagon", "pentagon", "pentagon"),
                ("pentagon", "pentagon", "pentagon", "pentagon"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("pentagon", "pentagon", "pentagon"), 26),
                (("pentagon", "pentagon", "pentagon", "pentagon"), 10),
            ),
            expected_dual_candidate_geometries=(
                "archimedean-3-3-3-4-4",
                "archimedean-3-3-4-3-4",
            ),
            expected_dual_structure_signature=((3, 26), (4, 10)),
        ),
    ),
    "rhombille": ReferenceFamilySpec(
        geometry="rhombille",
        display_name="Rhombille",
        source_urls=("https://en.wikipedia.org/wiki/Rhombille_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("rhombus",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=54,
                expected_kind_counts=(("rhombus", 54),),
                expected_adjacency_pairs=(("rhombus", "rhombus"),),
                expected_degree_histogram=((1, 1), (2, 12), (3, 9), (4, 32)),
                expected_signature="0c57a0b0510a",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=6,
            slot_vocabulary=_prefixed_slots("s", 6),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("rhombus", "rhombus", "rhombus"),
                ("rhombus", "rhombus", "rhombus", "rhombus", "rhombus", "rhombus"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("rhombus", "rhombus", "rhombus"), 27),
                (("rhombus", "rhombus", "rhombus", "rhombus", "rhombus", "rhombus"), 10),
            ),
            expected_dual_geometry="trihexagonal-3-6-3-6",
        ),
    ),
    "deltoidal-hexagonal": ReferenceFamilySpec(
        geometry="deltoidal-hexagonal",
        display_name="Deltoidal Hexagonal",
        source_urls=("https://en.wikipedia.org/wiki/Deltoidal_hexagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("kite",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("kite", 108),),
                expected_adjacency_pairs=(("kite", "kite"),),
                expected_degree_histogram=((1, 2), (2, 12), (3, 18), (4, 76)),
                expected_signature="b5d904bfe95c",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=12,
            slot_vocabulary=tuple(sorted(_prefixed_slots("k", 12))),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("kite", "kite", "kite"),
                ("kite", "kite", "kite", "kite"),
                ("kite", "kite", "kite", "kite", "kite", "kite"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("kite", "kite", "kite"), 30),
                (("kite", "kite", "kite", "kite"), 43),
                (("kite", "kite", "kite", "kite", "kite", "kite"), 12),
            ),
            expected_dual_candidate_geometries=("archimedean-3-4-6-4",),
            expected_dual_structure_signature=((3, 30), (4, 43), (6, 12)),
        ),
    ),
    "tetrakis-square": ReferenceFamilySpec(
        geometry="tetrakis-square",
        display_name="Tetrakis Square",
        source_urls=("https://en.wikipedia.org/wiki/Tetrakis_square_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("triangle",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=36,
                expected_kind_counts=(("triangle", 36),),
                expected_adjacency_pairs=(("triangle", "triangle"),),
                expected_degree_histogram=((2, 12), (3, 24)),
                expected_signature="d7592c13db1e",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=4,
            slot_vocabulary=_prefixed_slots("s", 4),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("triangle", "triangle", "triangle", "triangle"),
                ("triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("triangle", "triangle", "triangle", "triangle"), 9),
                (("triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle"), 4),
            ),
            expected_dual_geometry="archimedean-4-8-8",
        ),
    ),
    "triakis-triangular": ReferenceFamilySpec(
        geometry="triakis-triangular",
        display_name="Triakis Triangular",
        source_urls=("https://en.wikipedia.org/wiki/Triakis_triangular_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("triangle",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=324,
                expected_kind_counts=(("triangle", 324),),
                expected_adjacency_pairs=(("triangle", "triangle"),),
                expected_degree_histogram=((1, 16), (2, 26), (3, 282)),
                expected_signature="8b5758b46c56",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=36,
            slot_vocabulary=_prefixed_slots("s", 36),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("triangle", "triangle", "triangle"),
                ("triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("triangle", "triangle", "triangle"), 94),
                (("triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle", "triangle"), 40),
            ),
            expected_dual_geometry="archimedean-3-12-12",
        ),
    ),
    "deltoidal-trihexagonal": ReferenceFamilySpec(
        geometry="deltoidal-trihexagonal",
        display_name="Deltoidal Trihexagonal",
        source_urls=("https://en.wikipedia.org/wiki/Deltoidal_trihexagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("kite",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("kite", 108),),
                expected_adjacency_pairs=(("kite", "kite"),),
                expected_degree_histogram=((1, 3), (2, 19), (3, 11), (4, 75)),
                expected_signature="8256bbb6a915",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=12,
            slot_vocabulary=tuple(sorted(_prefixed_slots("s", 12))),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("kite", "kite", "kite"),
                ("kite", "kite", "kite", "kite"),
                ("kite", "kite", "kite", "kite", "kite", "kite"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("kite", "kite", "kite"), 28),
                (("kite", "kite", "kite", "kite"), 40),
                (("kite", "kite", "kite", "kite", "kite", "kite"), 12),
            ),
            expected_dual_candidate_geometries=("archimedean-3-4-6-4",),
            expected_dual_structure_signature=((3, 28), (4, 40), (6, 12)),
        ),
    ),
    "prismatic-pentagonal": ReferenceFamilySpec(
        geometry="prismatic-pentagonal",
        display_name="Prismatic Pentagonal",
        source_urls=("https://en.wikipedia.org/wiki/Prismatic_pentagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=72,
                expected_kind_counts=(("pentagon", 72),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_degree_histogram=((2, 2), (3, 12), (4, 18), (5, 40)),
                expected_signature="5fc704eefa57",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=8,
            slot_vocabulary=_prefixed_slots("s", 8),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("pentagon", "pentagon", "pentagon"),
                ("pentagon", "pentagon", "pentagon", "pentagon"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("pentagon", "pentagon", "pentagon"), 60),
                (("pentagon", "pentagon", "pentagon", "pentagon"), 25),
            ),
            expected_dual_candidate_geometries=(
                "archimedean-3-3-3-4-4",
                "archimedean-3-3-4-3-4",
            ),
            expected_dual_structure_signature=((3, 60), (4, 25)),
        ),
    ),
    "floret-pentagonal": ReferenceFamilySpec(
        geometry="floret-pentagonal",
        display_name="Floret Pentagonal",
        source_urls=("https://en.wikipedia.org/wiki/Floret_pentagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=756,
                expected_kind_counts=(("pentagon", 756),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_degree_histogram=((1, 2), (2, 17), (3, 40), (4, 39), (5, 658)),
                expected_signature="68fc9ff72780",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=84,
            slot_vocabulary=_prefixed_slots("s", 84),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("pentagon", "pentagon", "pentagon"),
                ("pentagon", "pentagon", "pentagon", "pentagon", "pentagon", "pentagon"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("pentagon", "pentagon", "pentagon"), 938),
                (("pentagon", "pentagon", "pentagon", "pentagon", "pentagon", "pentagon"), 108),
            ),
            expected_dual_geometry="archimedean-3-3-3-3-6",
        ),
    ),
    "snub-square-dual": ReferenceFamilySpec(
        geometry="snub-square-dual",
        display_name="Snub Square Dual",
        source_urls=(
            "https://en.wikipedia.org/wiki/Snub_square_tiling",
            "https://en.wikipedia.org/wiki/Pentagonal_tiling",
        ),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=72,
                expected_kind_counts=(("pentagon", 72),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_degree_histogram=((1, 1), (2, 7), (3, 14), (4, 5), (5, 45)),
                expected_signature="562ddff9026d",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=8,
            slot_vocabulary=_prefixed_slots("s", 8),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("pentagon", "pentagon", "pentagon"),
                ("pentagon", "pentagon", "pentagon", "pentagon"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("pentagon", "pentagon", "pentagon"), 55),
                (("pentagon", "pentagon", "pentagon", "pentagon"), 25),
            ),
            expected_dual_candidate_geometries=(
                "archimedean-3-3-3-4-4",
                "archimedean-3-3-4-3-4",
            ),
            expected_dual_structure_signature=((3, 55), (4, 25)),
        ),
    ),
}
