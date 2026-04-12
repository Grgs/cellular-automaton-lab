from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, ClassVar, Protocol, cast

from playwright.sync_api import Response, ViewportSize
from playwright.sync_api import expect

try:
    from tests.e2e.browser_support.bootstrap import BrowserAppTestCase, WaitUntilState
    from tests.e2e.browser_support.diagnostics import GridSummary, parse_grid_summary_text
    from tests.e2e.support_runtime_host import BrowserRuntimeHost
    from tests.e2e.support_server import JsonApiClient
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.browser_support.bootstrap import BrowserAppTestCase, WaitUntilState
    from tests.e2e.browser_support.diagnostics import GridSummary, parse_grid_summary_text
    from tests.e2e.support_runtime_host import BrowserRuntimeHost
    from tests.e2e.support_server import JsonApiClient


class SharedUiFlowCase(Protocol):
    page_viewport: ClassVar[ViewportSize | None]
    page: Any
    host: BrowserRuntimeHost
    api: JsonApiClient | None

    def goto_page(
        self,
        url: str,
        *,
        wait_until: WaitUntilState | None = None,
        timeout: float | None = None,
    ) -> Response | None: ...

    def reload_page(
        self,
        *,
        wait_until: WaitUntilState | None = None,
        timeout: float | None = None,
    ) -> Response | None: ...

    def addCleanup(self, function: Any, /, *args: Any, **kwargs: Any) -> None: ...
    def assertEqual(self, first: Any, second: Any, msg: str | None = None) -> None: ...
    def assertTrue(self, expr: Any, msg: str | None = None) -> None: ...
    def assertGreater(self, first: Any, second: Any, msg: str | None = None) -> None: ...
    def assertGreaterEqual(self, first: Any, second: Any, msg: str | None = None) -> None: ...


class SharedUiFlowMixin:
    def _case(self) -> SharedUiFlowCase:
        return cast(SharedUiFlowCase, self)

    def initialize_shared_ui_flow(self) -> None:
        case = self._case()
        case.goto_page(f"{case.host.base_url}/", wait_until="load")
        self._ensure_drawer_open()

    def _expect(self, selector: str) -> Any:
        case = self._case()
        return cast(Any, expect(case.page.locator(selector)))

    def _ensure_drawer_open(self) -> None:
        case = self._case()
        if case.page.locator("#control-drawer").get_attribute("data-open") != "true":
            case.page.click("#drawer-toggle-btn")
            self._expect("#control-drawer").to_have_attribute("data-open", "true")

    def _read_generation(self) -> int:
        case = self._case()
        return int((case.page.locator("#generation-text").text_content() or "0").strip())

    def _grid_summary(self) -> GridSummary:
        case = self._case()
        return parse_grid_summary_text(case.page.locator("#grid-size-text").text_content())

    def _click_canvas_center(self) -> None:
        case = self._case()
        canvas = case.page.locator("#grid")
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
        self._expect("#undo-btn").to_be_enabled()

    def _canvas_visual_summary(self) -> dict[str, object]:
        case = self._case()
        summary = case.page.evaluate(
            """() => {
                const canvas = document.getElementById("grid");
                if (!(canvas instanceof HTMLCanvasElement)) {
                    throw new Error("grid canvas is missing");
                }
                const context = canvas.getContext("2d");
                if (!context) {
                    throw new Error("2d canvas context is unavailable");
                }
                const image = context.getImageData(0, 0, canvas.width, canvas.height);
                const { data, width, height } = image;
                let minX = width;
                let minY = height;
                let maxX = -1;
                let maxY = -1;
                const dominantFillColors = new Map();

                for (let y = 0; y < height; y += 1) {
                    for (let x = 0; x < width; x += 1) {
                        const index = ((y * width) + x) * 4;
                        const alpha = data[index + 3];
                        if (alpha < 32) {
                            continue;
                        }
                        if (x < minX) minX = x;
                        if (x > maxX) maxX = x;
                        if (y < minY) minY = y;
                        if (y > maxY) maxY = y;

                        if (alpha < 250) {
                            continue;
                        }
                        const r = data[index];
                        const g = data[index + 1];
                        const b = data[index + 2];
                        if (r < 140 || g < 100 || b < 60) {
                            continue;
                        }
                        const key = `${r},${g},${b}`;
                        dominantFillColors.set(key, (dominantFillColors.get(key) || 0) + 1);
                    }
                }

                return {
                    canvasWidth: width,
                    canvasHeight: height,
                    coverageWidthRatio: maxX >= minX ? (maxX - minX + 1) / width : 0,
                    coverageHeightRatio: maxY >= minY ? (maxY - minY + 1) / height : 0,
                    dominantFillColors: Array.from(dominantFillColors.entries())
                        .filter(([, count]) => count >= 100)
                        .sort((left, right) => right[1] - left[1]),
                };
            }""",
        )
        return cast(dict[str, object], summary)

    def _wait_for_patch_render_complete(self) -> None:
        case = self._case()
        case.page.wait_for_function(
            """() => {
                const grid = document.getElementById("grid");
                const overlay = document.getElementById("blocking-activity-overlay");
                const renderCellSize = Number(grid?.getAttribute("data-render-cell-size") || "0");
                const overlayHidden = overlay instanceof HTMLElement
                    ? overlay.hidden || overlay.getAttribute("hidden") !== null
                    : true;
                return Number.isFinite(renderCellSize) && renderCellSize > 0 && overlayHidden;
            }""",
        )

    def _select_tiling_family_and_wait_for_reset(
        self,
        tiling_family: str,
        *,
        timeout_ms: int = 60_000,
    ) -> None:
        case = self._case()
        if case.api is None:
            case.page.select_option("#tiling-family-select", tiling_family)
            case.page.wait_for_function(
                """(nextTilingFamily) => {
                    const select = document.getElementById("tiling-family-select");
                    return select instanceof HTMLSelectElement && select.value === nextTilingFamily;
                }""",
                arg=tiling_family,
                timeout=timeout_ms,
            )
            return
        with case.page.expect_response(
            lambda response: response.request.method == "POST" and "/api/control/reset" in response.url,
            timeout=timeout_ms,
        ) as response_info:
            case.page.select_option("#tiling-family-select", tiling_family)
        case.assertEqual(response_info.value.status, 200)

    def _wait_for_canvas_visual_patch(
        self,
        *,
        minimum_fill_colors: int,
        minimum_coverage_width_ratio: float,
        minimum_coverage_height_ratio: float,
    ) -> None:
        case = self._case()
        case.page.wait_for_function(
            """({ minimumFillColors, minimumCoverageWidthRatio, minimumCoverageHeightRatio }) => {
                const canvas = document.getElementById("grid");
                if (!(canvas instanceof HTMLCanvasElement)) {
                    return false;
                }
                const context = canvas.getContext("2d");
                if (!context) {
                    return false;
                }
                const overlay = document.getElementById("blocking-activity-overlay");
                if (overlay instanceof HTMLElement && !overlay.hidden) {
                    return false;
                }
                const image = context.getImageData(0, 0, canvas.width, canvas.height);
                const { data, width, height } = image;
                let minX = width;
                let minY = height;
                let maxX = -1;
                let maxY = -1;
                const dominantFillColors = new Map();

                for (let y = 0; y < height; y += 1) {
                    for (let x = 0; x < width; x += 1) {
                        const index = ((y * width) + x) * 4;
                        const alpha = data[index + 3];
                        if (alpha < 32) {
                            continue;
                        }
                        if (x < minX) minX = x;
                        if (x > maxX) maxX = x;
                        if (y < minY) minY = y;
                        if (y > maxY) maxY = y;

                        if (alpha < 250) {
                            continue;
                        }
                        const r = data[index];
                        const g = data[index + 1];
                        const b = data[index + 2];
                        if (r < 140 || g < 100 || b < 60) {
                            continue;
                        }
                        const key = `${r},${g},${b}`;
                        dominantFillColors.set(key, (dominantFillColors.get(key) || 0) + 1);
                    }
                }

                const dominantCount = Array.from(dominantFillColors.values()).filter((count) => count >= 100).length;
                const coverageWidthRatio = maxX >= minX ? (maxX - minX + 1) / width : 0;
                const coverageHeightRatio = maxY >= minY ? (maxY - minY + 1) / height : 0;
                return dominantCount >= minimumFillColors
                    && coverageWidthRatio > minimumCoverageWidthRatio
                    && coverageHeightRatio > minimumCoverageHeightRatio;
            }""",
            arg={
                "minimumFillColors": minimum_fill_colors,
                "minimumCoverageWidthRatio": minimum_coverage_width_ratio,
                "minimumCoverageHeightRatio": minimum_coverage_height_ratio,
            },
        )

    def _assert_browser_visible_aperiodic_patch(
        self,
        *,
        minimum_fill_colors: int,
        minimum_coverage_width_ratio: float = 0.75,
        minimum_coverage_height_ratio: float = 0.75,
    ) -> None:
        self._wait_for_patch_render_complete()
        self._wait_for_canvas_visual_patch(
            minimum_fill_colors=minimum_fill_colors,
            minimum_coverage_width_ratio=minimum_coverage_width_ratio,
            minimum_coverage_height_ratio=minimum_coverage_height_ratio,
        )
        case = self._case()
        summary = self._canvas_visual_summary()
        dominant_fill_colors = cast(list[list[object]], summary["dominantFillColors"])
        coverage_width_ratio = cast(float, summary["coverageWidthRatio"])
        coverage_height_ratio = cast(float, summary["coverageHeightRatio"])
        case.assertGreater(coverage_width_ratio, minimum_coverage_width_ratio)
        case.assertGreater(coverage_height_ratio, minimum_coverage_height_ratio)
        case.assertGreaterEqual(len(dominant_fill_colors), minimum_fill_colors)

    def _export_pattern_payload(self) -> dict[str, object]:
        case = self._case()
        with case.page.expect_download() as download_info:
            case.page.locator("#export-pattern-btn").evaluate("(node) => node.click()")
        download = download_info.value
        download_path = download.path()
        if download_path is None:
            raise AssertionError("pattern export did not produce a readable download")
        return json.loads(Path(download_path).read_text(encoding="utf-8"))

    def _write_clipboard_text(self, text: str) -> None:
        case = self._case()
        case.page.evaluate("(nextText) => navigator.clipboard.writeText(nextText)", text)

    def _read_clipboard_text(self) -> str:
        case = self._case()
        return str(case.page.evaluate("() => navigator.clipboard.readText()"))

    def test_rule_picker_updates_rule_ui(self) -> None:
        case = self._case()
        self._expect("#tiling-family-select").to_have_value("square")
        self._expect("#rule-select").to_have_value("conway")

        case.page.select_option("#rule-select", "highlife")

        self._expect("#rule-select").to_have_value("highlife")
        self._expect("#rule-text").to_contain_text("HighLife")
        self._expect("#rule-description").to_contain_text("6-neighbor")

    def test_export_pattern_after_painting_includes_cells(self) -> None:
        case = self._case()
        self._paint_canvas_center()

        exported_payload = self._export_pattern_payload()
        case.assertEqual(exported_payload["rule"], "conway")
        case.assertTrue(exported_payload["cells_by_id"])

    def test_penrose_topology_switch_updates_patch_depth_controls(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "penrose-p3-rhombs")

        self._expect("#tiling-family-select").to_have_value("penrose-p3-rhombs")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._expect("#adjacency-mode-field").to_be_visible()

    def test_spectre_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "spectre")

        self._expect("#tiling-family-select").to_have_value("spectre")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(
            minimum_fill_colors=1,
            minimum_coverage_width_ratio=0.95,
            minimum_coverage_height_ratio=0.95,
        )

    def test_taylor_socolar_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "taylor-socolar")

        self._expect("#tiling-family-select").to_have_value("taylor-socolar")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(
            minimum_fill_colors=1,
            minimum_coverage_width_ratio=0.9,
            minimum_coverage_height_ratio=0.9,
        )

    def test_sphinx_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "sphinx")

        self._expect("#tiling-family-select").to_have_value("sphinx")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(
            minimum_fill_colors=1,
            minimum_coverage_width_ratio=0.9,
            minimum_coverage_height_ratio=0.9,
        )

    def test_chair_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "chair")

        self._expect("#tiling-family-select").to_have_value("chair")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._wait_for_patch_render_complete()

    def test_chair_topology_switch_renders_browser_visible_multicolor_patch(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "chair")

        self._expect("#tiling-family-select").to_have_value("chair")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=4)

    def test_robinson_triangles_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "robinson-triangles")

        self._expect("#tiling-family-select").to_have_value("robinson-triangles")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=2)

    def test_hat_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "hat-monotile")

        self._expect("#tiling-family-select").to_have_value("hat-monotile")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=2)

    def test_tuebingen_triangle_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "tuebingen-triangle")

        self._expect("#tiling-family-select").to_have_value("tuebingen-triangle")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=2)

    def test_square_triangle_topology_switch_renders_aperiodic_patch(self) -> None:
        self._select_tiling_family_and_wait_for_reset("square-triangle")

        self._expect("#tiling-family-select").to_have_value("square-triangle")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=3)

    def test_shield_topology_switch_renders_aperiodic_patch(self) -> None:
        self._select_tiling_family_and_wait_for_reset("shield")

        self._expect("#tiling-family-select").to_have_value("shield")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=2)

    def test_pinwheel_topology_switch_renders_aperiodic_patch(self) -> None:
        self._select_tiling_family_and_wait_for_reset("pinwheel")

        self._expect("#tiling-family-select").to_have_value("pinwheel")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=2)

    def test_deltoidal_hexagonal_topology_switch_renders_periodic_patch(self) -> None:
        case = self._case()
        case.page.select_option("#tiling-family-select", "deltoidal-hexagonal")

        self._expect("#tiling-family-select").to_have_value("deltoidal-hexagonal")
        self._expect("#patch-depth-field").not_to_be_visible()
        self._expect("#grid-size-text").not_to_contain_text("Depth")
        case.page.wait_for_function(
            """() => {
                const value = Number(document.getElementById("grid")?.getAttribute("data-render-cell-size") || "0");
                return Number.isFinite(value) && value > 0;
            }""",
        )

    def test_run_toggle_advances_generation_and_pauses(self) -> None:
        case = self._case()
        initial_generation = self._read_generation()

        case.page.click("#run-toggle-btn")

        self._expect("#status-text").to_have_text("Running")
        case.page.wait_for_function(
            """(initialGeneration) => {
                const generation = Number(document.getElementById("generation-text")?.textContent || "0");
                return generation > initialGeneration;
            }""",
            arg=initial_generation,
        )

        case.page.click("#run-toggle-btn")

        self._expect("#status-text").to_have_text("Paused")
        case.assertGreater(self._read_generation(), initial_generation)

    def test_overlay_drawer_toggle_hides_and_restores_inspector(self) -> None:
        case = self._case()
        self._expect("#control-drawer").to_have_attribute("data-open", "true")
        self._expect("#drawer-toggle-btn").to_have_text("Hide Inspector")

        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "false")

        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "true")

    def test_canvas_editor_click_updates_exported_pattern(self) -> None:
        case = self._case()
        self._paint_canvas_center()

        exported_payload = self._export_pattern_payload()
        case.assertTrue(exported_payload["cells_by_id"])

    def test_pattern_import_replaces_board(self) -> None:
        case = self._case()
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
        case.addCleanup(lambda: Path(pattern_path).unlink(missing_ok=True))
        case.page.locator("#pattern-import-input").set_input_files(pattern_path)

        self._expect("#pattern-status").to_contain_text("Imported pattern")
        self._expect("#rule-select").to_have_value("highlife")
        self._expect("#grid-size-text").to_have_text("8 x 5")

        exported_payload = self._export_pattern_payload()
        case.assertEqual(exported_payload["rule"], "highlife")
        case.assertEqual(exported_payload["cells_by_id"], payload["cells_by_id"])

    def test_copy_and_paste_pattern_roundtrip(self) -> None:
        case = self._case()
        self._paint_canvas_center()

        case.page.locator("#copy-pattern-btn").evaluate("(node) => node.click()")
        self._expect("#pattern-status").to_have_text("Copied pattern to clipboard.")

        copied_payload = json.loads(self._read_clipboard_text())
        case.assertEqual(copied_payload["rule"], "conway")
        case.assertTrue(copied_payload["cells_by_id"])

        case.page.click("#reset-btn")
        self._expect("#status-text").to_have_text("Paused")

        self._write_clipboard_text(json.dumps(copied_payload))
        case.page.once("dialog", lambda dialog: dialog.accept())
        case.page.locator("#paste-pattern-btn").evaluate("(node) => node.click()")

        self._expect("#pattern-status").to_have_text("Pasted pattern from clipboard.")
        pasted_payload = self._export_pattern_payload()
        case.assertEqual(pasted_payload["cells_by_id"], copied_payload["cells_by_id"])


class CellularAutomatonUITests(SharedUiFlowMixin, BrowserAppTestCase):
    runtime_host_kind = "server"
    page_viewport: ClassVar[ViewportSize | None] = {"width": 1280, "height": 900}

    def setUp(self) -> None:
        super().setUp()
        self.initialize_shared_ui_flow()

    def test_server_restart_preserves_saved_state(self) -> None:
        if self.api is None:
            raise AssertionError("server browser tests require an API client")

        self.page.select_option("#rule-select", "highlife")
        self._expect("#rule-select").to_have_value("highlife")

        self.host.restart()
        self.goto_page(f"{self.host.base_url}/", wait_until="load")

        self._expect("#rule-select").to_have_value("highlife")
        self.assertEqual(self.api.get_state()["rule"]["name"], "highlife")


class StandaloneCellularAutomatonUITests(SharedUiFlowMixin, BrowserAppTestCase):
    runtime_host_kind = "standalone"
    page_viewport: ClassVar[ViewportSize | None] = {"width": 1280, "height": 900}

    def setUp(self) -> None:
        super().setUp()
        self.initialize_shared_ui_flow()

    def test_reload_restores_browser_persisted_state(self) -> None:
        self.page.select_option("#rule-select", "highlife")
        self._expect("#rule-select").to_have_value("highlife")

        self._paint_canvas_center()
        persisted_before_reload = self._export_pattern_payload()

        self.reload_page(wait_until="load")

        self._expect("#rule-select").to_have_value("highlife")
        persisted_after_reload = self._export_pattern_payload()
        self.assertEqual(persisted_after_reload["cells_by_id"], persisted_before_reload["cells_by_id"])


class StandaloneRuntimeFailureTests(BrowserAppTestCase):
    runtime_host_kind = "standalone"
    page_viewport: ClassVar[ViewportSize | None] = {"width": 1280, "height": 900}

    def test_worker_init_failure_shows_startup_error_banner(self) -> None:
        self.context.route("**/pyodide.js", lambda route: route.abort())
        self.page.goto(f"{self.host.base_url}/", wait_until="load")

        cast(Any, expect(self.page.locator("#app-startup-error"))).to_be_visible()
        cast(Any, expect(self.page.locator("#app-startup-error"))).to_contain_text(
            "Standalone runtime failed to initialize"
        )


if __name__ == "__main__":
    unittest.main()
