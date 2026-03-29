from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

from playwright.sync_api import expect

try:
    from tests.e2e.support_browser import BrowserAppTestCase, parse_grid_summary_text
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.support_browser import BrowserAppTestCase, parse_grid_summary_text


class SharedUiFlowMixin:
    page_viewport = {"width": 1280, "height": 900}

    def setUp(self) -> None:
        super().setUp()
        self.goto_page(f"{self.host.base_url}/", wait_until="load")
        self._ensure_drawer_open()

    def _ensure_drawer_open(self) -> None:
        if self.page.locator("#control-drawer").get_attribute("data-open") != "true":
            self.page.click("#drawer-toggle-btn")
            expect(self.page.locator("#control-drawer")).to_have_attribute("data-open", "true")

    def _read_generation(self) -> int:
        return int((self.page.locator("#generation-text").text_content() or "0").strip())

    def _grid_summary(self):
        return parse_grid_summary_text(self.page.locator("#grid-size-text").text_content())

    def _click_canvas_center(self) -> None:
        canvas = self.page.locator("#grid")
        render_cell_size_text = canvas.get_attribute("data-render-cell-size")
        if render_cell_size_text is None:
            raise AssertionError("canvas did not report a rendered cell size")
        render_cell_size = float(render_cell_size_text)
        if render_cell_size <= 0:
            raise AssertionError(f"canvas reported an invalid rendered cell size: {render_cell_size_text!r}")

        grid_summary = self._grid_summary()
        if grid_summary.kind != "regular" or grid_summary.width is None or grid_summary.height is None:
            raise AssertionError(f"grid summary did not describe a regular board: {grid_summary!r}")

        gap = 0 if render_cell_size <= 6 else 1
        pitch = render_cell_size + gap
        target_x = gap + ((grid_summary.width // 2) * pitch) + (render_cell_size / 2)
        target_y = gap + ((grid_summary.height // 2) * pitch) + (render_cell_size / 2)
        canvas.click(position={"x": target_x, "y": target_y})

    def _paint_canvas_center(self) -> None:
        self._click_canvas_center()
        self._click_canvas_center()
        expect(self.page.locator("#undo-btn")).to_be_enabled()

    def _export_pattern_payload(self) -> dict[str, object]:
        with self.page.expect_download() as download_info:
            self.page.locator("#export-pattern-btn").evaluate("(node) => node.click()")
        download = download_info.value
        download_path = download.path()
        if download_path is None:
            raise AssertionError("pattern export did not produce a readable download")
        return json.loads(Path(download_path).read_text(encoding="utf-8"))

    def _write_clipboard_text(self, text: str) -> None:
        self.page.evaluate("(nextText) => navigator.clipboard.writeText(nextText)", text)

    def _read_clipboard_text(self) -> str:
        return str(self.page.evaluate("() => navigator.clipboard.readText()"))

    def test_rule_picker_updates_rule_ui(self) -> None:
        expect(self.page.locator("#tiling-family-select")).to_have_value("square")
        expect(self.page.locator("#rule-select")).to_have_value("conway")

        self.page.select_option("#rule-select", "highlife")

        expect(self.page.locator("#rule-select")).to_have_value("highlife")
        expect(self.page.locator("#rule-text")).to_contain_text("HighLife")
        expect(self.page.locator("#rule-description")).to_contain_text("6-neighbor")

    def test_export_pattern_after_painting_includes_cells(self) -> None:
        self._paint_canvas_center()

        exported_payload = self._export_pattern_payload()
        self.assertEqual(exported_payload["rule"], "conway")
        self.assertTrue(exported_payload["cells_by_id"])

    def test_penrose_topology_switch_updates_patch_depth_controls(self) -> None:
        self.page.select_option("#tiling-family-select", "penrose-p3-rhombs")

        expect(self.page.locator("#tiling-family-select")).to_have_value("penrose-p3-rhombs")
        expect(self.page.locator("#patch-depth-field")).to_be_visible()
        expect(self.page.locator("#grid-size-text")).to_contain_text("Depth")
        expect(self.page.locator("#adjacency-mode-field")).to_be_visible()

    def test_run_toggle_advances_generation_and_pauses(self) -> None:
        initial_generation = self._read_generation()

        self.page.click("#run-toggle-btn")

        expect(self.page.locator("#status-text")).to_have_text("Running")
        self.page.wait_for_function(
            """(initialGeneration) => {
                const generation = Number(document.getElementById("generation-text")?.textContent || "0");
                return generation > initialGeneration;
            }""",
            arg=initial_generation,
        )

        self.page.click("#run-toggle-btn")

        expect(self.page.locator("#status-text")).to_have_text("Paused")
        self.assertGreater(self._read_generation(), initial_generation)

    def test_overlay_drawer_toggle_hides_and_restores_inspector(self) -> None:
        expect(self.page.locator("#control-drawer")).to_have_attribute("data-open", "true")
        expect(self.page.locator("#drawer-toggle-btn")).to_have_text("Hide Inspector")

        self.page.click("#drawer-toggle-btn")
        expect(self.page.locator("#control-drawer")).to_have_attribute("data-open", "false")

        self.page.click("#drawer-toggle-btn")
        expect(self.page.locator("#control-drawer")).to_have_attribute("data-open", "true")

    def test_canvas_editor_click_updates_exported_pattern(self) -> None:
        self._paint_canvas_center()

        exported_payload = self._export_pattern_payload()
        self.assertTrue(exported_payload["cells_by_id"])

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

        expect(self.page.locator("#pattern-status")).to_contain_text("Imported pattern")
        expect(self.page.locator("#rule-select")).to_have_value("highlife")
        expect(self.page.locator("#grid-size-text")).to_have_text("8 x 5")

        exported_payload = self._export_pattern_payload()
        self.assertEqual(exported_payload["rule"], "highlife")
        self.assertEqual(exported_payload["cells_by_id"], payload["cells_by_id"])

    def test_copy_and_paste_pattern_roundtrip(self) -> None:
        self._paint_canvas_center()

        self.page.locator("#copy-pattern-btn").evaluate("(node) => node.click()")
        expect(self.page.locator("#pattern-status")).to_have_text("Copied pattern to clipboard.")

        copied_payload = json.loads(self._read_clipboard_text())
        self.assertEqual(copied_payload["rule"], "conway")
        self.assertTrue(copied_payload["cells_by_id"])

        self.page.click("#reset-btn")
        expect(self.page.locator("#status-text")).to_have_text("Paused")

        self._write_clipboard_text(json.dumps(copied_payload))
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.page.locator("#paste-pattern-btn").evaluate("(node) => node.click()")

        expect(self.page.locator("#pattern-status")).to_have_text("Pasted pattern from clipboard.")
        pasted_payload = self._export_pattern_payload()
        self.assertEqual(pasted_payload["cells_by_id"], copied_payload["cells_by_id"])


class CellularAutomatonUITests(SharedUiFlowMixin, BrowserAppTestCase):
    runtime_host_kind = "server"

    def test_server_restart_preserves_saved_state(self) -> None:
        if self.api is None:
            raise AssertionError("server browser tests require an API client")

        self.page.select_option("#rule-select", "highlife")
        expect(self.page.locator("#rule-select")).to_have_value("highlife")

        self.host.restart()
        self.goto_page(f"{self.host.base_url}/", wait_until="load")

        expect(self.page.locator("#rule-select")).to_have_value("highlife")
        self.assertEqual(self.api.get_state()["rule"]["name"], "highlife")


class StandaloneCellularAutomatonUITests(SharedUiFlowMixin, BrowserAppTestCase):
    runtime_host_kind = "standalone"

    def test_reload_restores_browser_persisted_state(self) -> None:
        self.page.select_option("#rule-select", "highlife")
        expect(self.page.locator("#rule-select")).to_have_value("highlife")

        self._paint_canvas_center()
        persisted_before_reload = self._export_pattern_payload()

        self.reload_page(wait_until="load")

        expect(self.page.locator("#rule-select")).to_have_value("highlife")
        persisted_after_reload = self._export_pattern_payload()
        self.assertEqual(persisted_after_reload["cells_by_id"], persisted_before_reload["cells_by_id"])


class StandaloneRuntimeFailureTests(BrowserAppTestCase):
    runtime_host_kind = "standalone"
    page_viewport = {"width": 1280, "height": 900}

    def test_worker_init_failure_shows_startup_error_banner(self) -> None:
        self.context.route("**/pyodide.js", lambda route: route.abort())
        self.page.goto(f"{self.host.base_url}/", wait_until="load")

        expect(self.page.locator("#app-startup-error")).to_be_visible()
        expect(self.page.locator("#app-startup-error")).to_contain_text(
            "Standalone runtime failed to initialize"
        )


if __name__ == "__main__":
    unittest.main()
