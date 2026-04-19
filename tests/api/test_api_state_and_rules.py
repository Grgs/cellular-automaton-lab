import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.payload_types import RuleDefinitionPayload

try:
    from tests.api.support import ApiTestCase
    from tests.typed_payloads import require_server_meta_payload
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.api.support import ApiTestCase
    from tests.typed_payloads import require_server_meta_payload


class ApiStateAndRulesTests(ApiTestCase):
    def assert_universal_rule_contract(self, payload: RuleDefinitionPayload) -> None:
        self.assertTrue(payload['supports_all_topologies'])
        self.assertEqual(payload['rule_protocol'], 'universal-v1')
        self.assertNotIn('supported_topologies', payload)

    def test_meta_endpoint_reports_server_identity(self) -> None:
        response = self.client.get('/api/meta')

        self.assertEqual(response.status_code, 200)
        payload = require_server_meta_payload(
            response.get_json(),
            context="server meta response",
        )
        self.assertEqual(payload, {'app_name': 'cellular-automaton-lab'})

    def test_meta_endpoint_omits_local_host_details(self) -> None:
        response = self.client.get('/api/meta')

        self.assertEqual(response.status_code, 200)
        payload = require_server_meta_payload(
            response.get_json(),
            context="server meta response",
        )
        self.assertNotIn('pid', payload)
        self.assertNotIn('instance_path', payload)
        self.assertNotIn('started_at', payload)

    def test_rules_and_initial_state(self) -> None:
        rules = self.get_rules()
        payload = self.get_state()

        rule_names = [rule['name'] for rule in rules]
        self.assertTrue(all('supported_geometries' not in rule for rule in rules))
        self.assertIn('archlife488', rule_names)
        self.assertIn('archlife-3-12-12', rule_names)
        self.assertIn('archlife-3-4-6-4', rule_names)
        self.assertIn('archlife-4-6-12', rule_names)
        self.assertIn('archlife-3-3-4-3-4', rule_names)
        self.assertIn('archlife-3-3-3-4-4', rule_names)
        self.assertIn('archlife-3-3-3-3-6', rule_names)
        self.assertIn('conway', rule_names)
        self.assertIn('highlife', rule_names)
        self.assertIn('kagome-life', rule_names)
        self.assertIn('hexlife', rule_names)
        self.assertIn('life-b2-s23', rule_names)
        self.assertIn('penrose-greenberg-hastings', rule_names)
        self.assertIn('trilife', rule_names)
        self.assertIn('whirlpool', rule_names)
        self.assertIn('wireworld', rule_names)
        self.assertNotIn('ammann-beenker-life', rule_names)
        self.assertNotIn('cairo-life', rule_names)
        self.assertNotIn('penrose-p2-life', rule_names)
        self.assertNotIn('custom', rule_names)

        archlife = self.get_rule_definition('archlife488')
        self.assertEqual(archlife['default_paint_state'], 1)
        self.assertTrue(archlife['supports_randomize'])
        self.assert_universal_rule_contract(archlife)
        self.assertEqual([cell_state['value'] for cell_state in archlife['states']], [0, 1])

        archlife_31212 = self.get_rule_definition('archlife-3-12-12')
        self.assert_universal_rule_contract(archlife_31212)
        self.assertEqual([cell_state['value'] for cell_state in archlife_31212['states']], [0, 1])

        archlife_33336 = self.get_rule_definition('archlife-3-3-3-3-6')
        self.assert_universal_rule_contract(archlife_33336)
        self.assertEqual([cell_state['value'] for cell_state in archlife_33336['states']], [0, 1])

        hexlife = self.get_rule_definition('hexlife')
        self.assertEqual(hexlife['default_paint_state'], 1)
        self.assertTrue(hexlife['supports_randomize'])
        self.assert_universal_rule_contract(hexlife)
        self.assertEqual([cell_state['value'] for cell_state in hexlife['states']], [0, 1])

        whirlpool = self.get_rule_definition('whirlpool')
        self.assertEqual(whirlpool['default_paint_state'], 1)
        self.assertFalse(whirlpool['supports_randomize'])
        self.assert_universal_rule_contract(whirlpool)
        self.assertEqual([cell_state['value'] for cell_state in whirlpool['states']], [0, 1, 2, 3, 4])
        self.assertEqual(whirlpool['display_name'], 'Excitable: Outward Whirlpool')

        wireworld = self.get_rule_definition('wireworld')
        self.assertEqual(wireworld['default_paint_state'], 3)
        self.assertFalse(wireworld['supports_randomize'])
        self.assert_universal_rule_contract(wireworld)
        self.assertEqual([cell_state['value'] for cell_state in wireworld['states']], [0, 1, 2, 3])

        trilife = self.get_rule_definition('trilife')
        self.assertEqual(trilife['default_paint_state'], 1)
        self.assertTrue(trilife['supports_randomize'])
        self.assert_universal_rule_contract(trilife)
        self.assertEqual([cell_state['value'] for cell_state in trilife['states']], [0, 1])

        kagome = self.get_rule_definition('kagome-life')
        self.assertEqual(kagome['default_paint_state'], 1)
        self.assertTrue(kagome['supports_randomize'])
        self.assert_universal_rule_contract(kagome)
        self.assertEqual([cell_state['value'] for cell_state in kagome['states']], [0, 1])

        life_b2_s23 = self.get_rule_definition('life-b2-s23')
        self.assertEqual(life_b2_s23['display_name'], 'Life: B2/S23')
        self.assertEqual(life_b2_s23['default_paint_state'], 1)
        self.assertTrue(life_b2_s23['supports_randomize'])
        self.assert_universal_rule_contract(life_b2_s23)
        self.assertEqual([cell_state['value'] for cell_state in life_b2_s23['states']], [0, 1])

        penrose_greenberg_hastings = self.get_rule_definition('penrose-greenberg-hastings')
        self.assertEqual(penrose_greenberg_hastings['default_paint_state'], 1)
        self.assertTrue(penrose_greenberg_hastings['supports_randomize'])
        self.assert_universal_rule_contract(penrose_greenberg_hastings)
        self.assertEqual(
            [cell_state['label'] for cell_state in penrose_greenberg_hastings['states']],
            ['Resting', 'Excited', 'Trailing', 'Refractory'],
        )

        self.assertEqual(
            payload['topology_spec'],
            {
                'tiling_family': 'square',
                'adjacency_mode': 'edge',
                'sizing_mode': 'grid',
                'width': 10,
                'height': 6,
                'patch_depth': 4,
            },
        )
        self.assertFalse(payload['running'])
        self.assertEqual(payload['generation'], 0)
        self.assertEqual(payload['rule']['name'], 'conway')
        self.assertEqual(payload['rule']['default_paint_state'], 1)
        self.assertTrue(payload['rule']['supports_randomize'])
        self.assert_universal_rule_contract(payload['rule'])
        self.assertNotIn('supported_geometries', payload['rule'])
        self.assertEqual([cell_state['value'] for cell_state in payload['rule']['states']], [0, 1])
        self.assertIn('topology_revision', payload)
        self.assertEqual(payload['topology']['topology_spec'], payload['topology_spec'])
        self.assertEqual(len(payload['topology']['cells']), 60)
        self.assertEqual(len(payload['cell_states']), 60)
        self.assertEqual(payload['topology']['cells'][0]['id'], 'c:0:0')
        self.assertNotIn('logical_x', payload['topology']['cells'][0])
        self.assertNotIn('logical_y', payload['topology']['cells'][0])
        self.assertEqual(payload['cell_states'], [0] * 60)
        self.assertNotIn('geometry', payload)
        self.assertNotIn('width', payload)
        self.assertNotIn('height', payload)
        self.assertNotIn('patch_depth', payload)

    def test_topology_endpoint_and_archimedean_state_contract(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'archimedean-4-8-8',
                'adjacency_mode': 'edge',
                'width': 5,
                'height': 5,
                'patch_depth': 0,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'archimedean-4-8-8')
        self.assertEqual(state['topology_spec']['adjacency_mode'], 'edge')
        self.assertEqual(state['topology_spec']['width'], 5)
        self.assertEqual(state['topology_spec']['height'], 5)
        self.assertFalse(state['running'])
        self.assertEqual(state['generation'], 0)
        self.assert_archlife_rule(state)
        self.assertNotIn('grid', state)
        self.assertEqual(state['topology_revision'], topology['topology_revision'])
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertEqual(len(topology['cells']), 61)
        self.assertEqual(len(state['cell_states']), 61)
        self.assertEqual(topology['cells'][0]['id'], 'o:0:0')
        self.assertEqual(topology['cells'][24]['id'], 'o:4:4')
        self.assertEqual(topology['cells'][25]['id'], 's:0:0')
        self.assertNotIn('logical_x', topology['cells'][0])
        self.assertNotIn('logical_y', topology['cells'][0])
        self.assertNotIn('exposes_regular_grid', topology)
        self.assertTrue(all(cell_state == 0 for cell_state in state['cell_states']))

    def test_new_archimedean_geometries_reset_with_default_rules_and_slots(self) -> None:
        cases = [
            ('archimedean-3-12-12', 'archlife-3-12-12', {'triangle', 'dodecagon'}),
            ('archimedean-3-4-6-4', 'archlife-3-4-6-4', {'triangle', 'square', 'hexagon'}),
            ('archimedean-4-6-12', 'archlife-4-6-12', {'square', 'hexagon', 'dodecagon'}),
            ('archimedean-3-3-4-3-4', 'archlife-3-3-4-3-4', {'triangle', 'square'}),
            ('archimedean-3-3-3-4-4', 'archlife-3-3-3-4-4', {'triangle', 'square'}),
            ('archimedean-3-3-3-3-6', 'archlife-3-3-3-3-6', {'triangle', 'hexagon'}),
        ]

        for geometry, rule_name, expected_kinds in cases:
            with self.subTest(geometry=geometry):
                reset = self.client.post('/api/control/reset', json={
                    'topology_spec': {
                        'tiling_family': geometry,
                        'adjacency_mode': 'edge',
                        'width': 1,
                        'height': 1,
                        'patch_depth': 0,
                    },
                    'speed': 6,
                    'randomize': False,
                })
                self.assertEqual(reset.status_code, 200)
                state = reset.get_json()
                topology = self.get_topology()

                self.assertEqual(state['topology_spec']['tiling_family'], geometry)
                self.assertEqual(state['rule']['name'], rule_name)
                self.assertEqual(topology['topology_spec']['tiling_family'], geometry)
                self.assertEqual(topology['topology_spec']['width'], 1)
                self.assertEqual(topology['topology_spec']['height'], 1)
                self.assertTrue(all(cell_state == 0 for cell_state in state['cell_states']))
                self.assertTrue(all('slot' in cell for cell in topology['cells']))
                self.assertEqual({cell['kind'] for cell in topology['cells']}, expected_kinds)

    def test_new_periodic_mixed_geometries_reset_with_generic_default_rule_and_slots(self) -> None:
        cases = [
            ('rhombille', {'rhombus'}, 3),
            ('deltoidal-hexagonal', {'kite'}, 1),
            ('tetrakis-square', {'triangle'}, 3),
            ('triakis-triangular', {'triangle'}, 1),
            ('deltoidal-trihexagonal', {'kite'}, 1),
            ('prismatic-pentagonal', {'pentagon'}, 1),
            ('floret-pentagonal', {'pentagon'}, 1),
            ('snub-square-dual', {'pentagon'}, 1),
        ]

        for geometry, expected_kinds, expected_dimension in cases:
            with self.subTest(geometry=geometry):
                reset = self.client.post('/api/control/reset', json={
                    'topology_spec': {
                        'tiling_family': geometry,
                        'adjacency_mode': 'edge',
                        'width': 1,
                        'height': 1,
                        'patch_depth': 0,
                    },
                    'speed': 6,
                    'randomize': False,
                })
                self.assertEqual(reset.status_code, 200)
                state = reset.get_json()
                topology = self.get_topology()

                self.assertEqual(state['topology_spec']['tiling_family'], geometry)
                self.assertEqual(state['rule']['name'], 'life-b2-s23')
                self.assertEqual(topology['topology_spec']['tiling_family'], geometry)
                self.assertEqual(topology['topology_spec']['width'], expected_dimension)
                self.assertEqual(topology['topology_spec']['height'], expected_dimension)
                self.assertTrue(all(cell_state == 0 for cell_state in state['cell_states']))
                self.assertTrue(all('slot' in cell for cell in topology['cells']))
                self.assertEqual({cell['kind'] for cell in topology['cells']}, expected_kinds)

    def test_topology_endpoint_and_kagome_state_contract(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'trihexagonal-3-6-3-6',
                'adjacency_mode': 'edge',
                'width': 4,
                'height': 3,
                'patch_depth': 0,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'trihexagonal-3-6-3-6')
        self.assertEqual(state['topology_spec']['width'], 4)
        self.assertEqual(state['topology_spec']['height'], 3)
        self.assertFalse(state['running'])
        self.assertEqual(state['generation'], 0)
        self.assert_kagome_rule(state)
        self.assertNotIn('grid', state)
        self.assertEqual(state['topology_revision'], topology['topology_revision'])
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertEqual(len(topology['cells']), 4 * 3 * 3)
        self.assertEqual(len(state['cell_states']), 4 * 3 * 3)
        self.assertEqual(topology['cells'][0]['id'], 'h:0:0')
        self.assertEqual(topology['cells'][12]['id'], 'tu:0:0')
        self.assertEqual(topology['cells'][13]['id'], 'tu:1:0')
        self.assertEqual(topology['cells'][24]['id'], 'td:0:0')
        self.assertTrue(all(cell_state == 0 for cell_state in state['cell_states']))

    def test_topology_endpoint_and_penrose_state_contract(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'penrose-p3-rhombs',
                'adjacency_mode': 'edge',
                'patch_depth': 99,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'penrose-p3-rhombs')
        self.assertEqual(state['topology_spec']['adjacency_mode'], 'edge')
        self.assertEqual(state['topology_spec']['patch_depth'], 6)
        self.assertFalse(state['running'])
        self.assertEqual(state['generation'], 0)
        self.assertEqual(state['rule']['name'], 'life-b2-s23')
        self.assertNotIn('grid', state)
        self.assertEqual(state['topology_revision'], topology['topology_revision'])
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertEqual(len(topology['cells']), len(state['cell_states']))
        self.assertGreater(len(topology['cells']), 100)
        self.assertTrue(all(cell_state == 0 for cell_state in state['cell_states']))
        self.assertIn('center', topology['cells'][0])
        self.assertIn('vertices', topology['cells'][0])

    def test_penrose_greenberg_hastings_reset_returns_excitable_palette(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'penrose-p3-rhombs',
                'adjacency_mode': 'edge',
                'patch_depth': 3,
            },
            'speed': 6,
            'rule': 'penrose-greenberg-hastings',
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        self.assertEqual(state['topology_spec']['tiling_family'], 'penrose-p3-rhombs')
        self.assertEqual(state['topology_spec']['patch_depth'], 3)
        self.assertEqual(state['rule']['name'], 'penrose-greenberg-hastings')
        self.assertEqual(
            [cell_state['label'] for cell_state in state['rule']['states']],
            ['Resting', 'Excited', 'Trailing', 'Refractory'],
        )
        self.assertTrue(all(cell_state == 0 for cell_state in state['cell_states']))

    def test_penrose_greenberg_hastings_random_reset_uses_resting_and_excited_only(self) -> None:
        deterministic_states = [0, 1] * 60
        with patch(
            'backend.simulation.service.random.choices',
            return_value=deterministic_states,
        ):
            reset = self.client.post('/api/control/reset', json={
                'topology_spec': {
                    'tiling_family': 'penrose-p3-rhombs',
                    'adjacency_mode': 'edge',
                    'patch_depth': 2,
                },
                'speed': 6,
                'rule': 'penrose-greenberg-hastings',
                'randomize': True,
            })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        self.assertEqual(state['rule']['name'], 'penrose-greenberg-hastings')
        self.assertTrue(any(cell_state == 1 for cell_state in state['cell_states']))
        self.assertTrue(all(cell_state in {0, 1} for cell_state in state['cell_states']))

    def test_topology_endpoint_and_penrose_vertex_state_contract(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'penrose-p3-rhombs',
                'adjacency_mode': 'vertex',
                'patch_depth': 4,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'penrose-p3-rhombs')
        self.assertEqual(state['topology_spec']['adjacency_mode'], 'vertex')
        self.assertEqual(state['topology_spec']['patch_depth'], 4)
        self.assertEqual(state['rule']['name'], 'conway')
        self.assertNotIn('grid', state)
        self.assertEqual(state['topology_revision'], topology['topology_revision'])
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertGreater(len(topology['cells']), 50)
        self.assertTrue(all(cell_state == 0 for cell_state in state['cell_states']))

    def test_ammann_beenker_patch_depth_is_capped_at_four(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'ammann-beenker',
                'adjacency_mode': 'edge',
                'patch_depth': 99,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'ammann-beenker')
        self.assertEqual(state['topology_spec']['patch_depth'], 4)
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertEqual(len(topology['cells']), len(state['cell_states']))
        self.assertGreater(len(topology['cells']), 100)

    def test_spectre_patch_depth_uses_generic_rule_and_caps_at_three(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'spectre',
                'adjacency_mode': 'edge',
                'patch_depth': 99,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'spectre')
        self.assertEqual(state['topology_spec']['patch_depth'], 3)
        self.assertEqual(state['rule']['name'], 'life-b2-s23')
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertEqual(len(topology['cells']), len(state['cell_states']))
        self.assertGreater(len(topology['cells']), 500)
        self.assertTrue(all(cell['kind'] == 'spectre' for cell in topology['cells']))

    def test_taylor_socolar_patch_depth_uses_generic_rule_and_caps_at_five(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'taylor-socolar',
                'adjacency_mode': 'edge',
                'patch_depth': 99,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'taylor-socolar')
        self.assertEqual(state['topology_spec']['patch_depth'], 5)
        self.assertEqual(state['rule']['name'], 'life-b2-s23')
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertEqual(len(topology['cells']), len(state['cell_states']))
        self.assertGreater(len(topology['cells']), 100)
        self.assertTrue(all(cell['kind'] == 'taylor-half-hex' for cell in topology['cells']))

    def test_sphinx_patch_depth_uses_generic_rule_and_caps_at_five(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'sphinx',
                'adjacency_mode': 'edge',
                'patch_depth': 99,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'sphinx')
        self.assertEqual(state['topology_spec']['patch_depth'], 5)
        self.assertEqual(state['rule']['name'], 'life-b2-s23')
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertEqual(len(topology['cells']), len(state['cell_states']))
        self.assertGreater(len(topology['cells']), 20)
        self.assertTrue(all(cell['kind'] == 'sphinx' for cell in topology['cells']))

    def test_chair_patch_depth_uses_generic_rule_and_caps_at_five(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'chair',
                'adjacency_mode': 'edge',
                'patch_depth': 99,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'chair')
        self.assertEqual(state['topology_spec']['patch_depth'], 5)
        self.assertEqual(state['rule']['name'], 'life-b2-s23')
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertEqual(len(topology['cells']), len(state['cell_states']))
        self.assertGreater(len(topology['cells']), 50)
        self.assertTrue(all(cell['kind'] == 'chair' for cell in topology['cells']))

    def test_robinson_triangles_patch_depth_uses_generic_rule_and_caps_at_five(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'robinson-triangles',
                'adjacency_mode': 'edge',
                'patch_depth': 99,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'robinson-triangles')
        self.assertEqual(state['topology_spec']['patch_depth'], 5)
        self.assertEqual(state['rule']['name'], 'life-b2-s23')
        self.assertEqual(topology['topology_spec'], state['topology_spec'])
        self.assertEqual(len(topology['cells']), len(state['cell_states']))
        self.assertGreater(len(topology['cells']), 100)
        self.assertEqual({cell['kind'] for cell in topology['cells']}, {'robinson-thick', 'robinson-thin'})

    def test_new_aperiodic_wave_tilings_reset_with_metadata_and_expected_caps(self) -> None:
        cases = (
            ('hat-monotile', 3, {'hat'}),
            ('tuebingen-triangle', 5, {'tuebingen-thick', 'tuebingen-thin'}),
            ('dodecagonal-square-triangle', 4, {'dodecagonal-square-triangle-square', 'dodecagonal-square-triangle-triangle'}),
            ('shield', 5, {'shield-shield', 'shield-square', 'shield-triangle'}),
            ('pinwheel', 4, {'pinwheel-triangle'}),
        )

        for geometry, expected_patch_depth, expected_kinds in cases:
            with self.subTest(geometry=geometry):
                reset = self.client.post('/api/control/reset', json={
                    'topology_spec': {
                        'tiling_family': geometry,
                        'adjacency_mode': 'edge',
                        'patch_depth': 99,
                    },
                    'speed': 6,
                    'randomize': False,
                })
                self.assertEqual(reset.status_code, 200)

                state = reset.get_json()
                topology = self.get_topology()

                self.assertEqual(state['topology_spec']['tiling_family'], geometry)
                self.assertEqual(state['topology_spec']['patch_depth'], expected_patch_depth)
                self.assertEqual(state['rule']['name'], 'life-b2-s23')
                self.assertEqual(topology['topology_spec'], state['topology_spec'])
                self.assertEqual(len(topology['cells']), len(state['cell_states']))
                self.assertTrue(all(cell['kind'] in expected_kinds for cell in topology['cells']))
                self.assertTrue(all(cell.get('tile_family') is not None for cell in topology['cells']))
                if geometry in {'hat-monotile', 'tuebingen-triangle', 'pinwheel'}:
                    self.assertTrue(all(cell.get('orientation_token') is not None for cell in topology['cells']))
                    self.assertTrue(all(cell.get('chirality_token') is not None for cell in topology['cells']))
                if geometry == 'dodecagonal-square-triangle':
                    self.assertTrue(any(cell['kind'] == 'dodecagonal-square-triangle-square' for cell in topology['cells']))
                    self.assertTrue(all(cell.get('orientation_token') is not None for cell in topology['cells']))
                if geometry == 'shield':
                    self.assertTrue(any(cell['kind'] == 'shield-square' for cell in topology['cells']))
                    self.assertTrue(all(cell.get('orientation_token') is not None for cell in topology['cells']))

    def test_unsafe_size_override_allows_patch_depth_above_family_cap(self) -> None:
        reset = self.client.post('/api/control/reset', json={
            'topology_spec': {
                'tiling_family': 'spectre',
                'adjacency_mode': 'edge',
                'patch_depth': 4,
                'unsafe_size_override': True,
            },
            'speed': 6,
            'randomize': False,
        })
        self.assertEqual(reset.status_code, 200)

        state = reset.get_json()
        topology = self.get_topology()

        self.assertEqual(state['topology_spec']['tiling_family'], 'spectre')
        self.assertEqual(state['topology_spec']['patch_depth'], 4)
        self.assertEqual(topology['topology_spec']['patch_depth'], 4)
        self.assertTrue(all(cell['kind'] == 'spectre' for cell in topology['cells']))

    def test_retired_penrose_rule_names_resolve_to_canonical_rules(self) -> None:
        for requested_rule, expected_rule in (
            ('penrose-life', 'life-b2-s23'),
            ('penrose-vertex-life', 'conway'),
        ):
            with self.subTest(rule=requested_rule):
                reset = self.client.post('/api/control/reset', json={
                    'topology_spec': {
                        'tiling_family': 'square',
                        'adjacency_mode': 'edge',
                        'width': 5,
                        'height': 4,
                        'patch_depth': 0,
                    },
                    'speed': 6,
                    'rule': requested_rule,
                    'randomize': False,
                })
                self.assertEqual(reset.status_code, 200)
                self.assertEqual(reset.get_json()['rule']['name'], expected_rule)

    def test_legacy_b2_s23_rule_names_are_rejected(self) -> None:
        for legacy_name, tiling_family in (
            ('cairo-life', 'cairo-pentagonal'),
            ('penrose-p2-life', 'penrose-p2-kite-dart'),
            ('ammann-beenker-life', 'ammann-beenker'),
        ):
            with self.subTest(rule=legacy_name):
                reset = self.client.post('/api/control/reset', json={
                    'topology_spec': {
                        'tiling_family': tiling_family,
                        'adjacency_mode': 'edge',
                        'width': 5,
                        'height': 4,
                        'patch_depth': 2,
                    },
                    'speed': 6,
                    'rule': legacy_name,
                    'randomize': False,
                })
                self.assertEqual(reset.status_code, 400)
                self.assertEqual(reset.get_json(), {'error': "'rule' must reference a known rule module."})


if __name__ == '__main__':
    unittest.main()
