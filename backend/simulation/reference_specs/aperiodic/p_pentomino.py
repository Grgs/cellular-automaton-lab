from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    P_PENTOMINO_GEOMETRY,
    P_PENTOMINO_KIND,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
    P_PENTOMINO_GEOMETRY: ReferenceFamilySpec(
        geometry=P_PENTOMINO_GEOMETRY,
        display_name=_reference_label(P_PENTOMINO_GEOMETRY),
        source_urls=("https://en.wikipedia.org/wiki/Rep-tile",),
        root_seed_policy="two P-pentomino roots forming a compact 5x2 rectangle",
        allowed_public_cell_kinds=_public_cell_kinds(P_PENTOMINO_GEOMETRY),
        required_metadata=(
            MetadataRequirement(
                kind=P_PENTOMINO_KIND,
                fields=("orientation_token",),
            ),
        ),
        depth_expectations={
            0: ReferenceDepthExpectation(
                exact_total_cells=2,
                expected_orientation_token_counts=(("1", 1), ("3", 1)),
                required_kinds=(P_PENTOMINO_KIND,),
            ),
            1: ReferenceDepthExpectation(
                exact_total_cells=8,
                expected_orientation_token_counts=(
                    ("0", 1),
                    ("2", 1),
                    ("4", 1),
                    ("5", 1),
                    ("6", 2),
                    ("7", 2),
                ),
                required_adjacency_pairs=((P_PENTOMINO_KIND, P_PENTOMINO_KIND),),
                min_unique_orientation_tokens=6,
            ),
            2: ReferenceDepthExpectation(
                exact_total_cells=32,
                expected_orientation_token_counts=(
                    ("0", 4),
                    ("1", 6),
                    ("2", 4),
                    ("3", 6),
                    ("4", 4),
                    ("5", 4),
                    ("6", 2),
                    ("7", 2),
                ),
                min_unique_orientation_tokens=8,
            ),
            3: ReferenceDepthExpectation(
                exact_total_cells=128,
                expected_orientation_token_counts=(
                    ("0", 16),
                    ("1", 12),
                    ("2", 16),
                    ("3", 12),
                    ("4", 16),
                    ("5", 16),
                    ("6", 20),
                    ("7", 20),
                ),
                min_unique_orientation_tokens=8,
            ),
        },
        notes=(
            "The P-pentomino is the unique rep-4 pentomino (every other pentomino fails "
            "rep-4, verified by exhaustive exact cover); the representative patch starts "
            "from two roots forming a 5x2 rectangle, then applies the exact self-similar "
            "substitution.",
            "Being chiral, the substitution closes over the full eight-element dihedral "
            "group D4, so all eight orientation tokens appear from depth 2 onward. Patch "
            "depth counts substitution rounds (2 * 4**depth cells).",
        ),
    ),
}
