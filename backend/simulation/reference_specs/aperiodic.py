from __future__ import annotations

from .helpers import REGULAR_TILING_SOURCES, _alphabetic_slots, _prefixed_slots
from .types import (
    BuilderSignalExpectation,
    MetadataRequirement,
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)


APERIODIC_REFERENCE_FAMILY_SPECS: dict[str, ReferenceFamilySpec] = {
    "penrose-p3-rhombs": ReferenceFamilySpec(
        geometry="penrose-p3-rhombs",
        display_name="Penrose Rhombs",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/",
        ),
        canonical_root_seed_policy="five thick-rhomb star seed",
        allowed_public_cell_kinds=("thick-rhomb", "thin-rhomb"),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=5,
                required_kinds=("thick-rhomb",),
                required_adjacency_pairs=(("thick-rhomb", "thick-rhomb"),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=10,
                required_kinds=("thick-rhomb", "thin-rhomb"),
                required_adjacency_pairs=(
                    ("thick-rhomb", "thick-rhomb"),
                    ("thick-rhomb", "thin-rhomb"),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=24),
            3: ReferenceDepthExpectation(exact_total_cells=66),
        },
    ),
    "penrose-p3-rhombs-vertex": ReferenceFamilySpec(
        geometry="penrose-p3-rhombs-vertex",
        display_name="Penrose Rhombs (Vertex Adjacency)",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/",
        ),
        canonical_root_seed_policy="five thick-rhomb star seed with vertex-neighbor topology",
        allowed_public_cell_kinds=("thick-rhomb", "thin-rhomb"),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=5,
                required_kinds=("thick-rhomb",),
                required_adjacency_pairs=(("thick-rhomb", "thick-rhomb"),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=10,
                required_kinds=("thick-rhomb", "thin-rhomb"),
                required_adjacency_pairs=(
                    ("thick-rhomb", "thick-rhomb"),
                    ("thick-rhomb", "thin-rhomb"),
                    ("thin-rhomb", "thin-rhomb"),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=24),
            3: ReferenceDepthExpectation(exact_total_cells=66),
        },
        notes=(
            "This is the app's vertex-adjacency topology variant of the Penrose rhomb tiling.",
        ),
    ),
    "penrose-p2-kite-dart": ReferenceFamilySpec(
        geometry="penrose-p2-kite-dart",
        display_name="Penrose Kite-Dart",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/penrose-kite-dart/",
        ),
        canonical_root_seed_policy="five-kite star seed",
        allowed_public_cell_kinds=("kite", "dart"),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=5,
                required_kinds=("kite",),
                required_adjacency_pairs=(("kite", "kite"),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=20,
                required_kinds=("kite", "dart"),
                required_adjacency_pairs=(
                    ("dart", "dart"),
                    ("dart", "kite"),
                    ("kite", "kite"),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=70),
            3: ReferenceDepthExpectation(exact_total_cells=240),
        },
    ),
    "ammann-beenker": ReferenceFamilySpec(
        geometry="ammann-beenker",
        display_name="Ammann-Beenker",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/ammann-beenker/",
        ),
        canonical_root_seed_policy="eight-rhomb star seed",
        allowed_public_cell_kinds=("rhomb", "square"),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=8,
                required_kinds=("rhomb",),
                required_adjacency_pairs=(("rhomb", "rhomb"),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=24,
                required_kinds=("rhomb", "square"),
                required_adjacency_pairs=(
                    ("rhomb", "rhomb"),
                    ("rhomb", "square"),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=208),
            3: ReferenceDepthExpectation(exact_total_cells=1304),
        },
    ),
    "spectre": ReferenceFamilySpec(
        geometry="spectre",
        display_name="Spectre",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/spectre/",
            "https://doi.org/10.5070/C64264241",
        ),
        canonical_root_seed_policy="delta supertile seed",
        allowed_public_cell_kinds=("spectre",),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(exact_total_cells=1, required_kinds=("spectre",)),
            1: ReferenceDepthExpectation(
                exact_total_cells=9,
                required_adjacency_pairs=(("spectre", "spectre"),),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=71),
            3: ReferenceDepthExpectation(exact_total_cells=559),
        },
    ),
    "taylor-socolar": ReferenceFamilySpec(
        geometry="taylor-socolar",
        display_name="Taylor-Socolar",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/half-hex/",
            "https://www.mdpi.com/2073-8994/5/1/1",
        ),
        canonical_root_seed_policy="paired half-hex seed",
        allowed_public_cell_kinds=("taylor-half-hex",),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=2,
                required_kinds=("taylor-half-hex",),
                required_adjacency_pairs=(("taylor-half-hex", "taylor-half-hex"),),
            ),
            1: ReferenceDepthExpectation(exact_total_cells=8),
            2: ReferenceDepthExpectation(exact_total_cells=32),
            3: ReferenceDepthExpectation(exact_total_cells=128),
        },
    ),
    "sphinx": ReferenceFamilySpec(
        geometry="sphinx",
        display_name="Sphinx",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/sphinx/",
        ),
        canonical_root_seed_policy="single sphinx rep-tile seed",
        allowed_public_cell_kinds=("sphinx",),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(exact_total_cells=1, required_kinds=("sphinx",)),
            1: ReferenceDepthExpectation(
                exact_total_cells=4,
                required_adjacency_pairs=(("sphinx", "sphinx"),),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=16),
            3: ReferenceDepthExpectation(exact_total_cells=64),
        },
    ),
    "chair": ReferenceFamilySpec(
        geometry="chair",
        display_name="Chair",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/chair/",
        ),
        canonical_root_seed_policy="single chair substitution seed",
        allowed_public_cell_kinds=("chair",),
        required_metadata=(
            MetadataRequirement(
                kind="chair",
                fields=("orientation_token",),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=1,
                expected_orientation_token_counts=(("0", 1),),
                required_kinds=("chair",),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=4,
                expected_orientation_token_counts=(("0", 2), ("1", 1), ("3", 1)),
                required_adjacency_pairs=(("chair", "chair"),),
                min_unique_orientation_tokens=3,
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=16,
                expected_orientation_token_counts=(("0", 6), ("1", 4), ("2", 2), ("3", 4)),
                min_unique_orientation_tokens=4,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=64,
                expected_orientation_token_counts=(("0", 20), ("1", 16), ("2", 12), ("3", 16)),
                min_unique_orientation_tokens=4,
            ),
        },
        notes=(
            "The representative patch is a true chair substitution over four orientation classes.",
            "Patch depth counts substitution rounds, not the earlier nested-corner hierarchy.",
        ),
    ),
    "robinson-triangles": ReferenceFamilySpec(
        geometry="robinson-triangles",
        display_name="Robinson Triangles",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/robinson-triangle/",
        ),
        canonical_root_seed_policy="Penrose-derived Robinson triangle refinement",
        allowed_public_cell_kinds=("robinson-thick", "robinson-thin"),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=10,
                required_kinds=("robinson-thick",),
                required_adjacency_pairs=(("robinson-thick", "robinson-thick"),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=40,
                required_kinds=("robinson-thick", "robinson-thin"),
                required_adjacency_pairs=(
                    ("robinson-thick", "robinson-thick"),
                    ("robinson-thick", "robinson-thin"),
                    ("robinson-thin", "robinson-thin"),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=140),
            3: ReferenceDepthExpectation(
                exact_total_cells=480,
                expected_kind_counts=(
                    ("robinson-thick", 200),
                    ("robinson-thin", 280),
                ),
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
    "hat-monotile": ReferenceFamilySpec(
        geometry="hat-monotile",
        display_name="Hat",
        source_urls=(
            "https://arxiv.org/abs/2303.10798",
            "https://tilings.math.uni-bielefeld.de/substitution/hat-metatiles/",
        ),
        canonical_root_seed_policy="H8 metatile root seed",
        allowed_public_cell_kinds=("hat",),
        required_metadata=(
            MetadataRequirement(
                kind="hat",
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=8,
                required_kinds=("hat",),
                min_unique_chirality_tokens=2,
                required_chirality_adjacency_pairs=(("left", "right"),),
            ),
            1: ReferenceDepthExpectation(
                min_unique_chirality_tokens=2,
                required_adjacency_pairs=(("hat", "hat"),),
                required_chirality_adjacency_pairs=(("left", "right"),),
            ),
            2: ReferenceDepthExpectation(
                min_three_opposite_chirality_neighbor_cells=1,
            ),
        },
        notes=(
            "The hat literature describes a metatile substitution rather than a single-tile root seed.",
            "Representative patches should include reflected copies of the monotile.",
            "The reflected copies should participate in the characteristic three-neighbor local pattern described in the hat-metatiles source.",
        ),
    ),
    "tuebingen-triangle": ReferenceFamilySpec(
        geometry="tuebingen-triangle",
        display_name="Tuebingen Triangle",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/tuebingen-triangle/",
        ),
        canonical_root_seed_policy="handed Robinson-triangle substitution patch",
        allowed_public_cell_kinds=("tuebingen-thick", "tuebingen-thin"),
        required_metadata=(
            MetadataRequirement(
                kind="tuebingen-thick",
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
            MetadataRequirement(
                kind="tuebingen-thin",
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            1: ReferenceDepthExpectation(
                required_kinds=("tuebingen-thick", "tuebingen-thin"),
                required_adjacency_pairs=(
                    ("tuebingen-thick", "tuebingen-thick"),
                    ("tuebingen-thick", "tuebingen-thin"),
                ),
                min_unique_chirality_tokens=2,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=210,
                expected_kind_counts=(
                    ("tuebingen-thick", 130),
                    ("tuebingen-thin", 80),
                ),
                required_kinds=("tuebingen-thick", "tuebingen-thin"),
                required_adjacency_pairs=(
                    ("tuebingen-thick", "tuebingen-thick"),
                    ("tuebingen-thick", "tuebingen-thin"),
                ),
                min_unique_chirality_tokens=2,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
        notes=(
            "The Tuebingen triangle substitution distinguishes left- and right-handed Robinson triangles.",
        ),
    ),
    "dodecagonal-square-triangle": ReferenceFamilySpec(
        geometry="dodecagonal-square-triangle",
        display_name="Dodecagonal Square-Triangle",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/square-triangle/",
        ),
        canonical_root_seed_policy="dodecagonal square-triangle substitution patch",
        allowed_public_cell_kinds=(
            "dodecagonal-square-triangle-square",
            "dodecagonal-square-triangle-triangle",
        ),
        required_metadata=(
            MetadataRequirement(
                kind="dodecagonal-square-triangle-square",
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind="dodecagonal-square-triangle-triangle",
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            1: ReferenceDepthExpectation(
                required_kinds=(
                    "dodecagonal-square-triangle-square",
                    "dodecagonal-square-triangle-triangle",
                ),
                required_adjacency_pairs=(
                    ("dodecagonal-square-triangle-square", "dodecagonal-square-triangle-triangle"),
                    ("dodecagonal-square-triangle-triangle", "dodecagonal-square-triangle-triangle"),
                ),
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=462,
                expected_kind_counts=(
                    ("dodecagonal-square-triangle-square", 140),
                    ("dodecagonal-square-triangle-triangle", 322),
                ),
                required_kinds=(
                    "dodecagonal-square-triangle-square",
                    "dodecagonal-square-triangle-triangle",
                ),
                expected_adjacency_pairs=(
                    ("dodecagonal-square-triangle-square", "dodecagonal-square-triangle-triangle"),
                    ("dodecagonal-square-triangle-triangle", "dodecagonal-square-triangle-triangle"),
                ),
                min_unique_orientation_tokens=12,
                min_unique_chirality_tokens=3,
                expected_signature="f66a7171fb67",  # pragma: allowlist secret
                canonical_patch_fixture_key="dense-depth-3",
            ),
        },
        notes=(
            "The public tiling collapses marked internal prototiles to squares and triangles.",
            "The app's canonical sample uses a cleaned dense central component of the literature patch.",
        ),
    ),
    "shield": ReferenceFamilySpec(
        geometry="shield",
        display_name="Shield",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/shield/",
        ),
        canonical_root_seed_policy="dense 12-fold shield patch cropped from a literature-derived canonical reference field",
        allowed_public_cell_kinds=("shield-shield", "shield-square", "shield-triangle"),
        required_metadata=(
            MetadataRequirement(
                kind="shield-shield",
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind="shield-square",
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind="shield-triangle",
                fields=("tile_family", "orientation_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=36,
                required_kinds=("shield-shield", "shield-square", "shield-triangle"),
                required_adjacency_pairs=(
                    ("shield-shield", "shield-triangle"),
                    ("shield-square", "shield-triangle"),
                    ("shield-triangle", "shield-triangle"),
                ),
                min_unique_orientation_tokens=10,
                max_bounds_aspect_ratio=1.5,
                expected_signature="36eab8ec9a3e",  # pragma: allowlist secret
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=80,
                min_unique_orientation_tokens=12,
                expected_signature="722843e917b9",  # pragma: allowlist secret
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=444,
                required_kinds=("shield-shield", "shield-square", "shield-triangle"),
                required_adjacency_pairs=(
                    ("shield-shield", "shield-square"),
                    ("shield-shield", "shield-triangle"),
                    ("shield-square", "shield-triangle"),
                    ("shield-triangle", "shield-triangle"),
                ),
                min_unique_orientation_tokens=12,
                expected_signature="457feb3fbf5e",  # pragma: allowlist secret
                canonical_patch_fixture_key="dense-depth-3",
            ),
        },
        notes=(
            "The shipped patch is a dense literature-derived central field extracted from the Bielefeld shield patch image.",
            "Odd patch depths apply the documented 15-degree alternation around the central dodecagonal seed.",
            "The public model preserves only public kinds plus orientation metadata; the literature matching-rule decorations are not part of the runtime payload.",
        ),
    ),
    "pinwheel": ReferenceFamilySpec(
        geometry="pinwheel",
        display_name="Pinwheel",
        source_urls=(
            "https://annals.math.princeton.edu/1994/139-3/p05",
            "https://tilings.math.uni-bielefeld.de/substitution/pinwheel/",
        ),
        canonical_root_seed_policy="paired right triangles forming a rectangle",
        allowed_public_cell_kinds=("pinwheel-triangle",),
        required_metadata=(
            MetadataRequirement(
                kind="pinwheel-triangle",
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=2,
                required_kinds=("pinwheel-triangle",),
                required_adjacency_pairs=(("pinwheel-triangle", "pinwheel-triangle"),),
                min_unique_chirality_tokens=2,
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=10,
                min_unique_orientation_tokens=4,
                min_bounds_longest_span=3.0,
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=50,
                min_unique_orientation_tokens=10,
                min_bounds_longest_span=6.0,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=250,
                min_unique_orientation_tokens=30,
                min_bounds_longest_span=12.0,
                canonical_patch_fixture_key="exact-depth-3",
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
        ),
    ),
}
