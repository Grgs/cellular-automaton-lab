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


def _open_fresh_page(host: StandaloneRuntimeHost, page: Page) -> None:
    page.goto(f"{host.base_url}/", wait_until="load")
    _wait_ready(page)


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
    _click(page, ".compare-toggle")
    page.locator(".compare-dialog").wait_for(state="visible", timeout=TIMEOUT_MS)
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
    _click(page, ".compare-run")
    page.locator(".compare-grid tbody tr").nth(0).wait_for(state="visible", timeout=TIMEOUT_MS)
    page.add_style_tag(
        content="""
            .compare-backdrop {
                position: absolute !important;
                align-items: flex-start !important;
                padding-top: 22px !important;
            }
            .compare-dialog {
                max-height: none !important;
                overflow: visible !important;
            }
            .compare-actions {
                position: static !important;
            }
        """
    )
    _save_locator_png(page, ".compare-dialog", output_dir / "readme-compare-results-hero.png")


def _capture_snub_workspace(page: Page, output_dir: Path) -> None:
    select_tiling_family(page, "archimedean-3-3-3-3-6", timeout_ms=TIMEOUT_MS)
    _wait_ready(page)
    _select_native_value(page, "#rule-select", "kagome-life")
    _wait_ready(page)
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


def capture_readme_screenshots(output_dir: Path) -> None:
    ensure_current_standalone_build(str(ROOT_DIR))
    scenarios: tuple[Callable[[Page, Path], None], ...] = (
        _capture_compare_results,
        _capture_snub_workspace,
        _capture_pinwheel_workspace,
        _capture_picker_thumbnails,
    )
    host = StandaloneRuntimeHost()
    host.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for scenario in scenarios:
                    context = browser.new_context(
                        viewport=VIEWPORT,
                        device_scale_factor=1,
                        reduced_motion="reduce",
                    )
                    try:
                        page = context.new_page()
                        page.set_default_timeout(TIMEOUT_MS)
                        page.set_default_navigation_timeout(TIMEOUT_MS)
                        _open_fresh_page(host, page)
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
