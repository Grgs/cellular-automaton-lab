import sys
import unittest
from pathlib import Path

try:
    from tests.api.support import ApiTestCase
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.api.support import ApiTestCase


class ApiCellTests(ApiTestCase):
    def test_invalid_payloads_return_400(self) -> None:
        bad_width = self.client.post('/api/config', json={'width': 'abc'})
        missing_id = self.client.post('/api/cells/toggle', json={})
        unknown_rule = self.client.post('/api/config', json={'rule': 'missing'})
        bad_geometry = self.client.post('/api/config', json={'geometry': 'hex'})
        bad_state = self.client.post('/api/cells/set', json={'id': 'c:1:1', 'state': 2})
        legacy_coordinates = self.client.post('/api/cells/set', json={'x': 1, 'y': 1, 'state': 1})
        empty_batch = self.client.post('/api/cells/set-many', json={'cells': []})

        self.assertEqual(bad_width.status_code, 400)
        self.assertEqual(missing_id.status_code, 400)
        self.assertEqual(unknown_rule.status_code, 400)
        self.assertEqual(bad_geometry.status_code, 400)
        self.assertEqual(bad_state.status_code, 400)
        self.assertEqual(legacy_coordinates.status_code, 400)
        self.assertEqual(empty_batch.status_code, 400)

    def test_coordinate_style_mutation_payloads_are_rejected_without_mutating_state(self) -> None:
        toggle = self.client.post('/api/cells/toggle', json={'x': 2, 'y': 3})
        batch = self.client.post('/api/cells/set-many', json={'cells': [
            {'id': 'c:1:1', 'state': 1},
            {'x': 4, 'y': 2, 'state': 1},
        ]})

        self.assertEqual(toggle.status_code, 400)
        self.assertEqual(batch.status_code, 400)

        payload = self.get_state()
        self.assertEqual(self.regular_cell_state(payload, 1, 1), 0)
        self.assertEqual(sum(self.cells_by_id(payload).values()), 0)

    def test_resize_and_toggle(self) -> None:
        config = self.client.post('/api/config', json={'topology_spec': {'width': 12, 'height': 8}, 'speed': 9, 'rule': 'highlife'})
        toggled = self.client.post('/api/cells/toggle', json={'id': 'c:11:7'})

        self.assertEqual(config.status_code, 200)
        self.assertEqual(toggled.status_code, 200)
        payload = toggled.get_json()
        self.assertEqual(payload['topology_spec']['height'], 8)
        self.assertEqual(payload['topology_spec']['width'], 12)
        self.assertIn('topology', payload)
        self.assertEqual(self.regular_cell_state(payload, 11, 7), 1)

    def test_state_only_cell_mutations_include_topology_when_revision_is_unchanged(self) -> None:
        initial = self.get_state()
        initial_revision = initial['topology_revision']

        single = self.client.post('/api/cells/set', json={'id': 'c:2:3', 'state': 1})
        batch = self.client.post('/api/cells/set-many', json={'cells': [
            {'id': 'c:4:1', 'state': 1},
            {'id': 'c:5:2', 'state': 1},
        ]})
        toggle = self.client.post('/api/cells/toggle', json={'id': 'c:1:1'})

        self.assertEqual(single.status_code, 200)
        self.assertEqual(batch.status_code, 200)
        self.assertEqual(toggle.status_code, 200)

        for response in (single, batch, toggle):
            payload = response.get_json()
            self.assertIn('topology', payload)
            self.assertEqual(payload['topology_revision'], initial_revision)
            self.assertIn('cell_states', payload)
            self.assertEqual(payload['topology_revision'], payload['topology']['topology_revision'])

    def test_set_cell_and_set_many(self) -> None:
        single = self.client.post('/api/cells/set', json={'id': 'c:2:3', 'state': 1})
        batch = self.client.post('/api/cells/set-many', json={'cells': [
            {'id': 'c:4:1', 'state': 1},
            {'id': 'c:5:2', 'state': 1},
        ]})

        self.assertEqual(single.status_code, 200)
        self.assertEqual(batch.status_code, 200)
        payload = batch.get_json()
        self.assertEqual(self.regular_cell_state(payload, 2, 3), 1)
        self.assertEqual(self.regular_cell_state(payload, 4, 1), 1)
        self.assertEqual(self.regular_cell_state(payload, 5, 2), 1)

    def test_unknown_ids_are_ignored_for_set_operations(self) -> None:
        single = self.client.post('/api/cells/set', json={'id': 'missing:-1:0', 'state': 1})
        batch = self.client.post('/api/cells/set-many', json={'cells': [
            {'id': 'c:1:1', 'state': 1},
            {'id': 'missing:-1:0', 'state': 1},
            {'id': 'missing:999:999', 'state': 1},
        ]})

        self.assertEqual(single.status_code, 200)
        self.assertEqual(batch.status_code, 200)

        payload = batch.get_json()
        self.assertEqual(self.regular_cell_state(payload, 1, 1), 1)
        self.assertEqual(sum(self.cells_by_id(payload).values()), 1)

    def test_archimedean_cell_mutations_accept_cell_ids(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'archimedean-4-8-8',
                'adjacency_mode': 'edge',
                'width': 5,
                'height': 5,
                'patch_depth': 0,
            },
            'speed': 5,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)
        topology = self.get_topology()
        index_by_id = {
            cell['id']: index
            for index, cell in enumerate(topology['cells'])
        }

        single = self.client.post('/api/cells/set', json={'id': 's:1:1', 'state': 1})
        toggled = self.client.post('/api/cells/toggle', json={'id': 'o:2:2'})
        batch = self.client.post('/api/cells/set-many', json={'cells': [
            {'id': 's:2:2', 'state': 1},
            {'id': 'o:1:1', 'state': 1},
        ]})

        self.assertEqual(single.status_code, 200)
        self.assertEqual(toggled.status_code, 200)
        self.assertEqual(batch.status_code, 200)

        payload = batch.get_json()
        self.assertNotIn('grid', payload)
        self.assertEqual(payload['cell_states'][index_by_id['s:1:1']], 1)
        self.assertEqual(payload['cell_states'][index_by_id['o:2:2']], 1)
        self.assertEqual(payload['cell_states'][index_by_id['s:2:2']], 1)
        self.assertEqual(payload['cell_states'][index_by_id['o:1:1']], 1)

    def test_kagome_cell_mutations_accept_cell_ids(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'trihexagonal-3-6-3-6',
                'adjacency_mode': 'edge',
                'width': 4,
                'height': 4,
                'patch_depth': 0,
            },
            'speed': 5,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)
        topology = self.get_topology()
        index_by_id = {
            cell['id']: index
            for index, cell in enumerate(topology['cells'])
        }

        single = self.client.post('/api/cells/set', json={'id': 'tu:1:1', 'state': 1})
        toggled = self.client.post('/api/cells/toggle', json={'id': 'h:1:1'})
        batch = self.client.post('/api/cells/set-many', json={'cells': [
            {'id': 'td:1:1', 'state': 1},
            {'id': 'h:2:1', 'state': 1},
        ]})

        self.assertEqual(single.status_code, 200)
        self.assertEqual(toggled.status_code, 200)
        self.assertEqual(batch.status_code, 200)

        payload = batch.get_json()
        self.assertNotIn('grid', payload)
        self.assertEqual(payload['cell_states'][index_by_id['tu:1:1']], 1)
        self.assertEqual(payload['cell_states'][index_by_id['h:1:1']], 1)
        self.assertEqual(payload['cell_states'][index_by_id['td:1:1']], 1)
        self.assertEqual(payload['cell_states'][index_by_id['h:2:1']], 1)


if __name__ == '__main__':
    unittest.main()
