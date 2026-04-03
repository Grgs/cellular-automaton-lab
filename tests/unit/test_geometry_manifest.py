import unittest

from backend.simulation.topology_catalog import (
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    AMMANN_BEENKER_GEOMETRY,
    CHAIR_GEOMETRY,
    DELTOIDAL_HEXAGONAL_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    FLORET_PENTAGONAL_GEOMETRY,
    GEOMETRY_DEFAULT_RULES,
    HAT_MONOTILE_GEOMETRY,
    PINWHEEL_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
    SPHINX_GEOMETRY,
    SPECTRE_GEOMETRY,
    SQUARE_TRIANGLE_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    TUEBINGEN_TRIANGLE_GEOMETRY,
    describe_topologies,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    SUPPORTED_GEOMETRIES,
    TOPOLOGY_VARIANTS,
    describe_topology_variants,
    geometry_uses_backend_viewport_sync,
    geometry_uses_patch_depth,
    get_topology_definition,
    get_topology_variant_for_geometry,
    is_penrose_geometry,
    minimum_grid_dimension_for_geometry,
)


class GeometryManifestTests(unittest.TestCase):
    def test_supported_geometries_are_unique_and_manifest_backed(self) -> None:
        manifest_ids = [definition.geometry_key for definition in TOPOLOGY_VARIANTS]

        self.assertEqual(SUPPORTED_GEOMETRIES, tuple(manifest_ids))
        self.assertEqual(len(manifest_ids), len(set(manifest_ids)))

    def test_default_rule_map_derives_from_manifest(self) -> None:
        self.assertEqual(
            GEOMETRY_DEFAULT_RULES,
            {definition.geometry_key: definition.default_rule for definition in TOPOLOGY_VARIANTS},
        )
        self.assertEqual(GEOMETRY_DEFAULT_RULES[PENROSE_GEOMETRY], "life-b2-s23")
        self.assertEqual(GEOMETRY_DEFAULT_RULES[PENROSE_VERTEX_GEOMETRY], "conway")

    def test_penrose_modes_expose_expected_capabilities(self) -> None:
        edge = get_topology_variant_for_geometry(PENROSE_GEOMETRY)
        vertex = get_topology_variant_for_geometry(PENROSE_VERTEX_GEOMETRY)

        self.assertEqual(edge.family, "aperiodic")
        self.assertEqual(edge.tiling_family, PENROSE_GEOMETRY)
        self.assertEqual(edge.adjacency_mode, "edge")
        self.assertEqual(vertex.family, "aperiodic")
        self.assertEqual(vertex.tiling_family, PENROSE_GEOMETRY)
        self.assertEqual(vertex.adjacency_mode, "vertex")
        self.assertTrue(geometry_uses_patch_depth(PENROSE_GEOMETRY))
        self.assertTrue(geometry_uses_patch_depth(PENROSE_VERTEX_GEOMETRY))
        self.assertFalse(geometry_uses_backend_viewport_sync(PENROSE_GEOMETRY))
        self.assertFalse(geometry_uses_backend_viewport_sync(PENROSE_VERTEX_GEOMETRY))
        self.assertTrue(is_penrose_geometry(PENROSE_GEOMETRY))
        self.assertTrue(is_penrose_geometry(PENROSE_VERTEX_GEOMETRY))

    def test_mixed_capability_helpers_match_manifest(self) -> None:
        self.assertTrue(geometry_uses_backend_viewport_sync("square"))
        self.assertTrue(geometry_uses_backend_viewport_sync(ARCHIMEDEAN_31212_GEOMETRY))
        self.assertTrue(geometry_uses_backend_viewport_sync("trihexagonal-3-6-3-6"))
        self.assertFalse(geometry_uses_patch_depth("square"))

    def test_topology_catalog_exposes_expected_sizing_policy_by_family(self) -> None:
        described = {
            entry["tiling_family"]: entry
            for entry in describe_topologies()
        }

        self.assertEqual(
            described["square"]["sizing_policy"],
            {"control": "cell_size", "default": 12, "min": 8, "max": 24},
        )
        self.assertEqual(described["square"]["render_kind"], "regular_grid")
        self.assertEqual(
            described["hex"]["sizing_policy"],
            {"control": "cell_size", "default": 16, "min": 10, "max": 24},
        )
        self.assertEqual(
            described["triangle"]["sizing_policy"],
            {"control": "cell_size", "default": 20, "min": 12, "max": 24},
        )
        self.assertEqual(
            described[ARCHIMEDEAN_33336_GEOMETRY]["sizing_policy"],
            {"control": "cell_size", "default": 16, "min": 14, "max": 20},
        )
        self.assertEqual(
            described[PENROSE_GEOMETRY]["sizing_policy"],
            {"control": "patch_depth", "default": 4, "min": 0, "max": 6},
        )
        self.assertEqual(
            described[PENROSE_P2_GEOMETRY]["sizing_policy"],
            {"control": "patch_depth", "default": 4, "min": 0, "max": 6},
        )
        self.assertEqual(
            described[AMMANN_BEENKER_GEOMETRY]["sizing_policy"],
            {"control": "patch_depth", "default": 4, "min": 0, "max": 4},
        )
        self.assertEqual(
            described[SPECTRE_GEOMETRY]["sizing_policy"],
            {"control": "patch_depth", "default": 3, "min": 0, "max": 3},
        )
        self.assertEqual(
            described[TAYLOR_SOCOLAR_GEOMETRY]["sizing_policy"],
            {"control": "patch_depth", "default": 3, "min": 0, "max": 5},
        )
        self.assertEqual(
            described[SPHINX_GEOMETRY]["sizing_policy"],
            {"control": "patch_depth", "default": 3, "min": 0, "max": 5},
        )
        self.assertEqual(
            described[CHAIR_GEOMETRY]["sizing_policy"],
            {"control": "patch_depth", "default": 3, "min": 0, "max": 5},
        )
        self.assertEqual(
            described[ROBINSON_TRIANGLES_GEOMETRY]["sizing_policy"],
            {"control": "patch_depth", "default": 3, "min": 0, "max": 5},
        )
        self.assertEqual(described[SPECTRE_GEOMETRY]["render_kind"], "polygon_aperiodic")
        self.assertEqual(described[ARCHIMEDEAN_33336_GEOMETRY]["render_kind"], "polygon_periodic")

    def test_new_archimedean_geometries_have_expected_manifest_defaults(self) -> None:
        expected = {
            ARCHIMEDEAN_31212_GEOMETRY: "archlife-3-12-12",
            ARCHIMEDEAN_3464_GEOMETRY: "archlife-3-4-6-4",
            ARCHIMEDEAN_4612_GEOMETRY: "archlife-4-6-12",
            ARCHIMEDEAN_33434_GEOMETRY: "archlife-3-3-4-3-4",
            ARCHIMEDEAN_33344_GEOMETRY: "archlife-3-3-3-4-4",
            ARCHIMEDEAN_33336_GEOMETRY: "archlife-3-3-3-3-6",
        }

        for geometry, default_rule in expected.items():
            with self.subTest(geometry=geometry):
                definition = get_topology_variant_for_geometry(geometry)
                self.assertEqual(definition.family, "mixed")
                self.assertEqual(definition.sizing_mode, "grid")
                self.assertEqual(definition.viewport_sync_mode, "backend-sync")
                self.assertEqual(definition.default_rule, default_rule)
                self.assertEqual(GEOMETRY_DEFAULT_RULES[geometry], default_rule)
                self.assertEqual(minimum_grid_dimension_for_geometry(geometry), 1)

        self.assertEqual(minimum_grid_dimension_for_geometry("square"), 3)
        self.assertEqual(minimum_grid_dimension_for_geometry("archimedean-4-8-8"), 3)

    def test_new_periodic_mixed_geometries_use_generic_defaults_and_expected_grid_minimums(self) -> None:
        expected = {
            RHOMBILLE_GEOMETRY: 3,
            DELTOIDAL_HEXAGONAL_GEOMETRY: 1,
            TETRAKIS_SQUARE_GEOMETRY: 3,
            TRIAKIS_TRIANGULAR_GEOMETRY: 1,
            DELTOIDAL_TRIHEXAGONAL_GEOMETRY: 1,
            PRISMATIC_PENTAGONAL_GEOMETRY: 1,
            FLORET_PENTAGONAL_GEOMETRY: 1,
            SNUB_SQUARE_DUAL_GEOMETRY: 1,
        }

        for geometry, minimum_dimension in expected.items():
            with self.subTest(geometry=geometry):
                definition = get_topology_variant_for_geometry(geometry)
                self.assertEqual(definition.family, "mixed")
                self.assertEqual(definition.sizing_mode, "grid")
                self.assertEqual(definition.viewport_sync_mode, "backend-sync")
                self.assertEqual(definition.default_rule, "life-b2-s23")
                self.assertEqual(GEOMETRY_DEFAULT_RULES[geometry], "life-b2-s23")
                self.assertEqual(minimum_grid_dimension_for_geometry(geometry), minimum_dimension)

    def test_spectre_geometry_uses_aperiodic_patch_depth_defaults(self) -> None:
        definition = get_topology_variant_for_geometry(SPECTRE_GEOMETRY)

        self.assertEqual(definition.family, "aperiodic")
        self.assertEqual(definition.sizing_mode, "patch_depth")
        self.assertEqual(definition.viewport_sync_mode, "presentation-only")
        self.assertEqual(definition.default_rule, "life-b2-s23")
        self.assertEqual(GEOMETRY_DEFAULT_RULES[SPECTRE_GEOMETRY], "life-b2-s23")
        self.assertTrue(geometry_uses_patch_depth(SPECTRE_GEOMETRY))
        self.assertFalse(geometry_uses_backend_viewport_sync(SPECTRE_GEOMETRY))

    def test_taylor_socolar_geometry_uses_aperiodic_patch_depth_defaults(self) -> None:
        definition = get_topology_variant_for_geometry(TAYLOR_SOCOLAR_GEOMETRY)

        self.assertEqual(definition.family, "aperiodic")
        self.assertEqual(definition.sizing_mode, "patch_depth")
        self.assertEqual(definition.viewport_sync_mode, "presentation-only")
        self.assertEqual(definition.default_rule, "life-b2-s23")
        self.assertEqual(GEOMETRY_DEFAULT_RULES[TAYLOR_SOCOLAR_GEOMETRY], "life-b2-s23")
        self.assertTrue(geometry_uses_patch_depth(TAYLOR_SOCOLAR_GEOMETRY))
        self.assertFalse(geometry_uses_backend_viewport_sync(TAYLOR_SOCOLAR_GEOMETRY))

    def test_sphinx_geometry_uses_aperiodic_patch_depth_defaults(self) -> None:
        definition = get_topology_variant_for_geometry(SPHINX_GEOMETRY)
        family_definition = get_topology_definition(SPHINX_GEOMETRY)

        self.assertEqual(definition.family, "aperiodic")
        self.assertEqual(definition.sizing_mode, "patch_depth")
        self.assertEqual(definition.viewport_sync_mode, "presentation-only")
        self.assertEqual(definition.default_rule, "life-b2-s23")
        self.assertEqual(family_definition.render_kind, "polygon_aperiodic")
        self.assertEqual(GEOMETRY_DEFAULT_RULES[SPHINX_GEOMETRY], "life-b2-s23")
        self.assertTrue(geometry_uses_patch_depth(SPHINX_GEOMETRY))
        self.assertFalse(geometry_uses_backend_viewport_sync(SPHINX_GEOMETRY))

    def test_chair_geometry_uses_aperiodic_patch_depth_defaults(self) -> None:
        definition = get_topology_variant_for_geometry(CHAIR_GEOMETRY)
        family_definition = get_topology_definition(CHAIR_GEOMETRY)

        self.assertEqual(definition.family, "aperiodic")
        self.assertEqual(definition.sizing_mode, "patch_depth")
        self.assertEqual(definition.viewport_sync_mode, "presentation-only")
        self.assertEqual(definition.default_rule, "life-b2-s23")
        self.assertEqual(family_definition.render_kind, "polygon_aperiodic")
        self.assertEqual(GEOMETRY_DEFAULT_RULES[CHAIR_GEOMETRY], "life-b2-s23")
        self.assertTrue(geometry_uses_patch_depth(CHAIR_GEOMETRY))
        self.assertFalse(geometry_uses_backend_viewport_sync(CHAIR_GEOMETRY))

    def test_robinson_triangles_geometry_uses_aperiodic_patch_depth_defaults(self) -> None:
        definition = get_topology_variant_for_geometry(ROBINSON_TRIANGLES_GEOMETRY)
        family_definition = get_topology_definition(ROBINSON_TRIANGLES_GEOMETRY)

        self.assertEqual(definition.family, "aperiodic")
        self.assertEqual(definition.sizing_mode, "patch_depth")
        self.assertEqual(definition.viewport_sync_mode, "presentation-only")
        self.assertEqual(definition.default_rule, "life-b2-s23")
        self.assertEqual(family_definition.render_kind, "polygon_aperiodic")
        self.assertEqual(GEOMETRY_DEFAULT_RULES[ROBINSON_TRIANGLES_GEOMETRY], "life-b2-s23")
        self.assertTrue(geometry_uses_patch_depth(ROBINSON_TRIANGLES_GEOMETRY))
        self.assertFalse(geometry_uses_backend_viewport_sync(ROBINSON_TRIANGLES_GEOMETRY))

    def test_new_substitution_tilings_use_aperiodic_patch_depth_defaults(self) -> None:
        expected = {
            HAT_MONOTILE_GEOMETRY: {"default": 2, "min": 0, "max": 3},
            TUEBINGEN_TRIANGLE_GEOMETRY: {"default": 3, "min": 0, "max": 5},
            SQUARE_TRIANGLE_GEOMETRY: {"default": 3, "min": 0, "max": 4},
            SHIELD_GEOMETRY: {"default": 3, "min": 0, "max": 4},
            PINWHEEL_GEOMETRY: {"default": 3, "min": 0, "max": 4},
        }

        described = {entry["tiling_family"]: entry for entry in describe_topologies()}
        for geometry, sizing_policy in expected.items():
            with self.subTest(geometry=geometry):
                definition = get_topology_variant_for_geometry(geometry)
                family_definition = get_topology_definition(geometry)
                self.assertEqual(definition.family, "aperiodic")
                self.assertEqual(definition.sizing_mode, "patch_depth")
                self.assertEqual(definition.viewport_sync_mode, "presentation-only")
                self.assertEqual(definition.default_rule, "life-b2-s23")
                self.assertEqual(family_definition.render_kind, "polygon_aperiodic")
                self.assertEqual(GEOMETRY_DEFAULT_RULES[geometry], "life-b2-s23")
                self.assertTrue(geometry_uses_patch_depth(geometry))
                self.assertFalse(geometry_uses_backend_viewport_sync(geometry))
                self.assertEqual(described[geometry]["sizing_policy"], {"control": "patch_depth", **sizing_policy})
                self.assertEqual(described[geometry]["render_kind"], "polygon_aperiodic")

    def test_describe_geometries_returns_frontend_ready_metadata(self) -> None:
        described = describe_topology_variants()

        self.assertEqual([entry["id"] for entry in described], list(SUPPORTED_GEOMETRIES))
        vertex_entry = next(
            entry
            for entry in described
            if entry["id"] == PENROSE_VERTEX_GEOMETRY
        )
        self.assertEqual(
            vertex_entry,
            {
                "id": PENROSE_VERTEX_GEOMETRY,
                "geometry_key": PENROSE_VERTEX_GEOMETRY,
                "label": "Penrose P3 Rhombs",
                "picker_group": "Aperiodic",
                "picker_order": 220,
                "default_rule": "conway",
                "sizing_mode": "patch_depth",
                "family": "aperiodic",
                "viewport_sync_mode": "presentation-only",
                "tiling_family": PENROSE_GEOMETRY,
                "adjacency_mode": "vertex",
            },
        )


if __name__ == "__main__":
    unittest.main()
