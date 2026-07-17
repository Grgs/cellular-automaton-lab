from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

try:
    from backend.browser_runtime import handle_request, initialize_runtime, tick_running
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.browser_runtime import handle_request, initialize_runtime, tick_running


class BrowserRuntimeTests(unittest.TestCase):
    def test_oversized_topology_error_is_structured(self) -> None:
        initialize_runtime()

        response = json.loads(
            handle_request(
                "/api/control/reset",
                json.dumps(
                    {
                        "topology_spec": {
                            "tiling_family": "square",
                            "adjacency_mode": "edge",
                            "sizing_mode": "grid",
                            "width": 201,
                            "height": 100,
                            "patch_depth": 0,
                            "unsafe_size_override": True,
                        },
                        "rule": "conway",
                    }
                ),
            )
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["code"], "topology_cell_budget_exceeded")
        self.assertEqual(response["limit"], 20_000)
        self.assertEqual(response["estimated_cells"], 20_100)

    def test_initialize_runtime_returns_default_snapshot(self) -> None:
        payload = json.loads(initialize_runtime())

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["snapshot"]["rule"]["name"], "conway")
        self.assertFalse(payload["snapshot"]["running"])
        self.assertEqual(payload["snapshot"]["state_revision"], 0)
        self.assertEqual(payload["persisted_snapshot"]["version"], 5)
        self.assertNotIn("state_revision", payload["persisted_snapshot"])

    def test_handle_request_supports_cell_mutations_and_runtime_ticks(self) -> None:
        initialize_runtime()

        set_response = json.loads(
            handle_request("/api/cells/set", json.dumps({"id": "c:0:0", "state": 1}))
        )
        self.assertTrue(set_response["ok"])
        self.assertEqual(set_response["base_state_revision"], 0)
        self.assertEqual(set_response["state_revision"], 1)
        self.assertEqual(set_response["cell_updates"], [{"id": "c:0:0", "state": 1}])
        self.assertNotIn("snapshot", set_response)

        no_op_response = json.loads(
            handle_request("/api/cells/set", json.dumps({"id": "c:0:0", "state": 1}))
        )
        self.assertEqual(no_op_response["state_revision"], 1)
        self.assertEqual(no_op_response["cell_updates"], [])

        start_response = json.loads(handle_request("/api/control/start"))
        self.assertTrue(start_response["ok"])
        self.assertTrue(start_response["snapshot"]["running"])
        self.assertEqual(start_response["snapshot"]["state_revision"], 2)

        repeated_start = json.loads(handle_request("/api/control/start"))
        self.assertEqual(repeated_start["snapshot"]["state_revision"], 2)

        tick_response = json.loads(tick_running())
        self.assertTrue(tick_response["ok"])
        self.assertTrue(tick_response["stepped"])
        self.assertGreaterEqual(tick_response["snapshot"]["generation"], 1)
        self.assertEqual(tick_response["snapshot"]["state_revision"], 3)

    def test_handle_request_runs_compare_filmstrip(self) -> None:
        initialize_runtime()

        response = json.loads(
            handle_request(
                "/api/compare/filmstrip",
                json.dumps(
                    {
                        "seed": "11",
                        "rule": "conway",
                        "geometries": ["square", "hex"],
                        "frames": 5,
                    }
                ),
            )
        )
        self.assertTrue(response["ok"])
        filmstrip = response["filmstrip"]
        self.assertEqual(filmstrip["frame_count"], 5)
        self.assertEqual(
            {tiling["tiling_family"] for tiling in filmstrip["tilings"]}, {"square", "hex"}
        )
        self.assertEqual(len(filmstrip["tilings"][0]["frames"]), 5)

    def test_handle_request_rejects_filmstrip_without_geometries(self) -> None:
        initialize_runtime()

        response = json.loads(handle_request("/api/compare/filmstrip", json.dumps({"seed": "11"})))
        self.assertFalse(response["ok"])
        self.assertIn("geometries", response["error"])

    def test_initialize_runtime_restores_serialized_snapshot(self) -> None:
        initialize_runtime()
        response = json.loads(
            handle_request("/api/cells/set", json.dumps({"id": "c:0:0", "state": 1}))
        )
        self.assertTrue(response["ok"])
        state_response = json.loads(handle_request("/api/state"))

        restored = json.loads(initialize_runtime(json.dumps(state_response["persisted_snapshot"])))

        self.assertTrue(restored["ok"])
        self.assertEqual(restored["snapshot"]["cell_states"][0], 1)
        self.assertEqual(restored["snapshot"]["state_revision"], 0)

    def test_handle_request_reports_validation_errors(self) -> None:
        initialize_runtime()

        response = json.loads(
            handle_request("/api/cells/set", json.dumps({"id": "c:0:0", "state": 999}))
        )

        self.assertFalse(response["ok"])
        self.assertIn("supported by rule", response["error"])

    def test_handle_request_matches_config_validation_contract(self) -> None:
        initialize_runtime()

        response = json.loads(
            handle_request(
                "/api/config",
                json.dumps(
                    {
                        "topology_spec": {"patch_depth": 4},
                    }
                ),
            )
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "'patch_depth' can only be changed through reset.")


if __name__ == "__main__":
    unittest.main()
