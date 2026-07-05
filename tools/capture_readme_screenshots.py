"""Capture the README screenshot set from the standalone UI."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, ViewportSize, sync_playwright

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tests.e2e.support_runtime_host import StandaloneRuntimeHost, ensure_current_standalone_build
from tools.render_review.browser_support.render_review import (
    select_tiling_family,
    set_patch_depth,
    wait_for_page_bootstrapped,
    wait_for_patch_render_complete,
)

DEFAULT_OUTPUT_DIR = ROOT_DIR / "docs" / "images"
VIEWPORT: ViewportSize = {"width": 1440, "height": 980}
TIMEOUT_MS = 60_000


def _wait_ready(page: Page) -> None:
    wait_for_page_bootstrapped(page, timeout_ms=TIMEOUT_MS)
    wait_for_patch_render_complete(page, timeout_ms=TIMEOUT_MS)


def _open_fresh_page(host: StandaloneRuntimeHost, page: Page, *, route: str = "") -> None:
    page.goto(f"{host.base_url}/{route}", wait_until="load")
    if "/lab" in route:
        # Editor readiness (review-api diagnostics) exists only once the Lab
        # has booted; wall scenarios wait on their own wall selectors instead.
        _wait_ready(page)
    else:
        page.locator(".wall-page").wait_for(state="visible", timeout=TIMEOUT_MS)


def _open_inspector_sheet(page: Page) -> None:
    # The Lab's inspector is a bottom sheet, closed (and inert) by default;
    # controls like the rule picker live inside it.
    if page.locator("#control-drawer").get_attribute("data-open") != "true":
        page.locator("#drawer-toggle-btn").click(timeout=TIMEOUT_MS)
        page.locator('#control-drawer[data-open="true"]').wait_for(timeout=TIMEOUT_MS)


def _save_optimized_png(page: Page, path: Path, *, full_page: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=full_page)
    _optimize_png(path)


def _save_locator_png(page: Page, selector: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page.locator(selector).screenshot(path=str(path))
    _optimize_png(path)


def _optimize_png(path: Path) -> None:
    with Image.open(path) as image:
        image.save(path, optimize=True)


def _select_native_value(page: Page, selector: str, value: str) -> None:
    page.locator(selector).select_option(value, timeout=TIMEOUT_MS)


def _click(page: Page, selector: str) -> None:
    page.locator(selector).click(timeout=TIMEOUT_MS)


def _capture_compare_results(page: Page, output_dir: Path) -> None:
    # The bare URL lands on the wall page; no toggle click is needed.
    page.locator(".wall-page").wait_for(state="visible", timeout=TIMEOUT_MS)
    # Configuration lives in a bottom sheet the dock gear slides up.
    page.locator('.compare-dock-icon[aria-label="Configure the run"]').click(timeout=TIMEOUT_MS)
    page.locator(".compare-config-run").evaluate("(section) => { section.open = true; }")
    selects = page.locator("select.compare-field")
    selects.nth(1).select_option("acorn", timeout=TIMEOUT_MS)
    page.locator("input.compare-field").evaluate_all(
        """(inputs) => {
            const numberInputs = inputs.filter((input) => input instanceof HTMLInputElement && input.type === "number");
            const steps = numberInputs[0];
            const gridSize = numberInputs[1];
            if (steps) {
                steps.value = "120";
                steps.dispatchEvent(new Event("input", { bubbles: true }));
                steps.dispatchEvent(new Event("change", { bubbles: true }));
            }
            if (gridSize) {
                gridSize.value = "18";
                gridSize.dispatchEvent(new Event("input", { bubbles: true }));
                gridSize.dispatchEvent(new Event("change", { bubbles: true }));
            }
        }"""
    )
    # The analytical run lives in a collapsed disclosure below the stage.
    page.locator(".compare-config-analysis").evaluate("(section) => { section.open = true; }")
    page.get_by_role("button", name="Run comparison", exact=True).click(timeout=TIMEOUT_MS)
    page.locator(".compare-grid tbody tr").nth(0).wait_for(state="visible", timeout=TIMEOUT_MS)
    # Flatten the fixed config sheet so a full-height capture includes the whole
    # analysis section, which now lives inside it.
    page.add_style_tag(
        content="""
            .compare-config-sheet {
                position: absolute !important;
                transform: none !important;
                max-height: none !important;
            }
            .compare-config-sheet-body {
                overflow: visible !important;
            }
        """
    )
    _save_locator_png(page, ".compare-config-sheet", output_dir / "readme-compare-results-hero.png")


def _capture_wall_hero(page: Page, output_dir: Path) -> None:
    # A first visit autoplays the featured demo; the reduced-motion context makes
    # it rest, paused, on a lively frame — a deterministic hero shot.
    page.locator(".wall-page").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator(".compare-filmstrip-board").nth(3).wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator(".compare-filmstrip-board .compare-thumb").nth(3).wait_for(
        state="visible", timeout=TIMEOUT_MS
    )
    _save_locator_png(page, ".wall-page", output_dir / "readme-wall-hero.png")


def _capture_snub_workspace(page: Page, output_dir: Path) -> None:
    select_tiling_family(page, "archimedean-3-3-3-3-6", timeout_ms=TIMEOUT_MS)
    _wait_ready(page)
    _open_inspector_sheet(page)
    _select_native_value(page, "#rule-select", "kagome-life")
    _wait_ready(page)
    # Close the sheet so the captured workspace shows the full board.
    _click(page, "#drawer-toggle-btn")
    _click(page, "#random-btn")
    _wait_ready(page)
    for _ in range(12):
        _click(page, "#step-btn")
        _wait_ready(page)
    _save_optimized_png(page, output_dir / "readme-snub-trihexagonal-overview.png")


def _capture_pinwheel_workspace(page: Page, output_dir: Path) -> None:
    select_tiling_family(page, "pinwheel", timeout_ms=TIMEOUT_MS)
    _wait_ready(page)
    set_patch_depth(page, 3, timeout_ms=TIMEOUT_MS)
    _wait_ready(page)
    _save_optimized_png(page, output_dir / "readme-pinwheel-overview.png")


def _capture_picker_thumbnails(page: Page, output_dir: Path) -> None:
    _click(page, "#tiling-picker-toggle")
    page.locator("#tiling-picker-menu").wait_for(state="visible", timeout=TIMEOUT_MS)
    search = page.locator("#tiling-picker-menu .tiling-picker-search")
    search.fill("pentagonal", timeout=TIMEOUT_MS)
    page.locator(".tiling-preview-card[data-tiling-family='type-7-pentagonal']").wait_for(
        state="visible",
        timeout=TIMEOUT_MS,
    )
    _save_optimized_png(page, output_dir / "readme-tiling-picker-thumbnails.png")


DEMO_SEEN_INIT_SCRIPT = """
window.localStorage.setItem(
    "cellular-automaton-lab.compare.v1",
    JSON.stringify({ runs: [], tilingSets: [], demoSeenAt: 1 })
);
"""


def capture_readme_screenshots(output_dir: Path) -> None:
    ensure_current_standalone_build(str(ROOT_DIR))
    # Each scenario: (capture, route, seed_demo_seen). Editor scenarios open the
    # Lab route; wall scenarios land on the bare URL. Pre-seeding the demo flag
    # keeps the featured demo from racing a scripted setup — only the wall hero
    # wants the demo (reduced motion parks it on a lively still frame).
    scenarios: tuple[tuple[Callable[[Page, Path], None], str, bool], ...] = (
        (_capture_wall_hero, "", False),
        (_capture_compare_results, "", True),
        (_capture_snub_workspace, "#/lab", True),
        (_capture_pinwheel_workspace, "#/lab", True),
        (_capture_picker_thumbnails, "#/lab", True),
    )
    host = StandaloneRuntimeHost()
    host.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for scenario, route, seed_demo_seen in scenarios:
                    context = browser.new_context(
                        viewport=VIEWPORT,
                        device_scale_factor=1,
                        reduced_motion="reduce",
                    )
                    try:
                        if seed_demo_seen:
                            context.add_init_script(DEMO_SEEN_INIT_SCRIPT)
                        page = context.new_page()
                        page.set_default_timeout(TIMEOUT_MS)
                        page.set_default_navigation_timeout(TIMEOUT_MS)
                        _open_fresh_page(host, page, route=route)
                        scenario(page, output_dir)
                    finally:
                        context.close()
            finally:
                browser.close()
    finally:
        host.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"directory for captured PNGs (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    capture_readme_screenshots(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
