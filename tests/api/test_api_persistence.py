import json
import sys
import unittest
from pathlib import Path

try:
    from backend.defaults import APP_DEFAULTS
    from tests.api.support import ApiTestCase
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.defaults import APP_DEFAULTS
    from tests.api.support import ApiTestCase


class ApiPersistenceTests(ApiTestCase):
    def test_app_ignores_preexisting_persisted_snapshot_with_retired_version(self) -> None:
        state_path = Path(self.app.instance_path) / 'simulation_state.json'
        state_path.write_text(json.dumps({
            'version': 4,
            'topology_spec': {
                'tiling_family': 'hex',
                'adjacency_mode': 'edge',
                'sizing_mode': 'grid',
                'width': 7,
                'height': 5,
                'patch_depth': 0,
            },
            'speed': 9,
            'running': True,
            'generation': 4,
            'rule': 'hexwhirlpool',
            'cells_by_id': {
                'c:1:1': 1,
                'c:2:1': 2,
                'c:3:1': 3,
            },
        }), encoding='utf-8')

        with self.assertLogs('backend.simulation.coordinator', level='WARNING') as logs:
            type(self).recreate_app(persist_current=False)
        payload = self.get_state()

        self.assertIn('Persisted simulation state version is unsupported.', '\n'.join(logs.output))
        self.assertEqual(payload['topology_spec']['tiling_family'], 'square')
        self.assertEqual(payload['topology_spec']['width'], APP_DEFAULTS['simulation']['topology_spec']['width'])
        self.assertEqual(payload['topology_spec']['height'], APP_DEFAULTS['simulation']['topology_spec']['height'])
        self.assertEqual(payload['speed'], APP_DEFAULTS['simulation']['speed'])
        self.assertEqual(payload['rule']['name'], APP_DEFAULTS['simulation']['rule'])
        self.assertFalse(payload['running'])
        self.assertEqual(payload['generation'], 0)
        self.assertTrue(all(state == 0 for state in payload['cell_states']))

    def test_app_boots_from_preexisting_persisted_snapshot_v5(self) -> None:
        state_path = Path(self.app.instance_path) / 'simulation_state.json'
        state_path.write_text(json.dumps({
            'version': 5,
            'topology_spec': {
                'tiling_family': 'hex',
                'adjacency_mode': 'edge',
                'sizing_mode': 'grid',
                'width': 7,
                'height': 5,
                'patch_depth': 0,
            },
            'speed': 9,
            'running': True,
            'generation': 4,
            'rule': 'hexwhirlpool',
            'cells_by_id': {
                'c:1:1': 1,
                'c:2:1': 2,
                'c:3:1': 3,
            },
        }), encoding='utf-8')

        type(self).recreate_app(persist_current=False)
        payload = self.get_state()

        self.assertEqual(payload['topology_spec']['tiling_family'], 'hex')
        self.assertEqual(payload['topology_spec']['width'], 7)
        self.assertEqual(payload['topology_spec']['height'], 5)
        self.assertEqual(payload['speed'], 9)
        self.assertEqual(payload['rule']['name'], 'whirlpool')
        self.assertFalse(payload['running'])
        self.assertEqual(payload['generation'], 4)
        index_by_id = {
            cell['id']: index
            for index, cell in enumerate(payload['topology']['cells'])
        }
        self.assertEqual(payload['cell_states'][index_by_id['c:1:1']], 1)
        self.assertEqual(payload['cell_states'][index_by_id['c:2:1']], 2)
        self.assertEqual(payload['cell_states'][index_by_id['c:3:1']], 3)

    def test_state_restores_after_app_recreation(self) -> None:
        self.client.post('/api/control/reset', json={
            'topology_spec': {'tiling_family': 'hex', 'adjacency_mode': 'edge', 'width': 8, 'height': 6, 'patch_depth': 0},
            'speed': 7,
            'rule': 'hexwhirlpool',
            'randomize': False,
        })
        self.client.post('/api/cells/set-many', json={
            'cells': [
                {'id': 'c:2:2', 'state': 1},
                {'id': 'c:3:2', 'state': 2},
                {'id': 'c:4:2', 'state': 3},
            ],
        })
        self.client.post('/api/control/step')
        before_restart = self.get_state()

        type(self).recreate_app()
        after_restart = self.get_state()

        self.assertEqual(after_restart['topology_spec']['tiling_family'], 'hex')
        self.assertEqual(after_restart['topology_spec']['width'], 8)
        self.assertEqual(after_restart['topology_spec']['height'], 6)
        self.assertEqual(after_restart['speed'], 7)
        self.assertEqual(after_restart['rule']['name'], 'whirlpool')
        self.assertFalse(after_restart['running'])
        self.assertEqual(after_restart['generation'], before_restart['generation'])
        self.assertEqual(after_restart['cell_states'], before_restart['cell_states'])

    def test_clean_shutdown_persists_latest_running_state_and_restores_paused(self) -> None:
        self.reset_simulation(width=8, height=8, speed=10, rule='highlife', randomize=True)
        self.client.post('/api/control/start')
        before_shutdown = self.wait_for_state(lambda state: state['running'] and state['generation'] >= 1)

        type(self).recreate_app()
        after_restart = self.get_state()

        self.assertFalse(after_restart['running'])
        self.assertGreaterEqual(after_restart['generation'], before_shutdown['generation'])
        self.assertEqual(after_restart['topology_spec']['width'], before_shutdown['topology_spec']['width'])
        self.assertEqual(after_restart['topology_spec']['height'], before_shutdown['topology_spec']['height'])
        self.assertEqual(after_restart['speed'], before_shutdown['speed'])
        self.assertEqual(after_restart['rule']['name'], before_shutdown['rule']['name'])

    def test_penrose_vertex_state_restores_after_app_recreation(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {'tiling_family': 'penrose-p3-rhombs', 'adjacency_mode': 'vertex', 'patch_depth': 3},
            'speed': 7,
            'rule': 'conway',
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)
        topology = self.get_topology()
        seed_ids = [cell['id'] for cell in topology['cells'][:3]]
        self.client.post('/api/cells/set-many', json={
            'cells': [{'id': cell_id, 'state': 1} for cell_id in seed_ids],
        })
        before_restart = self.get_state()

        type(self).recreate_app()
        after_restart = self.get_state()

        self.assertEqual(after_restart['topology_spec']['tiling_family'], 'penrose-p3-rhombs')
        self.assertEqual(after_restart['topology_spec']['adjacency_mode'], 'vertex')
        self.assertEqual(after_restart['topology_spec']['patch_depth'], 3)
        self.assertEqual(after_restart['speed'], 7)
        self.assertEqual(after_restart['rule']['name'], 'conway')
        self.assertFalse(after_restart['running'])
        self.assertEqual(after_restart['generation'], before_restart['generation'])
        self.assertEqual(after_restart['cell_states'], before_restart['cell_states'])

    def test_archimedean_3464_state_restores_after_app_recreation(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {'tiling_family': 'archimedean-3-4-6-4', 'adjacency_mode': 'edge', 'width': 2, 'height': 2, 'patch_depth': 0},
            'speed': 6,
            'rule': 'archlife-3-4-6-4',
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)
        topology = self.get_topology()
        seed_ids = [cell['id'] for cell in topology['cells'][:4]]
        self.client.post('/api/cells/set-many', json={
            'cells': [{'id': cell_id, 'state': 1} for cell_id in seed_ids],
        })
        before_restart = self.get_state()

        type(self).recreate_app()
        after_restart = self.get_state()

        self.assertEqual(after_restart['topology_spec']['tiling_family'], 'archimedean-3-4-6-4')
        self.assertEqual(after_restart['topology_spec']['width'], 2)
        self.assertEqual(after_restart['topology_spec']['height'], 2)
        self.assertEqual(after_restart['rule']['name'], 'archlife-3-4-6-4')
        self.assertEqual(after_restart['cell_states'], before_restart['cell_states'])


if __name__ == '__main__':
    unittest.main()
