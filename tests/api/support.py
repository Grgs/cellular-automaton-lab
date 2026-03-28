import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Callable, ClassVar

from flask import Flask
from flask.testing import FlaskClient

try:
    from backend.api import create_app
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.api import create_app


class ApiTestCase(unittest.TestCase):
    instance_dir: ClassVar[tempfile.TemporaryDirectory[str]]
    app: ClassVar[Flask]
    client: ClassVar[FlaskClient]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.instance_dir = tempfile.TemporaryDirectory(prefix="cellular-automaton-api-instance-")
        cls.app = create_app(instance_path=cls.instance_dir.name)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.app.extensions["simulation_coordinator"].shutdown()
        cls.instance_dir.cleanup()
        super().tearDownClass()

    @classmethod
    def recreate_app(cls, *, persist_current: bool = True) -> None:
        if persist_current:
            cls.app.extensions["simulation_coordinator"].shutdown()
        else:
            cls.app.extensions["simulation_coordinator"].stop_background_loop()
        cls.app = create_app(instance_path=cls.instance_dir.name)
        cls.client = cls.app.test_client()

    def setUp(self) -> None:
        self.reset_simulation()

    def reset_simulation(self, **overrides: Any) -> dict[str, Any]:
        topology_spec = {
            'tiling_family': 'square',
            'adjacency_mode': 'edge',
            'width': 10,
            'height': 6,
            'patch_depth': 0,
        }
        if "width" in overrides:
            topology_spec["width"] = overrides.pop("width")
        if "height" in overrides:
            topology_spec["height"] = overrides.pop("height")
        if "patch_depth" in overrides:
            topology_spec["patch_depth"] = overrides.pop("patch_depth")
        payload: dict[str, Any] = {
            'topology_spec': topology_spec,
            'speed': 5,
            'rule': 'conway',
            'randomize': False,
        }
        payload.update(overrides)
        response = self.client.post('/api/control/reset', json=payload)
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        assert isinstance(payload, dict)
        return payload

    def get_state(self) -> dict[str, Any]:
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        assert isinstance(payload, dict)
        return payload

    def get_topology(self) -> dict[str, Any]:
        response = self.client.get('/api/topology')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        assert isinstance(payload, dict)
        return payload

    def wait_for_state(
        self,
        predicate: Callable[[dict[str, Any]], bool],
        timeout: float = 2.0,
        interval: float = 0.05,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        last_state: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            last_state = self.get_state()
            if predicate(last_state):
                return last_state
            time.sleep(interval)
        raise AssertionError(f'backend state did not satisfy predicate in time: {last_state}')

    def assert_generation_stable(self, duration: float = 0.25, interval: float = 0.05) -> int:
        generation = self.get_state()['generation']
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            time.sleep(interval)
            self.assertEqual(self.get_state()['generation'], generation)
        return generation

    def get_rules(self) -> list[dict[str, Any]]:
        response = self.client.get('/api/rules')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        assert isinstance(payload, dict)
        rules = payload['rules']
        assert isinstance(rules, list)
        return rules

    def get_rule_definition(self, rule_name: str) -> dict[str, Any]:
        return next(rule for rule in self.get_rules() if rule['name'] == rule_name)

    def assert_grid_uses_rule_states(self, payload: dict[str, Any]) -> None:
        allowed_states = {cell_state['value'] for cell_state in payload['rule']['states']}
        for state in self.cells_by_id(payload).values():
            self.assertIn(state, allowed_states)

    @staticmethod
    def regular_cell_id(x: int, y: int) -> str:
        return f"c:{x}:{y}"

    def cells_by_id(self, payload: dict[str, Any]) -> dict[str, int]:
        topology = payload.get('topology')
        if not isinstance(topology, dict):
            topology = self.get_topology()
            payload_revision = payload.get('topology_revision')
            topology_revision = topology.get('topology_revision')
            if payload_revision is not None and topology_revision != payload_revision:
                raise AssertionError('payload topology revision did not match the current topology endpoint')
        cells = topology.get('cells') if isinstance(topology, dict) else None
        cell_states = payload.get('cell_states')

        if not isinstance(cells, list) or not isinstance(cell_states, list):
            raise AssertionError('payload did not contain topology cells and cell_states needed to derive cell states')
        if len(cells) != len(cell_states):
            raise AssertionError('payload topology cells and cell_states had different lengths')

        cells_by_id: dict[str, int] = {}
        for index, cell in enumerate(cells):
            if not isinstance(cell, dict):
                raise AssertionError('payload topology contained a non-object cell entry')
            cell_id = cell.get('id')
            if not isinstance(cell_id, str) or not cell_id:
                raise AssertionError('payload topology cell did not contain a valid id')
            cells_by_id[cell_id] = int(cell_states[index])

        return cells_by_id

    def regular_cell_state(self, payload: dict[str, Any], x: int, y: int) -> int:
        return self.cells_by_id(payload).get(self.regular_cell_id(x, y), 0)

    def assert_regular_rows(self, payload: dict[str, Any], rows: list[list[int]]) -> None:
        expected: dict[str, int] = {}
        for y, row in enumerate(rows):
            for x, value in enumerate(row):
                expected[self.regular_cell_id(x, y)] = int(value)
        self.assertEqual(self.cells_by_id(payload), expected)

    def assert_wireworld_rule(self, payload: dict[str, Any]) -> None:
        self.assertEqual(payload['rule']['name'], 'wireworld')
        self.assertEqual(payload['rule']['default_paint_state'], 3)
        self.assertFalse(payload['rule']['supports_randomize'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1, 2, 3])

    def assert_whirlpool_rule(self, payload: dict[str, Any]) -> None:
        self.assertEqual(payload['rule']['name'], 'whirlpool')
        self.assertEqual(payload['rule']['display_name'], 'Excitable: Outward Whirlpool')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertFalse(payload['rule']['supports_randomize'])
        self.assertEqual([cell_state['label'] for cell_state in payload['rule']['states']], [
            'Resting',
            'Excited',
            'Trailing',
            'Refractory',
            'Source',
        ])

    def assert_hexlife_rule(self, payload: dict[str, Any]) -> None:
        self.assertEqual(payload['rule']['name'], 'hexlife')
        self.assertEqual(payload['rule']['display_name'], 'Life: Hex (B2/S34)')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertTrue(payload['rule']['supports_randomize'])
        self.assertEqual(payload['rule']['rule_protocol'], 'universal-v1')
        self.assertTrue(payload['rule']['supports_all_topologies'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1])

    def assert_hexwhirlpool_rule(self, payload: dict[str, Any]) -> None:
        self.assert_whirlpool_rule(payload)

    def assert_trilife_rule(self, payload: dict[str, Any]) -> None:
        self.assertEqual(payload['rule']['name'], 'trilife')
        self.assertEqual(payload['rule']['display_name'], 'Life: Triangle (B4/S345)')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertTrue(payload['rule']['supports_randomize'])
        self.assertEqual(payload['rule']['rule_protocol'], 'universal-v1')
        self.assertTrue(payload['rule']['supports_all_topologies'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1])

    def assert_archlife_rule(self, payload: dict[str, Any]) -> None:
        self.assertEqual(payload['rule']['name'], 'archlife488')
        self.assertEqual(payload['rule']['display_name'], 'Mixed Life: Square-Octagon (4.8.8)')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertTrue(payload['rule']['supports_randomize'])
        self.assertEqual(payload['rule']['rule_protocol'], 'universal-v1')
        self.assertTrue(payload['rule']['supports_all_topologies'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1])

    def assert_kagome_rule(self, payload: dict[str, Any]) -> None:
        self.assertEqual(payload['rule']['name'], 'kagome-life')
        self.assertEqual(payload['rule']['display_name'], 'Mixed Life: Kagome (3.6.3.6)')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertTrue(payload['rule']['supports_randomize'])
        self.assertEqual(payload['rule']['rule_protocol'], 'universal-v1')
        self.assertTrue(payload['rule']['supports_all_topologies'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1])
