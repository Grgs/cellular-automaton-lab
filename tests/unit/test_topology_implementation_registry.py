import unittest

from backend.simulation.topology_implementation_registry import (
    describe_topology_implementations,
    get_topology_implementation,
    render_kind_for_geometry,
)


class TopologyImplementationRegistryTests(unittest.TestCase):
    def test_regular_periodic_and_aperiodic_geometries_resolve_expected_builder_and_render_kinds(self) -> None:
        self.assertEqual(get_topology_implementation("square").builder_kind, "regular_grid")
        self.assertEqual(get_topology_implementation("square").render_kind, "regular_grid")
        self.assertEqual(
            get_topology_implementation("archimedean-4-8-8").builder_kind,
            "periodic_face",
        )
        self.assertEqual(
            render_kind_for_geometry("archimedean-4-8-8"),
            "polygon_periodic",
        )
        self.assertEqual(get_topology_implementation("spectre").builder_kind, "substitution_patch")
        self.assertEqual(render_kind_for_geometry("spectre"), "polygon_aperiodic")

    def test_registry_covers_new_sphinx_geometry(self) -> None:
        implementation = get_topology_implementation("sphinx")

        self.assertEqual(implementation.geometry_key, "sphinx")
        self.assertEqual(implementation.builder_kind, "substitution_patch")
        self.assertEqual(implementation.render_kind, "polygon_aperiodic")

    def test_unknown_geometry_falls_back_to_square_implementation(self) -> None:
        implementation = get_topology_implementation("not-a-geometry")

        self.assertEqual(implementation.geometry_key, "square")
        self.assertEqual(implementation.builder_kind, "regular_grid")

    def test_registry_describes_supported_implementation_definitions(self) -> None:
        geometries = {definition.geometry_key for definition in describe_topology_implementations()}

        self.assertIn("square", geometries)
        self.assertIn("spectre", geometries)
        self.assertIn("sphinx", geometries)


if __name__ == "__main__":
    unittest.main()
