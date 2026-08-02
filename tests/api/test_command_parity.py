from __future__ import annotations

import json
import tempfile
import unittest
from itertools import count
from typing import Any

from flask import Flask
from flask.testing import FlaskClient

from backend.api import create_app
from backend.application_commands import COMMAND_SPECS, CommandResultKind
from backend.browser_runtime import handle_request, initialize_runtime

BASELINE_RESET = {
    "topology_spec": {
        "tiling_family": "square",
        "adjacency_mode": "edge",
        "sizing_mode": "grid",
        "width": 10,
        "height": 6,
        "patch_depth": 0,
    },
    "speed": 5,
    "rule": "conway",
    "randomize": False,
}


class SharedCommandParityTests(unittest.TestCase):
    instance_dir: tempfile.TemporaryDirectory[str]
    app: Flask
    client: FlaskClient
    session_counter = count()

    @classmethod
    def setUpClass(cls) -> None:
        cls.instance_dir = tempfile.TemporaryDirectory(prefix="command-parity-")
        cls.app = create_app(instance_path=cls.instance_dir.name)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.app.extensions["simulation_sessions"].shutdown()
        cls.instance_dir.cleanup()

    @staticmethod
    def session_path(path: str, session_id: str) -> str:
        return f"/api/sessions/{session_id}{path.removeprefix('/api')}"

    def reset_hosts(self, session_id: str) -> None:
        initialize_runtime()
        server = self.client.post(
            self.session_path("/api/control/reset", session_id),
            json=BASELINE_RESET,
        )
        self.assertEqual(server.status_code, 200)
        browser = json.loads(handle_request("/api/control/reset", json.dumps(BASELINE_RESET)))
        self.assertTrue(browser["ok"])

    def request_server(
        self,
        path: str,
        payload: dict[str, object] | None,
        session_id: str,
    ) -> tuple[int, Any]:
        routed_path = self.session_path(path, session_id)
        response = (
            self.client.get(routed_path)
            if payload is None and path in {"/api/state", "/api/rules"}
            else self.client.post(routed_path, json=payload)
        )
        return response.status_code, self.normalize(response.get_json())

    @staticmethod
    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: SharedCommandParityTests.normalize(entry)
                for key, entry in value.items()
                if key != "state_epoch"
            }
        if isinstance(value, list):
            return [SharedCommandParityTests.normalize(entry) for entry in value]
        return value

    @staticmethod
    def request_browser(path: str, payload: dict[str, object] | None) -> tuple[int, Any]:
        raw = handle_request(path, None if payload is None else json.dumps(payload))
        response = json.loads(raw)
        ok = bool(response.pop("ok"))
        response.pop("persisted_snapshot", None)
        if "snapshot" in response:
            response = response["snapshot"]
        elif "rules" in response:
            response = {"rules": response["rules"]}
        return (200 if ok else 400), SharedCommandParityTests.normalize(response)

    def assert_parity(self, path: str, payload: dict[str, object] | None = None) -> None:
        session_id = f"parity-{next(self.session_counter)}"
        self.reset_hosts(session_id)
        self.assertEqual(
            self.request_browser(path, payload),
            self.request_server(path, payload, session_id),
            path,
        )

    def test_inventory_has_unique_transport_paths_and_expected_result_shapes(self) -> None:
        self.assertEqual(len({spec.command for spec in COMMAND_SPECS}), len(COMMAND_SPECS))
        self.assertEqual(len({spec.transport_path for spec in COMMAND_SPECS}), len(COMMAND_SPECS))
        self.assertEqual(
            {spec.result for spec in COMMAND_SPECS},
            set(CommandResultKind),
        )

    def test_shared_read_and_analysis_commands_have_transport_parity(self) -> None:
        cases: tuple[tuple[str, dict[str, object] | None], ...] = (
            ("/api/state", None),
            ("/api/rules", None),
            (
                "/api/compare",
                {"seed": "11", "rule": "conway", "geometries": ["square"], "steps": 3},
            ),
            (
                "/api/compare/filmstrip",
                {"seed": "11", "rule": "conway", "geometries": ["square"], "frames": 3},
            ),
            (
                "/api/topology/preview",
                {"geometry": "square", "width": 4, "height": 4},
            ),
        )
        for path, payload in cases:
            with self.subTest(path=path):
                self.assert_parity(path, payload)

    def test_shared_mutation_commands_have_transport_parity(self) -> None:
        cases: tuple[tuple[str, dict[str, object] | None], ...] = (
            ("/api/control/start", None),
            ("/api/control/pause", None),
            ("/api/control/resume", None),
            ("/api/control/step", None),
            ("/api/control/reset", BASELINE_RESET),
            ("/api/config", {"speed": 9}),
            ("/api/cells/toggle", {"id": "c:0:0"}),
            ("/api/cells/set", {"id": "c:0:0", "state": 1}),
            (
                "/api/cells/set-many",
                {"cells": [{"id": "c:0:0", "state": 1}, {"id": "c:1:0", "state": 1}]},
            ),
        )
        for path, payload in cases:
            with self.subTest(path=path):
                self.assert_parity(path, payload)

    def test_public_validation_errors_have_transport_parity(self) -> None:
        cases: tuple[tuple[str, dict[str, object]], ...] = (
            ("/api/config", {"rule": "missing"}),
            ("/api/config", {"topology_spec": {"patch_depth": 4}}),
            ("/api/cells/toggle", {}),
            ("/api/cells/set", {"id": "c:0:0", "state": 999}),
            ("/api/cells/set-many", {"cells": []}),
            ("/api/compare/filmstrip", {"seed": "11"}),
        )
        for path, payload in cases:
            with self.subTest(path=path):
                self.assert_parity(path, payload)


if __name__ == "__main__":
    unittest.main()
