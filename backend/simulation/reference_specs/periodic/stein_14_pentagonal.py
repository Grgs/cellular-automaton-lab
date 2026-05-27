from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

# Stein-14 pentagonal: the 14th of the 15 known monohedral convex pentagonal
# tilings (Rolf Stein, 1985). Completely determined tile (no degrees of
# freedom):
#   2a = 2c = d = e, A = 90 deg, 2B + C = 360 deg, C + E = 180 deg
# with sin(B) = (sqrt(57) - 3) / 8 and b/a = sqrt((11*sqrt(57) - 25) / 8).
#
# Tiling structure: p2 (2222) symmetry, 6 pentagons per primitive unit,
# 3-isohedral (3 tile orbits). The lattice is a genuine skewed parallelogram
# (not a brick lattice), which is why the descriptor uses lattice_skew_x
# instead of row_offset_x.
#
# Non-edge-to-edge: pentagon edges meet at T-junctions where one pentagon's
# vertex sits on the midpoint of another pentagon's edge. Because the
# vertex coordinates are irrational, the midpoint relationship can't be
# enforced bit-exactly in float arithmetic; topology_validation uses a
# looser overlap tolerance (1e-3) for this geometry (and any future
# geometry registered as non-edge-to-edge + irrational). See
# _NON_EDGE_TO_EDGE_IRRATIONAL_GEOMETRIES in topology_validation.py.
#
# Interior vertex configurations are not reported by the periodic-face
# verifier for non-edge-to-edge tilings (the vertex-star detector assumes
# each vertex is a corner of every adjacent polygon, which T-junctions
# violate). The reference spec asserts what the verifier actually observes:
# kind counts, adjacency, and the open-boundary 3x3 degree histogram.

SPECS = {
    "stein-14-pentagonal": ReferenceFamilySpec(
        geometry="stein-14-pentagonal",
        display_name="Stein 14 Pentagonal",
        source_urls=("https://en.wikipedia.org/wiki/Pentagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("stein14",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=54,
                expected_kind_counts=(("stein14", 54),),
                expected_adjacency_pairs=(("stein14", "stein14"),),
                expected_degree_histogram=(
                    (2, 6),
                    (3, 7),
                    (4, 8),
                    (5, 13),
                    (6, 12),
                    (7, 8),
                ),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=6,
            slot_vocabulary=("t0", "t1", "t2", "t3", "t4", "t5"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            # Non-edge-to-edge: the vertex-star detector returns empty for
            # this geometry, so we don't assert vertex configurations.
            expected_interior_vertex_configurations=(),
            expected_interior_vertex_configuration_frequencies=(),
        ),
    ),
}
