import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Callable, ClassVar, NotRequired, TypedDict, Unpack

from flask import Flask
from flask.testing import FlaskClient

from backend.payload_types import (
    ResetControlRequestPayload,
    RuleDefinitionPayload,
    SimulationStatePayload,
    TopologyPayload,
    TopologySpecPayload,
)

try:
    from backend.api import create_app
    from tests.typed_payloads import (
        require_rules_response_payload,
        require_simulation_state_payload,
        require_topology_payload,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.api import create_app
    from tests.typed_payloads import (
        require_rules_response_payload,
        require_simulation_state_payload,
        require_topology_payload,
    )


class ResetSimulationOverrides(TypedDict, total=False):
    width: NotRequired[object]
    height: NotRequired[object]
    patch_depth: NotRequired[object]
    speed: NotRequired[object]
    rule: NotRequired[object]
    randomize: NotRequired[object]


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

    @staticmethod
    def _coerce_override_int(value: object, *, key: str) -> int:
        if isinstance(value, (str, bytes, bytearray, int, float)) and not isinstance(value, bool):
            return int(value)
        raise AssertionError(f"reset override '{key}' must be int-compatible.")

    def build_reset_payload(self, **overrides: Unpack[ResetSimulationOverrides]) -> ResetControlRequestPayload:
        topology_spec: TopologySpecPayload = {
            'tiling_family': 'square',
            'adjacency_mode': 'edge',
            'sizing_mode': 'grid',
            'width': 10,
            'height': 6,
            'patch_depth': 0,
        }
        if "width" in overrides:
            topology_spec["width"] = self._coerce_override_int(overrides.pop("width"), key="width")
        if "height" in overrides:
            topology_spec["height"] = self._coerce_override_int(overrides.pop("height"), key="height")
        if "patch_depth" in overrides:
            topology_spec["patch_depth"] = self._coerce_override_int(
                overrides.pop("patch_depth"),
                key="patch_depth",
            )
        payload: ResetControlRequestPayload = {
            'topology_spec': topology_spec,
            'speed': 5,
            'rule': 'conway',
            'randomize': False,
        }
        if "speed" in overrides:
            speed = overrides.pop("speed")
            if isinstance(speed, (str, bytes, bytearray, int, float)) and not isinstance(speed, bool):
                payload["speed"] = float(speed)
            else:
                raise AssertionError("reset override 'speed' must be numeric.")
        if "rule" in overrides:
            rule = overrides.pop("rule")
            if not isinstance(rule, str) or not rule:
                raise AssertionError("reset override 'rule' must be a non-empty string.")
            payload["rule"] = rule
        if "randomize" in overrides:
            randomize = overrides.pop("randomize")
            if not isinstance(randomize, bool):
                raise AssertionError("reset override 'randomize' must be a boolean.")
            payload["randomize"] = randomize
        if overrides:
            raise AssertionError(f"unsupported reset overrides: {sorted(overrides)}")
        return payload

    def reset_simulation(self, **overrides: Unpack[ResetSimulationOverrides]) -> SimulationStatePayload:
        payload = self.build_reset_payload(**overrides)
        response = self.client.post('/api/control/reset', json=payload)
        self.assertEqual(response.status_code, 200)
        return require_simulation_state_payload(
            response.get_json(),
            context="reset response",
        )

    def get_state(self) -> SimulationStatePayload:
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 200)
        return require_simulation_state_payload(
            response.get_json(),
            context="state response",
        )

    def get_topology(self) -> TopologyPayload:
        response = self.client.get('/api/topology')
        self.assertEqual(response.status_code, 200)
        return require_topology_payload(
            response.get_json(),
            context="topology response",
        )

    def wait_for_state(
        self,
        predicate: Callable[[SimulationStatePayload], bool],
        timeout: float = 2.0,
        interval: float = 0.05,
    ) -> SimulationStatePayload:
        deadline = time.monotonic() + timeout
        last_state: SimulationStatePayload | None = None
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

    def get_rules(self) -> list[RuleDefinitionPayload]:
        response = self.client.get('/api/rules')
        self.assertEqual(response.status_code, 200)
        return require_rules_response_payload(
            response.get_json(),
            context="rules response",
        )["rules"]

    def get_rule_definition(self, rule_name: str) -> RuleDefinitionPayload:
        return next(rule for rule in self.get_rules() if rule['name'] == rule_name)

    def assert_grid_uses_rule_states(self, payload: SimulationStatePayload) -> None:
        allowed_states = {cell_state['value'] for cell_state in payload['rule']['states']}
        for state in self.cells_by_id(payload).values():
            self.assertIn(state, allowed_states)

    @staticmethod
    def regular_cell_id(x: int, y: int) -> str:
        return f"c:{x}:{y}"

    def cells_by_id(self, payload: SimulationStatePayload) -> dict[str, int]:
        topology = payload['topology']
        cells = topology['cells']
        cell_states = payload['cell_states']

        if len(cells) != len(cell_states):
            raise AssertionError('payload topology cells and cell_states had different lengths')

        cells_by_id: dict[str, int] = {}
        for index, cell in enumerate(cells):
            cell_id = cell['id']
            if not cell_id:
                raise AssertionError('payload topology cell did not contain a valid id')
            cells_by_id[cell_id] = int(cell_states[index])

        return cells_by_id

    def regular_cell_state(self, payload: SimulationStatePayload, x: int, y: int) -> int:
        return self.cells_by_id(payload).get(self.regular_cell_id(x, y), 0)

    def assert_regular_rows(self, payload: SimulationStatePayload, rows: list[list[int]]) -> None:
        expected: dict[str, int] = {}
        for y, row in enumerate(rows):
            for x, value in enumerate(row):
                expected[self.regular_cell_id(x, y)] = int(value)
        self.assertEqual(self.cells_by_id(payload), expected)

    def assert_wireworld_rule(self, payload: SimulationStatePayload) -> None:
        self.assertEqual(payload['rule']['name'], 'wireworld')
        self.assertEqual(payload['rule']['default_paint_state'], 3)
        self.assertFalse(payload['rule']['supports_randomize'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1, 2, 3])

    def assert_whirlpool_rule(self, payload: SimulationStatePayload) -> None:
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

    def assert_hexlife_rule(self, payload: SimulationStatePayload) -> None:
        self.assertEqual(payload['rule']['name'], 'hexlife')
        self.assertEqual(payload['rule']['display_name'], 'Life: Hex (B2/S34)')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertTrue(payload['rule']['supports_randomize'])
        self.assertEqual(payload['rule']['rule_protocol'], 'universal-v1')
        self.assertTrue(payload['rule']['supports_all_topologies'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1])

    def assert_hexwhirlpool_rule(self, payload: SimulationStatePayload) -> None:
        self.assert_whirlpool_rule(payload)

    def assert_trilife_rule(self, payload: SimulationStatePayload) -> None:
        self.assertEqual(payload['rule']['name'], 'trilife')
        self.assertEqual(payload['rule']['display_name'], 'Life: Triangle (B4/S345)')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertTrue(payload['rule']['supports_randomize'])
        self.assertEqual(payload['rule']['rule_protocol'], 'universal-v1')
        self.assertTrue(payload['rule']['supports_all_topologies'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1])

    def assert_archlife_rule(self, payload: SimulationStatePayload) -> None:
        self.assertEqual(payload['rule']['name'], 'archlife488')
        self.assertEqual(payload['rule']['display_name'], 'Mixed Life: Square-Octagon (4.8.8)')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertTrue(payload['rule']['supports_randomize'])
        self.assertEqual(payload['rule']['rule_protocol'], 'universal-v1')
        self.assertTrue(payload['rule']['supports_all_topologies'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1])

    def assert_kagome_rule(self, payload: SimulationStatePayload) -> None:
        self.assertEqual(payload['rule']['name'], 'kagome-life')
        self.assertEqual(payload['rule']['display_name'], 'Mixed Life: Kagome (3.6.3.6)')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertTrue(payload['rule']['supports_randomize'])
        self.assertEqual(payload['rule']['rule_protocol'], 'universal-v1')
        self.assertTrue(payload['rule']['supports_all_topologies'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1])
