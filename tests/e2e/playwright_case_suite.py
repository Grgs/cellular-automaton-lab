from __future__ import annotations

import base64
import json
import re
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, cast

from playwright.sync_api import ViewportSize, expect

try:
    from backend.rules import RuleRegistry
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
    from tools.standalone_runtime_budget import load_runtime_budget
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.rules import RuleRegistry
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
    from tools.standalone_runtime_budget import load_runtime_budget


def _encode_compare_run_fragment(config: dict[str, object]) -> str:
    """Mirror compare-run-link.ts encodeCompareRunFragment: run=v1.<base64url(JSON)>."""
    payload = base64.urlsafe_b64encode(json.dumps(config).encode("utf-8")).decode("ascii")
    return f"run=v1.{payload.rstrip('=')}"


class SharedUiFlowMixin(SharedUiFlowHelpers):
    def _select_compare_board(self, index: int) -> None:
        case = self._case()
        board = case.page.locator(".compare-filmstrip-board").nth(index)
        board.focus()
        board.press("Enter")
        expect(board).to_have_class(re.compile(r"\bis-selected\b"))

    def _remove_selected_compare_board(self, index: int) -> None:
        case = self._case()
        self._select_compare_board(index)
        remove = case.page.locator(".compare-inspector-remove")
        expect(remove).to_be_visible()
        expect(remove).to_be_enabled(timeout=60_000)
        remove.click()

    def test_theme_reset_immediately_resumes_following_the_os_scheme(self) -> None:
        case = self._case()
        storage_key = str(
            case.page.evaluate(
                """() => window.APP_DEFAULTS?.theme?.storage_key ||
                    'cellular-automaton-theme'"""
            )
        )
        case.page.evaluate("(key) => window.localStorage.removeItem(key)", storage_key)

        case.page.emulate_media(color_scheme="light")
        self._expect("html").to_have_attribute("data-theme", "light")

        case.page.emulate_media(color_scheme="dark")
        self._expect("html").to_have_attribute("data-theme", "dark")

        case.page.click("#shell-menu-toggle")
        case.page.click("#shell-preferences-btn")
        case.page.get_by_role("radio", name="Light").check()
        self._expect("html").to_have_attribute("data-theme", "light")
        case.assertEqual(
            case.page.evaluate("(key) => window.localStorage.getItem(key)", storage_key),
            "light",
        )
        case.page.click("#shell-preferences-close")

        self._ensure_drawer_open()
        case.page.click('.drawer-nav-pill[href="#advanced-section"]')
        case.page.click("#reset-all-settings-btn")
        self._expect("html").to_have_attribute("data-theme", "dark")
        case.assertEqual(
            case.page.evaluate("(key) => window.localStorage.getItem(key)", storage_key),
            None,
        )

        case.page.emulate_media(color_scheme="light")
        self._expect("html").to_have_attribute("data-theme", "light")

    def test_shell_menu_navigates_and_exposes_workspace_actions(self) -> None:
        case = self._case()
        case.page.set_viewport_size({"width": 1280, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [1280, 800])
        storage_key = str(
            case.page.evaluate(
                """() => window.APP_DEFAULTS?.theme?.storage_key ||
                    'cellular-automaton-theme'"""
            )
        )
        case.page.evaluate("(key) => window.localStorage.removeItem(key)", storage_key)
        case.page.emulate_media(color_scheme="light")
        self._expect("#shell-workspace-status").to_have_text("Lab editor")
        expect(case.page.locator(".shell-route-switcher")).to_be_visible()
        self._expect("#open-lab-btn").to_have_attribute("aria-current", "page")

        menu = case.page.locator("#shell-menu-panel")
        menu_toggle = case.page.get_by_role("button", name="Open app menu")
        expect(menu_toggle).to_be_visible()
        menu_toggle.focus()
        menu_toggle.press("Enter")
        expect(menu_toggle).to_have_attribute("aria-expanded", "true")
        expect(menu).to_be_visible()
        expect(case.page.locator(".shell-menu-navigation")).not_to_be_visible()
        expect(case.page.locator("#shell-menu-lab-actions")).to_be_visible()
        expect(case.page.locator("#shell-menu-compare-actions")).not_to_be_visible()
        expect(case.page.get_by_role("button", name="Preferences", exact=True)).to_be_visible()

        case.page.click("#shell-menu-lab-rule")
        expect(case.page.locator("#control-drawer")).to_have_attribute("data-open", "true")
        expect(menu).not_to_be_visible()

        menu_toggle.click()
        menu_toggle.press("Escape")
        expect(menu).not_to_be_visible()
        case.assertEqual(
            case.page.evaluate("() => document.activeElement?.id"),
            "shell-menu-toggle",
        )

        case.page.locator("#wall-view-btn").press("Enter")
        case.page.wait_for_function("() => window.location.hash === ''")
        self._expect(".wall-page").to_be_visible()
        self._expect("#shell-workspace-status").to_have_text("Compare workspace")
        self._expect("#wall-view-btn").to_have_attribute("aria-current", "page")

        menu_toggle.click()
        expect(menu).to_be_visible()
        expect(case.page.locator("#shell-menu-compare-actions")).to_be_visible()
        expect(case.page.locator("#shell-menu-lab-actions")).not_to_be_visible()
        desktop_menu_rect = case.page.locator("#shell-menu-panel").bounding_box()
        if desktop_menu_rect is None:
            raise AssertionError("desktop app menu rectangle was unavailable")
        case.assertGreaterEqual(desktop_menu_rect["x"], 0)
        case.assertLessEqual(
            desktop_menu_rect["x"] + desktop_menu_rect["width"],
            1280,
        )
        case.assertLessEqual(
            int(case.page.evaluate("() => document.documentElement.scrollWidth")),
            1280,
        )

        case.page.click("#shell-menu-compare-wall")
        setup_sheet = case.page.locator(".compare-config-sheet")
        expect(setup_sheet).to_have_class(re.compile(r"\bis-open\b"))
        expect(case.page.locator("#compare-config-panel-tilings")).to_be_visible()

        menu_toggle.click()
        case.page.click("#shell-menu-compare-rule")
        expect(setup_sheet).to_have_class(re.compile(r"\bis-open\b"))
        expect(case.page.locator("#compare-config-panel-setup")).to_be_visible()
        expect(case.page.get_by_label("Comparison rule")).to_be_focused()

        menu_toggle.click()
        case.page.locator(".wall-brand").click()
        expect(menu).not_to_be_visible()

        def theme_colors() -> dict[str, dict[str, str]]:
            colors = case.page.evaluate(
                """() => Object.fromEntries(
                    Object.entries({
                        shell: "#shell-header",
                        wall: ".wall-page",
                        setup: ".compare-setup-sidebar",
                        inspector: ".compare-inspector",
                        dock: ".compare-dock",
                        overlay: ".compare-analysis-panel",
                        field: "input.compare-field",
                        menu: "#shell-menu-panel",
                    }).map(([name, selector]) => {
                        const node = document.querySelector(selector);
                        if (!(node instanceof HTMLElement)) {
                            throw new Error(`Missing theme surface: ${selector}`);
                        }
                        const style = getComputedStyle(node);
                        return [name, {
                            background: style.backgroundColor,
                            color: style.color,
                            border: style.borderColor,
                        }];
                    })
                )"""
            )
            if not isinstance(colors, dict):
                raise AssertionError(f"invalid theme color snapshot: {colors!r}")
            return cast(dict[str, dict[str, str]], colors)

        light_colors = theme_colors()
        menu_toggle.click()
        case.page.click("#shell-preferences-btn")
        preferences = case.page.get_by_role("dialog", name="Preferences")
        expect(preferences).to_be_visible()
        case.page.get_by_role("radio", name="Dark").check()
        self._expect("html").to_have_attribute("data-theme", "dark")
        case.assertEqual(
            case.page.evaluate("(key) => window.localStorage.getItem(key)", storage_key),
            "dark",
        )
        dark_colors = theme_colors()
        for surface in ("shell", "wall", "setup", "inspector", "dock", "overlay", "field", "menu"):
            with case.subTest(theme_surface=surface):
                case.assertNotEqual(
                    light_colors[surface]["background"],
                    dark_colors[surface]["background"],
                )
                case.assertNotEqual(
                    light_colors[surface]["color"],
                    dark_colors[surface]["color"],
                )

        case.page.set_viewport_size({"width": 390, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [390, 800])
        case.page.keyboard.press("Escape")
        expect(preferences).not_to_be_visible()
        case.assertEqual(
            case.page.evaluate("() => document.activeElement?.id"),
            "shell-menu-toggle",
        )
        expect(case.page.locator(".shell-route-switcher")).not_to_be_visible()
        menu_toggle.click()
        expect(case.page.locator(".shell-menu-navigation")).to_be_visible()
        mobile_menu_rect = case.page.locator("#shell-menu-panel").bounding_box()
        if mobile_menu_rect is None:
            raise AssertionError("mobile app menu rectangle was unavailable")
        case.assertGreaterEqual(mobile_menu_rect["x"], 0)
        case.assertLessEqual(
            mobile_menu_rect["x"] + mobile_menu_rect["width"],
            390,
        )
        case.assertLessEqual(
            int(case.page.evaluate("() => document.documentElement.scrollWidth")),
            390,
        )
        case.page.locator("#shell-menu-lab").press("Enter")
        case.page.wait_for_function("() => window.location.hash === '#/lab'")
        self._expect("#grid").to_be_visible()
        menu_toggle.click()
        case.page.locator("#shell-menu-compare").press("Enter")
        case.page.wait_for_function("() => window.location.hash === ''")
        self._expect(".wall-page").to_be_visible()

        menu_toggle.click()
        case.page.click("#shell-preferences-btn")
        expect(preferences).to_be_visible()
        case.page.emulate_media(color_scheme="light")
        case.page.get_by_role("radio", name="Follow System").check()
        self._expect("html").to_have_attribute("data-theme", "light")
        case.assertEqual(
            case.page.evaluate("(key) => window.localStorage.getItem(key)", storage_key),
            None,
        )
        case.page.click("#shell-preferences-close")
        expect(preferences).not_to_be_visible()

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_compare_summary_toolbar_edits_canonical_configuration_at_both_widths(
        self,
    ) -> None:
        case = self._case()
        case.page.set_viewport_size({"width": 1280, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [1280, 800])
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        toolbar = case.page.locator(".compare-setup-strip")
        expect(toolbar).to_be_visible()
        case.assertEqual(toolbar.locator('select[aria-label="Comparison rule"]').count(), 1)
        case.assertEqual(
            case.page.locator('select[aria-label="Comparison rule"]').count(),
            1,
        )
        case.assertTrue(
            bool(
                toolbar.evaluate(
                    "(node) => node.closest('.compare-wall-workspace') !== null "
                    "&& node.closest('.compare-setup-sidebar') === null"
                )
            )
        )
        expect(case.page.locator(".compare-setup-state")).to_have_text("Current")
        expect(case.page.locator(".compare-setup-run")).to_have_text("Up to date")
        expect(case.page.locator(".compare-setup-run")).to_be_disabled()

        seed_summary = case.page.get_by_role("button", name="Edit comparison seed")
        seed_summary.click()
        expect(case.page.locator(".compare-config-sheet")).to_have_class(re.compile(r"\bis-open\b"))
        expect(case.page.locator("#compare-config-panel-setup")).to_be_visible()
        seed_editor = case.page.locator('select[aria-label="Comparison seed"]')
        expect(seed_editor).to_be_focused()
        self._expect(".compare-filmstrip-board").to_have_count(4)
        case.page.click(".compare-config-sheet-close")

        tilings_summary = case.page.get_by_role("button", name="Choose tilings on the wall")
        tilings_summary.click()
        expect(case.page.locator("#compare-config-panel-tilings")).to_be_visible()
        expect(case.page.locator(".compare-tilings-search")).to_be_focused()
        self._expect(".compare-filmstrip-board").to_have_count(4)
        case.page.click(".compare-config-sheet-close")

        rule = case.page.locator('select[aria-label="Comparison rule"]')
        rule.select_option("wireworld")
        expect(rule).to_have_value("wireworld")
        expect(case.page.locator(".compare-setup-state")).to_have_text("Update queued")
        expect(case.page.locator(".compare-setup-run")).to_have_text("Update now")
        case.page.click(".compare-setup-run")
        expect(case.page.locator(".compare-setup-state")).to_have_text("Current", timeout=60_000)
        expect(case.page.locator(".compare-setup-run")).to_have_text("Up to date")

        # The canonical control and finished wall survive the existing route
        # round trip; returning does not reconstruct a second Rule select.
        case.page.click("#open-lab-btn")
        case.page.wait_for_function("() => window.location.hash === '#/lab'")
        self._expect("#grid").to_be_visible()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        expect(rule).to_have_value("wireworld")
        case.assertEqual(
            case.page.locator('select[aria-label="Comparison rule"]').count(),
            1,
        )

        def toolbar_colors() -> dict[str, str]:
            colors = case.page.evaluate(
                """() => {
                    const toolbar = document.querySelector(".compare-setup-strip");
                    const seed = document.querySelector(".compare-seed-summary");
                    const rule = document.querySelector(
                        'select[aria-label="Comparison rule"]'
                    );
                    if (!(toolbar instanceof HTMLElement)
                        || !(seed instanceof HTMLElement)
                        || !(rule instanceof HTMLElement)) {
                        throw new Error("Missing Compare summary toolbar surface");
                    }
                    return {
                        toolbar: getComputedStyle(toolbar).backgroundColor,
                        seed: getComputedStyle(seed).backgroundColor,
                        rule: getComputedStyle(rule).color,
                    };
                }"""
            )
            if not isinstance(colors, dict):
                raise AssertionError(f"invalid toolbar color snapshot: {colors!r}")
            return cast(dict[str, str], colors)

        menu_toggle = case.page.get_by_role("button", name="Open app menu")
        menu_toggle.click()
        case.page.click("#shell-preferences-btn")
        case.page.get_by_role("radio", name="Light").check()
        self._expect("html").to_have_attribute("data-theme", "light")
        light_colors = toolbar_colors()
        case.page.get_by_role("radio", name="Dark").check()
        self._expect("html").to_have_attribute("data-theme", "dark")
        dark_colors = toolbar_colors()
        for surface in ("toolbar", "seed", "rule"):
            with case.subTest(toolbar_theme_surface=surface):
                case.assertNotEqual(light_colors[surface], dark_colors[surface])
        case.page.click("#shell-preferences-close")

        case.page.set_viewport_size({"width": 390, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [390, 800])
        expect(toolbar).to_be_visible()
        expect(rule).to_be_visible()
        expect(seed_summary).to_be_visible()
        expect(tilings_summary).to_be_visible()
        expect(case.page.locator(".compare-setup-run")).to_be_visible()
        case.assertLessEqual(
            int(case.page.evaluate("() => document.documentElement.scrollWidth")),
            390,
        )
        toolbar_rects = case.page.evaluate(
            """() => [
                document.querySelector(".compare-setup-strip"),
                ...document.querySelectorAll(".compare-setup-strip > *"),
            ].map((node) => {
                if (!(node instanceof HTMLElement)) {
                    throw new Error("Missing Compare toolbar item");
                }
                const rect = node.getBoundingClientRect();
                return { left: rect.left, right: rect.right };
            })"""
        )
        if not isinstance(toolbar_rects, list):
            raise AssertionError(f"invalid toolbar rectangles: {toolbar_rects!r}")
        for rect in toolbar_rects:
            if not isinstance(rect, dict):
                raise AssertionError(f"invalid toolbar rectangle: {rect!r}")
            case.assertGreaterEqual(float(rect["left"]), 0)
            case.assertLessEqual(float(rect["right"]), 390)

        seed_summary.click()
        expect(seed_editor).to_be_focused()
        case.page.click(".compare-config-sheet-close")
        tilings_summary.click()
        expect(case.page.locator(".compare-tilings-search")).to_be_focused()
        case.page.click(".compare-config-sheet-close")
        case.assertLessEqual(
            int(case.page.evaluate("() => document.documentElement.scrollWidth")),
            390,
        )

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_compare_resizable_layout_persists_resets_and_preserves_narrow_drawers(
        self,
    ) -> None:
        case = self._case()
        layout_key = "cellular-automaton-lab.compare-layout.v1"
        case.page.set_viewport_size({"width": 1280, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [1280, 800])
        case.page.evaluate("(key) => window.localStorage.removeItem(key)", layout_key)
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        setup = case.page.locator(".compare-setup-sidebar")
        inspector = case.page.locator(".compare-inspector")
        setup_toggle = case.page.get_by_role("button", name="Configure the run")
        inspector_toggle = case.page.get_by_role("button", name="Inspect selected board")
        setup_splitter = case.page.get_by_role("separator", name="Resize Setup panel")
        inspector_splitter = case.page.get_by_role("separator", name="Resize Inspector panel")
        expect(setup_splitter).not_to_be_visible()
        expect(inspector_splitter).not_to_be_visible()

        setup_toggle.click()
        inspector_toggle.click()
        expect(setup).to_be_visible()
        expect(inspector).to_be_visible()
        expect(setup_splitter).to_be_visible()
        expect(inspector_splitter).to_be_visible()
        expect(setup_splitter).to_have_attribute("aria-orientation", "vertical")
        expect(setup_splitter).to_have_attribute("aria-valuemin", "220")
        expect(setup_splitter).to_have_attribute("aria-valuemax", "420")
        expect(setup_splitter).to_have_attribute("aria-valuenow", "250")
        expect(inspector_splitter).to_have_attribute("aria-valuenow", "270")

        # Exercise a full pointer sequence against the rendered hit target.
        setup_box = setup_splitter.bounding_box()
        if setup_box is None:
            raise AssertionError("Setup splitter rectangle was unavailable")
        pointer_y = setup_box["y"] + setup_box["height"] / 2
        pointer_x = setup_box["x"] + setup_box["width"] / 2
        case.page.mouse.move(pointer_x, pointer_y)
        case.page.mouse.down()
        case.page.mouse.move(pointer_x + 60, pointer_y, steps=4)
        case.page.mouse.up()
        expect(setup_splitter).to_have_attribute("aria-valuenow", "310")

        # Setup grows rightward; Inspector grows leftward. Shift modifies the
        # normal 10px step to 40px, while Home/End select truthful limits.
        setup_splitter.focus()
        setup_splitter.press("ArrowRight")
        expect(setup_splitter).to_have_attribute("aria-valuenow", "320")
        setup_splitter.press("Shift+ArrowLeft")
        expect(setup_splitter).to_have_attribute("aria-valuenow", "280")
        setup_splitter.press("Home")
        expect(setup_splitter).to_have_attribute("aria-valuenow", "220")
        setup_splitter.press("End")
        expect(setup_splitter).to_have_attribute("aria-valuenow", "420")

        inspector_splitter.focus()
        inspector_splitter.press("ArrowLeft")
        expect(inspector_splitter).to_have_attribute("aria-valuenow", "280")
        inspector_splitter.press("Shift+ArrowRight")
        expect(inspector_splitter).to_have_attribute("aria-valuenow", "240")
        inspector_splitter.press("Home")
        expect(inspector_splitter).to_have_attribute("aria-valuenow", "240")
        inspector_splitter.press("End")
        expect(inspector_splitter).to_have_attribute("aria-valuenow", "440")
        expect(setup_splitter).to_have_attribute("aria-valuemax", "420")

        wall_width = case.page.locator(".compare-wall-workspace").bounding_box()
        if wall_width is None:
            raise AssertionError("Compare wall rectangle was unavailable")
        case.assertGreaterEqual(wall_width["width"], 400)

        stored_before_reload = case.page.evaluate(
            "(key) => window.localStorage.getItem(key)", layout_key
        )
        if not isinstance(stored_before_reload, str):
            raise AssertionError(f"invalid stored Compare layout: {stored_before_reload!r}")
        case.reload_page(wait_until="load")
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [1280, 800])
        self._expect(".wall-page").to_be_visible()
        setup = case.page.locator(".compare-setup-sidebar")
        inspector = case.page.locator(".compare-inspector")
        setup_splitter = case.page.get_by_role("separator", name="Resize Setup panel")
        inspector_splitter = case.page.get_by_role("separator", name="Resize Inspector panel")
        expect(setup).to_be_visible()
        expect(inspector).to_be_visible()
        expect(setup_splitter).to_have_attribute("aria-valuenow", "420")
        expect(inspector_splitter).to_have_attribute("aria-valuenow", "440")
        case.assertEqual(
            case.page.evaluate("(key) => window.localStorage.getItem(key)", layout_key),
            stored_before_reload,
        )

        # The splitter states follow both themes and survive the existing
        # Compare -> Lab -> Compare route round trip.
        menu_toggle = case.page.get_by_role("button", name="Open app menu")
        menu_toggle.click()
        case.page.click("#shell-preferences-btn")
        preferences = case.page.get_by_role("dialog", name="Preferences")
        expect(preferences).to_be_visible()
        case.page.get_by_role("radio", name="Light").check()
        light_splitter_color = setup_splitter.evaluate(
            "(node) => getComputedStyle(node).backgroundColor"
        )
        case.page.get_by_role("radio", name="Dark").check()
        dark_splitter_color = setup_splitter.evaluate(
            "(node) => getComputedStyle(node).backgroundColor"
        )
        case.assertNotEqual(light_splitter_color, dark_splitter_color)
        case.page.click("#shell-preferences-close")
        case.page.click("#open-lab-btn")
        case.page.wait_for_function("() => window.location.hash === '#/lab'")
        self._expect("#grid").to_be_visible()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        expect(setup_splitter).to_have_attribute("aria-valuenow", "420")
        expect(inspector_splitter).to_have_attribute("aria-valuenow", "440")

        # Global Preferences resets only this layout and applies immediately.
        menu_toggle.click()
        case.page.click("#shell-preferences-btn")
        case.page.get_by_role("button", name="Reset Compare layout").click()
        self._expect("#shell-preferences-compare-layout-status").to_have_text(
            "Compare layout reset."
        )
        case.assertEqual(
            case.page.evaluate("(key) => window.localStorage.getItem(key)", layout_key),
            None,
        )
        expect(setup).not_to_be_visible()
        expect(inspector).not_to_be_visible()
        expect(setup_splitter).not_to_be_visible()
        expect(inspector_splitter).not_to_be_visible()
        case.page.click("#shell-preferences-close")

        # Store a fresh desktop layout, then prove that narrow overlay activity
        # is exclusive and does not mutate it.
        setup_toggle = case.page.get_by_role("button", name="Configure the run")
        inspector_toggle = case.page.get_by_role("button", name="Inspect selected board")
        setup_toggle.click()
        inspector_toggle.click()
        setup_splitter.press("ArrowRight")
        inspector_splitter.press("ArrowLeft")
        desktop_layout = case.page.evaluate("(key) => window.localStorage.getItem(key)", layout_key)
        if not isinstance(desktop_layout, str):
            raise AssertionError(f"invalid stored desktop Compare layout: {desktop_layout!r}")

        case.page.set_viewport_size({"width": 390, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [390, 800])
        expect(setup_splitter).not_to_be_visible()
        expect(inspector_splitter).not_to_be_visible()
        expect(setup).not_to_be_visible()
        expect(inspector).not_to_be_visible()

        setup_toggle.click()
        expect(setup).to_be_visible()
        expect(inspector).not_to_be_visible()
        # The open overlay intentionally blocks pointer input to the dock; use
        # the keyboard path to exercise the controller's exclusive handoff.
        inspector_toggle.press("Enter")
        expect(setup).not_to_be_visible()
        expect(inspector).to_be_visible()
        case.page.get_by_role("button", name="Close inspector").click()
        expect(inspector).not_to_be_visible()
        case.assertEqual(
            case.page.evaluate("(key) => window.localStorage.getItem(key)", layout_key),
            desktop_layout,
        )
        case.assertLessEqual(
            int(case.page.evaluate("() => document.documentElement.scrollWidth")),
            390,
        )

        case.page.set_viewport_size({"width": 1280, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [1280, 800])
        expect(setup).to_be_visible()
        expect(inspector).to_be_visible()
        expect(setup_splitter).to_have_attribute("aria-valuenow", "260")
        expect(inspector_splitter).to_have_attribute("aria-valuenow", "280")
        case.assertLessEqual(
            int(case.page.evaluate("() => document.documentElement.scrollWidth")),
            1280,
        )

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_compare_tabs_and_selected_actions_preserve_order_focus_and_toolbelt(
        self,
    ) -> None:
        case = self._case()
        case.page.set_viewport_size({"width": 1280, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [1280, 800])
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        setup_toggle = case.page.get_by_role("button", name="Configure the run")
        setup_toggle.click()
        tablist = case.page.get_by_role("tablist", name="Configuration views")
        expect(tablist).to_be_visible()
        expect(tablist).to_have_attribute("aria-orientation", "horizontal")
        tabs = {
            name: case.page.get_by_role("tab", name=name, exact=True)
            for name in ("Setup", "Tilings", "Help", "Saved")
        }
        expect(tabs["Setup"]).to_have_attribute("aria-selected", "true")
        expect(tabs["Setup"]).to_have_attribute("tabindex", "0")
        for name in ("Tilings", "Help", "Saved"):
            expect(tabs[name]).to_have_attribute("aria-selected", "false")
            expect(tabs[name]).to_have_attribute("tabindex", "-1")

        tab_rects = tablist.locator('[role="tab"]').evaluate_all(
            """tabs => tabs.map((tab) => {
                const rect = tab.getBoundingClientRect();
                return { left: rect.left, right: rect.right };
            })"""
        )
        for previous, following in zip(tab_rects, tab_rects[1:], strict=False):
            case.assertLessEqual(abs(float(previous["right"]) - float(following["left"])), 1.5)

        tabs["Setup"].focus()
        tabs["Setup"].press("ArrowRight")
        expect(tabs["Tilings"]).to_be_focused()
        expect(tabs["Tilings"]).to_have_attribute("aria-selected", "true")
        expect(case.page.get_by_role("tabpanel", name="Tilings")).to_be_visible()
        tabs["Tilings"].press("ArrowRight")
        expect(tabs["Help"]).to_be_focused()
        expect(case.page.get_by_role("tabpanel", name="Help")).to_be_visible()
        tabs["Help"].press("End")
        expect(tabs["Saved"]).to_be_focused()
        expect(case.page.get_by_role("tabpanel", name="Saved")).to_be_visible()
        tabs["Saved"].press("Home")
        expect(tabs["Setup"]).to_be_focused()
        tabs["Setup"].press("ArrowLeft")
        expect(tabs["Saved"]).to_be_focused()

        def selected_tab_colors() -> list[str]:
            return cast(
                list[str],
                tabs["Saved"].evaluate(
                    """selected => {
                        const other = selected.parentElement?.querySelector(
                            '[role="tab"]:not([aria-selected="true"])'
                        );
                        if (!(other instanceof HTMLElement)) {
                            throw new Error("missing unselected Compare tab");
                        }
                        const selectedStyle = getComputedStyle(selected);
                        const otherStyle = getComputedStyle(other);
                        return [
                            selectedStyle.backgroundColor,
                            selectedStyle.borderBottomColor,
                            selectedStyle.boxShadow,
                            otherStyle.backgroundColor,
                            otherStyle.borderBottomColor,
                        ];
                    }"""
                ),
            )

        menu_toggle = case.page.get_by_role("button", name="Open app menu")
        menu_toggle.click()
        case.page.get_by_role("button", name="Preferences", exact=True).click()
        case.page.get_by_role("radio", name="Light").check()
        self._expect("html").to_have_attribute("data-theme", "light")
        light_tab_colors = selected_tab_colors()
        case.page.get_by_role("radio", name="Dark").check()
        self._expect("html").to_have_attribute("data-theme", "dark")
        dark_tab_colors = selected_tab_colors()
        case.assertNotEqual(light_tab_colors[0], light_tab_colors[3])
        case.assertNotEqual(dark_tab_colors[0], dark_tab_colors[3])
        case.page.get_by_role("button", name="Close preferences").click()
        case.page.get_by_role("button", name="Close configuration").click()

        labels_before = case.page.locator(".compare-filmstrip-label").all_text_contents()
        case.assertEqual(case.page.locator(".compare-filmstrip-remove").count(), 0)
        self._select_compare_board(1)
        selected_name = labels_before[1]
        toolbelt = case.page.locator(".compare-hero-toolbelt")
        expect(toolbelt).to_be_visible()
        case.page.evaluate(
            """() => {
                window.__phase4Toolbelt = document.querySelector('.compare-hero-toolbelt');
            }"""
        )
        replace_selected = case.page.locator(".compare-inspector-replace")
        remove_selected = case.page.locator(".compare-inspector-remove")
        expect(replace_selected).to_have_text("Replace selected")
        expect(remove_selected).to_have_text("Remove selected")
        expect(replace_selected).to_have_attribute(
            "aria-label", re.compile(re.escape(selected_name))
        )
        expect(remove_selected).to_have_attribute(
            "aria-label", re.compile(re.escape(selected_name))
        )

        replace_selected.click()
        search = case.page.locator(".compare-board-tiling-picker-search")
        expect(search).to_be_focused()
        disabled_reasons = case.page.locator(".compare-board-tiling-choice:disabled").evaluate_all(
            "choices => choices.map((choice) => choice.title)"
        )
        case.assertTrue(
            any(
                "current tiling" in reason or "already on the wall" in reason
                for reason in disabled_reasons
            )
        )
        replacement = case.page.locator(".compare-board-tiling-choice:not(:disabled)").first
        replacement_name = replacement.locator(
            ".compare-board-tiling-choice-copy > span"
        ).inner_text()
        search.fill(replacement_name)
        replacement = case.page.locator(".compare-board-tiling-choice:not(:disabled)").first
        replacement.click()
        expected_after_replace = list(labels_before)
        expected_after_replace[1] = replacement_name
        expect(case.page.locator(".compare-setup-run")).to_have_text("Up to date", timeout=60_000)
        case.assertEqual(
            case.page.locator(".compare-filmstrip-label").all_text_contents(),
            expected_after_replace,
        )
        expect(
            case.page.locator(".compare-filmstrip-board.is-selected .compare-filmstrip-label")
        ).to_have_text(replacement_name)
        case.assertTrue("focus=" in case.page.evaluate("() => window.location.hash"))
        case.assertTrue(
            case.page.evaluate(
                """() => window.__phase4Toolbelt ===
                    document.querySelector('.compare-hero-toolbelt') &&
                    document.querySelector('.compare-hero-toolbelt')?.isConnected === true"""
            )
        )

        remove_selected.click()
        self._expect(".compare-filmstrip-board").to_have_count(3, timeout=60_000)
        expected_after_remove = [
            expected_after_replace[0],
            expected_after_replace[2],
            expected_after_replace[3],
        ]
        case.assertEqual(
            case.page.locator(".compare-filmstrip-label").all_text_contents(),
            expected_after_remove,
        )
        case.assertTrue("focus=" not in case.page.evaluate("() => window.location.hash"))
        expect(
            case.page.locator(".compare-filmstrip-board.is-selected .compare-filmstrip-label")
        ).to_have_text(expected_after_remove[1])

        # The nearest survivor remains selected, so one more activation reaches
        # the floor without a separate per-board action.
        remove_selected.click()
        self._expect(".compare-filmstrip-board").to_have_count(2, timeout=60_000)
        case.assertEqual(
            case.page.locator(".compare-filmstrip-label").all_text_contents(),
            [expected_after_remove[0], expected_after_remove[2]],
        )
        expect(remove_selected).to_be_visible()
        expect(remove_selected).to_be_disabled()
        expect(remove_selected).to_have_attribute("title", "Keep at least two tilings on the wall")

        # One persistent node moves to the speaker hero and back to Inspector,
        # retaining its visible action labels and current target.
        self._select_compare_board(0)
        case.assertTrue(
            case.page.evaluate(
                """() => window.__phase4Toolbelt === document.querySelector(
                    '.compare-filmstrip-board.is-hero .compare-hero-toolbelt'
                )"""
            )
        )
        expect(toolbelt).to_contain_text("Replace selected")
        expect(toolbelt).to_contain_text("Remove selected")
        case.page.locator(".compare-hero-back").click()
        case.assertTrue(
            case.page.evaluate(
                """() => window.__phase4Toolbelt === document.querySelector(
                    '.compare-inspector-body > .compare-hero-toolbelt'
                )"""
            )
        )

        # Compare -> Lab -> Compare keeps the ordered wall and selected toolbelt.
        self._select_compare_board(0)
        case.page.locator(".compare-hero-open-lab").click()
        self._expect("#grid").to_be_visible(timeout=60_000)
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        case.assertEqual(
            case.page.locator(".compare-filmstrip-label").all_text_contents(),
            [expected_after_remove[0], expected_after_remove[2]],
        )
        case.assertTrue(
            case.page.evaluate(
                """() => window.__phase4Toolbelt ===
                    document.querySelector('.compare-hero-toolbelt')"""
            )
        )

        case.page.set_viewport_size({"width": 390, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [390, 800])
        setup_toggle.click()
        expect(tablist).to_be_visible()
        tabs["Saved"].focus()
        tabs["Saved"].press("Home")
        expect(tabs["Setup"]).to_be_focused()
        tabs["Setup"].press("ArrowRight")
        expect(tabs["Tilings"]).to_be_focused()
        case.page.get_by_role("button", name="Close configuration").click()
        case.assertLessEqual(
            int(case.page.evaluate("() => document.documentElement.scrollWidth")),
            390,
        )
        self._select_compare_board(1)
        expect(toolbelt).to_be_visible()
        expect(remove_selected).to_be_disabled()
        expect(remove_selected).to_have_attribute("title", "Keep at least two tilings on the wall")
        case.page.locator(".compare-hero-back").click()
        case.assertTrue(
            case.page.evaluate(
                """() => window.__phase4Toolbelt ===
                    document.querySelector('.compare-hero-toolbelt') &&
                    document.querySelector('.compare-hero-toolbelt')?.isConnected === true"""
            )
        )
        case.assertLessEqual(
            int(case.page.evaluate("() => document.documentElement.scrollWidth")),
            390,
        )

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_compare_wall_history_restores_membership_playback_and_shortcuts(
        self,
    ) -> None:
        case = self._case()
        case.page.set_viewport_size({"width": 1280, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [1280, 800])
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        boards = case.page.locator(".compare-filmstrip-board")
        labels = case.page.locator(".compare-filmstrip-label")
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        initial_labels = labels.all_text_contents()

        case.page.get_by_role("button", name="Step forward one generation").click()
        expect(case.page.locator(".compare-filmstrip-counter")).to_contain_text("gen 1 /")
        playback = case.page.locator('.compare-filmstrip-btn[title="Play / pause"]')
        playback.click()
        expect(playback).to_contain_text("Pause")
        self._select_compare_board(1)
        selected_name = initial_labels[1]
        case.page.locator(".compare-inspector-replace").click()
        replacement = case.page.locator(".compare-board-tiling-choice:not(:disabled)").first
        replacement_name = replacement.locator(
            ".compare-board-tiling-choice-copy > span"
        ).inner_text()
        replacement.click()

        history = case.page.locator(".compare-history-snackbar")
        history_action = case.page.locator(".compare-history-action")
        expected_replaced = list(initial_labels)
        expected_replaced[1] = replacement_name
        expect(case.page.locator(".compare-setup-run")).to_have_text("Up to date", timeout=60_000)
        expect(history).to_be_visible()
        expect(history).to_contain_text(f"Replace {selected_name} with {replacement_name}")
        expect(history_action).to_have_text("Undo")
        expect(playback).to_contain_text("Play")
        case.assertEqual(labels.all_text_contents(), expected_replaced)

        def history_colors() -> list[str]:
            return cast(
                list[str],
                history.evaluate(
                    """node => {
                        const style = getComputedStyle(node);
                        return [style.backgroundColor, style.color, style.borderColor];
                    }"""
                ),
            )

        case.page.click("#shell-menu-toggle")
        case.page.click("#shell-preferences-btn")
        case.page.get_by_role("radio", name="Light").check()
        light_history_colors = history_colors()
        case.page.get_by_role("radio", name="Dark").check()
        dark_history_colors = history_colors()
        case.assertNotEqual(light_history_colors[0], dark_history_colors[0])
        case.assertNotEqual(light_history_colors[1], dark_history_colors[1])
        case.assertNotEqual(light_history_colors[0], "rgba(0, 0, 0, 0)")
        case.assertNotEqual(dark_history_colors[0], "rgba(0, 0, 0, 0)")
        case.page.get_by_role("button", name="Close preferences").click()

        history_action.click()
        expect(history_action).to_have_text("Redo", timeout=60_000)
        case.assertEqual(labels.all_text_contents(), initial_labels)
        expect(playback).to_contain_text("Pause")
        expect(
            case.page.locator(".compare-filmstrip-board.is-selected .compare-filmstrip-label")
        ).to_have_text(selected_name)
        case.assertTrue("focus=" in str(case.page.evaluate("() => window.location.hash")))
        playback.click()
        expect(playback).to_contain_text("Play")

        history_action.click()
        expect(history_action).to_have_text("Undo", timeout=60_000)
        case.assertEqual(labels.all_text_contents(), expected_replaced)
        expect(playback).to_contain_text("Play")
        expect(
            case.page.locator(".compare-filmstrip-board.is-selected .compare-filmstrip-label")
        ).to_have_text(replacement_name)

        case.page.locator(".compare-inspector-remove").click()
        expected_removed = [expected_replaced[0], *expected_replaced[2:]]
        expect(boards).to_have_count(3)
        case.assertEqual(labels.all_text_contents(), expected_removed)
        expect(history).to_contain_text(f"Remove {replacement_name}")
        history_action.click()
        expect(history_action).to_have_text("Redo", timeout=60_000)
        case.assertEqual(labels.all_text_contents(), expected_replaced)
        history_action.click()
        expect(history_action).to_have_text("Undo", timeout=60_000)
        case.assertEqual(labels.all_text_contents(), expected_removed)

        case.page.locator(".compare-filmstrip-add").click()
        add_choice = case.page.locator(".compare-board-tiling-choice:not(:disabled)").first
        added_name = add_choice.locator(".compare-board-tiling-choice-copy > span").inner_text()
        add_choice.click()
        expect(case.page.locator(".compare-setup-run")).to_have_text("Up to date", timeout=60_000)
        expected_added = [*expected_removed, added_name]
        case.assertEqual(labels.all_text_contents(), expected_added)
        expect(history).to_contain_text(f"Add {added_name}")

        wall_page = case.page.locator(".wall-page")
        wall_page.focus()
        case.page.keyboard.press("Control+z")
        expect(history_action).to_have_text("Redo", timeout=60_000)
        case.assertEqual(labels.all_text_contents(), expected_removed)
        case.page.keyboard.press("Control+Shift+z")
        expect(history_action).to_have_text("Undo", timeout=60_000)
        case.assertEqual(labels.all_text_contents(), expected_added)
        case.page.keyboard.press("Control+z")
        expect(history_action).to_have_text("Redo", timeout=60_000)
        case.assertEqual(labels.all_text_contents(), expected_removed)
        case.page.keyboard.press("Control+y")
        expect(history_action).to_have_text("Undo", timeout=60_000)
        case.assertEqual(labels.all_text_contents(), expected_added)

        # Use the always-visible rule selector for the real-browser editor
        # check. The seed bit input lives inside a collapsed <details> region,
        # so attempting to focus it leaves focus on the wall and would
        # correctly trigger wall undo instead of exercising shortcut yielding.
        rule_select = case.page.get_by_label("Comparison rule")
        expect(rule_select).to_be_visible()
        rule_select.focus()
        case.page.keyboard.press("Control+z")
        case.assertEqual(labels.all_text_contents(), expected_added)
        case.page.evaluate(
            """() => {
                const event = new KeyboardEvent('keydown', {
                    key: 'z',
                    ctrlKey: true,
                    bubbles: true,
                    cancelable: true,
                });
                event.preventDefault();
                document.querySelector('.wall-page')?.dispatchEvent(event);
            }"""
        )
        case.assertEqual(labels.all_text_contents(), expected_added)

        self._select_compare_board(0)
        case.page.locator(".compare-hero-open-lab").click()
        self._expect("#grid").to_be_visible(timeout=60_000)
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        case.assertEqual(labels.all_text_contents(), expected_added)
        expect(history_action).to_have_text("Undo")

        case.page.set_viewport_size({"width": 390, "height": 800})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [390, 800])
        snackbar_rect = cast(
            dict[str, float],
            history.evaluate(
                """node => {
                    const rect = node.getBoundingClientRect();
                    return {
                        left: rect.left,
                        right: rect.right,
                        top: rect.top,
                        bottom: rect.bottom,
                    };
                }"""
            ),
        )
        case.assertGreaterEqual(float(snackbar_rect["left"]), 0)
        case.assertLessEqual(float(snackbar_rect["right"]), 390)
        case.assertGreaterEqual(float(snackbar_rect["top"]), 0)
        case.assertLessEqual(float(snackbar_rect["bottom"]), 800)
        case.assertLessEqual(
            int(case.page.evaluate("() => document.documentElement.scrollWidth")),
            390,
        )

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

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
        self._expect("#patch-depth-input").to_have_value("4")
        # The one-shell stage is taller than the old top-bar layout, so the
        # fitted patch's bounding box covers slightly less width (~0.949);
        # 0.9 matches the other aperiodic patch cases.
        self._assert_browser_visible_aperiodic_patch(
            minimum_fill_colors=1,
            minimum_coverage_width_ratio=0.9,
            minimum_coverage_height_ratio=0.9,
        )
        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "false")
        self._assert_browser_visible_aperiodic_patch(
            minimum_fill_colors=1,
            minimum_coverage_width_ratio=0.9,
            minimum_coverage_height_ratio=0.9,
        )
        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "true")

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
        self._expect("#patch-depth-input").to_have_value("3")
        self._assert_browser_visible_aperiodic_patch(minimum_fill_colors=2)
        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "false")
        self._assert_browser_visible_aperiodic_patch(
            minimum_fill_colors=2,
            minimum_coverage_width_ratio=0.9,
            minimum_coverage_height_ratio=0.9,
        )
        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "true")

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

    def test_polygon_incremental_redraw_matches_full_render(self) -> None:
        case = self._case()

        def render_counts() -> tuple[int, int]:
            raw_counts = case.page.evaluate(
                """() => {
                    const canvas = document.getElementById("grid");
                    return [
                        Number(canvas?.getAttribute("data-render-full-count") || "0"),
                        Number(canvas?.getAttribute("data-render-incremental-count") || "0"),
                    ];
                }"""
            )
            if not isinstance(raw_counts, list) or len(raw_counts) != 2:
                raise AssertionError(f"invalid canvas render counters: {raw_counts!r}")
            return (int(raw_counts[0]), int(raw_counts[1]))

        def canvas_signature() -> str:
            signature = case.page.evaluate(
                """() => {
                    const canvas = document.getElementById("grid");
                    if (!(canvas instanceof HTMLCanvasElement)) {
                        throw new Error("grid canvas is missing");
                    }
                    return canvas.toDataURL("image/png");
                }"""
            )
            if not isinstance(signature, str):
                raise AssertionError("canvas signature was invalid")
            return signature

        for tiling_family in ("deltoidal-hexagonal", "shield"):
            with case.subTest(tiling_family=tiling_family):
                self._select_tiling_family_and_wait_for_reset(tiling_family)
                self._wait_for_patch_render_complete()
                target = case.page.evaluate(
                    """() => {
                        const diagnostics = window.__reviewApi?.getDiagnostics();
                        const sample = diagnostics?.transformReport?.sampleCells.centerNearest;
                        const width = diagnostics?.transformReport?.renderMetrics.cssWidth;
                        const height = diagnostics?.transformReport?.renderMetrics.cssHeight;
                        return sample && width && height
                            ? { id: sample.cellId, ...sample.renderedCenter, width, height }
                            : null;
                    }"""
                )
                if not isinstance(target, dict):
                    raise AssertionError(f"missing polygon render target for {tiling_family}")

                # The topology switch may finish through a fitted preview before its
                # stable render key is installed. A no-op review snapshot settles that
                # key without changing any cells, so the next update isolates the delta.
                self._apply_review_cell_states({})
                case.page.wait_for_timeout(75)

                canvas = case.page.locator("#grid")
                bounding_box = canvas.bounding_box()
                if bounding_box is None:
                    raise AssertionError("grid canvas bounding box was unavailable")
                position = {
                    "x": float(target["x"]) * bounding_box["width"] / float(target["width"]),
                    "y": float(target["y"]) * bounding_box["height"] / float(target["height"]),
                }
                full_count, incremental_count = render_counts()
                self._apply_review_cell_states({str(target["id"]): 1})
                case.page.wait_for_function(
                    """([previousFullCount, previousIncrementalCount]) => {
                        const canvas = document.getElementById("grid");
                        const fullCount = Number(canvas?.getAttribute(
                            "data-render-full-count"
                        ) || "0");
                        const incrementalCount = Number(canvas?.getAttribute(
                            "data-render-incremental-count"
                        ) || "0");
                        return fullCount + incrementalCount >
                            previousFullCount + previousIncrementalCount;
                    }""",
                    arg=[full_count, incremental_count],
                )
                case.assertEqual(
                    render_counts()[1],
                    incremental_count + 1,
                    case.page.locator("#grid").evaluate(
                        "canvas => JSON.stringify({ ...canvas.dataset })"
                    ),
                )
                self._expect("#grid").to_have_attribute("data-render-mode", "incremental")
                case.page.wait_for_timeout(350)
                incremental_signature = canvas_signature()

                full_count, _ = render_counts()
                case.page.evaluate(
                    """async () => {
                        if (typeof window.__reviewApi?.forceFullRender !== "function") {
                            throw new Error("review full-render hook is unavailable");
                        }
                        await window.__reviewApi.forceFullRender();
                    }"""
                )
                case.page.wait_for_function(
                    """(previousCount) =>
                        Number(document.getElementById("grid")?.getAttribute(
                            "data-render-full-count"
                        ) || "0") > previousCount""",
                    arg=full_count,
                )
                self._expect("#grid").to_have_attribute("data-render-mode", "full")
                case.assertEqual(canvas_signature(), incremental_signature)

                if tiling_family == "deltoidal-hexagonal":
                    cell_size = case.page.locator("#cell-size-input")
                    self._expect("#cell-size-input").to_be_visible()
                    original_size = int(cell_size.input_value())
                    maximum_size = int(cell_size.get_attribute("max") or original_size)
                    next_size = (
                        original_size + 1 if original_size < maximum_size else original_size - 1
                    )
                    full_count, _ = render_counts()
                    cell_size.fill(str(next_size))
                    case.page.wait_for_function(
                        """(previousCount) =>
                            Number(document.getElementById("grid")?.getAttribute(
                                "data-render-full-count"
                            ) || "0") > previousCount""",
                        arg=full_count,
                    )
                    full_count, _ = render_counts()
                    cell_size.fill(str(original_size))
                    case.page.wait_for_function(
                        """(previousCount) =>
                            Number(document.getElementById("grid")?.getAttribute(
                                "data-render-full-count"
                            ) || "0") > previousCount""",
                        arg=full_count,
                    )

                committed_counts = render_counts()
                case.page.mouse.move(
                    bounding_box["x"] + position["x"],
                    bounding_box["y"] + position["y"],
                )
                canvas.click(button="right", position=position)
                self._expect("#selection-inspector-title").to_contain_text("1 Cell Selected")
                case.assertEqual(render_counts(), committed_counts)
                canvas.click(button="right", position=position)

                self._apply_review_cell_states({str(target["id"]): 0})
                arm_button = case.page.locator("#canvas-toolbar-arm-btn")
                if arm_button.is_visible() and arm_button.get_attribute("aria-pressed") != "true":
                    arm_button.click()
                canvas.click(position=position)
                self._expect("#canvas-toolbar-undo-btn").to_be_enabled()

                if tiling_family == "deltoidal-hexagonal":
                    viewport = case.page.viewport_size
                    if viewport is None:
                        raise AssertionError("browser viewport size was unavailable")
                    full_count, _ = render_counts()
                    case.page.set_viewport_size(
                        {"width": viewport["width"] - 120, "height": viewport["height"] - 80}
                    )
                    case.page.wait_for_function(
                        """(previousCount) =>
                            Number(document.getElementById("grid")?.getAttribute(
                                "data-render-full-count"
                            ) || "0") > previousCount""",
                        arg=full_count,
                    )
                    case.page.set_viewport_size(viewport)

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
        self._expect("#drawer-toggle-btn").to_have_text("Hide Controls")

        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "false")

        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "true")

    def test_canvas_hud_does_not_overlap_canvas_at_supported_widths(self) -> None:
        case = self._case()

        for width in (1280, 820):
            with case.subTest(width=width):
                case.page.set_viewport_size({"width": width, "height": 900})
                case.page.wait_for_function(
                    "([width, height]) => innerWidth === width && innerHeight === height",
                    arg=[width, 900],
                )
                geometry = cast(
                    dict[str, float],
                    case.page.evaluate(
                        """() => {
                            const hud = document.getElementById("canvas-hud");
                            const viewport = document.getElementById("grid-viewport");
                            const canvas = document.getElementById("grid");
                            if (!hud || !viewport || !(canvas instanceof HTMLCanvasElement)) {
                                throw new Error("Lab canvas geometry is unavailable");
                            }
                            const hudRect = hud.getBoundingClientRect();
                            const viewportRect = viewport.getBoundingClientRect();
                            const canvasRect = canvas.getBoundingClientRect();
                            return {
                                hudBottom: hudRect.bottom,
                                viewportTop: viewportRect.top,
                                canvasTop: canvasRect.top,
                            };
                        }"""
                    ),
                )
                case.assertGreaterEqual(geometry["viewportTop"], geometry["hudBottom"])
                case.assertGreaterEqual(geometry["canvasTop"], geometry["hudBottom"])

    def test_canvas_stays_fixed_when_lab_overlays_change(self) -> None:
        case = self._case()

        def canvas_metrics() -> dict[str, Any]:
            return cast(
                dict[str, Any],
                case.page.evaluate(
                    """() => {
                        const viewport = document.getElementById("grid-viewport");
                        const canvas = document.getElementById("grid");
                        if (!viewport || !(canvas instanceof HTMLCanvasElement)) {
                            throw new Error("Lab canvas is unavailable");
                        }
                        const canvasRect = canvas.getBoundingClientRect();
                        return {
                            innerWidth: window.innerWidth,
                            innerHeight: window.innerHeight,
                            board: document.getElementById("grid-size-text")?.textContent,
                            viewportWidth: viewport.clientWidth,
                            viewportHeight: viewport.clientHeight,
                            scrollWidth: viewport.scrollWidth,
                            scrollHeight: viewport.scrollHeight,
                            canvasLeft: canvasRect.left,
                            canvasTop: canvasRect.top,
                            canvasWidth: canvasRect.width,
                            canvasHeight: canvasRect.height,
                            renderCellSize: Number(canvas.dataset.renderCellSize || "0"),
                        };
                    }"""
                ),
            )

        def wait_for_fitted_canvas() -> dict[str, Any]:
            case.page.wait_for_function(
                """() => {
                    const viewport = document.getElementById("grid-viewport");
                    return Boolean(
                        viewport &&
                        viewport.scrollWidth <= viewport.clientWidth + 1 &&
                        viewport.scrollHeight <= viewport.clientHeight + 1
                    );
                }"""
            )
            metrics = canvas_metrics()
            case.assertLessEqual(metrics["scrollWidth"], metrics["viewportWidth"] + 1)
            case.assertLessEqual(metrics["scrollHeight"], metrics["viewportHeight"] + 1)
            return metrics

        def settled_canvas_metrics() -> dict[str, Any]:
            # The old resize path was debounced behind a ResizeObserver and the
            # drawer transition. Wait past both before comparing geometry.
            case.page.wait_for_timeout(250)
            return wait_for_fitted_canvas()

        def assert_canvas_geometry_unchanged(
            expected: dict[str, Any], actual: dict[str, Any], transition: str
        ) -> None:
            case.assertEqual(
                actual["viewportWidth"], expected["viewportWidth"], f"{transition} changed width"
            )
            case.assertEqual(
                actual["viewportHeight"],
                expected["viewportHeight"],
                f"{transition} changed height",
            )
            for key in (
                "canvasLeft",
                "canvasTop",
                "canvasWidth",
                "canvasHeight",
                "renderCellSize",
            ):
                case.assertLessEqual(
                    abs(float(actual[key]) - float(expected[key])),
                    0.25,
                    f"{transition} changed {key}",
                )

        self._ensure_drawer_open()
        initial = settled_canvas_metrics()
        initial_board = initial["board"]
        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "false")
        assert_canvas_geometry_unchanged(
            initial, settled_canvas_metrics(), "closing the control drawer"
        )
        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "true")
        assert_canvas_geometry_unchanged(
            initial, settled_canvas_metrics(), "opening the control drawer"
        )
        case.assertEqual(canvas_metrics()["board"], initial_board)

        case.page.click("#reset-btn")
        self._wait_for_exported_pattern_payload(expected_rule="conway", expected_cells_by_id={})
        arm_button = case.page.locator("#canvas-toolbar-arm-btn")
        idle = settled_canvas_metrics()
        arm_button.click()
        self._expect("#canvas-toolbar-controls").to_be_visible()
        assert_canvas_geometry_unchanged(idle, settled_canvas_metrics(), "arming the canvas editor")

        case.page.click("#canvas-toolbar-dismiss-btn")
        self._expect("#canvas-toolbar-arm-btn").to_be_visible()
        assert_canvas_geometry_unchanged(
            idle, settled_canvas_metrics(), "leaving the canvas editor"
        )

        arm_button.click()
        self._expect("#canvas-toolbar-controls").to_be_visible()
        brush_button = case.page.locator('[data-editor-tool="brush"]')
        if brush_button.get_attribute("aria-pressed") != "true":
            brush_button.click()
        brush_size_button = case.page.locator('[data-brush-size="1"]')
        if brush_size_button.get_attribute("aria-pressed") != "true":
            brush_size_button.click()
        state_button = case.page.locator('[data-state-value="1"]')
        if state_button.get_attribute("aria-pressed") != "true":
            state_button.click()
        self._ensure_drawer_open()
        before_pointer = settled_canvas_metrics()
        self._click_canvas_center()
        self._expect("#canvas-toolbar-undo-btn").to_be_enabled()
        assert_canvas_geometry_unchanged(
            before_pointer, settled_canvas_metrics(), "clicking outside the canvas editor controls"
        )
        painted_payload = self._export_pattern_payload()
        painted_cells = painted_payload.get("cells_by_id")
        if not isinstance(painted_cells, dict):
            raise AssertionError(f"painted cells payload was invalid: {painted_cells!r}")
        case.assertEqual(len(painted_cells), 1)

        case.page.click("#run-toggle-btn")
        self._expect("#status-text").to_have_text("Running")
        self._expect("#canvas-toolbar").to_be_hidden()
        assert_canvas_geometry_unchanged(
            before_pointer, settled_canvas_metrics(), "hiding the canvas editor while running"
        )
        case.page.click("#run-toggle-btn")
        self._expect("#status-text").to_have_text("Paused")
        self._expect("#canvas-toolbar-arm-btn").to_be_visible()
        assert_canvas_geometry_unchanged(
            before_pointer, settled_canvas_metrics(), "restoring the canvas editor after running"
        )

        case.page.set_viewport_size({"width": 820, "height": 900})
        case.page.wait_for_function("() => window.innerWidth === 820 && window.innerHeight === 900")
        self._ensure_drawer_open()
        narrow_open = settled_canvas_metrics()
        case.assertEqual(narrow_open["innerWidth"], 820)
        case.assertEqual(narrow_open["innerHeight"], 900)
        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "false")
        assert_canvas_geometry_unchanged(
            narrow_open, settled_canvas_metrics(), "closing the narrow control drawer"
        )
        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "true")
        assert_canvas_geometry_unchanged(
            narrow_open, settled_canvas_metrics(), "opening the narrow control drawer"
        )
        case.page.click("#drawer-toggle-btn")
        self._expect("#control-drawer").to_have_attribute("data-open", "false")
        assert_canvas_geometry_unchanged(
            narrow_open, settled_canvas_metrics(), "closing the narrow control drawer again"
        )
        arm_button.click()
        self._expect("#canvas-toolbar-controls").to_be_visible()
        assert_canvas_geometry_unchanged(
            narrow_open, settled_canvas_metrics(), "arming the narrow canvas editor"
        )
        case.page.click("#canvas-toolbar-dismiss-btn")
        self._expect("#canvas-toolbar-arm-btn").to_be_visible()
        assert_canvas_geometry_unchanged(
            narrow_open, settled_canvas_metrics(), "leaving the narrow canvas editor"
        )

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

    def test_wall_playback_controls_preserve_the_shared_clock_contract(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        play_pause = case.page.locator('.compare-filmstrip-btn[aria-label="Play / pause"]')
        reset = case.page.locator('.compare-filmstrip-btn[title="Back to the seed"]')
        step_forward = case.page.locator(
            '.compare-filmstrip-btn[title="Step forward one generation"]'
        )
        scrubber = case.page.locator('input[aria-label="Generation"]')
        speed = case.page.locator('select[aria-label="Playback speed"]')
        counter = case.page.locator(".compare-filmstrip-counter")
        frame_max = scrubber.get_attribute("max")
        if frame_max is None:
            raise AssertionError("filmstrip generation scrubber is missing its maximum")
        final_generation = str(frame_max)

        reset.click()
        expect(counter).to_have_text(f"gen 0 / {final_generation}")
        step_forward.click()
        expect(counter).to_have_text(f"gen 1 / {final_generation}")
        scrubber.fill("3")
        expect(counter).to_have_text(f"gen 3 / {final_generation}")
        speed.select_option("2")
        expect(speed).to_have_value("2")

        play_pause.click()
        expect(play_pause).to_contain_text("Pause")
        case.page.wait_for_function(
            "expected => document.querySelector('.compare-filmstrip-counter')?.textContent !== expected",
            arg=f"gen 3 / {final_generation}",
        )
        play_pause.click()
        expect(play_pause).to_contain_text("Play")
        reset.click()
        expect(counter).to_have_text(f"gen 0 / {final_generation}")

    def test_focused_wall_board_hides_its_expand_affordance(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        first_board = case.page.locator(".compare-filmstrip-board").first
        expand = first_board.locator(".compare-filmstrip-expand")
        expect(expand).to_be_visible()

        first_board.click()

        expect(first_board).to_have_class(re.compile(r"\bis-hero\b"))
        expect(expand).to_be_hidden()

    def test_wall_rerun_resets_the_focused_explainer_generation(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        case.page.locator(".compare-filmstrip-board").first.click()
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(1)
        generation = case.page.locator(
            ".compare-explainer-item",
            has=case.page.locator(".compare-explainer-key", has_text="Generation"),
        ).locator(".compare-explainer-copy")
        step_forward = case.page.locator(
            '.compare-filmstrip-btn[title="Step forward one generation"]'
        )
        for _ in range(3):
            step_forward.click()
        expect(generation).to_have_text(re.compile(r"3 of \d+"))

        # Changing the seed rebuilds the wall in place while preserving focus.
        # The replacement filmstrip starts at generation zero, and the
        # explainer must render that store snapshot rather than the old player.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        seed_select = case.page.locator('select[aria-label="Comparison seed"]')
        seed_select.select_option("")
        self._expect(".compare-setup-run").to_have_text("Up to date", timeout=60_000)
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(1)
        expect(generation).to_have_text(re.compile(r"0 of \d+"))
        case.assertTrue("focus=" in case.page.url)

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

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

    def test_wall_real_keyboard_routing_and_layered_escape(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        self._expect(".compare-status").to_contain_text("Filmstrip ready", timeout=60_000)
        play_pause = case.page.locator('.compare-filmstrip-btn[aria-label="Play / pause"]')
        expect(play_pause).to_be_enabled()
        expect(play_pause).to_contain_text("Play")

        # Only the wall background owns global playback keys.
        case.page.locator(".wall-page").focus()
        case.page.keyboard.press("Space")
        expect(play_pause).to_contain_text("Pause")
        case.page.keyboard.press("Space")
        expect(play_pause).to_contain_text("Play")

        # Board Enter/Space owns focus, never the clock; Escape removes exactly
        # that speaker layer.
        first_board = case.page.locator(".compare-filmstrip-board").first
        first_board.focus()
        first_board.press("Enter")
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(1)
        expect(play_pause).to_contain_text("Play")
        case.page.keyboard.press("Escape")
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(0)

        # Search fields keep literal spaces. Escape closes the picker without
        # leaving the wall or touching playback.
        replace_selected = case.page.locator(".compare-inspector-replace")
        expect(replace_selected).to_have_attribute("aria-label", re.compile("Square"))
        replace_selected.press("Enter")
        picker_search = case.page.locator(".compare-board-tiling-picker-search")
        expect(picker_search).to_be_focused()
        picker_search.press("Space")
        expect(picker_search).to_have_value(" ")
        expect(play_pause).to_contain_text("Play")
        case.page.keyboard.press("Escape")
        self._expect(".compare-board-tiling-picker").to_have_count(0)

        # A focused setup field also retains Space. Layered Escape closes the
        # sheet first and speaker view second.
        first_board.focus()
        first_board.press("Space")
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(1)
        case.page.set_viewport_size({"width": 820, "height": 900})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [820, 900])
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        self._expect(".compare-config-sheet.is-open").to_be_visible()
        grid_size = case.page.locator(".compare-form label", has_text="Grid size").locator("input")
        grid_size.focus()
        grid_size.press("Space")
        expect(play_pause).to_contain_text("Play")
        case.page.keyboard.press("Escape")
        self._expect(".compare-config-sheet.is-open").to_have_count(0)
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(1)
        case.page.keyboard.press("Escape")
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(0)

        # Native route-button activation remains native and pauses the hidden
        # wall rather than being stolen by the global transport handler.
        lab_route = case.page.locator("#open-lab-btn")
        lab_route.focus()
        lab_route.press("Space")
        case.page.wait_for_function("() => window.location.hash === '#/lab'")
        self._expect("#grid").to_be_visible()
        case.page.locator("#wall-view-btn").press("Enter")
        self._expect(".wall-page").to_be_visible()
        expect(play_pause).to_contain_text("Play")

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_wall_analysis_modal_contains_focus_and_restores_its_opener(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        opener = case.page.locator(".compare-analysis-open")
        close = case.page.locator(".compare-analysis-close")
        workspace = case.page.locator(".compare-workspace")
        dialog = case.page.get_by_role("dialog", name="Statistical analysis")

        for width in (1280, 820):
            case.page.set_viewport_size({"width": width, "height": 900})
            opener.click()
            expect(dialog).to_be_visible()
            expect(workspace).to_have_attribute("inert", "")
            expect(close).to_be_focused()

            # Shift+Tab wraps to the dialog's last control, and Tab wraps back
            # to the close button instead of entering the inert wall beneath.
            case.page.keyboard.press("Shift+Tab")
            case.assertTrue(
                case.page.evaluate(
                    """() => document.querySelector('.compare-analysis-overlay')
                        ?.contains(document.activeElement) === true"""
                )
            )
            case.page.keyboard.press("Tab")
            expect(close).to_be_focused()

            case.page.keyboard.press("Escape")
            expect(dialog).to_be_hidden()
            expect(workspace).not_to_have_attribute("inert", "")
            expect(opener).to_be_focused()

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_wall_analysis_begin_end_round_trips_preserve_the_workspace(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.set_viewport_size({"width": 1280, "height": 826})
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        # Keep two inexpensive ordinary representatives and preserve their order.
        for expected_count in (3, 2):
            self._remove_selected_compare_board(
                case.page.locator(".compare-filmstrip-board").count() - 1
            )
            self._expect(".compare-filmstrip-board").to_have_count(expected_count, timeout=60_000)
        labels = case.page.locator(".compare-filmstrip-label").all_text_contents()

        # Analysis steps live in the setup sheet; set them, then open the
        # stage-wide analysis overlay from the dock.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        self._expect(".compare-config-sheet.is-open").to_be_visible()
        analysis_steps = case.page.locator(
            ".compare-form label", has_text="Analysis steps"
        ).locator("input")
        analysis_steps.fill("12")
        case.page.click('.compare-dock-icon[aria-label="Analyze the tilings"]')
        self._expect(".compare-analysis-overlay").to_be_visible()
        case.page.click(".compare-run-secondary")
        self._expect(".compare-grid tbody tr").to_have_count(2, timeout=60_000)
        self._expect(".compare-status").to_contain_text("Done — 2 tilings")

        # The wide overlay lets the multi-column result table read without a
        # nested horizontal scroll.
        table_overflow = case.page.locator(".compare-grid-scroll").evaluate(
            "el => el.scrollWidth - el.clientWidth"
        )
        case.assertLessEqual(
            table_overflow, 1, "analysis table should fit the overlay without horizontal scroll"
        )

        first_row = case.page.locator(".compare-grid tbody tr").first
        analysis_geometry = first_row.get_attribute("data-geometry")
        if analysis_geometry is None:
            raise AssertionError("analysis row did not expose its geometry")
        first_row.hover()
        case.assertGreater(
            case.page.locator(".compare-portrait [data-geometry].is-dimmed").count(), 0
        )
        case.page.mouse.move(0, 0)

        def open_phase_in_lab(phase: str) -> dict[str, object]:
            # The overlay closes when the wall is left; reopen it (cached results
            # come straight back) before acting on a row.
            if not case.page.locator(".compare-analysis-overlay").is_visible():
                case.page.click('.compare-dock-icon[aria-label="Analyze the tilings"]')
                self._expect(".compare-grid tbody tr").to_have_count(2, timeout=60_000)
            row_selector = f'.compare-grid tbody tr[data-geometry="{analysis_geometry}"]'
            row = case.page.locator(row_selector)
            self._expect(row_selector).to_have_count(1)
            row.locator(
                ".compare-action-menu", has=case.page.get_by_text("Open", exact=True)
            ).locator("summary").click()
            row.get_by_role("button", name=phase, exact=True).click()
            self._expect("#grid").to_be_visible()
            self._expect(".wall-page").to_be_hidden()
            payload = self._export_pattern_payload()
            case.assertEqual(payload["rule"], "conway")
            case.assertTrue(isinstance(payload["cells_by_id"], dict))
            return payload

        begin = open_phase_in_lab("Begin")
        case.page.locator("#wall-view-btn").press("Enter")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-grid tbody tr").to_have_count(2)
        case.assertEqual(case.page.locator(".compare-filmstrip-label").all_text_contents(), labels)

        end = open_phase_in_lab("End")
        case.assertEqual(end["topology_spec"], begin["topology_spec"])
        case.page.locator("#wall-view-btn").press("Enter")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-grid tbody tr").to_have_count(2)
        case.assertEqual(case.page.locator(".compare-filmstrip-label").all_text_contents(), labels)
        self._expect('.compare-filmstrip-btn[aria-label="Play / pause"]').to_contain_text("Play")

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

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

    def test_wall_multiple_forks_capacity_replacement_and_route_lifecycle(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        labels = case.page.locator(".compare-filmstrip-label").all_text_contents()

        # Save the current setup so loading it later is a true whole-wall
        # replacement, not a direct implementation hook.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        case.page.click("#compare-config-tab-saved")
        case.page.fill('input[aria-label="Saved run name"]', "Fork lifecycle")
        case.page.get_by_role("button", name="Save run", exact=True).click()
        case.page.get_by_role("button", name="Close configuration").click()

        def fork_and_run(index: int, expected_count: int) -> None:
            case.page.locator(".compare-filmstrip-board").nth(index).click()
            case.page.click(".compare-hero-fork")
            self._expect(".compare-focus-pane").to_have_count(expected_count, timeout=60_000)
            hero = case.page.locator(".compare-filmstrip-board.is-hero")
            hero.get_by_role("button", name="Run", exact=True).click()
            expect(hero.locator(".compare-focus-pane-badge")).to_contain_text("live · gen")
            case.page.click(".compare-hero-back")

        fork_and_run(0, 1)
        fork_and_run(1, 2)
        self._expect(".compare-focus-pane").to_have_count(2)
        self._expect(".compare-filmstrip-board.is-hero").to_have_count(0)
        case.assertEqual(case.page.locator(".compare-filmstrip-label").all_text_contents(), labels)

        if case.api is None:
            # Standalone owns two Pyodide fork runtimes. The third request is
            # refused visibly; discarding one returns capacity immediately.
            case.page.locator(".compare-filmstrip-board").nth(2).click()
            case.page.click(".compare-hero-fork")
            self._expect(".compare-status").to_contain_text(
                "Only 2 live forks at a time here — discard one first."
            )
            self._expect(".compare-focus-pane").to_have_count(2)
            case.page.click(".compare-hero-back")

            case.page.locator(".compare-filmstrip-board").first.click()
            case.page.click(".compare-focus-pane-discard")
            self._expect(".compare-focus-pane").to_have_count(1)
            case.page.click(".compare-hero-back")
            fork_and_run(2, 2)

        # Loading the saved run replaces the authoritative wall and tears down
        # every fork before the replacement is rerun.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        case.page.click("#compare-config-tab-saved")
        case.page.get_by_role("button", name="Load run", exact=True).click()
        self._expect(".compare-focus-pane").to_have_count(0)
        self._expect(".compare-status").to_contain_text("Loaded run link")
        case.page.get_by_role("button", name="Close configuration").click()
        self._expect(".compare-status").to_contain_text("Filmstrip ready", timeout=60_000)
        case.assertEqual(case.page.locator(".compare-filmstrip-label").all_text_contents(), labels)

        # Route deactivation disposes the remaining live pane once; returning
        # restores the same authoritative board order without any fork badge.
        case.page.locator(".compare-filmstrip-board").first.click()
        case.page.click(".compare-hero-fork")
        self._expect(".compare-focus-pane").to_have_count(1, timeout=60_000)
        case.page.click("#open-lab-btn")
        case.page.wait_for_function("() => window.location.hash === '#/lab'")
        case.page.locator("#wall-view-btn").press("Enter")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-focus-pane").to_have_count(0)
        case.assertEqual(case.page.locator(".compare-filmstrip-label").all_text_contents(), labels)

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

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

    def test_wall_narrow_workspace_uses_exclusive_accessible_drawers(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        case.page.set_viewport_size({"width": 820, "height": 900})
        setup = case.page.locator(".compare-setup-sidebar")
        inspector = case.page.locator(".compare-inspector")
        setup_toggle = case.page.get_by_role("button", name="Configure the run")
        inspector_toggle = case.page.get_by_role("button", name="Inspect selected board")
        expect(setup).to_have_attribute("inert", "")
        expect(inspector).to_have_attribute("inert", "")
        expect(setup).not_to_be_visible()
        expect(inspector).not_to_be_visible()
        expect(setup_toggle).to_have_attribute("aria-expanded", "false")
        expect(inspector_toggle).to_be_enabled()

        setup_toggle.press("Enter")
        expect(setup).not_to_have_attribute("inert", "")
        expect(setup).to_be_visible()
        expect(setup_toggle).to_have_attribute("aria-expanded", "true")
        self._expect(".compare-setup-run").to_be_visible()

        inspector_toggle.press("Enter")
        expect(setup).to_have_attribute("inert", "")
        expect(inspector).not_to_have_attribute("inert", "")
        expect(setup).not_to_be_visible()
        expect(inspector).to_be_visible()
        expect(inspector_toggle).to_have_attribute("aria-expanded", "true")
        # Opening the inspector without a chosen board shows the general
        # explainer, and the board-specific actions stay disabled.
        self._expect(".compare-explainer-body").to_contain_text("Same seed")
        self._expect(".compare-hero-open-lab").to_be_disabled()
        self._expect(".compare-inspector-replace").to_be_disabled()
        self._expect(".compare-inspector-remove").to_be_disabled()

        case.page.get_by_role("button", name="Close inspector").press("Enter")
        expect(inspector).to_have_attribute("inert", "")
        expect(inspector_toggle).to_be_focused()

        # A narrow inspector is a full overlay, so focusing a board does not pop
        # it over the board; the ⓘ button opens it on the focused board, with
        # its stats, toolbelt, and enabled actions.
        case.page.locator(".compare-filmstrip-board").first.click()
        expect(inspector).to_have_attribute("inert", "")
        inspector_toggle.click()
        expect(inspector).not_to_have_attribute("inert", "")
        expect(inspector).to_be_visible()
        expect(inspector_toggle).to_have_attribute("aria-expanded", "true")
        self._expect(".compare-explainer-body").to_contain_text("Generation0")
        self._expect(".compare-hero-open-lab").to_be_enabled()
        self._expect(".compare-hero-fork").to_be_enabled()
        self._expect(".compare-inspector-replace").to_be_enabled()
        self._expect(".compare-inspector-remove").to_be_enabled()
        self._expect('.compare-dock-icon[aria-label="Copy run link"]').to_be_visible()

        case.page.get_by_role("button", name="Close inspector").press("Enter")
        expect(inspector).to_have_attribute("inert", "")
        self._expect(".compare-edit-toggle").to_be_visible()
        self._expect('.compare-filmstrip-btn[aria-label="Play / pause"]').to_be_visible()
        case.assertLessEqual(
            case.page.evaluate("() => document.documentElement.scrollWidth"),
            case.page.evaluate("() => innerWidth"),
        )

    def test_wall_names_boards_and_edits_the_selection_in_place(self) -> None:
        # Boards carry their friendly catalog label (not the raw geometry
        # key), selected-board replacement preserves its wall position, and
        # removal stays in the persistent Inspector toolbelt.
        case = self._case()
        case.page.add_init_script(
            "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });"
        )
        case.reload_page(wait_until="load")
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [1280, 900])
        case.page.set_viewport_size({"width": 800, "height": 900})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [800, 900])

        self._expect(".compare-filmstrip-label >> nth=0").to_have_text("Square")
        self._expect(".compare-filmstrip-label >> nth=2").to_have_text("Penrose P3 Rhombs")

        # Selection is the sole target; Replace selected keeps that position.
        labels_before = case.page.locator(".compare-filmstrip-label").all_text_contents()
        self._select_compare_board(2)
        replace_selected = case.page.locator(".compare-inspector-replace")
        expect(replace_selected).to_have_text("Replace selected")
        expect(replace_selected).to_have_attribute(
            "aria-label", re.compile(re.escape(labels_before[2]))
        )
        replace_selected.click()
        self._expect(".compare-board-tiling-picker-search").to_be_focused()
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

        # Tiles have no mutation controls. The selected action names its target.
        case.assertEqual(case.page.locator(".compare-filmstrip-remove").count(), 0)
        first_label = case.page.locator(".compare-filmstrip-label").first.inner_text()
        self._select_compare_board(0)
        first_remove = case.page.locator(".compare-inspector-remove")
        expect(first_remove).to_be_visible()
        expect(first_remove).to_have_text("Remove selected")
        expect(first_remove).to_have_attribute("aria-label", re.compile(re.escape(first_label)))
        first_remove.click()
        self._expect(".compare-status").to_contain_text("Removed Square")
        self._expect(".compare-filmstrip-board").to_have_count(3, timeout=60_000)
        self._expect(".compare-filmstrip-label >> nth=0").to_have_text(
            "Kagome / Trihexagonal (3.6.3.6)"
        )

        # Compact once more to the two-board minimum. Survivor order is stable,
        # and the single Remove action remains visible, disabled, and explained.
        survivor_labels = case.page.locator(".compare-filmstrip-label").all_text_contents()[1:]
        self._select_compare_board(0)
        second_remove = case.page.locator(".compare-inspector-remove")
        expect(second_remove).to_be_enabled(timeout=60_000)
        second_remove.press("Enter")
        self._expect(".compare-filmstrip-board").to_have_count(2, timeout=60_000)
        case.assertEqual(
            case.page.locator(".compare-filmstrip-label").all_text_contents(), survivor_labels
        )
        minimum_remove = case.page.locator(".compare-inspector-remove")
        expect(minimum_remove).to_be_visible()
        expect(minimum_remove).to_be_disabled()
        expect(minimum_remove).to_have_attribute("title", "Keep at least two tilings on the wall")

        # Add through the wall-local visual picker up to the capable desktop
        # ceiling. Each addition appends, and the first picker is opened from
        # the keyboard to keep the in-wall workflow accessible.
        additions = [
            "Ammann-Beenker",
            "Penrose P3 Rhombs",
            "Kagome / Trihexagonal (3.6.3.6)",
            "Snub Trihexagonal (3.3.3.3.6)",
        ]
        for index, add_label in enumerate(additions):
            labels_before_add = case.page.locator(".compare-filmstrip-label").all_text_contents()
            add_button = case.page.locator(".compare-filmstrip-add")
            expect(add_button).to_be_visible()
            expect(add_button).to_be_enabled(timeout=60_000)
            if index == 0:
                add_button.press("Enter")
            else:
                add_button.click()
            self._expect(".compare-board-tiling-picker[aria-label='Add tiling']").to_be_visible()
            self._expect(".compare-board-tiling-picker-search").to_be_focused()
            case.page.fill(".compare-board-tiling-picker-search", add_label)
            filtered_choices = case.page.locator(".compare-board-tiling-choice:not(:disabled)")
            case.assertEqual(filtered_choices.count(), 1)
            filtered_choices.first.click()
            self._expect(".compare-filmstrip-board").to_have_count(
                len(labels_before_add) + 1, timeout=60_000
            )
            labels_after_add = case.page.locator(".compare-filmstrip-label").all_text_contents()
            case.assertEqual(labels_after_add[:-1], labels_before_add)
            case.assertEqual(labels_after_add[-1], add_label)

        # Maximum + 1 is represented as a persistent disabled action rather
        # than a disappearing control or a seventh board.
        maximum_add = case.page.locator(".compare-filmstrip-add")
        expect(maximum_add).to_be_visible()
        expect(maximum_add).to_be_disabled()
        expect(maximum_add).to_have_attribute("title", "The wall supports up to 6 tilings at once.")
        self._expect(".compare-filmstrip-board").to_have_count(6)

        add_label = additions[-1]
        dense_board = case.page.locator(".compare-filmstrip-board").filter(
            has=case.page.locator(".compare-filmstrip-label", has_text=add_label)
        )
        expect(dense_board.locator(".compare-thumb")).to_be_visible(timeout=60_000)
        expect(dense_board.locator(".compare-filmstrip-slot")).not_to_have_text("too large")

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_wall_local_removal_reconciles_pending_setup_and_keyboard_state(self) -> None:
        # A setup edit queued inside the scheduler must be rebased onto the
        # survivor set, never restore a board removed during the debounce. The
        # same local transaction closes stale pickers and restores keyboard
        # focus to a useful surviving control.
        case = self._case()
        case.page.add_init_script(
            "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });"
        )
        case.reload_page(wait_until="load")
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        labels_before = case.page.locator(".compare-filmstrip-label").all_text_contents()
        self._select_compare_board(0)
        expect(case.page.locator(".compare-inspector-remove")).to_be_enabled(timeout=60_000)

        # Reach the setup field through the visible sheet, then dispatch the
        # input and keyboard-focused removal in one task to pin the debounce
        # ordering deterministically.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        self._expect(".compare-config-sheet.is-open").to_be_visible()
        wall_generations = case.page.locator(
            ".compare-form label", has_text="Wall generations"
        ).locator("input")
        expect(wall_generations).to_be_visible()
        removal_state = case.page.evaluate(
            """() => {
                const generations = [...document.querySelectorAll('.compare-form label')]
                    .find((label) => label.textContent?.includes('Wall generations'))
                    ?.querySelector('input');
                const remove = document.querySelector('.compare-inspector-remove');
                if (!(generations instanceof HTMLInputElement) || !(remove instanceof HTMLButtonElement)) {
                    throw new Error('missing pending-removal controls');
                }
                generations.value = String(Number(generations.value) + 1);
                generations.dispatchEvent(new Event('input', { bubbles: true }));
                remove.focus();
                remove.click();
                return {
                    count: document.querySelectorAll('.compare-filmstrip-board').length,
                    activeLabel: document.activeElement?.getAttribute('aria-label'),
                };
            }"""
        )
        case.assertEqual(removal_state["count"], 3)
        case.assertEqual(
            removal_state["activeLabel"],
            f"Remove selected {labels_before[1]} from the wall",
        )
        case.page.click(".compare-config-sheet-close")

        # The queued run settles with the setup change and the same three
        # survivors. A stale four-board completion would fail both count/order
        # and leave the setup action stale rather than Up to date.
        expect(case.page.locator(".compare-setup-run")).to_have_text("Up to date", timeout=60_000)
        self._expect(".compare-filmstrip-board").to_have_count(3)
        case.assertEqual(
            case.page.locator(".compare-filmstrip-label").all_text_contents(), labels_before[1:]
        )
        self._expect(".compare-stage-caption").to_contain_text("3 tilings")

        # Removing while the Add search owns focus closes and clears the picker,
        # focuses the stable Add button, and the next Enter reopens immediately.
        add_button = case.page.locator(".compare-filmstrip-add")
        add_button.press("Enter")
        self._expect(".compare-board-tiling-picker-search").to_be_focused()
        case.page.evaluate("() => document.querySelector('.compare-inspector-remove')?.click()")
        self._expect(".compare-filmstrip-board").to_have_count(2)
        case.assertEqual(case.page.locator(".compare-board-tiling-picker").count(), 0)
        expect(add_button).to_be_focused()
        add_button.press("Enter")
        self._expect(".compare-board-tiling-picker").to_be_visible()
        self._expect(".compare-board-tiling-picker-search").to_be_focused()
        case.page.click(".compare-board-tiling-picker-close")

        case.page.click('.compare-filmstrip-btn[aria-label="Play / pause"]')
        self._expect(".compare-status").to_contain_text("Playing 2 tilings")
        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_wall_rapid_board_removal_holds_the_two_board_minimum(self) -> None:
        # Removal is local and instant, but the selected action must still stop
        # synchronously at the two-board floor during a repeated activation.
        case = self._case()
        case.page.add_init_script(
            "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });"
        )
        case.reload_page(wait_until="load")
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        self._select_compare_board(0)
        # Wait for the wall to go idle (selected Remove enabled) so the burst is
        # not swallowed by the initial in-flight-rebuild guard.
        expect(case.page.locator(".compare-inspector-remove")).to_be_enabled(timeout=60_000)

        # Reuse the one persistent button. Its target advances to the nearest
        # survivor, then it disables before the third activation.
        case.page.evaluate(
            """() => {
                const remove = document.querySelector('.compare-inspector-remove');
                if (!(remove instanceof HTMLButtonElement)) {
                    throw new Error('missing selected Remove action');
                }
                remove.click();
                remove.click();
                remove.click();
            }"""
        )

        # The wall settles at the floor -- two boards, never the collapsed hero
        # -- and Remove stays visible, disabled, and explained.
        self._expect(".compare-filmstrip-board").to_have_count(2, timeout=60_000)
        self._expect(".compare-stage-hero").not_to_be_visible()
        remove = case.page.locator(".compare-inspector-remove")
        expect(remove).to_be_visible()
        expect(remove).to_be_disabled()
        expect(remove).to_have_attribute("title", "Keep at least two tilings on the wall")

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_wall_mobile_capacity_keeps_actions_visible_and_blocks_max_plus_one(self) -> None:
        case = self._case()
        case.page.add_init_script(
            "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });"
        )
        case.reload_page(wait_until="load")
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        def add_tiling(label: str, expected_count: int) -> None:
            labels_before = case.page.locator(".compare-filmstrip-label").all_text_contents()
            add_button = case.page.locator(".compare-filmstrip-add")
            expect(add_button).to_be_visible()
            expect(add_button).to_be_enabled(timeout=60_000)
            add_button.click()
            self._expect(".compare-board-tiling-picker-search").to_be_focused()
            case.page.fill(".compare-board-tiling-picker-search", label)
            choice = case.page.locator(".compare-board-tiling-choice:not(:disabled)").filter(
                has=case.page.get_by_text(label, exact=True)
            )
            case.assertEqual(choice.count(), 1)
            choice.click()
            self._expect(".compare-filmstrip-board").to_have_count(expected_count, timeout=60_000)
            labels_after = case.page.locator(".compare-filmstrip-label").all_text_contents()
            case.assertEqual(labels_after[:-1], labels_before)
            case.assertEqual(labels_after[-1], label)

        # Begin at the capable desktop maximum with two structural outliers:
        # an aperiodic patch and the dense periodic snub trihexagonal board.
        add_tiling("Ammann-Beenker", 5)
        dense_label = "Snub Trihexagonal (3.3.3.3.6)"
        add_tiling(dense_label, 6)
        desktop_labels = case.page.locator(".compare-filmstrip-label").all_text_contents()
        desktop_maximum = case.page.locator(".compare-filmstrip-add")
        expect(desktop_maximum).to_be_visible()
        expect(desktop_maximum).to_be_disabled()
        expect(desktop_maximum).to_have_attribute(
            "title", "The wall supports up to 6 tilings at once."
        )

        # Narrowing changes only future capacity. Existing boards and order are
        # preserved, while the one-past action remains visible and explained.
        case.page.set_viewport_size({"width": 390, "height": 844})
        case.assertEqual(case.page.evaluate("() => [innerWidth, innerHeight]"), [390, 844])
        self._expect("#drawer-backdrop").to_be_hidden()
        self._expect(".compare-filmstrip-board").to_have_count(6)
        case.assertEqual(
            case.page.locator(".compare-filmstrip-label").all_text_contents(), desktop_labels
        )
        mobile_add = case.page.locator(".compare-filmstrip-add")
        expect(mobile_add).to_be_visible()
        expect(mobile_add).to_be_disabled()
        expect(mobile_add).to_have_attribute(
            "title",
            "This screen or device supports up to 4 tilings at once (maximum 6).",
        )
        case.assertLessEqual(
            case.page.evaluate("() => document.documentElement.scrollWidth"),
            case.page.evaluate("() => innerWidth"),
        )

        # Remove from the beginning at three different board positions. The
        # survivors stay ordered, then the mobile maximum accepts exactly one.
        expected_labels = list(desktop_labels)
        removed_labels: list[str] = []
        for index in (0, 2, 1):
            self._remove_selected_compare_board(index)
            removed_labels.append(expected_labels.pop(index))
            self._expect(".compare-filmstrip-board").to_have_count(
                len(expected_labels), timeout=60_000
            )
            case.assertEqual(
                case.page.locator(".compare-filmstrip-label").all_text_contents(), expected_labels
            )
        add_tiling(removed_labels[0], 4)
        mobile_labels = case.page.locator(".compare-filmstrip-label").all_text_contents()
        expect(case.page.locator(".compare-filmstrip-add")).to_be_visible()
        expect(case.page.locator(".compare-filmstrip-add")).to_be_disabled()

        # Cross the responsive breakpoint without reordering, then restore wide
        # capacity and append back to six.
        case.page.set_viewport_size({"width": 800, "height": 900})
        case.assertEqual(
            case.page.locator(".compare-filmstrip-label").all_text_contents(), mobile_labels
        )
        case.page.set_viewport_size({"width": 1280, "height": 900})
        add_tiling(removed_labels[1], 5)
        add_tiling(removed_labels[2], 6)
        maximum_add = case.page.locator(".compare-filmstrip-add")
        expect(maximum_add).to_be_visible()
        expect(maximum_add).to_be_disabled()
        expect(maximum_add).to_have_attribute("title", "The wall supports up to 6 tilings at once.")
        case.assertLessEqual(
            case.page.evaluate("() => document.documentElement.scrollWidth"),
            case.page.evaluate("() => innerWidth"),
        )

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_wall_enforces_setup_boundaries_and_uses_the_selected_limits(self) -> None:
        # The live wall and statistical analysis have different compute ceilings.
        # Keep both jobs explicit, block one-past values before dispatch, and prove
        # the accepted maxima reach the rendered wall / analysis result.
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        # Use two ordinary survivors so the boundary journey remains fast in the
        # standalone worker while still crossing board-management and rerun state.
        for expected_count in (3, 2):
            self._remove_selected_compare_board(
                case.page.locator(".compare-filmstrip-board").count() - 1
            )
            self._expect(".compare-filmstrip-board").to_have_count(expected_count, timeout=60_000)
            if expected_count > 2:
                expect(case.page.locator(".compare-inspector-remove")).to_be_enabled(timeout=60_000)
        labels = case.page.locator(".compare-filmstrip-label").all_text_contents()

        # The setup form opens on demand from the dock gear.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        self._expect(".compare-config-sheet.is-open").to_be_visible()
        wall_generations = case.page.locator(
            ".compare-form label", has_text="Wall generations"
        ).locator("input")
        analysis_steps = case.page.locator(
            ".compare-form label", has_text="Analysis steps"
        ).locator("input")
        grid_size = case.page.locator(".compare-form label", has_text="Grid size").locator("input")
        wall_run = case.page.locator(".compare-setup-run")
        analysis_run = case.page.locator(".compare-run-secondary")

        expect(wall_generations).to_have_attribute("max", "240")
        expect(analysis_steps).to_have_attribute("max", "500")
        expect(grid_size).to_have_attribute("max", "64")

        wall_generations.fill("241")
        expect(wall_run).to_be_disabled()
        expect(wall_run).to_have_attribute(
            "title", "Wall generations must be an integer from 1 to 240."
        )
        expect(analysis_run).to_be_enabled()

        wall_generations.fill("240")
        analysis_steps.fill("501")
        expect(wall_run).to_be_enabled()
        # The analysis Run button lives on the overlay; out-of-range steps
        # disable it with an explaining title (readable while it is still off-screen).
        expect(analysis_run).to_be_disabled()
        expect(analysis_run).to_have_attribute(
            "title", "Analysis steps must be an integer from 1 to 500."
        )

        analysis_steps.fill("500")
        grid_size.fill("65")
        expect(wall_run).to_be_disabled()
        expect(analysis_run).to_be_disabled()
        expect(wall_run).to_have_attribute("title", "Grid size must be an integer from 2 to 64.")

        # Minimum grid with maximum wall length: the counter proves all 240
        # selected generations reached the rendered result.
        grid_size.fill("2")
        expect(wall_run).to_be_enabled()
        expect(analysis_run).to_be_enabled()
        wall_run.click()
        case.page.get_by_role("button", name="Close configuration").click()
        self._expect(".compare-status").to_contain_text("Filmstrip ready", timeout=60_000)
        self._expect(".compare-filmstrip-counter").to_contain_text("gen 0 / 239")
        case.assertEqual(case.page.locator(".compare-filmstrip-label").all_text_contents(), labels)

        # The separate 500-step maximum remains usable for analysis without
        # changing the running wall or its participant order.
        case.page.click('.compare-dock-icon[aria-label="Analyze the tilings"]')
        self._expect(".compare-analysis-overlay").to_be_visible()
        analysis_run.click()
        self._expect(".compare-status").to_contain_text("Done — 2 tilings", timeout=60_000)
        case.assertEqual(case.page.locator(".compare-filmstrip-label").all_text_contents(), labels)
        case.page.click(".compare-analysis-close")

        # Maximum grid with the minimum one-frame wall: the square board's cell
        # count proves the selected 64 x 64 request, rather than a silent clamp.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        wall_generations.fill("1")
        grid_size.fill("64")
        wall_run.click()
        case.page.get_by_role("button", name="Close configuration").click()
        self._expect(".compare-status").to_contain_text("Filmstrip ready", timeout=60_000)
        self._expect(".compare-filmstrip-counter").to_contain_text("gen 0 / 0")
        square_board = case.page.locator(".compare-filmstrip-board").filter(
            has=case.page.locator(".compare-filmstrip-label", has_text="Square")
        )
        expect(square_board.locator("[data-cell-id]")).to_have_count(4096)
        case.assertEqual(case.page.locator(".compare-filmstrip-label").all_text_contents(), labels)

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

    def test_wall_applies_wireworld_and_hides_tiling_specific_rules(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        # The setup strip's rule picker lives in the on-demand config sheet.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        rule_select = case.page.locator("select[aria-label='Comparison rule']")
        rule_values = rule_select.locator("option").evaluate_all(
            "options => options.map(option => option.value)"
        )
        expected_wall_rules = {
            rule["name"]
            for rule in RuleRegistry().describe_rules()
            if rule["supports_all_topologies"] and rule["compatible_tiling_families"] is None
        }
        case.assertEqual(set(rule_values), expected_wall_rules)
        case.assertTrue("wireworld" in rule_values)
        case.assertTrue("kagome-life" not in rule_values)
        case.assertTrue(not any(value.startswith("archlife") for value in rule_values))

        rule_select.select_option("wireworld")
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

    def test_wall_applies_bits_seed_from_the_setup_strip(self) -> None:
        case = self._case()
        self._mark_compare_demo_seen()
        case.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)

        # The setup strip's seed picker lives in the on-demand config sheet.
        case.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        seed_select = case.page.locator('select[aria-label="Comparison seed"]')
        self._expect('select[aria-label="Comparison seed"]').to_have_value("r-pentomino")
        seed_select.select_option("")
        self._expect(".compare-setup-run").to_have_text("Up to date", timeout=60_000)
        self._expect(".compare-status").not_to_contain_text("Error:")
        self._expect('select[aria-label="Comparison seed"]').to_have_value("")

        unexpected_console = [
            message
            for message in case.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        case.assertEqual(unexpected_console, [])

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
        # The config sheet opens on demand from the dock gear.
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

    def test_wall_failed_update_keeps_previous_result_and_retries_latest_setup(self) -> None:
        self._mark_compare_demo_seen()
        self.page.click("#wall-view-btn")
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        labels = self.page.locator(".compare-filmstrip-label").all_text_contents()
        self.page.locator('.compare-filmstrip-btn[aria-label="Play / pause"]').click()
        self._select_compare_board(0)

        requests: list[dict[str, Any]] = []

        def intercept_filmstrip(route: Any) -> None:
            payload = route.request.post_data_json
            requests.append(cast(dict[str, Any], payload))
            if len(requests) == 1:
                # A truncated success payload exercises frontend recovery
                # without Chromium's expected failed-resource console noise.
                route.fulfill(status=200, content_type="application/json", body="{")
                return
            route.continue_()

        self.page.route("**/compare/filmstrip", intercept_filmstrip)
        self.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        self.page.select_option('select[aria-label="Comparison rule"]', "wireworld")
        self.page.click(".compare-setup-run")
        self._expect(".compare-stale-notice").to_be_visible(timeout=60_000)
        self._expect(".compare-stale-notice").to_contain_text(
            "The wall is still showing the previous result."
        )
        self._expect('.compare-filmstrip-btn[aria-label="Play / pause"]').to_contain_text("Pause")
        self._expect(".compare-filmstrip-board").to_have_count(4)
        for selector in (
            ".compare-filmstrip-add",
            ".compare-inspector-replace",
            ".compare-inspector-remove",
        ):
            controls = self.page.locator(selector)
            for control in controls.all():
                expect(control).to_be_disabled()
                expect(control).to_have_attribute(
                    "title", "Retry the failed update before editing this wall"
                )

        # Recovery intentionally reads the current controls, not the failed
        # request snapshot.
        self.page.select_option('select[aria-label="Comparison seed"]', "glider")
        self.page.click(".compare-stale-retry")
        self._expect(".compare-status").to_contain_text("Filmstrip ready", timeout=60_000)
        self._expect(".compare-stale-notice").to_be_hidden()
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[1]["rule"], "wireworld")
        self.assertEqual(requests[1]["pattern"], "glider")
        self.assertEqual(self.page.locator(".compare-filmstrip-label").all_text_contents(), labels)
        expect(self.page.locator(".compare-filmstrip-add")).to_be_enabled()
        self.page.unroute("**/compare/filmstrip", intercept_filmstrip)

        unexpected_console = [
            message
            for message in self.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        self.assertEqual(unexpected_console, [])

    def test_wall_undo_cancels_a_pending_membership_request(self) -> None:
        self._mark_compare_demo_seen()
        self.page.click("#wall-view-btn")
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        initial_labels = self.page.locator(".compare-filmstrip-label").all_text_contents()
        self._remove_selected_compare_board(0)
        self._expect(".compare-filmstrip-board").to_have_count(3)

        held_routes: list[Any] = []

        def hold_membership_update(route: Any) -> None:
            held_routes.append(route)

        self.page.route("**/compare/filmstrip", hold_membership_update)
        self.page.locator(".compare-filmstrip-add").click()
        self.page.locator(".compare-board-tiling-choice:not(:disabled)").first.click()
        for _ in range(100):
            if held_routes:
                break
            self.page.wait_for_timeout(25)
        self.assertEqual(len(held_routes), 1)
        expect(self.page.locator(".compare-history-action")).to_have_text("Undo")

        self.page.locator(".wall-page").focus()
        self.page.keyboard.press("Control+z")
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        expect(self.page.locator(".compare-history-action")).to_have_text("Redo", timeout=60_000)
        self.assertEqual(
            self.page.locator(".compare-filmstrip-label").all_text_contents(),
            initial_labels,
        )

        # Release the intercepted request after cancellation. Chromium may
        # suppress the response event entirely for the already-aborted fetch;
        # either way, the route can no longer replace the restored wall or
        # create a history entry. The unit suite separately resolves an
        # aborted backend promise to cover that late-settlement path.
        held_routes[0].continue_()
        self.page.wait_for_timeout(500)
        self.assertEqual(
            self.page.locator(".compare-filmstrip-label").all_text_contents(),
            initial_labels,
        )
        expect(self.page.locator(".compare-history-action")).to_have_text("Redo")
        self.page.unroute("**/compare/filmstrip", hold_membership_update)

        unexpected_console = [
            message
            for message in self.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        self.assertEqual(unexpected_console, [])

    def test_wall_loaded_run_cannot_be_overwritten_by_a_held_old_response(self) -> None:
        self._mark_compare_demo_seen()
        self.page.click("#wall-view-btn")
        self._expect(".compare-filmstrip-board").to_have_count(4, timeout=60_000)
        held_routes: list[Any] = []

        def hold_first_filmstrip(route: Any) -> None:
            if not held_routes:
                held_routes.append(route)
                return
            route.continue_()

        self.page.route("**/compare/filmstrip", hold_first_filmstrip)
        self.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        self.page.select_option('select[aria-label="Comparison rule"]', "wireworld")
        self.page.click(".compare-setup-run")
        expect(self.page.locator(".compare-setup-run")).to_be_disabled()
        for _ in range(100):
            if held_routes:
                break
            self.page.wait_for_timeout(25)
        self.assertEqual(len(held_routes), 1)

        fragment = _encode_compare_run_fragment(
            {
                "seed": "101",
                "rule": "conway",
                "traversal": "bfs",
                "frames": 12,
                "grid_size": 8,
                "geometries": ["hex", "square"],
            }
        )
        self.page.evaluate(
            "fragment => { window.location.hash = '#/compare&' + fragment; }", fragment
        )
        self._expect(".compare-status").to_contain_text("Loaded run link")
        expect(self.page.locator(".compare-filmstrip-board").first).not_to_be_visible()
        self._expect(".compare-stage-hero").to_be_visible()

        with self.page.expect_response("**/compare/filmstrip", timeout=60_000) as response_info:
            held_routes[0].continue_()
        response_info.value.body()
        self._expect(".compare-status").to_contain_text("Loaded run link")
        expect(self.page.locator(".compare-filmstrip-board").first).not_to_be_visible()
        self._expect(".compare-stale-notice").to_be_hidden()

        self.page.click(".compare-setup-run")
        self._expect(".compare-status").to_contain_text("Filmstrip ready", timeout=60_000)
        self.assertEqual(
            self.page.locator(".compare-filmstrip-label").all_text_contents(),
            ["Hexagonal", "Square"],
        )
        self.page.unroute("**/compare/filmstrip", hold_first_filmstrip)
        unexpected_console = [
            message
            for message in self.console_messages
            if message.startswith("[console:error]") or message.startswith("[pageerror]")
        ]
        self.assertEqual(unexpected_console, [])


class StandaloneCellularAutomatonUITests(SharedUiFlowMixin, BrowserAppTestCase):
    runtime_host_kind = "standalone"
    page_viewport: ClassVar[ViewportSize | None] = {"width": 1280, "height": 900}

    def setUp(self) -> None:
        super().setUp()
        self.initialize_shared_ui_flow()

    def test_cold_start_stays_within_the_explicit_budget(self) -> None:
        measurement = self.page.evaluate("() => window.__standaloneStartupMs")
        if not isinstance(measurement, (int, float)):
            raise AssertionError(f"invalid standalone startup measurement: {measurement!r}")
        self.assertLessEqual(measurement, load_runtime_budget().cold_start_limit_ms)

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
        # the Pyodide build and restores the saved setup. An invalid one-board
        # comparison is rejected inline without starting backend work.
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
        self._expect(".compare-status").to_contain_text("Select at least two tilings")
        self._expect(".compare-grid").to_have_count(0)

    def test_saved_compare_run_persists_across_reload_in_standalone(self) -> None:
        # C3 parity: saving a run writes to localStorage in the Pyodide build and
        # the run is still listed after a full reload. setUp lands in the Lab;
        # the top-bar Wall button is the navigation to the wall.
        self._mark_compare_demo_seen()
        self.page.click("#wall-view-btn")
        self._expect(".wall-page").to_be_visible()

        run_name = "Standalone smoke run"
        # The config sheet opens on demand, so reach the Saved tab through the
        # dock gear whenever the sheet is collapsed.
        saved_tab = self.page.locator("#compare-config-tab-saved")
        if not saved_tab.is_visible():
            self.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        saved_tab.click()
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
        saved_tab = self.page.locator("#compare-config-tab-saved")
        if not saved_tab.is_visible():
            self.page.click('.compare-dock-icon[aria-label="Configure the run"]')
        saved_tab.click()
        self._expect('select[aria-label="Saved compare runs"]').to_contain_text(run_name)


class StandaloneRuntimeFailureTests(BrowserAppTestCase):
    runtime_host_kind = "standalone"
    page_viewport: ClassVar[ViewportSize | None] = {"width": 1280, "height": 900}

    def test_worker_init_failure_shows_startup_error_banner(self) -> None:
        self.context.route("**/pyodide.mjs", lambda route: route.abort())
        self.page.goto(f"{self.host.base_url}/", wait_until="load")

        cast(Any, expect(self.page.locator("#app-startup-error"))).to_be_visible()
        cast(Any, expect(self.page.locator("#app-startup-error"))).to_contain_text(
            "Standalone runtime failed to initialize"
        )


if __name__ == "__main__":
    unittest.main()
