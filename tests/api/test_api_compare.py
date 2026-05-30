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

    def test_compare_rejects_out_of_range_steps(self) -> None:
        response = self.client.post(
            "/api/compare",
            json={"seed": "111", "geometries": ["square"], "steps": 100000},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
