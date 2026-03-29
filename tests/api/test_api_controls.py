import sys
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from tests.api.support import ApiTestCase
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.api.support import ApiTestCase


class ApiControlTests(ApiTestCase):
    def test_reset_rejects_legacy_geometry_style_payloads(self) -> None:
        cases = [
            (
                {'geometry': 'hex', 'width': 9, 'height': 7},
                "'geometry' must be provided through 'topology_spec'.",
            ),
            (
                {'width': 9, 'height': 7},
                "'width' and 'height' must be provided through 'topology_spec'.",
            ),
            (
                {'patch_depth': 4},
                "'patch_depth' must be provided through 'topology_spec'.",
            ),
        ]

        for payload, expected_error in cases:
            with self.subTest(payload=payload):
                response = self.client.post('/api/control/reset', json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.get_json(), {'error': expected_error})

    def test_config_rejects_patch_depth_changes(self) -> None:
        response = self.client.post('/api/config', json={
            'topology_spec': {'patch_depth': 4},
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {
            'error': "'patch_depth' can only be changed through reset.",
        })

    def test_pause_resume_and_reset(self) -> None:
        self.reset_simulation(width=8, height=8, speed=10, rule='highlife', randomize=True)
        self.client.post('/api/control/start')
        running = self.wait_for_state(lambda state: state['running'] and state['generation'] >= 1)

        pause_response = self.client.post('/api/control/pause')
        self.assertEqual(pause_response.status_code, 200)
        paused = self.wait_for_state(lambda state: not state['running'])
        paused_generation = self.assert_generation_stable()

        self.client.post('/api/control/resume')
        resumed = self.wait_for_state(
            lambda state: state['running'] and state['generation'] > paused_generation
        )

        self.reset_simulation(width=9, height=7, speed=3, rule='conway', randomize=False)
        reset = self.wait_for_state(
            lambda state: (
                not state['running']
                and state['generation'] == 0
                and state['topology_spec']['width'] == 9
                and state['topology_spec']['height'] == 7
                and state['rule']['name'] == 'conway'
            )
        )

        self.assertGreaterEqual(running['generation'], 1)
        self.assertEqual(paused['generation'], paused_generation)
        self.assertGreater(resumed['generation'], paused_generation)
        self.assertEqual(reset['generation'], 0)
        self.assertFalse(reset['running'])
        self.assertEqual(reset['topology_spec']['width'], 9)
        self.assertEqual(reset['topology_spec']['height'], 7)
        self.assertEqual(reset['rule']['name'], 'conway')

    def test_state_only_control_responses_include_topology_when_revision_is_unchanged(self) -> None:
        self.client.post('/api/cells/toggle', json={'id': 'c:1:1'})
        initial = self.get_state()
        initial_revision = initial['topology_revision']

        started = self.client.post('/api/control/start')
        paused = self.client.post('/api/control/pause')
        resumed = self.client.post('/api/control/resume')
        stepped = self.client.post('/api/control/step')

        for response in (started, paused, resumed, stepped):
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertIn('topology', payload)
            self.assertEqual(payload['topology_revision'], initial_revision)
            self.assertIn('cell_states', payload)
            self.assertEqual(payload['topology_revision'], payload['topology']['topology_revision'])

    def test_speed_only_config_update_keeps_running_when_simulation_is_active(self) -> None:
        self.reset_simulation(width=8, height=8, speed=5, rule='conway', randomize=False)
        self.client.post('/api/control/start')
        self.wait_for_state(lambda state: state['running'] and state['generation'] >= 1)

        response = self.client.post('/api/config', json={'speed': 9})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertTrue(payload['running'])
        self.assertEqual(payload['speed'], 9)
        self.assertIn('topology', payload)
        active = self.wait_for_state(lambda state: state['running'] and state['speed'] == 9)
        self.assertTrue(active['running'])
        self.assertEqual(active['speed'], 9)

    def test_dimension_changing_config_update_pauses_running_simulation(self) -> None:
        self.reset_simulation(width=8, height=8, speed=5, rule='conway', randomize=False)
        self.client.post('/api/control/start')
        self.wait_for_state(lambda state: state['running'] and state['generation'] >= 1)

        response = self.client.post('/api/config', json={'topology_spec': {'width': 12, 'height': 9}})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertFalse(payload['running'])
        self.assertEqual(payload['topology_spec']['width'], 12)
        self.assertEqual(payload['topology_spec']['height'], 9)
        self.assertIn('topology', payload)
        paused = self.wait_for_state(
            lambda state: (
                not state['running']
                and state['topology_spec']['width'] == 12
                and state['topology_spec']['height'] == 9
            )
        )
        self.assertFalse(paused['running'])

    def test_step_while_running_pauses_and_advances_generation(self) -> None:
        self.reset_simulation(width=8, height=8, speed=10, rule='highlife', randomize=True)
        self.client.post('/api/control/start')
        running = self.wait_for_state(lambda state: state['running'] and state['generation'] >= 1)

        stepped_response = self.client.post('/api/control/step')
        self.assertEqual(stepped_response.status_code, 200)
        stepped_payload = stepped_response.get_json()
        self.assertIsInstance(stepped_payload, dict)
        self.assertFalse(stepped_payload['running'])
        self.assertGreaterEqual(stepped_payload['generation'], running['generation'] + 1)

        paused_generation = self.assert_generation_stable()
        self.assertEqual(paused_generation, stepped_payload['generation'])

    def test_reset_and_config_return_exact_state_payloads(self) -> None:
        resized = self.client.post('/api/config', json={'topology_spec': {'width': 12, 'height': 8}})
        self.assertEqual(resized.status_code, 200)
        resized_payload = resized.get_json()
        self.assertIn('topology', resized_payload)
        self.assertEqual(resized_payload['topology_revision'], resized_payload['topology']['topology_revision'])

        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'archimedean-3-3-3-3-6',
                'adjacency_mode': 'edge',
                'width': 4,
                'height': 3,
                'patch_depth': 0,
            },
            'speed': 5,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)
        reset_payload = reset.get_json()
        self.assertIn('topology', reset_payload)
        self.assertEqual(reset_payload['topology_revision'], reset_payload['topology']['topology_revision'])

    def test_random_reset_succeeds_for_supported_binary_rules(self) -> None:
        deterministic_rows = [
            [0, 1, 0, 1, 0],
            [1, 0, 1, 0, 1],
            [0, 0, 1, 1, 0],
            [1, 1, 0, 0, 1],
            [0, 1, 1, 0, 0],
        ]
        deterministic_states = [cell for row in deterministic_rows for cell in row]

        for rule_name in ('conway', 'highlife'):
            with self.subTest(rule_name=rule_name):
                with patch(
                    'backend.simulation.service.random.choices',
                    return_value=deterministic_states[:],
                ):
                    response = self.client.post('/api/control/reset', json={
                        'topology_spec': {'tiling_family': 'square', 'adjacency_mode': 'edge', 'width': 5, 'height': 5, 'patch_depth': 0},
                        'speed': 8,
                        'rule': rule_name,
                        'randomize': True,
                    })

                self.assertEqual(response.status_code, 200)
                payload = response.get_json()
                self.assertFalse(payload['running'])
                self.assertEqual(payload['generation'], 0)
                self.assertEqual(payload['topology_spec']['width'], 5)
                self.assertEqual(payload['topology_spec']['height'], 5)
                self.assertEqual(payload['speed'], 8)
                self.assertEqual(payload['rule']['name'], rule_name)
                self.assert_regular_rows(payload, deterministic_rows)
                self.assert_grid_uses_rule_states(payload)

    def test_reset_can_switch_geometry_and_uses_geometry_default_rule(self) -> None:
        for geometry, width, height, rule_name in (
            ('hex', 9, 7, 'hexlife'),
            ('triangle', 11, 9, 'trilife'),
        ):
            with self.subTest(geometry=geometry):
                response = self.client.post('/api/control/reset', json={
                    'topology_spec': {'tiling_family': geometry, 'adjacency_mode': 'edge', 'width': width, 'height': height, 'patch_depth': 0},
                    'speed': 6,
                    'randomize': False,
                })

                self.assertEqual(response.status_code, 200)
                payload = response.get_json()
                self.assertEqual(payload['topology_spec']['tiling_family'], geometry)
                self.assertEqual(payload['topology_spec']['width'], width)
                self.assertEqual(payload['topology_spec']['height'], height)
                self.assertEqual(payload['speed'], 6)
                self.assertFalse(payload['running'])
                self.assertEqual(payload['generation'], 0)
                self.assertEqual(payload['rule']['name'], rule_name)
                self.assertTrue(all(cell == 0 for cell in self.cells_by_id(payload).values()))

    def test_reset_can_switch_to_archimedean_geometry(self) -> None:
        response = self.client.post('/api/control/reset', json={
            'topology_spec': {'tiling_family': 'archimedean-4-8-8', 'adjacency_mode': 'edge', 'width': 5, 'height': 5, 'patch_depth': 0},
            'speed': 6,
            'randomize': False,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['topology_spec']['tiling_family'], 'archimedean-4-8-8')
        self.assertEqual(payload['topology_spec']['width'], 5)
        self.assertEqual(payload['topology_spec']['height'], 5)
        self.assertEqual(payload['speed'], 6)
        self.assertFalse(payload['running'])
        self.assertEqual(payload['generation'], 0)
        self.assert_archlife_rule(payload)
        self.assertNotIn('grid', payload)
        self.assertEqual(payload['topology']['topology_spec']['tiling_family'], 'archimedean-4-8-8')
        self.assertEqual(len(payload['cell_states']), 61)
        self.assertTrue(all(cell_state == 0 for cell_state in payload['cell_states']))

    def test_reset_can_switch_to_kagome_geometry(self) -> None:
        response = self.client.post('/api/control/reset', json={
            'topology_spec': {'tiling_family': 'trihexagonal-3-6-3-6', 'adjacency_mode': 'edge', 'width': 4, 'height': 3, 'patch_depth': 0},
            'speed': 6,
            'randomize': False,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['topology_spec']['tiling_family'], 'trihexagonal-3-6-3-6')
        self.assertEqual(payload['topology_spec']['width'], 4)
        self.assertEqual(payload['topology_spec']['height'], 3)
        self.assertEqual(payload['speed'], 6)
        self.assertFalse(payload['running'])
        self.assertEqual(payload['generation'], 0)
        self.assert_kagome_rule(payload)
        self.assertNotIn('grid', payload)
        self.assertEqual(payload['topology']['topology_spec']['tiling_family'], 'trihexagonal-3-6-3-6')
        self.assertEqual(len(payload['cell_states']), 4 * 3 * 3)
        self.assertTrue(all(cell_state == 0 for cell_state in payload['cell_states']))


if __name__ == '__main__':
    unittest.main()
