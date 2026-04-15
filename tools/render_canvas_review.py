from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from playwright.sync_api import Page, sync_playwright

from tests.e2e.browser_support.render_review import (
    canvas_visual_summary,
    select_tiling_family,
    set_cell_size,
    set_patch_depth,
    wait_for_page_bootstrapped,
    wait_for_patch_render_complete,
)
from tests.e2e.support_runtime_host import StandaloneRuntimeHost

DEFAULT_VIEWPORT_WIDTH = 1200
DEFAULT_VIEWPORT_HEIGHT = 900
DEFAULT_THEME = "light"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output" / "render-review"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a topology through the standalone browser canvas path and save a PNG plus JSON summary.",
    )
    parser.add_argument("--family", required=True, help="Tiling family to render.")
    parser.add_argument("--patch-depth", type=int, help="Patch depth for aperiodic tilings.")
    parser.add_argument("--cell-size", type=int, help="Cell size for grid-sized tilings.")
    parser.add_argument("--viewport-width", type=int, default=DEFAULT_VIEWPORT_WIDTH)
    parser.add_argument("--viewport-height", type=int, default=DEFAULT_VIEWPORT_HEIGHT)
    parser.add_argument("--theme", choices=("light", "dark"), default=DEFAULT_THEME)
    parser.add_argument("--out", type=Path, help="PNG output path.")
    parser.add_argument("--summary-out", type=Path, help="JSON summary output path.")
    return parser


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.patch_depth is not None and args.cell_size is not None:
        parser.error("--patch-depth and --cell-size are mutually exclusive.")
    if args.viewport_width <= 0 or args.viewport_height <= 0:
        parser.error("--viewport-width and --viewport-height must be positive.")
    return args


def _resolve_actual_control_value(page: Page, selector: str) -> int | None:
    value = page.evaluate(
        """(elementSelector) => {
            const input = document.querySelector(elementSelector);
            if (!(input instanceof HTMLInputElement) || input.hidden) {
                return null;
            }
            const numericValue = Number(input.value);
            return Number.isFinite(numericValue) ? numericValue : null;
        }""",
        selector,
    )
    if value is None:
        return None
    return int(value)


def _default_output_stem(
    family: str,
    *,
    patch_depth: int | None,
    cell_size: int | None,
) -> str:
    if patch_depth is not None:
        return f"{family}-depth-{patch_depth}"
    if cell_size is not None:
        return f"{family}-size-{cell_size}"
    return family


def resolve_output_paths(
    *,
    family: str,
    patch_depth: int | None,
    cell_size: int | None,
    out: Path | None,
    summary_out: Path | None,
) -> tuple[Path, Path]:
    if out is None and summary_out is None:
        stem = _default_output_stem(family, patch_depth=patch_depth, cell_size=cell_size)
        return (DEFAULT_OUTPUT_DIR / f"{stem}.png", DEFAULT_OUTPUT_DIR / f"{stem}.json")
    if out is not None and summary_out is None:
        return (out, out.with_suffix(".json"))
    if out is None and summary_out is not None:
        return (summary_out.with_suffix(".png"), summary_out)
    assert out is not None and summary_out is not None
    return (out, summary_out)


def _apply_theme_init_script(page: Page, theme: str) -> None:
    selected_theme = json.dumps(theme)
    page.add_init_script(
        f"""
            (() => {{
                const selectedTheme = {selected_theme};
                try {{
                    window.localStorage.setItem("cellular-automaton-theme", selectedTheme);
                }} catch (error) {{
                    void error;
                }}
                document.documentElement.dataset.theme = selectedTheme;
            }})();
        """
    )


def _ensure_control_supported(
    page: Page,
    *,
    selector: str,
    requested_value: int | None,
    control_name: str,
    family: str,
) -> None:
    if requested_value is None:
        return
    is_visible = bool(
        page.evaluate(
            """(elementSelector) => {
                const input = document.querySelector(elementSelector);
                return input instanceof HTMLInputElement && !input.hidden;
            }""",
            selector,
        )
    )
    if not is_visible:
        raise RuntimeError(
            f"{control_name} is not available for tiling family {family!r}."
        )


def render_canvas_review(args: argparse.Namespace) -> tuple[Path, Path]:
    host = StandaloneRuntimeHost()
    host.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    viewport={
                        "width": int(args.viewport_width),
                        "height": int(args.viewport_height),
                    },
                )
                try:
                    page = context.new_page()
                    _apply_theme_init_script(page, str(args.theme))
                    page.goto(f"{host.base_url}/", wait_until="load")
                    wait_for_page_bootstrapped(page)
                    select_tiling_family(page, str(args.family), expect_reset_request=False)
                    _ensure_control_supported(
                        page,
                        selector="#patch-depth-input",
                        requested_value=args.patch_depth,
                        control_name="patch depth",
                        family=str(args.family),
                    )
                    _ensure_control_supported(
                        page,
                        selector="#cell-size-input",
                        requested_value=args.cell_size,
                        control_name="cell size",
                        family=str(args.family),
                    )
                    if args.patch_depth is not None:
                        set_patch_depth(page, int(args.patch_depth))
                    if args.cell_size is not None:
                        set_cell_size(page, int(args.cell_size))
                    wait_for_patch_render_complete(page)

                    actual_patch_depth = _resolve_actual_control_value(page, "#patch-depth-input")
                    actual_cell_size = _resolve_actual_control_value(page, "#cell-size-input")
                    png_path, summary_path = resolve_output_paths(
                        family=str(args.family),
                        patch_depth=actual_patch_depth,
                        cell_size=actual_cell_size,
                        out=args.out,
                        summary_out=args.summary_out,
                    )
                    png_path.parent.mkdir(parents=True, exist_ok=True)
                    summary_path.parent.mkdir(parents=True, exist_ok=True)
                    page.locator("#grid").screenshot(path=str(png_path))
                    visual_summary = canvas_visual_summary(page)
                    summary_payload: dict[str, Any] = {
                        "tiling_family": str(args.family),
                        "requestedPatchDepth": args.patch_depth,
                        "requestedCellSize": args.cell_size,
                        "patchDepth": actual_patch_depth,
                        "cellSize": actual_cell_size,
                        "viewportWidth": int(args.viewport_width),
                        "viewportHeight": int(args.viewport_height),
                        "theme": str(args.theme),
                        "canvasPixelWidth": int(visual_summary["canvasWidth"]),
                        "canvasPixelHeight": int(visual_summary["canvasHeight"]),
                        "coverageWidthRatio": float(visual_summary["coverageWidthRatio"]),
                        "coverageHeightRatio": float(visual_summary["coverageHeightRatio"]),
                        "dominantFillColors": visual_summary["dominantFillColors"],
                        "renderCellSize": float(visual_summary["renderCellSize"]),
                        "generationText": str(visual_summary["generationText"]),
                        "gridSizeText": str(visual_summary["gridSizeText"]),
                        "hostMode": "standalone",
                        "baseUrl": host.base_url,
                    }
                    summary_path.write_text(
                        json.dumps(summary_payload, indent=2, sort_keys=True),
                        encoding="utf-8",
                    )
                    return (png_path, summary_path)
                finally:
                    context.close()
            finally:
                browser.close()
    finally:
        host.close()


def main(argv: list[str] | None = None) -> int:
    args = parse_cli_args(argv)
    png_path, summary_path = render_canvas_review(args)
    print(f"render_png={png_path}")
    print(f"render_summary={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
