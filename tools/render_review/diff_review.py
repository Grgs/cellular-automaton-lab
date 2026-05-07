from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.render_review.browser_support.artifacts import create_artifact_dir
from tools.render_review.sweep import (
    RenderReviewSweepResult,
    resolve_sweep_request,
    run_render_review_sweep,
)

DEFAULT_DIFF_REVIEW_OUTPUT_DIR = ROOT_DIR / "output" / "render-review-diffs"
DEFAULT_CARD_IMAGE_WIDTH = 420
DEFAULT_CARD_IMAGE_HEIGHT = 300


@dataclass(frozen=True)
class ResolvedDiffReviewRequest:
    sweep_manifest: Path | None
    profile: str | None
    hosts: str | None
    themes: str | None
    patch_depths: str | None
    cell_sizes: str | None
    literature_review: bool
    reference: Path | None
    reference_cache_dir: Path | None
    artifact_dir: Path | None
    out_html: Path | None
    out_image: Path | None
    title: str | None
    columns: int | None
    allow_stale_standalone: bool
    card_image_width: int
    card_image_height: int


@dataclass(frozen=True)
class DiffReviewCase:
    index: int
    name: str
    host: str | None
    theme: str | None
    patch_depth: int | None
    cell_size: int | None
    image_path: Path
    render_png_path: Path | None
    render_montage_path: Path | None
    render_summary_path: Path | None
    metrics: dict[str, Any]
    visual_metrics: dict[str, Any] | None
    consistency_warnings: tuple[str, ...]
    provenance_warnings: tuple[str, ...]
    diagnostic_errors: tuple[str, ...]


@dataclass(frozen=True)
class DiffReviewResult:
    sweep_manifest: Path
    html_path: Path
    image_path: Path
    case_count: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build one side-by-side render-review diff sheet from an existing sweep manifest "
            "or by running a new render-review sweep first."
        ),
    )
    parser.add_argument(
        "--sweep-manifest",
        type=Path,
        help="Existing render-review sweep manifest to summarize.",
    )
    parser.add_argument(
        "--profile",
        help="Named render-review profile. Required when --sweep-manifest is omitted.",
    )
    parser.add_argument("--hosts", help="Comma-separated host kinds for a new sweep.")
    parser.add_argument("--themes", help="Comma-separated themes for a new sweep.")
    parser.add_argument("--patch-depths", help="Comma-separated patch depths for a new sweep.")
    parser.add_argument("--cell-sizes", help="Comma-separated cell sizes for a new sweep.")
    parser.add_argument(
        "--reference",
        type=Path,
        help="Optional reference image path to pass to a new sweep.",
    )
    parser.add_argument(
        "--literature-review",
        action="store_true",
        help="Pass profile-owned literature-reference settings through to a new sweep.",
    )
    parser.add_argument(
        "--reference-cache-dir",
        type=Path,
        help="Optional literature reference cache directory for a new sweep.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help=(
            "Artifact directory for a new sweep, or default output directory for sheets built "
            "from an existing manifest."
        ),
    )
    parser.add_argument("--out-html", type=Path, help="HTML diff sheet output path.")
    parser.add_argument("--out-image", type=Path, help="PNG contact-sheet output path.")
    parser.add_argument("--title", help="Optional title for the generated sheets.")
    parser.add_argument(
        "--allow-stale-standalone",
        action="store_true",
        help="Skip the standalone build freshness preflight for intentional stale-bundle diagnosis.",
    )
    parser.add_argument(
        "--columns",
        type=int,
        help="Number of image columns in the PNG sheet. Default: up to 3.",
    )
    parser.add_argument(
        "--card-image-width",
        type=int,
        default=DEFAULT_CARD_IMAGE_WIDTH,
        help=f"Per-case image panel width. Default: {DEFAULT_CARD_IMAGE_WIDTH}.",
    )
    parser.add_argument(
        "--card-image-height",
        type=int,
        default=DEFAULT_CARD_IMAGE_HEIGHT,
        help=f"Per-case image panel height. Default: {DEFAULT_CARD_IMAGE_HEIGHT}.",
    )
    return parser


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def _parser_error(parser: argparse.ArgumentParser, message: str) -> None:
    parser.error(message)


def resolve_diff_review_request(args: argparse.Namespace) -> ResolvedDiffReviewRequest:
    parser = build_parser()
    sweep_manifest = args.sweep_manifest
    profile = str(args.profile) if args.profile is not None else None
    if sweep_manifest is not None and profile is not None:
        _parser_error(parser, "--sweep-manifest and --profile are mutually exclusive.")
    if sweep_manifest is None and profile is None:
        _parser_error(parser, "either --sweep-manifest or --profile is required.")
    if sweep_manifest is not None and not sweep_manifest.exists():
        _parser_error(parser, f"sweep manifest does not exist: {sweep_manifest}")
    if args.reference is not None and not args.reference.exists():
        _parser_error(parser, f"reference image does not exist: {args.reference}")
    if args.columns is not None and args.columns <= 0:
        _parser_error(parser, "--columns must be positive.")
    if args.card_image_width <= 0 or args.card_image_height <= 0:
        _parser_error(parser, "--card-image-width and --card-image-height must be positive.")
    return ResolvedDiffReviewRequest(
        sweep_manifest=sweep_manifest,
        profile=profile,
        hosts=args.hosts,
        themes=args.themes,
        patch_depths=args.patch_depths,
        cell_sizes=args.cell_sizes,
        literature_review=bool(args.literature_review),
        reference=args.reference,
        reference_cache_dir=args.reference_cache_dir,
        artifact_dir=args.artifact_dir,
        out_html=args.out_html,
        out_image=args.out_image,
        title=str(args.title) if args.title is not None else None,
        columns=args.columns,
        allow_stale_standalone=bool(args.allow_stale_standalone),
        card_image_width=int(args.card_image_width),
        card_image_height=int(args.card_image_height),
    )


def _path_from_manifest(value: object, *, manifest_dir: Path) -> Path | None:
    if value is None:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    root_relative_path = ROOT_DIR / path
    manifest_relative_path = manifest_dir / path
    if root_relative_path.exists():
        return root_relative_path
    if manifest_relative_path.exists():
        return manifest_relative_path
    return root_relative_path if path.parts[:1] == ("output",) else manifest_relative_path


def _as_optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if not isinstance(value, str):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _as_string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(str(item) for item in value if str(item))


def load_sweep_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Sweep manifest is not a JSON object: {path}")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"Sweep manifest does not contain a cases list: {path}")
    return payload


def collect_diff_review_cases(
    sweep_manifest: dict[str, Any],
    *,
    manifest_path: Path,
) -> tuple[DiffReviewCase, ...]:
    manifest_dir = manifest_path.parent
    raw_cases = sweep_manifest.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("Sweep manifest does not contain a cases list.")

    cases: list[DiffReviewCase] = []
    for position, raw_case in enumerate(raw_cases, start=1):
        if not isinstance(raw_case, dict):
            continue
        render_png = _path_from_manifest(raw_case.get("renderPng"), manifest_dir=manifest_dir)
        render_montage = _path_from_manifest(
            raw_case.get("renderMontage"), manifest_dir=manifest_dir
        )
        image_path = render_montage or render_png
        if image_path is None:
            raise ValueError(f"Sweep case {position} does not declare renderPng/renderMontage.")
        metrics = raw_case.get("metrics")
        visual_metrics = raw_case.get("visualMetrics")
        cases.append(
            DiffReviewCase(
                index=_as_optional_int(raw_case.get("index")) or position,
                name=str(raw_case.get("name") or f"case-{position}"),
                host=str(raw_case.get("host")) if raw_case.get("host") is not None else None,
                theme=str(raw_case.get("theme")) if raw_case.get("theme") is not None else None,
                patch_depth=_as_optional_int(raw_case.get("patchDepth")),
                cell_size=_as_optional_int(raw_case.get("cellSize")),
                image_path=image_path,
                render_png_path=render_png,
                render_montage_path=render_montage,
                render_summary_path=_path_from_manifest(
                    raw_case.get("renderSummary"), manifest_dir=manifest_dir
                ),
                metrics=metrics if isinstance(metrics, dict) else {},
                visual_metrics=visual_metrics if isinstance(visual_metrics, dict) else None,
                consistency_warnings=_as_string_tuple(raw_case.get("consistencyWarnings")),
                provenance_warnings=_as_string_tuple(raw_case.get("provenanceWarnings")),
                diagnostic_errors=_as_string_tuple(raw_case.get("diagnosticErrors")),
            )
        )
    if not cases:
        raise ValueError("Sweep manifest contains no renderable cases.")
    return tuple(cases)


def _default_diff_artifact_dir(*, profile_name: str | None) -> Path:
    timestamp = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = profile_name or "manifest"
    return create_artifact_dir(
        name=f"{timestamp}-{suffix}",
        default_parent=DEFAULT_DIFF_REVIEW_OUTPUT_DIR,
    )


def _build_sweep_args(request: ResolvedDiffReviewRequest) -> argparse.Namespace:
    return argparse.Namespace(
        profile=request.profile,
        hosts=request.hosts,
        themes=request.themes,
        patch_depths=request.patch_depths,
        cell_sizes=request.cell_sizes,
        reference=request.reference,
        literature_review=request.literature_review,
        reference_cache_dir=request.reference_cache_dir,
        artifact_dir=request.artifact_dir
        or _default_diff_artifact_dir(profile_name=request.profile),
        allow_stale_standalone=request.allow_stale_standalone,
    )


def resolve_sweep_manifest_for_diff(request: ResolvedDiffReviewRequest) -> Path:
    if request.sweep_manifest is not None:
        return request.sweep_manifest
    sweep_request = resolve_sweep_request(_build_sweep_args(request))
    sweep_result: RenderReviewSweepResult = run_render_review_sweep(sweep_request)
    return sweep_result.manifest_path


def _default_sheet_paths(
    *,
    manifest_path: Path,
    artifact_dir: Path | None,
    out_html: Path | None,
    out_image: Path | None,
) -> tuple[Path, Path]:
    output_dir = artifact_dir or manifest_path.parent
    html_path = out_html or output_dir / "review-diff.html"
    image_path = out_image or output_dir / "review-diff.png"
    return html_path, image_path


def _relative_path(path: Path, *, base_dir: Path) -> str:
    try:
        return path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _metric_text(metrics: dict[str, Any], key: str) -> str | None:
    value = metrics.get(key)
    if value is None:
        return None
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def build_case_metadata_lines(case: DiffReviewCase) -> tuple[str, ...]:
    lines: list[str] = []
    host_theme = " / ".join(part for part in (case.host, case.theme) if part)
    if host_theme:
        lines.append(host_theme)
    if case.patch_depth is not None:
        lines.append(f"depth {case.patch_depth}")
    if case.cell_size is not None:
        lines.append(f"cell size {case.cell_size}")
    grid_size = _metric_text(case.metrics, "gridSizeText")
    if grid_size:
        lines.append(f"grid {grid_size}")
    browser_count = _metric_text(case.metrics, "browserTopologyCellCount")
    backend_count = _metric_text(case.metrics, "backendTopologyCellCount")
    if browser_count or backend_count:
        lines.append(f"cells browser={browser_count or '-'} backend={backend_count or '-'}")
    render_cell_size = _metric_text(case.metrics, "renderCellSize")
    if render_cell_size:
        lines.append(f"render cell {render_cell_size}")
    if case.visual_metrics:
        radial = _metric_text(case.visual_metrics, "radialSymmetryScore")
        aspect = _metric_text(case.visual_metrics, "visibleAspectRatio")
        if radial:
            lines.append(f"radial symmetry {radial}")
        if aspect:
            lines.append(f"visible aspect {aspect}")
    warning_count = (
        len(case.consistency_warnings) + len(case.provenance_warnings) + len(case.diagnostic_errors)
    )
    if warning_count:
        lines.append(f"warnings {warning_count}")
    return tuple(lines)


def build_diff_review_html(
    *,
    cases: tuple[DiffReviewCase, ...],
    sweep_manifest_path: Path,
    output_path: Path,
    title: str | None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_title = title or f"Render Review Diff: {sweep_manifest_path.parent.name}"
    case_cards: list[str] = []
    for case in cases:
        image_src = html.escape(_relative_path(case.image_path, base_dir=output_path.parent))
        metadata = "\n".join(
            f"<li>{html.escape(line)}</li>" for line in build_case_metadata_lines(case)
        )
        warnings = ""
        all_warnings = (
            *case.consistency_warnings,
            *case.provenance_warnings,
            *case.diagnostic_errors,
        )
        if all_warnings:
            warnings = (
                '<ul class="warnings">'
                + "\n".join(f"<li>{html.escape(warning)}</li>" for warning in all_warnings)
                + "</ul>"
            )
        summary_link = ""
        if case.render_summary_path is not None:
            href = html.escape(
                _relative_path(case.render_summary_path, base_dir=output_path.parent)
            )
            summary_link = f'<a href="{href}">summary</a>'
        case_cards.append(
            "\n".join(
                [
                    '<article class="case-card">',
                    f"<h2>{case.index}. {html.escape(case.name)}</h2>",
                    f'<img src="{image_src}" alt="{html.escape(case.name)} render" />',
                    f'<ul class="metadata">{metadata}</ul>',
                    warnings,
                    f'<p class="links">{summary_link}</p>' if summary_link else "",
                    "</article>",
                ]
            )
        )
    manifest_rel = html.escape(_relative_path(sweep_manifest_path, base_dir=output_path.parent))
    payload = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(page_title)}</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Georgia, "Times New Roman", serif;
      background: #f5f1e8;
      color: #211d17;
    }}
    body {{
      margin: 0;
      padding: 32px;
      background:
        radial-gradient(circle at 20% 10%, rgba(181, 112, 49, 0.16), transparent 34rem),
        linear-gradient(135deg, #fbf7ef 0%, #eadfcb 100%);
    }}
    header {{
      margin-bottom: 24px;
      max-width: 960px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 34px;
      letter-spacing: -0.02em;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
    }}
    .case-card {{
      border: 1px solid rgba(46, 38, 28, 0.18);
      border-radius: 16px;
      padding: 14px;
      background: rgba(255, 252, 245, 0.88);
      box-shadow: 0 18px 44px rgba(46, 38, 28, 0.12);
    }}
    .case-card h2 {{
      margin: 0 0 12px;
      font-size: 18px;
    }}
    .case-card img {{
      display: block;
      width: 100%;
      background: #eee7da;
      border-radius: 10px;
      border: 1px solid rgba(46, 38, 28, 0.14);
    }}
    .metadata, .warnings {{
      margin: 12px 0 0;
      padding-left: 20px;
      line-height: 1.35;
    }}
    .warnings {{
      color: #8a350f;
    }}
    .links {{
      margin: 12px 0 0;
      font-size: 14px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(page_title)}</h1>
    <p>Source sweep manifest: <a href="{manifest_rel}">{manifest_rel}</a></p>
  </header>
  <main class="grid">
    {"".join(case_cards)}
  </main>
</body>
</html>
"""
    output_path.write_text(payload, encoding="utf-8")
    return output_path


def _contained_image_panel(image_path: Path, *, width: int, height: int) -> Image.Image:
    panel = Image.new("RGBA", (width, height), (241, 237, 228, 255))
    if not image_path.exists():
        return panel
    with Image.open(image_path) as raw_image:
        image = raw_image.convert("RGBA")
        contained = ImageOps.contain(image, (width, height))
        offset = ((width - contained.width) // 2, (height - contained.height) // 2)
        panel.paste(contained, offset)
    return panel


def _draw_text_lines(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    lines: tuple[str, ...],
    fill: tuple[int, int, int, int],
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    max_width: int,
    line_height: int,
) -> None:
    x, y = origin
    for line in lines:
        rendered = line
        while rendered and draw.textlength(rendered, font=font) > max_width:
            rendered = rendered[:-1]
        if rendered != line and len(rendered) > 1:
            rendered = f"{rendered[:-1]}…"
        draw.text((x, y), rendered, fill=fill, font=font)
        y += line_height


def build_diff_review_image(
    *,
    cases: tuple[DiffReviewCase, ...],
    output_path: Path,
    title: str | None,
    columns: int | None,
    card_image_width: int,
    card_image_height: int,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_columns = columns or min(3, max(1, len(cases)))
    rows = int(math.ceil(len(cases) / resolved_columns))
    margin = 24
    gutter = 18
    header_height = 58
    metadata_height = 108
    card_width = card_image_width
    card_height = card_image_height + metadata_height
    sheet_width = margin * 2 + resolved_columns * card_width + (resolved_columns - 1) * gutter
    sheet_height = margin * 2 + header_height + rows * card_height + (rows - 1) * gutter
    sheet = Image.new("RGBA", (sheet_width, sheet_height), (246, 241, 231, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    title_text = title or "Render Review Diff"
    draw.text((margin, margin), title_text, fill=(33, 29, 23, 255), font=font)
    draw.text(
        (margin, margin + 22),
        f"{len(cases)} case{'s' if len(cases) != 1 else ''}",
        fill=(86, 75, 62, 255),
        font=font,
    )
    for offset, case in enumerate(cases):
        row = offset // resolved_columns
        column = offset % resolved_columns
        left = margin + column * (card_width + gutter)
        top = margin + header_height + row * (card_height + gutter)
        panel = _contained_image_panel(
            case.image_path,
            width=card_image_width,
            height=card_image_height,
        )
        sheet.paste(panel, (left, top))
        draw.rectangle(
            [left, top, left + card_width - 1, top + card_image_height - 1],
            outline=(205, 195, 181, 255),
        )
        metadata_lines = (
            f"{case.index}. {case.name}",
            *build_case_metadata_lines(case)[:5],
        )
        _draw_text_lines(
            draw,
            origin=(left, top + card_image_height + 10),
            lines=metadata_lines,
            fill=(33, 29, 23, 255),
            font=font,
            max_width=card_width - 10,
            line_height=16,
        )
    sheet.convert("RGB").save(output_path)
    return output_path


def run_render_review_diff(request: ResolvedDiffReviewRequest) -> DiffReviewResult:
    sweep_manifest_path = resolve_sweep_manifest_for_diff(request)
    sweep_manifest = load_sweep_manifest(sweep_manifest_path)
    cases = collect_diff_review_cases(sweep_manifest, manifest_path=sweep_manifest_path)
    html_path, image_path = _default_sheet_paths(
        manifest_path=sweep_manifest_path,
        artifact_dir=request.artifact_dir if request.sweep_manifest is not None else None,
        out_html=request.out_html,
        out_image=request.out_image,
    )
    title = request.title or f"Render Review Diff: {sweep_manifest.get('profile', 'sweep')}"
    build_diff_review_html(
        cases=cases,
        sweep_manifest_path=sweep_manifest_path,
        output_path=html_path,
        title=title,
    )
    build_diff_review_image(
        cases=cases,
        output_path=image_path,
        title=title,
        columns=request.columns,
        card_image_width=request.card_image_width,
        card_image_height=request.card_image_height,
    )
    return DiffReviewResult(
        sweep_manifest=sweep_manifest_path,
        html_path=html_path,
        image_path=image_path,
        case_count=len(cases),
    )


def main(argv: list[str] | None = None) -> int:
    request = resolve_diff_review_request(parse_cli_args(argv))
    try:
        result = run_render_review_diff(request)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"sweep_manifest={result.sweep_manifest}")
    print(f"diff_html={result.html_path}")
    print(f"diff_image={result.image_path}")
    print(f"diff_cases={result.case_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
