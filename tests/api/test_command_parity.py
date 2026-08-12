from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass
from itertools import count
from typing import Any

from flask import Flask
from flask.testing import FlaskClient

from backend.api import create_app
from backend.application_commands import (
    COMMAND_SPECS,
    ApplicationCommand,
    CommandResultKind,
    CommandSpec,
)
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


@dataclass(frozen=True)
class CommandParityScenario:
    valid_payload: dict[str, object] | None
    invalid_payloads: tuple[dict[str, object], ...] = ()


PARITY_SCENARIOS: dict[ApplicationCommand, CommandParityScenario] = {
    ApplicationCommand.STATE_GET: CommandParityScenario(None),
    ApplicationCommand.RULES_LIST: CommandParityScenario(None),
    ApplicationCommand.COMPARE_RUN: CommandParityScenario(
        {"seed": "11", "rule": "conway", "geometries": ["square"], "steps": 3},
        ({},),
    ),
    ApplicationCommand.FILMSTRIP_RUN: CommandParityScenario(
        {"seed": "11", "rule": "conway", "geometries": ["square"], "frames": 3},
        ({"seed": "11"},),
    ),
    ApplicationCommand.TOPOLOGY_PREVIEW: CommandParityScenario(
        {"geometry": "square", "width": 4, "height": 4},
        ({},),
    ),
    ApplicationCommand.SIMULATION_START: CommandParityScenario(None),
    ApplicationCommand.SIMULATION_PAUSE: CommandParityScenario(None),
    ApplicationCommand.SIMULATION_RESUME: CommandParityScenario(None),
    ApplicationCommand.SIMULATION_STEP: CommandParityScenario(None),
    ApplicationCommand.SIMULATION_RESET: CommandParityScenario(
        BASELINE_RESET,
        ({"geometry": "square"},),
    ),
    ApplicationCommand.SIMULATION_CONFIGURE: CommandParityScenario(
        {"speed": 9},
        (
            {"rule": "missing"},
            {"topology_spec": {"patch_depth": 4}},
        ),
    ),
    ApplicationCommand.CELL_TOGGLE: CommandParityScenario(
        {"id": "c:0:0"},
        ({},),
    ),
    ApplicationCommand.CELL_SET: CommandParityScenario(
        {"id": "c:0:0", "state": 1},
        ({"id": "c:0:0", "state": 999},),
    ),
    ApplicationCommand.CELLS_SET_MANY: CommandParityScenario(
        {"cells": [{"id": "c:0:0", "state": 1}, {"id": "c:1:0", "state": 1}]},
        ({"cells": []},),
    ),
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
        spec: CommandSpec,
        payload: dict[str, object] | None,
        session_id: str,
    ) -> tuple[int, Any]:
        routed_path = self.session_path(spec.transport_path, session_id)
        response = (
            self.client.get(routed_path)
            if spec.http_method == "GET"
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

    def assert_parity(
        self,
        spec: CommandSpec,
        payload: dict[str, object] | None,
        *,
        expected_status: int,
    ) -> None:
        session_id = f"parity-{next(self.session_counter)}"
        self.reset_hosts(session_id)
        browser = self.request_browser(spec.transport_path, payload)
        server = self.request_server(spec, payload, session_id)
        self.assertEqual(browser[0], expected_status, spec.command)
        self.assertEqual(server[0], expected_status, spec.command)
        self.assertEqual(
            browser,
            server,
            spec.command,
        )

    def test_inventory_is_complete_and_has_unique_transport_paths(self) -> None:
        self.assertEqual(len({spec.command for spec in COMMAND_SPECS}), len(COMMAND_SPECS))
        self.assertEqual(len({spec.transport_path for spec in COMMAND_SPECS}), len(COMMAND_SPECS))
        self.assertEqual({spec.command for spec in COMMAND_SPECS}, set(ApplicationCommand))
        self.assertEqual(
            {spec.result for spec in COMMAND_SPECS},
            set(CommandResultKind),
        )

    def test_scenario_inventory_covers_every_command_and_required_error_path(self) -> None:
        self.assertEqual(set(PARITY_SCENARIOS), {spec.command for spec in COMMAND_SPECS})
        for spec in COMMAND_SPECS:
            with self.subTest(command=spec.command.value):
                scenario = PARITY_SCENARIOS[spec.command]
                if spec.payload_requirement == "none":
                    self.assertEqual(scenario.invalid_payloads, ())
                else:
                    self.assertTrue(
                        scenario.invalid_payloads,
                        f"{spec.command.value} requires an invalid parity scenario",
                    )

    def test_flask_hosts_every_registered_transport(self) -> None:
        rules = tuple(self.app.url_map.iter_rules())
        for spec in COMMAND_SPECS:
            session_path = self.session_path(spec.transport_path, "<session_id>")
            with self.subTest(command=spec.command.value, host="default"):
                self.assertTrue(
                    any(
                        rule.rule == spec.transport_path
                        and spec.http_method in (rule.methods or set())
                        for rule in rules
                    ),
                    f"Flask is missing {spec.http_method} {spec.transport_path}",
                )
            with self.subTest(command=spec.command.value, host="session"):
                self.assertTrue(
                    any(
                        rule.rule == session_path and spec.http_method in (rule.methods or set())
                        for rule in rules
                    ),
                    f"Flask is missing {spec.http_method} {session_path}",
                )

    def test_every_registered_command_has_valid_transport_parity(self) -> None:
        for spec in COMMAND_SPECS:
            with self.subTest(command=spec.command.value):
                self.assert_parity(
                    spec,
                    PARITY_SCENARIOS[spec.command].valid_payload,
                    expected_status=200,
                )

    def test_every_relevant_command_has_invalid_transport_parity(self) -> None:
        for spec in COMMAND_SPECS:
            for payload in PARITY_SCENARIOS[spec.command].invalid_payloads:
                with self.subTest(command=spec.command.value, payload=payload):
                    self.assert_parity(spec, payload, expected_status=400)

    def test_hosts_reject_non_object_json_payloads(self) -> None:
        session_id = f"parity-{next(self.session_counter)}"
        self.reset_hosts(session_id)

        server = self.client.post(
            self.session_path("/api/control/reset", session_id),
            json=[1, 2, 3],
        )
        browser = json.loads(handle_request("/api/control/reset", "[1, 2, 3]"))

        self.assertEqual(server.status_code, 400)
        self.assertFalse(browser["ok"])
        self.assertEqual(server.get_json(), {"error": browser["error"]})


if __name__ == "__main__":
    unittest.main()
