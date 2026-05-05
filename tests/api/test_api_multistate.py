import sys
import unittest
from pathlib import Path

try:
    from tests.api.support import ApiTestCase
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.api.support import ApiTestCase


class ApiMultistateTests(ApiTestCase):
    def test_random_reset_is_rejected_for_nonrandomizable_rules(self) -> None:
        bad_wireworld = self.client.post(
            "/api/control/reset", json={"rule": "wireworld", "randomize": True}
        )
        bad_whirlpool = self.client.post(
            "/api/control/reset", json={"rule": "whirlpool", "randomize": True}
        )
        bad_hexwhirlpool = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "hex",
                    "adjacency_mode": "edge",
                    "width": 10,
                    "height": 6,
                    "patch_depth": 0,
                },
                "rule": "hexwhirlpool",
                "randomize": True,
            },
        )

        self.assertEqual(bad_wireworld.status_code, 400)
        self.assertEqual(bad_whirlpool.status_code, 400)
        self.assertEqual(bad_hexwhirlpool.status_code, 400)

    def test_wireworld_cells_accept_multistate_values(self) -> None:
        self.client.post("/api/config", json={"rule": "wireworld"})

        single = self.client.post("/api/cells/set", json={"id": "c:2:3", "state": 3})
        batch = self.client.post(
            "/api/cells/set-many",
            json={
                "cells": [
                    {"id": "c:4:1", "state": 1},
                    {"id": "c:5:2", "state": 2},
                ]
            },
        )
        toggle_on = self.client.post("/api/cells/toggle", json={"id": "c:1:1"})
        toggle_off = self.client.post("/api/cells/toggle", json={"id": "c:1:1"})
        invalid_state = self.client.post("/api/cells/set", json={"id": "c:0:0", "state": 9})

        self.assertEqual(single.status_code, 200)
        self.assertEqual(batch.status_code, 200)
        self.assertEqual(toggle_on.status_code, 200)
        self.assertEqual(toggle_off.status_code, 200)
        self.assertEqual(invalid_state.status_code, 400)

        payload = batch.get_json()
        self.assert_wireworld_rule(payload)
        self.assertEqual(self.regular_cell_state(payload, 2, 3), 3)
        self.assertEqual(self.regular_cell_state(payload, 4, 1), 1)
        self.assertEqual(self.regular_cell_state(payload, 5, 2), 2)
        self.assertEqual(self.regular_cell_state(toggle_on.get_json(), 1, 1), 3)
        self.assertEqual(self.regular_cell_state(toggle_off.get_json(), 1, 1), 0)

    def test_whirlpool_rule_metadata_multistate_values_and_toggle_behavior(self) -> None:
        self.client.post("/api/config", json={"rule": "whirlpool"})

        single = self.client.post("/api/cells/set", json={"id": "c:2:3", "state": 4})
        batch = self.client.post(
            "/api/cells/set-many",
            json={
                "cells": [
                    {"id": "c:4:1", "state": 1},
                    {"id": "c:5:2", "state": 2},
                    {"id": "c:0:4", "state": 3},
                ]
            },
        )
        toggle_on = self.client.post("/api/cells/toggle", json={"id": "c:1:1"})
        toggle_off = self.client.post("/api/cells/toggle", json={"id": "c:1:1"})

        self.assertEqual(single.status_code, 200)
        self.assertEqual(batch.status_code, 200)
        self.assertEqual(toggle_on.status_code, 200)
        self.assertEqual(toggle_off.status_code, 200)

        payload = self.get_state()
        self.assert_whirlpool_rule(payload)
        self.assertEqual(self.regular_cell_state(payload, 2, 3), 4)
        self.assertEqual(self.regular_cell_state(payload, 4, 1), 1)
        self.assertEqual(self.regular_cell_state(payload, 5, 2), 2)
        self.assertEqual(self.regular_cell_state(payload, 0, 4), 3)
        self.assertEqual(self.regular_cell_state(toggle_on.get_json(), 1, 1), 1)
        self.assertEqual(self.regular_cell_state(toggle_off.get_json(), 1, 1), 0)

    def test_whirlpool_source_cells_persist_and_emit_one_neighbor(self) -> None:
        self.reset_simulation(width=9, height=9, rule="whirlpool", randomize=False)
        painted = self.client.post("/api/cells/set", json={"id": "c:6:4", "state": 4})
        self.assertEqual(painted.status_code, 200)

        stepped = self.client.post("/api/control/step")
        self.assertEqual(stepped.status_code, 200)
        payload = stepped.get_json()

        self.assert_whirlpool_rule(payload)
        self.assertEqual(self.regular_cell_state(payload, 6, 4), 4)
        self.assertEqual(self.regular_cell_state(payload, 7, 5), 1)

    def test_whirlpool_eye_cells_reignite_instead_of_dying_when_supported(self) -> None:
        self.reset_simulation(width=9, height=9, rule="whirlpool", randomize=False)
        painted = self.client.post(
            "/api/cells/set-many",
            json={
                "cells": [
                    {"id": "c:4:4", "state": 3},
                    {"id": "c:4:3", "state": 1},
                ]
            },
        )
        self.assertEqual(painted.status_code, 200)

        stepped = self.client.post("/api/control/step")
        self.assertEqual(stepped.status_code, 200)
        payload = stepped.get_json()

        self.assert_whirlpool_rule(payload)
        self.assertEqual(self.regular_cell_state(payload, 4, 4), 1)

    def test_hexwhirlpool_eye_cells_reignite_instead_of_dying_when_supported(self) -> None:
        reset = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "hex",
                    "adjacency_mode": "edge",
                    "width": 9,
                    "height": 7,
                    "patch_depth": 0,
                },
                "speed": 5,
                "rule": "hexwhirlpool",
                "randomize": False,
            },
        )
        self.assertEqual(reset.status_code, 200)

        painted = self.client.post(
            "/api/cells/set-many",
            json={
                "cells": [
                    {"id": "c:1:0", "state": 3},
                    {"id": "c:2:0", "state": 1},
                ]
            },
        )
        self.assertEqual(painted.status_code, 200)

        stepped = self.client.post("/api/control/step")
        self.assertEqual(stepped.status_code, 200)
        payload = stepped.get_json()

        self.assert_hexwhirlpool_rule(payload)
        self.assertEqual(self.regular_cell_state(payload, 1, 0), 1)

    def test_hexwhirlpool_source_cells_persist_and_emit_one_neighbor(self) -> None:
        reset = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "hex",
                    "adjacency_mode": "edge",
                    "width": 9,
                    "height": 7,
                    "patch_depth": 0,
                },
                "speed": 5,
                "rule": "hexwhirlpool",
                "randomize": False,
            },
        )
        self.assertEqual(reset.status_code, 200)

        painted = self.client.post("/api/cells/set", json={"id": "c:5:4", "state": 4})
        self.assertEqual(painted.status_code, 200)

        stepped = self.client.post("/api/control/step")
        self.assertEqual(stepped.status_code, 200)
        payload = stepped.get_json()

        self.assert_hexwhirlpool_rule(payload)
        self.assertEqual(self.regular_cell_state(payload, 5, 4), 4)
        self.assertEqual(self.regular_cell_state(payload, 4, 5), 1)

    def test_switching_between_wireworld_and_highlife_coerces_grid_and_updates_rule_metadata(
        self,
    ) -> None:
        self.client.post("/api/config", json={"rule": "wireworld"})
        painted = self.client.post(
            "/api/cells/set-many",
            json={
                "cells": [
                    {"id": "c:1:1", "state": 3},
                    {"id": "c:2:1", "state": 2},
                    {"id": "c:3:1", "state": 1},
                ]
            },
        )
        self.assertEqual(painted.status_code, 200)

        highlife = self.client.post("/api/config", json={"rule": "highlife"})
        self.assertEqual(highlife.status_code, 200)
        highlife_payload = highlife.get_json()
        self.assertEqual(highlife_payload["rule"]["name"], "highlife")
        self.assertEqual(highlife_payload["rule"]["default_paint_state"], 1)
        self.assertTrue(highlife_payload["rule"]["supports_randomize"])
        self.assertEqual(
            [cell_state["value"] for cell_state in highlife_payload["rule"]["states"]], [0, 1]
        )
        self.assertEqual(self.regular_cell_state(highlife_payload, 1, 1), 0)
        self.assertEqual(self.regular_cell_state(highlife_payload, 2, 1), 0)
        self.assertEqual(self.regular_cell_state(highlife_payload, 3, 1), 1)

        wireworld = self.client.post("/api/config", json={"rule": "wireworld"})
        self.assertEqual(wireworld.status_code, 200)
        wireworld_payload = wireworld.get_json()
        self.assert_wireworld_rule(wireworld_payload)
        self.assertEqual(self.regular_cell_state(wireworld_payload, 1, 1), 0)
        self.assertEqual(self.regular_cell_state(wireworld_payload, 2, 1), 0)
        self.assertEqual(self.regular_cell_state(wireworld_payload, 3, 1), 1)

    def test_wireworld_step_applies_multistate_transitions(self) -> None:
        self.client.post("/api/config", json={"rule": "wireworld"})
        painted = self.client.post(
            "/api/cells/set-many",
            json={
                "cells": [
                    {"id": "c:1:1", "state": 3},
                    {"id": "c:2:1", "state": 1},
                    {"id": "c:3:1", "state": 2},
                ]
            },
        )
        self.assertEqual(painted.status_code, 200)

        stepped = self.client.post("/api/control/step")
        self.assertEqual(stepped.status_code, 200)
        payload = stepped.get_json()

        self.assertEqual(payload["generation"], 1)
        self.assertEqual(payload["rule"]["name"], "wireworld")
        self.assertEqual(self.regular_cell_state(payload, 1, 1), 1)
        self.assertEqual(self.regular_cell_state(payload, 2, 1), 2)
        self.assertEqual(self.regular_cell_state(payload, 3, 1), 3)

    def test_invalid_wireworld_batch_does_not_apply_partial_updates(self) -> None:
        self.client.post("/api/config", json={"rule": "wireworld"})
        before = self.get_state()

        invalid_batch = self.client.post(
            "/api/cells/set-many",
            json={
                "cells": [
                    {"id": "c:1:1", "state": 3},
                    {"id": "c:2:1", "state": 9},
                ]
            },
        )
        after = self.get_state()

        self.assertEqual(invalid_batch.status_code, 400)
        self.assertEqual(self.cells_by_id(after), self.cells_by_id(before))

    def test_square_rules_can_now_be_selected_on_hex_geometry(self) -> None:
        reset = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "hex",
                    "adjacency_mode": "edge",
                    "width": 8,
                    "height": 6,
                    "patch_depth": 0,
                },
                "speed": 5,
                "randomize": False,
            },
        )
        self.assertEqual(reset.status_code, 200)

        response = self.client.post("/api/config", json={"rule": "conway"})
        self.assertEqual(response.status_code, 200)

        state = self.get_state()
        self.assertEqual(state["topology_spec"]["tiling_family"], "hex")
        self.assertEqual(state["rule"]["name"], "conway")

    def test_trilife_can_be_selected_on_triangle_and_square(self) -> None:
        triangle_reset = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "triangle",
                    "adjacency_mode": "edge",
                    "width": 9,
                    "height": 7,
                    "patch_depth": 0,
                },
                "speed": 5,
                "randomize": False,
            },
        )
        self.assertEqual(triangle_reset.status_code, 200)
        self.assert_trilife_rule(triangle_reset.get_json())

        triangle_switch = self.client.post("/api/config", json={"rule": "trilife"})
        self.assertEqual(triangle_switch.status_code, 200)
        self.assert_trilife_rule(triangle_switch.get_json())

        square_reset = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "square",
                    "adjacency_mode": "edge",
                    "width": 9,
                    "height": 7,
                    "patch_depth": 0,
                },
                "speed": 5,
                "rule": "conway",
                "randomize": False,
            },
        )
        self.assertEqual(square_reset.status_code, 200)

        square_switch = self.client.post("/api/config", json={"rule": "trilife"})
        self.assertEqual(square_switch.status_code, 200)
        self.assertEqual(square_switch.get_json()["rule"]["name"], "trilife")

    def test_hexwhirlpool_alias_selects_whirlpool_on_hex_and_square(self) -> None:
        hex_reset = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "hex",
                    "adjacency_mode": "edge",
                    "width": 9,
                    "height": 7,
                    "patch_depth": 0,
                },
                "speed": 5,
                "randomize": False,
            },
        )
        self.assertEqual(hex_reset.status_code, 200)
        self.assert_hexlife_rule(hex_reset.get_json())

        hex_switch = self.client.post("/api/config", json={"rule": "hexwhirlpool"})
        self.assertEqual(hex_switch.status_code, 200)
        self.assert_hexwhirlpool_rule(hex_switch.get_json())
        self.assertEqual(hex_switch.get_json()["topology_spec"]["width"], 9)
        self.assertEqual(hex_switch.get_json()["topology_spec"]["height"], 7)

        square_reset = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "square",
                    "adjacency_mode": "edge",
                    "width": 9,
                    "height": 7,
                    "patch_depth": 0,
                },
                "speed": 5,
                "rule": "conway",
                "randomize": False,
            },
        )
        self.assertEqual(square_reset.status_code, 200)

        square_switch = self.client.post("/api/config", json={"rule": "hexwhirlpool"})
        self.assertEqual(square_switch.status_code, 200)
        self.assertEqual(square_switch.get_json()["rule"]["name"], "whirlpool")

    def test_reset_preserves_rectangular_whirlpool_dimensions(self) -> None:
        square_rule = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "square",
                    "adjacency_mode": "edge",
                    "width": 12,
                    "height": 8,
                    "patch_depth": 0,
                },
                "speed": 5,
                "rule": "whirlpool",
                "randomize": False,
            },
        )
        hex_rule = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "hex",
                    "adjacency_mode": "edge",
                    "width": 11,
                    "height": 7,
                    "patch_depth": 0,
                },
                "speed": 5,
                "rule": "hexwhirlpool",
                "randomize": False,
            },
        )

        self.assertEqual(square_rule.status_code, 200)
        self.assertEqual(square_rule.get_json()["topology_spec"]["width"], 12)
        self.assertEqual(square_rule.get_json()["topology_spec"]["height"], 8)
        self.assertEqual(hex_rule.status_code, 200)
        self.assertEqual(hex_rule.get_json()["topology_spec"]["width"], 11)
        self.assertEqual(hex_rule.get_json()["topology_spec"]["height"], 7)

    def test_switching_into_whirlpool_rule_preserves_rectangular_dimensions_and_overlap(
        self,
    ) -> None:
        self.reset_simulation(width=10, height=6, rule="conway", randomize=False)
        painted = self.client.post(
            "/api/cells/set-many",
            json={
                "cells": [
                    {"id": "c:1:1", "state": 1},
                    {"id": "c:5:5", "state": 1},
                    {"id": "c:8:1", "state": 1},
                ]
            },
        )
        self.assertEqual(painted.status_code, 200)

        whirlpool = self.client.post("/api/config", json={"rule": "whirlpool"})
        self.assertEqual(whirlpool.status_code, 200)
        payload = whirlpool.get_json()

        self.assert_whirlpool_rule(payload)
        self.assertEqual(payload["topology_spec"]["width"], 10)
        self.assertEqual(payload["topology_spec"]["height"], 6)
        self.assertEqual(self.regular_cell_state(payload, 1, 1), 1)
        self.assertEqual(self.regular_cell_state(payload, 5, 5), 1)
        self.assertEqual(self.regular_cell_state(payload, 8, 1), 1)
        self.assertEqual(sum(self.cells_by_id(payload).values()), 3)

    def test_archlife_can_be_selected_on_archimedean_and_square(self) -> None:
        arch_reset = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "archimedean-4-8-8",
                    "adjacency_mode": "edge",
                    "width": 5,
                    "height": 5,
                    "patch_depth": 0,
                },
                "speed": 5,
                "randomize": False,
            },
        )
        self.assertEqual(arch_reset.status_code, 200)
        self.assert_archlife_rule(arch_reset.get_json())

        arch_switch = self.client.post("/api/config", json={"rule": "archlife488"})
        self.assertEqual(arch_switch.status_code, 200)
        self.assert_archlife_rule(arch_switch.get_json())

        square_reset = self.client.post(
            "/api/control/reset",
            json={
                "topology_spec": {
                    "tiling_family": "square",
                    "adjacency_mode": "edge",
                    "width": 9,
                    "height": 7,
                    "patch_depth": 0,
                },
                "speed": 5,
                "rule": "conway",
                "randomize": False,
            },
        )
        self.assertEqual(square_reset.status_code, 200)

        square_switch = self.client.post("/api/config", json={"rule": "archlife488"})
        self.assertEqual(square_switch.status_code, 200)
        self.assertEqual(square_switch.get_json()["rule"]["name"], "archlife488")


if __name__ == "__main__":
    unittest.main()
