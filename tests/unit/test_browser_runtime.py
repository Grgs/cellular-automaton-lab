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
    def test_initialize_runtime_returns_default_snapshot(self) -> None:
        payload = json.loads(initialize_runtime())

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["snapshot"]["rule"]["name"], "conway")
        self.assertFalse(payload["snapshot"]["running"])
        self.assertEqual(payload["persisted_snapshot"]["version"], 5)

    def test_handle_request_supports_cell_mutations_and_runtime_ticks(self) -> None:
        initialize_runtime()

        set_response = json.loads(
            handle_request("/api/cells/set", json.dumps({"id": "c:0:0", "state": 1}))
        )
        self.assertTrue(set_response["ok"])
        self.assertEqual(set_response["snapshot"]["cell_states"][0], 1)

        start_response = json.loads(handle_request("/api/control/start"))
        self.assertTrue(start_response["ok"])
        self.assertTrue(start_response["snapshot"]["running"])

        tick_response = json.loads(tick_running())
        self.assertTrue(tick_response["ok"])
        self.assertTrue(tick_response["stepped"])
        self.assertGreaterEqual(tick_response["snapshot"]["generation"], 1)

    def test_initialize_runtime_restores_serialized_snapshot(self) -> None:
        initialize_runtime()
        response = json.loads(
            handle_request("/api/cells/set", json.dumps({"id": "c:0:0", "state": 1}))
        )

        restored = json.loads(initialize_runtime(json.dumps(response["persisted_snapshot"])))

        self.assertTrue(restored["ok"])
        self.assertEqual(restored["snapshot"]["cell_states"][0], 1)

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
