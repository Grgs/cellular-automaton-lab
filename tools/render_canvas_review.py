from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image
from playwright.sync_api import ConsoleMessage, Page, sync_playwright

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tests.e2e.browser_support.artifacts import (
    capture_browser_failure_artifacts,
    create_artifact_dir,
)
from tests.e2e.browser_support.render_review import (
    canvas_visual_summary,
    select_tiling_family,
    set_cell_size,
    set_patch_depth,
    wait_for_page_bootstrapped,
    wait_for_patch_render_complete,
)
from tests.e2e.support_runtime_host import BrowserRuntimeHost, create_runtime_host
from tools.render_review_profiles import resolve_render_review_profile

DEFAULT_VIEWPORT_WIDTH = 1200
DEFAULT_VIEWPORT_HEIGHT = 900
DEFAULT_THEME = "light"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output" / "render-review"
DEFAULT_ARTIFACTS_DIR = ROOT_DIR / "output" / "render-review-artifacts"


@dataclass(frozen=True)
class ResolvedRenderReviewRequest:
    family: str
    patch_depth: int | None
    cell_size: int | None
    viewport_width: int
    viewport_height: int
    theme: str
    out: Path | None
    summary_out: Path | None
    reference: Path | None
    montage_out: Path | None
    profile_name: str | None


@dataclass(frozen=True)
class RenderCanvasReviewResult:
    png_path: Path
    summary_path: Path
    montage_path: Path | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a topology through the browser canvas path and save a PNG plus JSON summary.",
    )
    parser.add_argument("--family", help="Tiling family to render.")
    parser.add_argument("--profile", help="Named render-review profile to use.")
    parser.add_argument("--patch-depth", type=int, help="Patch depth for aperiodic tilings.")
    parser.add_argument("--cell-size", type=int, help="Cell size for grid-sized tilings.")
    parser.add_argument("--viewport-width", type=int, default=DEFAULT_VIEWPORT_WIDTH)
    parser.add_argument("--viewport-height", type=int, default=DEFAULT_VIEWPORT_HEIGHT)
    parser.add_argument("--theme", choices=("light", "dark"), default=DEFAULT_THEME)
    parser.add_argument("--out", type=Path, help="PNG output path.")
    parser.add_argument("--summary-out", type=Path, help="JSON summary output path.")
    parser.add_argument("--reference", type=Path, help="Optional reference image path.")
    parser.add_argument("--montage-out", type=Path, help="Optional side-by-side montage output path.")
    return parser


def _parser_error(parser: argparse.ArgumentParser, message: str) -> None:
    parser.error(message)


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.viewport_width <= 0 or args.viewport_height <= 0:
        _parser_error(parser, "--viewport-width and --viewport-height must be positive.")
    if args.patch_depth is not None and args.cell_size is not None:
        _parser_error(parser, "--patch-depth and --cell-size are mutually exclusive.")
    if args.montage_out is not None and args.reference is None:
        _parser_error(parser, "--montage-out requires --reference.")
    return args


def resolve_render_review_request(args: argparse.Namespace) -> ResolvedRenderReviewRequest:
    parser = build_parser()
    profile = None
    if args.profile is not None:
        try:
            profile = resolve_render_review_profile(str(args.profile))
        except ValueError as exc:
            _parser_error(parser, str(exc))
    family = args.family or (profile.family if profile is not None else None)
    if not family:
        _parser_error(parser, "either --family or --profile is required.")
    patch_depth = args.patch_depth if args.patch_depth is not None else (
        profile.patch_depth if profile is not None else None
    )
    cell_size = args.cell_size if args.cell_size is not None else (
        profile.cell_size if profile is not None else None
    )
    if patch_depth is not None and cell_size is not None:
        _parser_error(parser, "--patch-depth and --cell-size are mutually exclusive after profile resolution.")
    viewport_width = int(args.viewport_width if args.viewport_width is not None else profile.viewport_width)
    viewport_height = int(args.viewport_height if args.viewport_height is not None else profile.viewport_height)
    theme = str(args.theme if args.theme is not None else profile.theme)
    reference = args.reference
    if reference is not None and not reference.exists():
        _parser_error(parser, f"reference image does not exist: {reference}")
    return ResolvedRenderReviewRequest(
        family=str(family),
        patch_depth=patch_depth,
        cell_size=cell_size,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        theme=theme,
        out=args.out,
        summary_out=args.summary_out,
        reference=reference,
        montage_out=args.montage_out,
        profile_name=str(args.profile) if args.profile is not None else None,
    )


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


def resolve_montage_path(
    *,
    png_path: Path,
    reference: Path | None,
    montage_out: Path | None,
) -> Path | None:
    if reference is None:
        return None
    if montage_out is not None:
        return montage_out
    return png_path.with_name(f"{png_path.stem}-montage.png")


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


def build_reference_montage(
    rendered_path: Path,
    reference_path: Path,
    montage_path: Path,
) -> dict[str, Any]:
    montage_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(rendered_path) as rendered_image, Image.open(reference_path) as reference_image:
        rendered = rendered_image.convert("RGBA")
        reference = reference_image.convert("RGBA")
        montage = Image.new(
            "RGBA",
            (rendered.width + reference.width, max(rendered.height, reference.height)),
            (255, 255, 255, 255),
        )
        montage.paste(rendered, (0, 0))
        montage.paste(reference, (rendered.width, 0))
        montage.save(montage_path)
        return {
            "montageImagePath": str(montage_path),
            "outputImagePath": str(rendered_path),
            "outputImageWidth": rendered.width,
            "outputImageHeight": rendered.height,
            "referenceImagePath": str(reference_path),
            "referenceImageWidth": reference.width,
            "referenceImageHeight": reference.height,
        }


def render_canvas_review(
    args: argparse.Namespace | ResolvedRenderReviewRequest,
    *,
    host: BrowserRuntimeHost | None = None,
    host_kind: str = "standalone",
    artifact_dir: Path | None = None,
    run_manifest: dict[str, Any] | None = None,
) -> RenderCanvasReviewResult:
    request = args if isinstance(args, ResolvedRenderReviewRequest) else resolve_render_review_request(args)
    console_messages: list[str] = []
    owned_host = host is None
    active_host = host or create_runtime_host(host_kind)
    page: Page | None = None
    try:
        active_host.start()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    viewport={
                        "width": int(request.viewport_width),
                        "height": int(request.viewport_height),
                    },
                )
                try:
                    page = context.new_page()
                    page.on(
                        "console",
                        lambda message: console_messages.append(
                            f"[console:{message.type}] {message.text}"
                        ),
                    )
                    page.on("pageerror", lambda error: console_messages.append(f"[pageerror] {error}"))
                    _apply_theme_init_script(page, request.theme)
                    page.goto(f"{active_host.base_url}/", wait_until="load")
                    wait_for_page_bootstrapped(page)
                    select_tiling_family(
                        page,
                        request.family,
                        expect_reset_request=active_host.client() is not None,
                    )
                    _ensure_control_supported(
                        page,
                        selector="#patch-depth-input",
                        requested_value=request.patch_depth,
                        control_name="patch depth",
                        family=request.family,
                    )
                    _ensure_control_supported(
                        page,
                        selector="#cell-size-input",
                        requested_value=request.cell_size,
                        control_name="cell size",
                        family=request.family,
                    )
                    if request.patch_depth is not None:
                        set_patch_depth(page, int(request.patch_depth))
                    if request.cell_size is not None:
                        set_cell_size(page, int(request.cell_size))
                    wait_for_patch_render_complete(page)

                    actual_patch_depth = _resolve_actual_control_value(page, "#patch-depth-input")
                    actual_cell_size = _resolve_actual_control_value(page, "#cell-size-input")
                    png_path, summary_path = resolve_output_paths(
                        family=request.family,
                        patch_depth=actual_patch_depth,
                        cell_size=actual_cell_size,
                        out=request.out,
                        summary_out=request.summary_out,
                    )
                    montage_path = resolve_montage_path(
                        png_path=png_path,
                        reference=request.reference,
                        montage_out=request.montage_out,
                    )
                    png_path.parent.mkdir(parents=True, exist_ok=True)
                    summary_path.parent.mkdir(parents=True, exist_ok=True)
                    page.locator("#grid").screenshot(path=str(png_path))
                    visual_summary = canvas_visual_summary(page)
                    summary_payload: dict[str, Any] = {
                        "tiling_family": request.family,
                        "profile": request.profile_name,
                        "requestedPatchDepth": request.patch_depth,
                        "requestedCellSize": request.cell_size,
                        "patchDepth": actual_patch_depth,
                        "cellSize": actual_cell_size,
                        "viewportWidth": int(request.viewport_width),
                        "viewportHeight": int(request.viewport_height),
                        "theme": request.theme,
                        "canvasPixelWidth": int(visual_summary["canvasWidth"]),
                        "canvasPixelHeight": int(visual_summary["canvasHeight"]),
                        "coverageWidthRatio": float(visual_summary["coverageWidthRatio"]),
                        "coverageHeightRatio": float(visual_summary["coverageHeightRatio"]),
                        "dominantFillColors": visual_summary["dominantFillColors"],
                        "renderCellSize": float(visual_summary["renderCellSize"]),
                        "generationText": str(visual_summary["generationText"]),
                        "gridSizeText": str(visual_summary["gridSizeText"]),
                        "hostMode": host_kind,
                        "baseUrl": active_host.base_url,
                    }
                    if request.reference is not None and montage_path is not None:
                        summary_payload["comparison"] = build_reference_montage(
                            png_path,
                            request.reference,
                            montage_path,
                        )
                    summary_path.write_text(
                        json.dumps(summary_payload, indent=2, sort_keys=True),
                        encoding="utf-8",
                    )
                    return RenderCanvasReviewResult(
                        png_path=png_path,
                        summary_path=summary_path,
                        montage_path=montage_path,
                    )
                finally:
                    context.close()
            finally:
                browser.close()
    except Exception as exc:
        failure_dir = artifact_dir or create_artifact_dir(
            name=f"render-review-{request.family}",
            default_parent=DEFAULT_ARTIFACTS_DIR,
        )
        manifest = dict(run_manifest or {})
        manifest.update(
            {
                "baseUrl": active_host.base_url,
                "exitStatus": "failure",
                "failureReason": str(exc),
                "hostKind": host_kind,
                "tilingFamily": request.family,
            }
        )
        capture_browser_failure_artifacts(
            failure_dir,
            host=active_host,
            page=page,
            console_messages=console_messages,
            run_manifest=manifest,
        )
        raise
    finally:
        if owned_host:
            active_host.close()


def main(argv: list[str] | None = None) -> int:
    parsed_args = parse_cli_args(argv)
    result = render_canvas_review(parsed_args)
    print(f"render_png={result.png_path}")
    print(f"render_summary={result.summary_path}")
    if result.montage_path is not None:
        print(f"render_montage={result.montage_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
