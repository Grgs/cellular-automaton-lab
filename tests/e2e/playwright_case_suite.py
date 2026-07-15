from __future__ import annotations

import base64
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
        is_control_reset_response_url,
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
        is_control_reset_response_url,
        select_tiling_family,
        set_patch_depth,
    )


def _encode_compare_run_fragment(config: dict[str, object]) -> str:
    """Mirror compare-run-link.ts encodeCompareRunFragment: run=v1.<base64url(JSON)>."""
    payload = base64.urlsafe_b64encode(json.dumps(config).encode("utf-8")).decode("ascii")
    return f"run=v1.{payload.rstrip('=')}"


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
        # The one-shell stage is taller than the old top-bar layout, so the
        # fitted patch's bounding box covers slightly less width (~0.949);
        # 0.9 matches the other aperiodic patch cases.
        self._assert_browser_visible_aperiodic_patch(
            minimum_fill_colors=1,
            minimum_coverage_width_ratio=0.9,
            minimum_coverage_height_ratio=0.9,
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
                    response.request.method == "POST"
                    and is_control_reset_response_url(response.url)
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
        self._paint_canvas_center()
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

    def test_wall_edit_mode_paints_the_seed_at_gen_zero(self) -> None:
        # The wall's edit mode: the dock's ✎ arms painting, a board click at
        # gen 0 pulls the cell back to a seed bit (converting the shape demo to
        # an editable bit-string on first paint), and the wall re-runs from it.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        self._expect(".compare-edit-toggle").to_be_enabled()
        case.page.click(".compare-edit-toggle")
        self._expect(".compare-edit-toggle").to_have_attribute("aria-pressed", "true")

        # The default filmstrip rests on a lively frame; seed edits happen at
        # gen 0, so step back to the seed first.
        case.page.click('.compare-filmstrip-btn[title="Back to the seed"]')
        board = case.page.locator(".compare-filmstrip-board").first
        board.locator("[data-cell-id]").first.click()

        # Painting must not zoom the board, and the shape demo converts to an
        # editable bit seed the debounced re-run then replays everywhere.
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(0)
        case.page.wait_for_function(
            """() => {
                const field = [...document.querySelectorAll('input.compare-field[type="text"]')]
                    .find((input) => !input.disabled && /^[01]+$/.test(input.value));
                return Boolean(field);
            }"""
        )
        self._expect(".compare-status").to_contain_text("Filmstrip ready", timeout=60_000)

    def test_space_on_lab_route_button_navigates_without_starting_playback(self) -> None:
        # Space is the native activation key for the header route button. The
        # wall's global playback shortcut must not steal it and start the clock.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        play_pause_selector = '.compare-filmstrip-btn[title="Play / pause"]'
        self._expect(play_pause_selector).to_contain_text("Play")
        lab_route = case.page.locator("#open-lab-btn")
        lab_route.focus()
        lab_route.press("Space")

        case.page.wait_for_function("() => window.location.hash === '#/lab'")
        self._expect("#grid").to_be_visible()
        self._expect(play_pause_selector).to_contain_text("Play")

    def test_wall_fork_persists_across_gallery_and_speaker_view(self) -> None:
        # Forking a board leaves the shared clock for its own live session; that
        # fork must survive leaving the board (it keeps running as a compact
        # live tile in the gallery) rather than being torn down by the focus
        # change, and re-focusing the same board must reuse it, not re-fork it.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        board = case.page.locator(".compare-filmstrip-board").first
        board.click()
        self._expect(".compare-hero-fork").to_have_text("Edit live")
        case.page.click(".compare-hero-fork")
        self._expect(".compare-filmstrip-board.is-hero .compare-focus-pane").to_be_visible(
            timeout=30_000
        )

        # Leave the board: the fork is not disposed, and it keeps rendering
        # (compactly -- no chip actions) in its own, now non-hero, tile.
        case.page.click(".compare-hero-back")
        self._expect(".compare-focus-pane").to_have_count(1)
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(0)
        self._expect(".compare-focus-pane-actions").not_to_be_visible()

        # Re-entering the same board shows the same live pane as the hero again
        # (no second fork), so the toolbelt's fork button hides.
        board.click()
        self._expect(".compare-filmstrip-board.is-hero .compare-focus-pane").to_be_visible()
        self._expect(".compare-focus-pane").to_have_count(1)
        self._expect(".compare-hero-fork").to_be_hidden()

        # Discard tears it down.
        case.page.click(".compare-focus-pane-discard")
        self._expect(".compare-focus-pane").to_have_count(0)

    def test_wall_fork_rejoins_the_wall_as_the_new_shared_seed(self) -> None:
        # A fork detaches from the shared clock; "Run wall from here" is the
        # way back: the fork's current state pulls back through the board's
        # traversal to become the shared seed, and every board re-runs from it
        # as generation 0 (the re-run also disposes the fork).
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        case.page.locator(".compare-filmstrip-board").first.click()
        case.page.click(".compare-hero-fork")
        self._expect(".compare-filmstrip-board.is-hero .compare-focus-pane").to_be_visible(
            timeout=30_000
        )

        case.page.click(".compare-focus-pane-rejoin")
        self._expect(".compare-focus-pane").to_have_count(0)
        self._expect(".compare-status").to_contain_text("Filmstrip ready", timeout=60_000)
        self._expect(".compare-filmstrip-board").to_have_count(4)

    def test_wall_fork_carries_brush_and_undo_redo_chrome(self) -> None:
        # A live fork is a real editor: its chip carries brush-size cycling and
        # per-paint undo/redo. Undo/redo start disabled (nothing painted), and
        # an auto-forked paint (painting a board away from gen 0) seeds the
        # history, so undo enables and the paint is undoable/redoable. The
        # actual inverse-write behaviour is pinned by the focus-pane unit test;
        # here we prove the chrome is wired end-to-end on a real backend.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        case.page.locator(".compare-filmstrip-board").first.click()
        case.page.click(".compare-hero-fork")
        self._expect(".compare-filmstrip-board.is-hero .compare-focus-pane").to_be_visible(
            timeout=30_000
        )
        self._expect(".compare-focus-pane-badge").to_contain_text("live · gen")

        # Nothing painted yet, so history is empty.
        self._expect(".compare-focus-pane-undo").to_be_disabled()
        self._expect(".compare-focus-pane-redo").to_be_disabled()

        # The brush button cycles 1 -> 2 -> 3 -> 1.
        self._expect(".compare-focus-pane-brush").to_have_text("Brush 1")
        case.page.click(".compare-focus-pane-brush")
        self._expect(".compare-focus-pane-brush").to_have_text("Brush 2")
        case.page.click(".compare-focus-pane-brush")
        self._expect(".compare-focus-pane-brush").to_have_text("Brush 3")
        case.page.click(".compare-focus-pane-brush")
        self._expect(".compare-focus-pane-brush").to_have_text("Brush 1")

    def test_wall_names_boards_and_edits_the_selection_in_place(self) -> None:
        # Boards carry their friendly catalog label (not the raw geometry
        # key), replacing a named board preserves its wall position, the dock's
        # ⊞ jumps straight to the searchable tiling checklist, and a board's
        # persistent upper-right × drops it with one debounced re-run.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        self._expect(".compare-filmstrip-label >> nth=0").to_have_text("Square")
        self._expect(".compare-filmstrip-label >> nth=2").to_have_text("Penrose P3 Rhombs")

        # A board-local replacement keeps the position the user acted on.
        labels_before = case.page.locator(".compare-filmstrip-label").all_text_contents()
        case.page.locator(".compare-filmstrip-label").nth(2).click()
        replacement = case.page.locator(
            ".compare-board-tiling-choice:not(:disabled):not(.is-current)"
        ).first
        replacement_label = replacement.locator(
            ".compare-board-tiling-choice-copy > span"
        ).inner_text()
        replacement.click()
        self._expect(".compare-filmstrip-label >> nth=2").to_have_text(
            replacement_label, timeout=60_000
        )
        labels_after = case.page.locator(".compare-filmstrip-label").all_text_contents()
        case.assertEqual(labels_after[:2], labels_before[:2])
        case.assertEqual(labels_after[3:], labels_before[3:])

        # ⊞ lands ready to type: sheet open, Tilings section expanded, search
        # focused.
        case.page.click(".compare-tilings-open")
        self._expect(".compare-config-sheet.is-open").to_be_visible()
        self._expect(".compare-tilings-search").to_be_focused()
        case.page.click(".compare-config-sheet-close")

        # The × is visible without hover and sits at the tile's upper-right.
        first_board = case.page.locator(".compare-filmstrip-board").first
        first_remove = case.page.locator(".compare-filmstrip-remove").first
        expect(first_remove).to_be_visible()
        board_box = first_board.bounding_box()
        remove_box = first_remove.bounding_box()
        case.assertIsNotNone(board_box)
        case.assertIsNotNone(remove_box)
        assert board_box is not None and remove_box is not None
        case.assertLessEqual(remove_box["y"] - board_box["y"], 12)
        case.assertLessEqual(
            (board_box["x"] + board_box["width"]) - (remove_box["x"] + remove_box["width"]),
            12,
        )
        first_remove.click()
        self._expect(".compare-status").to_contain_text("Removed Square")
        self._expect(".compare-filmstrip-board").to_have_count(3, timeout=60_000)
        self._expect(".compare-filmstrip-label >> nth=0").to_have_text(
            "Kagome / Trihexagonal (3.6.3.6)"
        )

        # Add is available directly on the wall. It opens the searchable visual
        # picker, and choosing a result appends it and immediately re-runs.
        labels_before_add = case.page.locator(".compare-filmstrip-label").all_text_contents()
        case.page.click(".compare-filmstrip-add")
        self._expect(".compare-board-tiling-picker[aria-label='Add tiling']").to_be_visible()
        self._expect(".compare-board-tiling-picker-search").to_be_focused()
        add_label = "Snub Trihexagonal (3.3.3.3.6)"
        case.page.fill(".compare-board-tiling-picker-search", add_label)
        filtered_choices = case.page.locator(".compare-board-tiling-choice:not(:disabled)")
        case.assertEqual(filtered_choices.count(), 1)
        filtered_choices.first.click()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        labels_after_add = case.page.locator(".compare-filmstrip-label").all_text_contents()
        case.assertEqual(labels_after_add[:-1], labels_before_add)
        case.assertEqual(labels_after_add[-1], add_label)
        dense_board = case.page.locator(".compare-filmstrip-board").filter(
            has=case.page.locator(".compare-filmstrip-label", has_text=add_label)
        )
        expect(dense_board.locator(".compare-thumb")).to_be_visible(timeout=60_000)
        expect(dense_board.locator(".compare-filmstrip-slot")).not_to_have_text("too large")

    def test_wall_applies_wireworld_and_hides_tiling_specific_rules(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        rule_select = case.page.locator("select[aria-label='Comparison rule']")
        rule_values = rule_select.locator("option").evaluate_all(
            "options => options.map(option => option.value)"
        )
        case.assertTrue("wireworld" in rule_values)
        case.assertTrue("kagome-life" not in rule_values)
        case.assertTrue(not any(value.startswith("archlife") for value in rule_values))

        rule_select.select_option("wireworld")
        self._expect(".compare-setup-run").to_have_text("Apply changes")
        case.page.click(".compare-setup-run")
        self._expect(".compare-setup-run").to_have_text("Up to date", timeout=60_000)
        self._expect(".compare-status").to_contain_text("Filmstrip ready")
        self._expect("select[aria-label='Comparison rule']").to_have_value("wireworld")

        # WireWorld's electron head deterministically becomes a tail. Checking
        # the rule's state colours before and after one shared step proves the
        # applied rule reached the filmstrip, beyond merely changing the select.
        first_live = (
            case.page.locator(".compare-filmstrip-board").first.locator("polygon.is-live").first
        )
        expect(first_live).to_have_attribute("fill", "#2f80ed")
        case.page.get_by_role("button", name="Step forward one generation").click()
        expect(first_live).to_have_attribute("fill", "#d64e4e")

    def test_wall_edit_mode_rewinds_mid_timeline_paint_to_shared_seed(self) -> None:
        # Edit seed should keep the edited board on the shared wall clock. If
        # the wall is resting on a lively later frame, arming edit mode rewinds
        # to generation 0 before paint, then the debounced rerun rebuilds every
        # board from that shared seed.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        self._expect(".compare-edit-toggle").to_be_enabled()
        case.page.click(".compare-edit-toggle")
        self._expect(".compare-edit-toggle").to_have_attribute("aria-pressed", "true")
        self._expect(".compare-filmstrip-counter").to_contain_text("gen 0 /")

        board = case.page.locator(".compare-filmstrip-board").first
        board.locator("[data-cell-id]").first.click()

        self._expect(".compare-filmstrip-board.is-hero").to_have_count(0)
        self._expect(".compare-focus-pane").to_have_count(0)
        self._expect(".compare-status").not_to_contain_text("Fork failed")
        self._expect(".compare-status").to_contain_text("Filmstrip ready", timeout=60_000)

        case.page.click('.compare-filmstrip-btn[title="Play / pause"]')
        self._expect('.compare-filmstrip-btn[title="Play / pause"]').to_contain_text("Pause")
        self._expect(".compare-focus-pane").to_have_count(0)

    def test_wall_paint_conversion_keeps_seed_placement_previews_live(self) -> None:
        # Painting the wall while a named shape is the seed source converts it
        # to a bit-string programmatically; the seed-placement thumbnails in
        # the config sheet must be refetched with the traversal order, or they
        # render every subsequent bit seed as an empty board.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        self._expect(".compare-edit-toggle").to_be_enabled()
        case.page.click(".compare-edit-toggle")
        case.page.click('.compare-filmstrip-btn[title="Back to the seed"]')
        board = case.page.locator(".compare-filmstrip-board").first
        board.locator("[data-cell-id]").first.click()
        case.page.wait_for_function(
            """() => {
                const field = [...document.querySelectorAll('input.compare-field[type="text"]')]
                    .find((input) => !input.disabled && /^[01]+$/.test(input.value));
                return Boolean(field);
            }"""
        )

        # The converted seed still has live bits, so the placement previews in
        # the config sheet must show them (accent-filled cells), not blanks.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        self._expect(".compare-config-sheet.is-open").to_be_visible()
        case.page.wait_for_function(
            """() => {
                const cells = document.querySelectorAll(".compare-seedpreview svg [fill]");
                return [...cells].some((cell) =>
                    (cell.getAttribute("fill") ?? "").includes("accent"));
            }""",
            timeout=60_000,
        )

    def test_wall_scrubs_an_invalid_focus_deep_link_from_the_hash(self) -> None:
        # A stale or mistyped #focus= slug must not linger in the URL claiming
        # a speaker view that isn't there; a valid slug still deep-links.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        case.page.evaluate("() => { window.location.hash = '#focus=not-a-board'; }")
        case.page.wait_for_function("() => !window.location.hash.includes('focus=')")
        self._expect(".compare-filmstrip--speaker").to_have_count(0)

        case.page.evaluate("() => { window.location.hash = '#focus=square'; }")
        self._expect(".compare-filmstrip--speaker").to_have_count(1)
        case.page.wait_for_function("() => window.location.hash.includes('focus=square')")

    def test_loading_saved_run_clears_previous_focused_board_route(self) -> None:
        # A saved run replaces the wall wholesale. Its previous speaker route
        # must be cleared with the old boards, or the replacement wall silently
        # focuses the same geometry as soon as its filmstrip attaches.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        case.page.click("#compare-config-tab-saved")
        case.page.fill('input[aria-label="Saved run name"]', "Focus replacement run")
        case.page.get_by_role("button", name="Save run", exact=True).click()
        self._expect(".compare-status").to_contain_text("Saved run")
        case.page.get_by_role("button", name="Close configuration").click()

        case.page.locator(".compare-filmstrip-board").first.click()
        self._expect(".compare-filmstrip--speaker").to_have_count(1)
        case.page.wait_for_function("() => window.location.hash.includes('focus=square')")

        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        case.page.click("#compare-config-tab-saved")
        case.page.get_by_role("button", name="Load run", exact=True).click()

        case.page.wait_for_function("() => !window.location.hash.includes('focus=')")
        self._expect(".compare-filmstrip--speaker:visible").to_have_count(0)
        case.page.get_by_role("button", name="Close configuration").click()
        run_button = case.page.locator('.compare-filmstrip-btn[aria-label="Run comparison"]')
        self._expect('.compare-filmstrip-btn[aria-label="Run comparison"]').to_be_enabled()
        run_button.click()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        self._expect(".compare-filmstrip--speaker:visible").to_have_count(0)
        case.page.wait_for_function("() => !window.location.hash.includes('focus=')")

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
        self.goto_page(f"{self.host.base_url}/#/lab", wait_until="load")

        self._expect("#rule-select").to_have_value("highlife")
        self.assertEqual(self.api.get_state()["rule"]["name"], "highlife")

    def test_bare_url_lands_on_wall_and_autoplays_demo_once(self) -> None:
        # The comparison wall is the landing view; a first visit autoplays the
        # curated featured demo, and the demo-seen flag makes it a one-time event.
        self.goto_page(f"{self.host.base_url}/", wait_until="load")

        self._expect(".wall-page").to_be_visible()
        # The featured demo builds the live side-by-side (four curated tilings);
        # the aperiodic boards take a few seconds to construct.
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        demo_seen = self.page.evaluate(
            """() => {
                try {
                    const raw = window.localStorage.getItem("cellular-automaton-lab.compare.v1");
                    return typeof JSON.parse(raw).demoSeenAt === "number";
                } catch {
                    return false;
                }
            }"""
        )
        self.assertTrue(demo_seen)

        # A second landing stays on the wall with the same participants loaded,
        # but paused instead of autoplaying over the user again.
        self.reload_page(wait_until="load")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        self._expect('.compare-filmstrip-btn[title="Play / pause"]').to_contain_text("Play")

    def test_lab_deep_link_shows_editor_without_the_wall(self) -> None:
        self.goto_page(f"{self.host.base_url}/#/lab", wait_until="load")

        self._expect("#grid").to_be_visible()
        self.page.wait_for_function("""() => document.querySelector(".wall-page") === null""")

    def test_wall_button_navigates_from_lab_to_wall(self) -> None:
        # setUp landed in the Lab; the top-bar Wall button is the way back.
        self._mark_compare_demo_seen()
        self.page.click("#wall-view-btn")

        self._expect(".wall-page").to_be_visible()
        # Leaving via the Lab route tab writes the /lab route back.
        self.page.click("#open-lab-btn")
        self.page.wait_for_function("() => window.location.hash === '#/lab'")


class StandaloneCellularAutomatonUITests(SharedUiFlowMixin, BrowserAppTestCase):
    runtime_host_kind = "standalone"
    page_viewport: ClassVar[ViewportSize | None] = {"width": 1280, "height": 900}

    def setUp(self) -> None:
        super().setUp()
        self.initialize_shared_ui_flow()

    def test_reload_restores_browser_persisted_state(self) -> None:
        self.page.select_option("#rule-select", "highlife")
        self._expect("#rule-select").to_have_value("highlife")
        self._wait_for_standalone_persisted_snapshot(
            expected_rule="highlife",
            expected_cells_by_id={},
        )

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
        persisted_after_reload = self._wait_for_exported_pattern_payload(
            expected_rule="highlife",
            expected_cells_by_id={
                str(cell_id): int(cell_state)
                for cell_id, cell_state in expected_cells_by_id.items()
            },
        )
        self.assertEqual(
            persisted_after_reload["cells_by_id"], persisted_before_reload["cells_by_id"]
        )

    def test_compare_run_link_restores_workspace_in_standalone(self) -> None:
        # C1 parity: a #/compare&run= deep link opens the full-page workspace in
        # the Pyodide build and restores the saved setup without auto-running.
        fragment = _encode_compare_run_fragment(
            {
                "seed": "101",
                "rule": "conway",
                "traversal": "bfs",
                "frames": 12,
                "grid_size": 8,
                "geometries": ["square"],
            }
        )
        self.page.evaluate("(hash) => { window.location.hash = hash; }", f"#/compare&{fragment}")

        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-seedbits input.compare-field").to_have_value("101")
        self._expect(".compare-status").to_contain_text("Loaded run link")
        # Reconstruct-and-wait: the link must not have started a comparison.
        self._expect(".compare-grid").to_have_count(0)

    def test_saved_compare_run_persists_across_reload_in_standalone(self) -> None:
        # C3 parity: saving a run writes to localStorage in the Pyodide build and
        # the run is still listed after a full reload. setUp lands in the Lab;
        # the top-bar Wall button is the navigation to the wall.
        self._mark_compare_demo_seen()
        self.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()

        run_name = "Standalone smoke run"
        # Configuration lives in a bottom sheet the dock gear opens; saved-run
        # controls live under the Saved tab.
        self.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        self.page.click("#compare-config-tab-saved")
        self.page.fill('input[aria-label="Saved run name"]', run_name)
        self.page.get_by_role("button", name="Save run", exact=True).click()
        self._expect(".compare-status").to_contain_text("Saved run")

        saved_run_names = self.page.evaluate(
            """() => {
                const raw = window.localStorage.getItem("cellular-automaton-lab.compare.v1");
                if (!raw) {
                    return [];
                }
                try {
                    return (JSON.parse(raw).runs || []).map((run) => run.name);
                } catch {
                    return [];
                }
            }"""
        )
        self.assertIn(run_name, saved_run_names)

        self.reload_page(wait_until="load")

        # The wall is the landing view, so the reload lands straight back on it.
        self._expect(".wall-page").to_be_visible()
        self.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        self.page.click("#compare-config-tab-saved")
        self._expect('select[aria-label="Saved compare runs"]').to_contain_text(run_name)


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
