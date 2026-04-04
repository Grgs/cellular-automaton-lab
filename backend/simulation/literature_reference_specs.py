from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class BuilderSignalExpectation:
    module: str
    attribute: str
    expected_value: object


@dataclass(frozen=True)
class MetadataRequirement:
    kind: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class ReferenceDepthExpectation:
    exact_total_cells: int | None = None
    minimum_total_cells: int | None = None
    expected_kind_counts: tuple[tuple[str, int], ...] | None = None
    required_kinds: tuple[str, ...] = ()
    expected_adjacency_pairs: tuple[tuple[str, str], ...] | None = None
    required_adjacency_pairs: tuple[tuple[str, str], ...] = ()
    expected_degree_histogram: tuple[tuple[int, int], ...] | None = None
    min_unique_orientation_tokens: int | None = None
    min_unique_chirality_tokens: int | None = None
    max_bounds_aspect_ratio: float | None = None
    expected_signature: str | None = None


@dataclass(frozen=True)
class ReferenceFamilySpec:
    geometry: str
    display_name: str
    source_urls: tuple[str, ...]
    canonical_root_seed_policy: str
    allowed_public_cell_kinds: tuple[str, ...]
    required_metadata: tuple[MetadataRequirement, ...]
    sample_mode: Literal["patch_depth", "grid"] = "patch_depth"
    depth_expectations: dict[int, ReferenceDepthExpectation] = field(default_factory=dict)
    builder_signals: tuple[BuilderSignalExpectation, ...] = ()
    exact_reference_mode: str | None = None
    notes: tuple[str, ...] = ()


REGULAR_TILING_SOURCES = (
    "https://en.wikipedia.org/wiki/Regular_tiling",
)
ARCHIMEDEAN_TILING_SOURCES = (
    "https://en.wikipedia.org/wiki/Archimedean_tilings",
)
UNIFORM_TILING_SOURCES = (
    "https://en.wikipedia.org/wiki/List_of_Euclidean_uniform_tilings",
)


REFERENCE_FAMILY_SPECS: dict[str, ReferenceFamilySpec] = {
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
    "archimedean-4-8-8": ReferenceFamilySpec(
        geometry="archimedean-4-8-8",
        display_name="Square-Octagon (4.8.8)",
        source_urls=ARCHIMEDEAN_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("octagon", "square"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=25,
                expected_kind_counts=(("octagon", 9), ("square", 16)),
                expected_adjacency_pairs=(("octagon", "octagon"), ("octagon", "square")),
                expected_signature="17bcb9c29121",  # pragma: allowlist secret
            ),
        },
    ),
    "archimedean-3-12-12": ReferenceFamilySpec(
        geometry="archimedean-3-12-12",
        display_name="Truncated Hexagonal (3.12.12)",
        source_urls=ARCHIMEDEAN_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("dodecagon", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=162,
                expected_kind_counts=(("dodecagon", 54), ("triangle", 108)),
                expected_adjacency_pairs=(("dodecagon", "dodecagon"), ("dodecagon", "triangle")),
                expected_signature="06279aa8cb8f",  # pragma: allowlist secret
            ),
        },
    ),
    "archimedean-3-4-6-4": ReferenceFamilySpec(
        geometry="archimedean-3-4-6-4",
        display_name="Rhombitrihexagonal (3.4.6.4)",
        source_urls=ARCHIMEDEAN_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("hexagon", "square", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("hexagon", 18), ("square", 54), ("triangle", 36)),
                expected_adjacency_pairs=(("hexagon", "square"), ("square", "triangle")),
                expected_signature="e116b6803eec",  # pragma: allowlist secret
            ),
        },
    ),
    "archimedean-4-6-12": ReferenceFamilySpec(
        geometry="archimedean-4-6-12",
        display_name="Truncated Trihexagonal (4.6.12)",
        source_urls=ARCHIMEDEAN_TILING_SOURCES,
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
                expected_signature="f9d9986097c7",  # pragma: allowlist secret
            ),
        },
    ),
    "archimedean-3-3-4-3-4": ReferenceFamilySpec(
        geometry="archimedean-3-3-4-3-4",
        display_name="Snub Square (3.3.4.3.4)",
        source_urls=ARCHIMEDEAN_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("square", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("square", 36), ("triangle", 72)),
                expected_adjacency_pairs=(("square", "triangle"), ("triangle", "triangle")),
                expected_signature="d68bc0cacc26",  # pragma: allowlist secret
            ),
        },
    ),
    "archimedean-3-3-3-4-4": ReferenceFamilySpec(
        geometry="archimedean-3-3-3-4-4",
        display_name="Elongated Triangular (3.3.3.4.4)",
        source_urls=ARCHIMEDEAN_TILING_SOURCES,
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
                expected_signature="5a6ddd8b8e23",  # pragma: allowlist secret
            ),
        },
    ),
    "archimedean-3-3-3-3-6": ReferenceFamilySpec(
        geometry="archimedean-3-3-3-3-6",
        display_name="Snub Trihexagonal (3.3.3.3.6)",
        source_urls=ARCHIMEDEAN_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("hexagon", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=1134,
                expected_kind_counts=(("hexagon", 126), ("triangle", 1008)),
                expected_adjacency_pairs=(("hexagon", "triangle"), ("triangle", "triangle")),
                expected_signature="65f0ec0732f0",  # pragma: allowlist secret
            ),
        },
    ),
    "trihexagonal-3-6-3-6": ReferenceFamilySpec(
        geometry="trihexagonal-3-6-3-6",
        display_name="Kagome / Trihexagonal (3.6.3.6)",
        source_urls=(
            "https://en.wikipedia.org/wiki/Trihexagonal_tiling",
            *ARCHIMEDEAN_TILING_SOURCES,
        ),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("hexagon", "triangle-down", "triangle-up"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=27,
                expected_kind_counts=(("hexagon", 9), ("triangle-down", 9), ("triangle-up", 9)),
                expected_adjacency_pairs=(("hexagon", "triangle-down"), ("hexagon", "triangle-up")),
                expected_signature="9e8a5ba64587",  # pragma: allowlist secret
            ),
        },
    ),
    "cairo-pentagonal": ReferenceFamilySpec(
        geometry="cairo-pentagonal",
        display_name="Cairo Pentagonal",
        source_urls=(
            "https://en.wikipedia.org/wiki/Cairo_pentagonal_tiling",
            *UNIFORM_TILING_SOURCES,
        ),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=36,
                expected_kind_counts=(("pentagon", 36),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_signature="e33351b2ed77",  # pragma: allowlist secret
            ),
        },
    ),
    "rhombille": ReferenceFamilySpec(
        geometry="rhombille",
        display_name="Rhombille",
        source_urls=(
            "https://en.wikipedia.org/wiki/Rhombille_tiling",
            *UNIFORM_TILING_SOURCES,
        ),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("rhombus",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=54,
                expected_kind_counts=(("rhombus", 54),),
                expected_adjacency_pairs=(("rhombus", "rhombus"),),
                expected_signature="0c57a0b0510a",  # pragma: allowlist secret
            ),
        },
    ),
    "deltoidal-hexagonal": ReferenceFamilySpec(
        geometry="deltoidal-hexagonal",
        display_name="Deltoidal Hexagonal",
        source_urls=UNIFORM_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("kite",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("kite", 108),),
                expected_adjacency_pairs=(("kite", "kite"),),
                expected_signature="b5d904bfe95c",  # pragma: allowlist secret
            ),
        },
    ),
    "tetrakis-square": ReferenceFamilySpec(
        geometry="tetrakis-square",
        display_name="Tetrakis Square",
        source_urls=UNIFORM_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("triangle",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=36,
                expected_kind_counts=(("triangle", 36),),
                expected_adjacency_pairs=(("triangle", "triangle"),),
                expected_signature="d7592c13db1e",  # pragma: allowlist secret
            ),
        },
    ),
    "triakis-triangular": ReferenceFamilySpec(
        geometry="triakis-triangular",
        display_name="Triakis Triangular",
        source_urls=UNIFORM_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("triangle",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=324,
                expected_kind_counts=(("triangle", 324),),
                expected_adjacency_pairs=(("triangle", "triangle"),),
                expected_signature="8b5758b46c56",  # pragma: allowlist secret
            ),
        },
    ),
    "deltoidal-trihexagonal": ReferenceFamilySpec(
        geometry="deltoidal-trihexagonal",
        display_name="Deltoidal Trihexagonal",
        source_urls=UNIFORM_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("kite",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("kite", 108),),
                expected_adjacency_pairs=(("kite", "kite"),),
                expected_signature="8256bbb6a915",  # pragma: allowlist secret
            ),
        },
    ),
    "prismatic-pentagonal": ReferenceFamilySpec(
        geometry="prismatic-pentagonal",
        display_name="Prismatic Pentagonal",
        source_urls=(
            "https://en.wikipedia.org/wiki/Prismatic_pentagonal_tiling",
            *UNIFORM_TILING_SOURCES,
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
                expected_signature="5fc704eefa57",  # pragma: allowlist secret
            ),
        },
    ),
    "floret-pentagonal": ReferenceFamilySpec(
        geometry="floret-pentagonal",
        display_name="Floret Pentagonal",
        source_urls=(
            "https://en.wikipedia.org/wiki/Floret_pentagonal_tiling",
            *UNIFORM_TILING_SOURCES,
        ),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=756,
                expected_kind_counts=(("pentagon", 756),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_signature="68fc9ff72780",  # pragma: allowlist secret
            ),
        },
    ),
    "snub-square-dual": ReferenceFamilySpec(
        geometry="snub-square-dual",
        display_name="Snub Square Dual",
        source_urls=UNIFORM_TILING_SOURCES,
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=72,
                expected_kind_counts=(("pentagon", 72),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_signature="562ddff9026d",  # pragma: allowlist secret
            ),
        },
    ),
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
        canonical_root_seed_policy="single chair rep-tile seed",
        allowed_public_cell_kinds=("chair",),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(exact_total_cells=1, required_kinds=("chair",)),
            1: ReferenceDepthExpectation(
                exact_total_cells=4,
                required_adjacency_pairs=(("chair", "chair"),),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=16),
            3: ReferenceDepthExpectation(exact_total_cells=64),
        },
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
            3: ReferenceDepthExpectation(exact_total_cells=480),
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
                minimum_total_cells=2,
                required_kinds=("hat",),
            ),
            1: ReferenceDepthExpectation(
                min_unique_chirality_tokens=2,
                required_adjacency_pairs=(("hat", "hat"),),
            ),
        },
        notes=(
            "The hat literature describes a metatile substitution rather than a single-tile root seed.",
            "Representative patches should include reflected copies of the monotile.",
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
        },
        notes=(
            "The Tuebingen triangle substitution distinguishes left- and right-handed Robinson triangles.",
        ),
    ),
    "square-triangle": ReferenceFamilySpec(
        geometry="square-triangle",
        display_name="Square-Triangle",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/square-triangle/",
        ),
        canonical_root_seed_policy="12-fold square-triangle substitution patch",
        allowed_public_cell_kinds=(
            "square-triangle-square",
            "square-triangle-triangle",
        ),
        required_metadata=(
            MetadataRequirement(
                kind="square-triangle-square",
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind="square-triangle-triangle",
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            1: ReferenceDepthExpectation(
                required_kinds=(
                    "square-triangle-square",
                    "square-triangle-triangle",
                ),
                required_adjacency_pairs=(
                    ("square-triangle-square", "square-triangle-triangle"),
                    ("square-triangle-triangle", "square-triangle-triangle"),
                ),
            ),
        },
        notes=(
            "The public tiling collapses marked internal prototiles to squares and triangles.",
        ),
    ),
    "shield": ReferenceFamilySpec(
        geometry="shield",
        display_name="Shield",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/shield/",
        ),
        canonical_root_seed_policy="decorated 12-fold shield substitution patch",
        allowed_public_cell_kinds=("shield-shield", "shield-square", "shield-triangle"),
        required_metadata=(
            MetadataRequirement(
                kind="shield-shield",
                fields=("tile_family", "orientation_token", "decoration_tokens"),
            ),
            MetadataRequirement(
                kind="shield-square",
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind="shield-triangle",
                fields=(
                    "tile_family",
                    "orientation_token",
                    "chirality_token",
                    "decoration_tokens",
                ),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                required_kinds=("shield-shield", "shield-square", "shield-triangle"),
                required_adjacency_pairs=(
                    ("shield-shield", "shield-square"),
                    ("shield-shield", "shield-triangle"),
                ),
                max_bounds_aspect_ratio=4.0,
            ),
        },
        notes=(
            "Decorations are authoritative for matching rules even though the renderer ignores them.",
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
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=50,
                min_unique_orientation_tokens=10,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=250,
                min_unique_orientation_tokens=30,
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


STAGED_REFERENCE_WAIVERS: frozenset[str] = frozenset()
