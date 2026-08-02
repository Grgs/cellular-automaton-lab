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
VIEWPORT: ViewportSize = {"width": 1440, "height": 810}
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
    page.get_by_label("Comparison seed", exact=True).select_option(
        "r-pentomino", timeout=TIMEOUT_MS
    )
    for label, value in (("Analysis steps", "10"), ("Grid size", "22")):
        field = page.get_by_label(label)
        field.fill(value, timeout=TIMEOUT_MS)
        field.dispatch_event("change")
    page.locator('.compare-dock-icon[aria-label="Analyze the tilings"]').click(timeout=TIMEOUT_MS)
    analysis_overlay = page.locator(".compare-analysis-overlay")
    analysis_overlay.wait_for(state="visible", timeout=TIMEOUT_MS)
    analysis_overlay.get_by_role("button", name="Run analysis", exact=True).click(
        timeout=TIMEOUT_MS
    )
    page.locator(".compare-grid tbody tr").nth(0).wait_for(state="visible", timeout=TIMEOUT_MS)
    # Tighten the real analysis panel for a legible README capture. The thicker
    # traces compensate for GitHub scaling the 1000px panel down on narrow pages.
    page.add_style_tag(
        content="""
            .compare-analysis-panel {
                width: min(1080px, calc(100% - 48px)) !important;
                max-height: none !important;
                background: #fbf8f1 !important;
            }
            .compare-analysis-body {
                overflow: visible !important;
                max-height: none !important;
            }
            .compare-intro,
            .compare-run-secondary {
                display: none !important;
            }
            .compare-portrait {
                max-height: 280px !important;
            }
            .compare-portrait__line {
                stroke-width: 2.6 !important;
                opacity: 1 !important;
            }
        """
    )
    _save_locator_png(
        page,
        ".compare-analysis-panel",
        output_dir / "readme-compare-results-hero.png",
    )


def _capture_wall_hero(page: Page, output_dir: Path) -> None:
    # A first visit autoplays the featured demo; the reduced-motion context makes
    # it rest, paused, on a lively frame — a deterministic hero shot.
    page.locator(".wall-page").wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator(".compare-filmstrip-board").nth(3).wait_for(state="visible", timeout=TIMEOUT_MS)
    page.locator(".compare-filmstrip-board .compare-thumb").nth(3).wait_for(
        state="visible", timeout=TIMEOUT_MS
    )
    _save_optimized_png(page, output_dir / "readme-wall-hero.png")


def _capture_uniform_2_3_workspace(page: Page, output_dir: Path) -> None:
    select_tiling_family(page, "uniform-2-3-44-33344", timeout_ms=TIMEOUT_MS)
    _wait_ready(page)
    _click(page, "#random-btn")
    _wait_ready(page)
    for _ in range(12):
        _click(page, "#step-btn")
        _wait_ready(page)
    page.evaluate("window.scrollTo(0, 0)")
    _save_optimized_png(page, output_dir / "readme-uniform-2-3-overview.png")


def _capture_picker_thumbnails(page: Page, output_dir: Path) -> None:
    select_tiling_family(page, "pinwheel", timeout_ms=TIMEOUT_MS)
    _wait_ready(page)
    set_patch_depth(page, 3, timeout_ms=TIMEOUT_MS)
    _wait_ready(page)
    _click(page, "#tiling-picker-toggle")
    page.locator("#tiling-picker-menu").wait_for(state="visible", timeout=TIMEOUT_MS)
    search = page.locator("#tiling-picker-menu .tiling-picker-search")
    search.fill("pentagonal", timeout=TIMEOUT_MS)
    page.locator(".tiling-preview-card[data-tiling-family='type-7-pentagonal']").wait_for(
        state="visible",
        timeout=TIMEOUT_MS,
    )
    page.evaluate("window.scrollTo(0, 0)")
    _save_optimized_png(page, output_dir / "readme-tiling-picker-thumbnails.png")


DEMO_SEEN_INIT_SCRIPT = """
window.localStorage.setItem(
    "cellular-automaton-lab.compare.v1",
    JSON.stringify({ runs: [], tilingSets: [], demoSeenAt: 1 })
);
"""


def capture_readme_screenshots(output_dir: Path, selected_scenarios: set[str]) -> None:
    ensure_current_standalone_build(str(ROOT_DIR))
    # Each scenario: (capture, route, seed_demo_seen). Editor scenarios open the
    # Lab route; wall scenarios land on the bare URL. Pre-seeding the demo flag
    # keeps the featured demo from racing a scripted setup — only the wall hero
    # wants the demo (reduced motion parks it on a lively still frame).
    scenarios: tuple[tuple[str, Callable[[Page, Path], None], str, bool], ...] = (
        ("wall", _capture_wall_hero, "", False),
        ("analysis", _capture_compare_results, "", True),
        ("uniform", _capture_uniform_2_3_workspace, "#/lab", True),
        ("picker", _capture_picker_thumbnails, "#/lab", True),
    )
    host = StandaloneRuntimeHost()
    host.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for name, scenario, route, seed_demo_seen in scenarios:
                    if selected_scenarios and name not in selected_scenarios:
                        continue
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
    parser.add_argument(
        "--scenario",
        action="append",
        choices=("wall", "analysis", "uniform", "picker"),
        default=[],
        help="capture only this named scenario; repeat to select more than one",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    capture_readme_screenshots(args.output_dir, set(args.scenario))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
