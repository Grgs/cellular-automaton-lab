from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

# House (home-plate) pentagon: the simplest Type 1 monohedral convex pentagonal
# tiling in the Reinhardt classification. The prototile is a unit square with a
# symmetric 45-degree roof, so its interior angles are 90 / 90 / 135 / 90 / 135
# (sum 540) and its pair of vertical sides is parallel.
#
# Tiling structure: upright houses pack in rows sharing their vertical edges;
# an inverted house fills the downward V between adjacent roofs, and the
# inverted tops carry the next row shifted by half a cell. That half-cell shift
# is a cumulative skew, so the descriptor uses lattice_skew_x (25, half the
# 50-unit cell width) with a two-tile primitive unit (one upright + one
# inverted). Unlike stein-14, every coordinate is rational, so the tiling is
# genuinely edge-to-edge: every shared edge matches bit-exactly, with no
# T-junctions and no irrational-tolerance handling. The verifier therefore can
# (and does) assert the interior vertex configurations.
#
# Interior vertices are either three houses meeting (90 + 135 + 135 = 360) or
# four houses meeting (90 * 4 = 360), in a 3:1 ratio on the open-boundary 3x3
# sample.

SPECS = {
    "house-pentagonal": ReferenceFamilySpec(
        geometry="house-pentagonal",
        display_name="House Pentagonal",
        source_urls=("https://en.wikipedia.org/wiki/Pentagonal_tiling",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("house-pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=18,
                expected_kind_counts=(("house-pentagon", 18),),
                expected_adjacency_pairs=(("house-pentagon", "house-pentagon"),),
                expected_degree_histogram=(
                    (2, 2),
                    (3, 6),
                    (4, 6),
                    (5, 4),
                ),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=2,
            slot_vocabulary=("down", "up"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("house-pentagon", "house-pentagon", "house-pentagon"),
                ("house-pentagon", "house-pentagon", "house-pentagon", "house-pentagon"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("house-pentagon", "house-pentagon", "house-pentagon"), 12),
                (
                    (
                        "house-pentagon",
                        "house-pentagon",
                        "house-pentagon",
                        "house-pentagon",
                    ),
                    4,
                ),
            ),
        ),
    ),
}
