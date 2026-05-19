from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    HAT_KIND,
    HAT_MONOTILE_GEOMETRY,
)
from backend.simulation.reference_specs.types import (
    MetadataRequirement,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

from ._helpers import _public_cell_kinds, _reference_label

SPECS = {
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
}
