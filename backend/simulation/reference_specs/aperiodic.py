from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    AMMANN_BEENKER_GEOMETRY,
    AMMANN_RHOMB_KIND,
    AMMANN_SQUARE_KIND,
    CHAIR_GEOMETRY,
    CHAIR_KIND,
    DART_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
    HAT_KIND,
    HAT_MONOTILE_GEOMETRY,
    KITE_KIND,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PINWHEEL_GEOMETRY,
    PINWHEEL_TRIANGLE_KIND,
    ROBINSON_THICK_KIND,
    ROBINSON_THIN_KIND,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SHIELD_SHIELD_KIND,
    SHIELD_SQUARE_KIND,
    SHIELD_TRIANGLE_KIND,
    SPECTRE_GEOMETRY,
    SPECTRE_KIND,
    SPHINX_GEOMETRY,
    SPHINX_KIND,
    TAYLOR_HALF_HEX_KIND,
    TAYLOR_SOCOLAR_GEOMETRY,
    THICK_RHOMB_KIND,
    THIN_RHOMB_KIND,
    TUEBINGEN_THICK_KIND,
    TUEBINGEN_THIN_KIND,
    TUEBINGEN_TRIANGLE_GEOMETRY,
    get_aperiodic_family_manifest_entry,
)
from .helpers import REGULAR_TILING_SOURCES, _alphabetic_slots, _prefixed_slots
from .types import (
    BuilderSignalExpectation,
    MetadataRequirement,
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)


def _reference_label(geometry: str) -> str:
    return get_aperiodic_family_manifest_entry(geometry).reference_label


def _public_cell_kinds(geometry: str) -> tuple[str, ...]:
    return get_aperiodic_family_manifest_entry(geometry).public_cell_kinds


APERIODIC_REFERENCE_FAMILY_SPECS: dict[str, ReferenceFamilySpec] = {
    PENROSE_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_GEOMETRY,
        display_name=_reference_label(PENROSE_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/",
        ),
        canonical_root_seed_policy="five thick-rhomb star seed",
        allowed_public_cell_kinds=_public_cell_kinds(PENROSE_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=5,
                required_kinds=(THICK_RHOMB_KIND,),
                required_adjacency_pairs=((THICK_RHOMB_KIND, THICK_RHOMB_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=10,
                required_kinds=(THICK_RHOMB_KIND, THIN_RHOMB_KIND),
                required_adjacency_pairs=(
                    (THICK_RHOMB_KIND, THICK_RHOMB_KIND),
                    (THICK_RHOMB_KIND, THIN_RHOMB_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=24),
            3: ReferenceDepthExpectation(exact_total_cells=66),
        },
    ),
    PENROSE_VERTEX_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_VERTEX_GEOMETRY,
        display_name="Penrose Rhombs (Vertex Adjacency)",
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/penrose-rhomb/",
        ),
        canonical_root_seed_policy="five thick-rhomb star seed with vertex-neighbor topology",
        allowed_public_cell_kinds=_public_cell_kinds(PENROSE_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=5,
                required_kinds=(THICK_RHOMB_KIND,),
                required_adjacency_pairs=((THICK_RHOMB_KIND, THICK_RHOMB_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=10,
                required_kinds=(THICK_RHOMB_KIND, THIN_RHOMB_KIND),
                required_adjacency_pairs=(
                    (THICK_RHOMB_KIND, THICK_RHOMB_KIND),
                    (THICK_RHOMB_KIND, THIN_RHOMB_KIND),
                    (THIN_RHOMB_KIND, THIN_RHOMB_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=24),
            3: ReferenceDepthExpectation(exact_total_cells=66),
        },
        notes=(
            "This is the app's vertex-adjacency topology variant of the Penrose rhomb tiling.",
        ),
    ),
    PENROSE_P2_GEOMETRY: ReferenceFamilySpec(
        geometry=PENROSE_P2_GEOMETRY,
        display_name=_reference_label(PENROSE_P2_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/penrose-kite-dart/",
        ),
        canonical_root_seed_policy="five-kite star seed",
        allowed_public_cell_kinds=_public_cell_kinds(PENROSE_P2_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=5,
                required_kinds=(KITE_KIND,),
                required_adjacency_pairs=((KITE_KIND, KITE_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=20,
                required_kinds=(KITE_KIND, DART_KIND),
                required_adjacency_pairs=(
                    (DART_KIND, DART_KIND),
                    (DART_KIND, KITE_KIND),
                    (KITE_KIND, KITE_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=70),
            3: ReferenceDepthExpectation(exact_total_cells=240),
        },
    ),
    AMMANN_BEENKER_GEOMETRY: ReferenceFamilySpec(
        geometry=AMMANN_BEENKER_GEOMETRY,
        display_name=_reference_label(AMMANN_BEENKER_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/ammann-beenker/",
        ),
        canonical_root_seed_policy="eight-rhomb star seed",
        allowed_public_cell_kinds=_public_cell_kinds(AMMANN_BEENKER_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=8,
                required_kinds=(AMMANN_RHOMB_KIND,),
                required_adjacency_pairs=((AMMANN_RHOMB_KIND, AMMANN_RHOMB_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=24,
                required_kinds=(AMMANN_RHOMB_KIND, AMMANN_SQUARE_KIND),
                required_adjacency_pairs=(
                    (AMMANN_RHOMB_KIND, AMMANN_RHOMB_KIND),
                    (AMMANN_RHOMB_KIND, AMMANN_SQUARE_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=208),
            3: ReferenceDepthExpectation(exact_total_cells=1304),
        },
    ),
    SPECTRE_GEOMETRY: ReferenceFamilySpec(
        geometry=SPECTRE_GEOMETRY,
        display_name=_reference_label(SPECTRE_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/spectre/",
            "https://doi.org/10.5070/C64264241",
        ),
        canonical_root_seed_policy="delta supertile seed",
        allowed_public_cell_kinds=_public_cell_kinds(SPECTRE_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(exact_total_cells=1, required_kinds=(SPECTRE_KIND,)),
            1: ReferenceDepthExpectation(
                exact_total_cells=9,
                required_adjacency_pairs=((SPECTRE_KIND, SPECTRE_KIND),),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=71),
            3: ReferenceDepthExpectation(
                exact_total_cells=559,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
    TAYLOR_SOCOLAR_GEOMETRY: ReferenceFamilySpec(
        geometry=TAYLOR_SOCOLAR_GEOMETRY,
        display_name=_reference_label(TAYLOR_SOCOLAR_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/half-hex/",
            "https://www.mdpi.com/2073-8994/5/1/1",
        ),
        canonical_root_seed_policy="paired half-hex seed",
        allowed_public_cell_kinds=_public_cell_kinds(TAYLOR_SOCOLAR_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=2,
                required_kinds=(TAYLOR_HALF_HEX_KIND,),
                required_adjacency_pairs=((TAYLOR_HALF_HEX_KIND, TAYLOR_HALF_HEX_KIND),),
            ),
            1: ReferenceDepthExpectation(exact_total_cells=8),
            2: ReferenceDepthExpectation(exact_total_cells=32),
            3: ReferenceDepthExpectation(
                exact_total_cells=128,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
    SPHINX_GEOMETRY: ReferenceFamilySpec(
        geometry=SPHINX_GEOMETRY,
        display_name=_reference_label(SPHINX_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/sphinx/",
        ),
        canonical_root_seed_policy="single sphinx rep-tile seed",
        allowed_public_cell_kinds=_public_cell_kinds(SPHINX_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(exact_total_cells=1, required_kinds=(SPHINX_KIND,)),
            1: ReferenceDepthExpectation(
                exact_total_cells=4,
                required_adjacency_pairs=((SPHINX_KIND, SPHINX_KIND),),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=16),
            3: ReferenceDepthExpectation(
                exact_total_cells=64,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
    CHAIR_GEOMETRY: ReferenceFamilySpec(
        geometry=CHAIR_GEOMETRY,
        display_name=_reference_label(CHAIR_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/chair/",
        ),
        canonical_root_seed_policy="single chair substitution seed",
        allowed_public_cell_kinds=_public_cell_kinds(CHAIR_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=CHAIR_KIND,
                fields=("orientation_token",),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=1,
                expected_orientation_token_counts=(("0", 1),),
                required_kinds=(CHAIR_KIND,),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=4,
                expected_orientation_token_counts=(("0", 2), ("1", 1), ("3", 1)),
                required_adjacency_pairs=((CHAIR_KIND, CHAIR_KIND),),
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
    ROBINSON_TRIANGLES_GEOMETRY: ReferenceFamilySpec(
        geometry=ROBINSON_TRIANGLES_GEOMETRY,
        display_name=_reference_label(ROBINSON_TRIANGLES_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/robinson-triangle/",
        ),
        canonical_root_seed_policy="Penrose-derived Robinson triangle refinement",
        allowed_public_cell_kinds=_public_cell_kinds(ROBINSON_TRIANGLES_GEOMETRY),
        required_metadata=(),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=10,
                required_kinds=(ROBINSON_THICK_KIND,),
                required_adjacency_pairs=((ROBINSON_THICK_KIND, ROBINSON_THICK_KIND),),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=40,
                required_kinds=(ROBINSON_THICK_KIND, ROBINSON_THIN_KIND),
                required_adjacency_pairs=(
                    (ROBINSON_THICK_KIND, ROBINSON_THICK_KIND),
                    (ROBINSON_THICK_KIND, ROBINSON_THIN_KIND),
                    (ROBINSON_THIN_KIND, ROBINSON_THIN_KIND),
                ),
            ),
            2: ReferenceDepthExpectation(exact_total_cells=140),
            3: ReferenceDepthExpectation(
                exact_total_cells=480,
                expected_kind_counts=(
                    (ROBINSON_THICK_KIND, 200),
                    (ROBINSON_THIN_KIND, 280),
                ),
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
    ),
    HAT_MONOTILE_GEOMETRY: ReferenceFamilySpec(
        geometry=HAT_MONOTILE_GEOMETRY,
        display_name=_reference_label(HAT_MONOTILE_GEOMETRY),
        source_urls=(
            "https://arxiv.org/abs/2303.10798",
            "https://tilings.math.uni-bielefeld.de/substitution/hat-metatiles/",
        ),
        canonical_root_seed_policy="H8 metatile root seed",
        allowed_public_cell_kinds=_public_cell_kinds(HAT_MONOTILE_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=HAT_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=8,
                required_kinds=(HAT_KIND,),
                min_unique_chirality_tokens=2,
                required_chirality_adjacency_pairs=(("left", "right"),),
            ),
            1: ReferenceDepthExpectation(
                min_unique_chirality_tokens=2,
                required_adjacency_pairs=((HAT_KIND, HAT_KIND),),
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
    TUEBINGEN_TRIANGLE_GEOMETRY: ReferenceFamilySpec(
        geometry=TUEBINGEN_TRIANGLE_GEOMETRY,
        display_name=_reference_label(TUEBINGEN_TRIANGLE_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/tuebingen-triangle/",
        ),
        canonical_root_seed_policy="handed Robinson-triangle substitution patch",
        allowed_public_cell_kinds=_public_cell_kinds(TUEBINGEN_TRIANGLE_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=TUEBINGEN_THICK_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
            MetadataRequirement(
                kind=TUEBINGEN_THIN_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            1: ReferenceDepthExpectation(
                required_kinds=(TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                required_adjacency_pairs=(
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THICK_KIND),
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                ),
                min_unique_chirality_tokens=2,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=210,
                expected_kind_counts=(
                    (TUEBINGEN_THICK_KIND, 130),
                    (TUEBINGEN_THIN_KIND, 80),
                ),
                required_kinds=(TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                required_adjacency_pairs=(
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THICK_KIND),
                    (TUEBINGEN_THICK_KIND, TUEBINGEN_THIN_KIND),
                ),
                min_unique_chirality_tokens=2,
                canonical_patch_fixture_key="exact-depth-3",
            ),
        },
        notes=(
            "The Tuebingen triangle substitution distinguishes left- and right-handed Robinson triangles.",
        ),
    ),
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY: ReferenceFamilySpec(
        geometry=DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        display_name=_reference_label(DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/square-triangle/",
        ),
        canonical_root_seed_policy="dodecagonal square-triangle substitution patch",
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
                required_kinds=(
                    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                ),
                required_adjacency_pairs=(
                    (DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND, DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND),
                    (DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND, DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND),
                ),
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=462,
                expected_kind_counts=(
                    (DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND, 140),
                    (DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND, 322),
                ),
                required_kinds=(
                    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                ),
                expected_adjacency_pairs=(
                    (DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND, DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND),
                    (DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND, DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND),
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
    SHIELD_GEOMETRY: ReferenceFamilySpec(
        geometry=SHIELD_GEOMETRY,
        display_name=_reference_label(SHIELD_GEOMETRY),
        source_urls=(
            "https://tilings.math.uni-bielefeld.de/substitution/shield/",
        ),
        canonical_root_seed_policy="dense 12-fold shield patch cropped from a literature-derived canonical field with a backend-owned dodecagonal center window",
        allowed_public_cell_kinds=_public_cell_kinds(SHIELD_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=SHIELD_SHIELD_KIND,
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind=SHIELD_SQUARE_KIND,
                fields=("tile_family", "orientation_token"),
            ),
            MetadataRequirement(
                kind=SHIELD_TRIANGLE_KIND,
                fields=("tile_family", "orientation_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=40,
                required_kinds=(SHIELD_SHIELD_KIND, SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                required_adjacency_pairs=(
                    (SHIELD_SHIELD_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_TRIANGLE_KIND, SHIELD_TRIANGLE_KIND),
                ),
                min_unique_orientation_tokens=10,
                max_bounds_aspect_ratio=1.5,
                expected_signature="37d013f30fc0",  # pragma: allowlist secret
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=81,
                min_unique_orientation_tokens=12,
                expected_signature="1d884216655b",  # pragma: allowlist secret
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=443,
                required_kinds=(SHIELD_SHIELD_KIND, SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                required_adjacency_pairs=(
                    (SHIELD_SHIELD_KIND, SHIELD_SQUARE_KIND),
                    (SHIELD_SHIELD_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND),
                    (SHIELD_TRIANGLE_KIND, SHIELD_TRIANGLE_KIND),
                ),
                min_unique_orientation_tokens=12,
                expected_signature="95a927bb2a20",  # pragma: allowlist secret
                canonical_patch_fixture_key="dense-depth-3",
            ),
        },
        notes=(
            "The shipped patch is a dense literature-derived central field extracted from the Bielefeld shield patch image.",
            "Runtime depth selection uses a backend-owned dodecagonal center window instead of graph-distance thresholds.",
            "Odd patch depths apply the documented 15-degree alternation around the central dodecagonal seed.",
            "Runtime geometry now applies a minimal inward trace-cleanup normalization to remove positive-area overlap from the traced polygons; any seam hiding is render-only.",
            "The public model preserves only public kinds plus orientation metadata; the literature matching-rule decorations are not part of the runtime payload.",
        ),
    ),
    PINWHEEL_GEOMETRY: ReferenceFamilySpec(
        geometry=PINWHEEL_GEOMETRY,
        display_name=_reference_label(PINWHEEL_GEOMETRY),
        source_urls=(
            "https://annals.math.princeton.edu/1994/139-3/p05",
            "https://tilings.math.uni-bielefeld.de/substitution/pinwheel/",
        ),
        canonical_root_seed_policy="paired right triangles forming a rectangle",
        allowed_public_cell_kinds=_public_cell_kinds(PINWHEEL_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=PINWHEEL_TRIANGLE_KIND,
                fields=("tile_family", "orientation_token", "chirality_token"),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=2,
                required_kinds=(PINWHEEL_TRIANGLE_KIND,),
                required_adjacency_pairs=((PINWHEEL_TRIANGLE_KIND, PINWHEEL_TRIANGLE_KIND),),
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
            "The representative literature patch starts from two right triangles forming a rectangle.",
        ),
    ),
}
