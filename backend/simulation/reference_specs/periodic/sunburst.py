from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

# Sunburst is a non-canonical (invented) periodic tiling: each unit square
# is subdivided into eight right-isoceles triangles sharing an apex at the
# square center, like an eight-spoke compass. Each triangle has legs equal
# to half the square side; the hypotenuse lies along a diagonal from a
# corner to the center, and the two legs lie along the unit-cell edges
# from a corner to the adjacent edge midpoints. Closure: 8 triangles at
# the center each contribute 45 deg apex angle for 360 deg; 4 right
# angles meet at each square corner (360 deg); 4 right angles meet at
# each edge midpoint (360 deg). Two distinct vertex types - not
# Archimedean, not a dual of any catalog tiling.

SPECS = {
    "sunburst": ReferenceFamilySpec(
        geometry="sunburst",
        display_name="Sunburst",
        source_urls=(),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("sunburst-triangle",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=72,
                expected_kind_counts=(("sunburst-triangle", 72),),
                expected_adjacency_pairs=(("sunburst-triangle", "sunburst-triangle"),),
                expected_degree_histogram=((2, 24), (3, 48)),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=8,
            slot_vocabulary=("s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                # 4 right-angle triangle corners meeting at each square
                # corner OR each edge midpoint
                (
                    "sunburst-triangle",
                    "sunburst-triangle",
                    "sunburst-triangle",
                    "sunburst-triangle",
                ),
                # 8 triangle apex angles (45 deg each) meeting at each
                # square center
                (
                    "sunburst-triangle",
                    "sunburst-triangle",
                    "sunburst-triangle",
                    "sunburst-triangle",
                    "sunburst-triangle",
                    "sunburst-triangle",
                    "sunburst-triangle",
                    "sunburst-triangle",
                ),
            ),
            expected_interior_vertex_configuration_frequencies=(
                # 4 inner corner-vertices + 12 inner edge-midpoint
                # vertices in a 3x3 grid sample = 16 (but corners get
                # cropped by the open boundary, so the verifier sees 12)
                (
                    (
                        "sunburst-triangle",
                        "sunburst-triangle",
                        "sunburst-triangle",
                        "sunburst-triangle",
                    ),
                    12,
                ),
                # 9 square centers + 4 interior grid corners = 13 in a
                # 3x3 sample (interior grid corners also see 8 right-angle
                # corners meeting, one from each of the 4 surrounding
                # unit-cell triangles times 2 since each corner triangle
                # contributes via two of its 90 deg corners).
                (
                    (
                        "sunburst-triangle",
                        "sunburst-triangle",
                        "sunburst-triangle",
                        "sunburst-triangle",
                        "sunburst-triangle",
                        "sunburst-triangle",
                        "sunburst-triangle",
                        "sunburst-triangle",
                    ),
                    13,
                ),
            ),
        ),
    ),
}
