import sys
import unittest
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

try:
    from backend.simulation.topology_catalog import ARCHIMEDEAN_488_GEOMETRY, KAGOME_GEOMETRY
    from backend.simulation.periodic_face_tilings import (
        PERIODIC_FACE_TILING_GEOMETRIES,
        get_periodic_face_tiling_descriptor,
    )
    from backend.simulation.topology import (
        PENROSE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        build_topology,
    )
    from backend.simulation.topology_validation import (
        recommended_validation_options,
        validate_topology,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.topology_catalog import ARCHIMEDEAN_488_GEOMETRY, KAGOME_GEOMETRY
    from backend.simulation.periodic_face_tilings import (
        PERIODIC_FACE_TILING_GEOMETRIES,
        get_periodic_face_tiling_descriptor,
    )
    from backend.simulation.topology import (
        PENROSE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        build_topology,
    )
    from backend.simulation.topology_validation import (
        recommended_validation_options,
        validate_topology,
    )


PERIODIC_FACE_GEOMETRY_STRATEGY = st.sampled_from(PERIODIC_FACE_TILING_GEOMETRIES)
PENROSE_GEOMETRY_STRATEGY = st.sampled_from((PENROSE_GEOMETRY, PENROSE_VERTEX_GEOMETRY))


def expected_periodic_face_cell_count(geometry: str, width: int, height: int) -> int:
    if geometry == ARCHIMEDEAN_488_GEOMETRY:
        return (width * height) + ((width + 1) * (height + 1))
    if geometry == KAGOME_GEOMETRY:
        return width * height * 3
    descriptor = get_periodic_face_tiling_descriptor(geometry)
    return descriptor.cell_count_per_unit * width * height


class HypothesisTopologyPropertyTests(unittest.TestCase):
    @given(
        geometry=PERIODIC_FACE_GEOMETRY_STRATEGY,
        width=st.integers(min_value=1, max_value=3),
        height=st.integers(min_value=1, max_value=3),
    )
    def test_periodic_face_tilings_preserve_descriptor_cell_count(self, geometry, width, height) -> None:
        topology = build_topology(geometry, width, height)

        self.assertEqual(
            topology.cell_count,
            expected_periodic_face_cell_count(geometry, width, height),
        )

    @given(
        geometry=PERIODIC_FACE_GEOMETRY_STRATEGY,
        width=st.integers(min_value=1, max_value=3),
        height=st.integers(min_value=1, max_value=3),
    )
    @settings(deadline=None)
    def test_periodic_face_tilings_pass_shared_validation_across_dimensions(self, geometry, width, height) -> None:
        topology = build_topology(geometry, width, height)
        validation = validate_topology(topology, **recommended_validation_options(geometry))

        self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))

    @given(
        geometry=PENROSE_GEOMETRY_STRATEGY,
        patch_depth=st.integers(min_value=0, max_value=4),
    )
    def test_penrose_modes_pass_shared_validation_across_depths(self, geometry, patch_depth) -> None:
        topology = build_topology(geometry, 0, 0, patch_depth=patch_depth)
        validation = validate_topology(topology, **recommended_validation_options(geometry))

        self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))


if __name__ == "__main__":
    unittest.main()
