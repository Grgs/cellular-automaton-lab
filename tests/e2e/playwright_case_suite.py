from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

from playwright.sync_api import expect
from backend.payload_types import ResetControlRequestPayload, SimulationStatePayload, TopologySpecPayload

try:
    from tests.e2e.support_browser import BrowserAppTestCase
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.support_browser import BrowserAppTestCase


DEFAULT_RESET_PAYLOAD: ResetControlRequestPayload = {
    "topology_spec": {
        "tiling_family": "square",
        "adjacency_mode": "edge",
        "sizing_mode": "grid",
        "width": 30,
        "height": 20,
        "patch_depth": 0,
    },
    "speed": 5,
    "rule": "conway",
    "randomize": False,
}


class CellularAutomatonUITests(BrowserAppTestCase):
    page_viewport = {"width": 1280, "height": 900}

    def setUp(self) -> None:
        super().setUp()
        self.api.reset(DEFAULT_RESET_PAYLOAD)
        self.goto_page(f"{self.api.base_url}/", wait_until="load")

    def read_backend_state(self) -> SimulationStatePayload:
        return self.api.get_state()

    def wait_for_backend_state(
        self,
        predicate,
        *,
        timeout_seconds: float = 6.0,
    ) -> SimulationStatePayload:
        deadline = time.time() + timeout_seconds
        last_state: SimulationStatePayload | None = None
        while time.time() < deadline:
            last_state = self.read_backend_state()
            if predicate(last_state):
                return last_state
            time.sleep(0.1)
        raise AssertionError(f"backend state did not satisfy predicate in time: {json.dumps(last_state, indent=2)}")

    def _topology_spec(self, state: SimulationStatePayload) -> TopologySpecPayload:
        return state["topology_spec"]

    def _click_canvas_center(self) -> None:
        canvas = self.page.locator("#grid")
        render_cell_size_text = canvas.get_attribute("data-render-cell-size")
        if render_cell_size_text is None:
            raise AssertionError("canvas did not report a rendered cell size")
        render_cell_size = float(render_cell_size_text)
        if render_cell_size <= 0:
            raise AssertionError(f"canvas reported an invalid rendered cell size: {render_cell_size_text!r}")

        topology_spec = self._topology_spec(self.read_backend_state())
        width = int(topology_spec.get("width", 0))
        height = int(topology_spec.get("height", 0))
        if width <= 0 or height <= 0:
            raise AssertionError(f"backend topology dimensions were invalid: {topology_spec!r}")

        # Click the center of the middle cell, not the geometric midpoint of the
        # canvas. On square boards the raw canvas midpoint lands on a grid-line gap.
        gap = 0 if render_cell_size <= 6 else 1
        pitch = render_cell_size + gap
        target_x = gap + ((width // 2) * pitch) + (render_cell_size / 2)
        target_y = gap + ((height // 2) * pitch) + (render_cell_size / 2)
        canvas.click(position={"x": target_x, "y": target_y})

    def test_rule_picker_updates_backend_rule(self) -> None:
        expect(self.page.locator("#tiling-family-select")).to_have_value("square")
        expect(self.page.locator("#rule-select")).to_have_value("conway")

        self.page.select_option("#rule-select", "highlife")
        backend_state = self.wait_for_backend_state(
            lambda state: state.get("rule", {}).get("name") == "highlife"
        )

        expect(self.page.locator("#rule-select")).to_have_value("highlife")
        expect(self.page.locator("#rule-text")).to_contain_text("HighLife")
        expect(self.page.locator("#rule-description")).to_contain_text("6-neighbor")
        self.assertEqual(backend_state["rule"]["name"], "highlife")

    def test_showcase_pattern_loads_demo(self) -> None:
        self.page.click("#showcase-whirlpool-btn")
        backend_state = self.wait_for_backend_state(
            lambda state: state.get("rule", {}).get("name") == "whirlpool"
            and any(cell != 0 for cell in state.get("cell_states", []))
        )

        expect(self.page.locator("#pattern-status")).to_have_text("Loaded Whirlpool demo.")
        self.assertIn(4, backend_state["cell_states"])

    def test_penrose_topology_switch_updates_patch_depth_controls(self) -> None:
        self.page.select_option("#tiling-family-select", "penrose-p3-rhombs")
        backend_state = self.wait_for_backend_state(
            lambda state: self._topology_spec(state).get("tiling_family") == "penrose-p3-rhombs"
        )

        expect(self.page.locator("#patch-depth-field")).to_be_visible()
        expect(self.page.locator("#grid-size-text")).to_contain_text("Depth")
        self.assertEqual(self._topology_spec(backend_state)["tiling_family"], "penrose-p3-rhombs")
        self.assertEqual(self._topology_spec(backend_state)["patch_depth"], 4)

    def test_server_restart_preserves_saved_state(self) -> None:
        self.page.select_option("#rule-select", "highlife")
        self.wait_for_backend_state(lambda state: state.get("rule", {}).get("name") == "highlife")

        self.server.restart()
        self.goto_page(f"{self.api.base_url}/", wait_until="load")
        backend_state = self.wait_for_backend_state(
            lambda state: state.get("rule", {}).get("name") == "highlife"
        )

        expect(self.page.locator("#rule-select")).to_have_value("highlife")
        self.assertEqual(backend_state["rule"]["name"], "highlife")

    def test_overlay_drawer_toggle_hides_and_restores_inspector(self) -> None:
        expect(self.page.locator("#control-drawer")).to_have_attribute("data-open", "true")
        expect(self.page.locator("#drawer-toggle-btn")).to_have_text("Hide Inspector")

        self.page.click("#drawer-toggle-btn")
        expect(self.page.locator("#control-drawer")).to_have_attribute("data-open", "false")

        self.page.click("#drawer-toggle-btn")
        expect(self.page.locator("#control-drawer")).to_have_attribute("data-open", "true")

    def test_canvas_editor_click_hides_quick_start_hint(self) -> None:
        expect(self.page.locator("#quick-start-hint")).to_be_visible()
        self._click_canvas_center()
        expect(self.page.locator("#quick-start-hint")).to_be_hidden()

    def test_pattern_import_replaces_board(self) -> None:
        payload = {
            "format": "cellular-automaton-lab-pattern",
            "version": 5,
            "topology_spec": {
                "tiling_family": "square",
                "adjacency_mode": "edge",
                "width": 8,
                "height": 5,
                "patch_depth": 0,
            },
            "rule": "highlife",
            "cells_by_id": {
                "c:1:1": 1,
                "c:2:1": 1,
                "c:3:1": 1,
            },
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as pattern_file:
            pattern_file.write(json.dumps(payload))
            pattern_path = pattern_file.name
        self.addCleanup(lambda: Path(pattern_path).unlink(missing_ok=True))
        self.page.locator("#pattern-import-input").set_input_files(pattern_path)

        backend_state = self.wait_for_backend_state(
            lambda state: (
                state.get("rule", {}).get("name") == "highlife"
                and self._topology_spec(state).get("width") == 8
                and self._topology_spec(state).get("height") == 5
            )
        )

        expect(self.page.locator("#pattern-status")).to_contain_text("Imported pattern")
        expect(self.page.locator("#rule-select")).to_have_value("highlife")
        expect(self.page.locator("#grid-size-text")).to_have_text("8 x 5")
        self.assertEqual(self._topology_spec(backend_state)["width"], 8)
        self.assertEqual(self._topology_spec(backend_state)["height"], 5)


if __name__ == "__main__":
    unittest.main()
