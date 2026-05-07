from __future__ import annotations

import json
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, cast

from playwright.sync_api import ViewportSize, expect

try:
    from tests.e2e.browser_support.bootstrap import BrowserAppTestCase
    from tests.e2e.playwright_case_helpers import SharedUiFlowHelpers
    from tools.render_review.browser_support.palette_regression import (
        PaletteFixtureCase,
        iter_palette_fixture_cases,
        palette_fixture_test_suffix,
    )
    from tools.render_review.browser_support.render_review import (
        select_tiling_family,
        set_patch_depth,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.browser_support.bootstrap import BrowserAppTestCase
    from tests.e2e.playwright_case_helpers import SharedUiFlowHelpers
    from tools.render_review.browser_support.palette_regression import (
        PaletteFixtureCase,
        iter_palette_fixture_cases,
        palette_fixture_test_suffix,
    )
    from tools.render_review.browser_support.render_review import (
        select_tiling_family,
        set_patch_depth,
    )


class SharedUiFlowMixin(SharedUiFlowHelpers):
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
        select_tiling_family(case.page, "penrose-p3-rhombs")

        self._expect("#tiling-family-select").to_have_value("penrose-p3-rhombs")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._expect("#adjacency-mode-field").to_be_visible()

    def test_spectre_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        select_tiling_family(case.page, "spectre")

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
        select_tiling_family(case.page, "taylor-socolar")

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
        select_tiling_family(case.page, "sphinx")

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
        select_tiling_family(case.page, "chair")

        self._expect("#tiling-family-select").to_have_value("chair")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._wait_for_patch_render_complete()

    def test_chair_topology_switch_renders_browser_visible_multicolor_patch(self) -> None:
        case = self._case()
        select_tiling_family(case.page, "chair")

        self._expect("#tiling-family-select").to_have_value("chair")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=4)

    def test_robinson_triangles_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        select_tiling_family(case.page, "robinson-triangles")

        self._expect("#tiling-family-select").to_have_value("robinson-triangles")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=2)

    def test_hat_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        select_tiling_family(case.page, "hat-monotile")

        self._expect("#tiling-family-select").to_have_value("hat-monotile")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=2)

    def test_tuebingen_triangle_topology_switch_renders_aperiodic_patch(self) -> None:
        case = self._case()
        select_tiling_family(case.page, "tuebingen-triangle")

        self._expect("#tiling-family-select").to_have_value("tuebingen-triangle")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=2)

    def test_dodecagonal_square_triangle_topology_switch_renders_aperiodic_patch(self) -> None:
        self._select_tiling_family_and_wait_for_reset("dodecagonal-square-triangle")

        self._expect("#tiling-family-select").to_have_value("dodecagonal-square-triangle")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#grid-size-text").to_contain_text("Depth")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=3)

    def test_dodecagonal_square_triangle_patch_depth_uses_configured_cap(self) -> None:
        case = self._case()
        self._select_tiling_family_and_wait_for_reset("dodecagonal-square-triangle")

        self._expect("#tiling-family-select").to_have_value("dodecagonal-square-triangle")
        self._expect("#patch-depth-field").to_be_visible()
        self._expect("#patch-depth-input").to_have_attribute("max", "6")
        case.assertEqual(self._patch_depth_input_state()["max"], "6")

        if case.page.locator("#unsafe-sizing-toggle").is_visible():
            case.page.locator("#unsafe-sizing-toggle").check()
            self._expect("#unsafe-sizing-toggle").to_be_checked()
            self._expect("#patch-depth-input").to_have_attribute("max", "60")

        if case.api is not None:
            with case.page.expect_response(
                lambda response: (
                    response.request.method == "POST" and "/api/control/reset" in response.url
                ),
                timeout=60_000,
            ) as response_info:
                set_patch_depth(case.page, 6, timeout_ms=60_000)
            case.assertEqual(int(response_info.value.status), 200)
        else:
            set_patch_depth(case.page, 6, timeout_ms=60_000)
        self._expect("#patch-depth-input").to_have_value("6")
        self._expect("#patch-depth-label").to_have_text("Depth 6")
        self._expect("#grid-size-text").to_contain_text("Depth 6")
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
        self._assert_canvas_centered_within_viewport()

    def test_deltoidal_hexagonal_topology_switch_renders_periodic_patch(self) -> None:
        case = self._case()
        select_tiling_family(case.page, "deltoidal-hexagonal")

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
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".json", delete=False
        ) as pattern_file:
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


def _build_palette_alias_regression_test(
    fixture_case: PaletteFixtureCase,
) -> Callable[[SharedUiFlowMixin], None]:
    def test_method(self: SharedUiFlowMixin) -> None:
        self._assert_fixture_dead_cells_do_not_alias_live_canvas_color(fixture_case)

    return test_method


for _palette_fixture_case in iter_palette_fixture_cases():
    setattr(
        SharedUiFlowMixin,
        f"test_{palette_fixture_test_suffix(_palette_fixture_case)}_dead_cells_do_not_alias_live_canvas_color",
        _build_palette_alias_regression_test(_palette_fixture_case),
    )


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
        expected_cells_by_id = persisted_before_reload["cells_by_id"]
        if not isinstance(expected_cells_by_id, dict):
            raise AssertionError(
                f"exported standalone cells_by_id payload was invalid: {expected_cells_by_id!r}"
            )
        self._wait_for_standalone_persisted_snapshot(
            expected_rule="highlife",
            expected_cells_by_id={
                str(cell_id): int(cell_state)
                for cell_id, cell_state in expected_cells_by_id.items()
            },
        )

        self.reload_page(wait_until="load")

        self._expect("#rule-select").to_have_value("highlife")
        persisted_after_reload = self._export_pattern_payload()
        self.assertEqual(
            persisted_after_reload["cells_by_id"], persisted_before_reload["cells_by_id"]
        )


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
