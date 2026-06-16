import sys
import unittest
from pathlib import Path

try:
    from tests.api.support import ApiTestCase
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.api.support import ApiTestCase


class ApiCompareTests(ApiTestCase):
    def test_compare_returns_one_result_per_requested_tiling(self) -> None:
        response = self.client.post(
            "/api/compare",
            json={
                "seed": "01100 11000 01000",
                "rule": "conway",
                "geometries": ["square", "hex", "sphinx"],
                "steps": 12,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        comparison = payload["comparison"]
        self.assertEqual(comparison["rule_name"], "conway")
        geometries = [result["geometry"] for result in comparison["results"]]
        self.assertEqual(geometries, ["square", "hex", "sphinx"])
        for result in comparison["results"]:
            self.assertEqual(len(result["population"]), result["steps_run"] + 1)
            self.assertIn("classification", result)

    def test_compare_does_not_disturb_running_simulation_state(self) -> None:
        before = self.get_state()["generation"]
        self.client.post("/api/compare", json={"seed": "111", "geometries": ["square"], "steps": 5})
        self.assertEqual(self.get_state()["generation"], before)

    def test_compare_rejects_empty_seed(self) -> None:
        response = self.client.post("/api/compare", json={"seed": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_compare_rejects_unknown_geometry(self) -> None:
        response = self.client.post(
            "/api/compare",
            json={"seed": "111", "geometries": ["not-a-real-tiling"]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_compare_include_states_returns_board_payloads(self) -> None:
        response = self.client.post(
            "/api/compare",
            json={
                "seed": "0111110",
                "geometries": ["square"],
                "steps": 8,
                "include_states": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        result = response.get_json()["comparison"]["results"][0]
        self.assertIn("topology_spec", result)
        self.assertIn("initial_cells_by_id", result)
        self.assertIn("final_cells_by_id", result)
        self.assertEqual(result["topology_spec"]["tiling_family"], "square")
        self.assertGreater(result["topology_spec"]["width"], 0)

    def test_compare_omits_states_by_default(self) -> None:
        response = self.client.post(
            "/api/compare",
            json={"seed": "111", "geometries": ["square"], "steps": 3},
        )
        result = response.get_json()["comparison"]["results"][0]
        self.assertNotIn("topology_spec", result)

    def test_compare_pattern_mode_seeds_a_shape_without_a_seed(self) -> None:
        response = self.client.post(
            "/api/compare",
            json={"pattern": "glider", "geometries": ["square", "hex"], "steps": 8},
        )
        self.assertEqual(response.status_code, 200)
        results = response.get_json()["comparison"]["results"]
        self.assertEqual([result["seed_cells"] for result in results], [5, 5])

    def test_compare_rejects_unknown_pattern(self) -> None:
        response = self.client.post(
            "/api/compare",
            json={"pattern": "spaceship", "geometries": ["square"]},
        )
        self.assertEqual(response.status_code, 400)

    def test_compare_rejects_out_of_range_steps(self) -> None:
        response = self.client.post(
            "/api/compare",
            json={"seed": "111", "geometries": ["square"], "steps": 100000},
        )
        self.assertEqual(response.status_code, 400)

    def test_filmstrip_returns_synchronized_frames_per_tiling(self) -> None:
        response = self.client.post(
            "/api/compare/filmstrip",
            json={
                "seed": "0110 1100 0100",
                "rule": "conway",
                "geometries": ["square", "hex", "triangle"],
                "frames": 10,
                "grid_size": 8,
            },
        )
        self.assertEqual(response.status_code, 200)
        filmstrip = response.get_json()["filmstrip"]
        self.assertEqual(filmstrip["frame_count"], 10)
        tilings = filmstrip["tilings"]
        self.assertEqual(
            [tiling["tiling_family"] for tiling in tilings], ["square", "hex", "triangle"]
        )
        for tiling in tilings:
            self.assertEqual(len(tiling["frames"]), 10)  # synchronized frame counts
            self.assertTrue(tiling["topology"]["cells"])  # renderable geometry
            self.assertEqual(tiling["topology_spec"]["tiling_family"], tiling["tiling_family"])

    def test_filmstrip_does_not_disturb_running_simulation_state(self) -> None:
        before = self.get_state()["generation"]
        self.client.post(
            "/api/compare/filmstrip",
            json={"seed": "111", "geometries": ["square"], "frames": 5},
        )
        self.assertEqual(self.get_state()["generation"], before)

    def test_filmstrip_requires_geometries(self) -> None:
        response = self.client.post("/api/compare/filmstrip", json={"seed": "111"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("geometries", response.get_json()["error"])

    def test_filmstrip_rejects_too_many_tilings(self) -> None:
        response = self.client.post(
            "/api/compare/filmstrip",
            json={"seed": "1", "geometries": ["square"] * 7},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
