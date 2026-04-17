from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps
from playwright.sync_api import ConsoleMessage, Page, sync_playwright

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tests.e2e.browser_support.artifacts import (
    capture_browser_failure_artifacts,
    create_artifact_dir,
)
from tests.e2e.browser_support.render_review import (
    browser_overlap_hotspots,
    browser_topology_summary,
    browser_transform_report,
    canvas_visual_summary,
    select_tiling_family,
    set_cell_size,
    set_patch_depth,
    wait_for_page_bootstrapped,
    wait_for_patch_render_complete,
)
from tests.e2e.support_runtime_host import BrowserRuntimeHost, create_runtime_host
from tools.render_review_profiles import (
    LiteratureReference,
    OverlapPolicy,
    RenderReviewProfile,
    describe_render_review_profile,
    iter_render_review_profiles,
    resolve_overlap_policy,
    resolve_render_review_profile,
    resolve_profile_reference_cache_path,
)

DEFAULT_VIEWPORT_WIDTH = 1200
DEFAULT_VIEWPORT_HEIGHT = 900
DEFAULT_THEME = "light"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output" / "render-review"
DEFAULT_ARTIFACTS_DIR = ROOT_DIR / "output" / "render-review-artifacts"
DEFAULT_REFERENCE_CACHE_DIR = ROOT_DIR / "output" / "literature-reference-cache"


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
    literature_review: bool
    reference_cache_dir: Path
    profile_name: str | None
    profile: RenderReviewProfile | None
    literature_reference: ResolvedLiteratureReference


@dataclass(frozen=True)
class ResolvedLiteratureReference:
    requested: bool
    citation_label: str | None
    source_urls: tuple[str, ...]
    review_note: str | None
    reference_status: str | None
    reference_path: Path | None
    cache_path: Path | None
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class RenderCanvasReviewResult:
    png_path: Path
    summary_path: Path
    montage_path: Path | None
    consistency_warnings: tuple[str, ...]
    provenance_warnings: tuple[str, ...]
    literature_warnings: tuple[str, ...]
    literature_reference_status: str | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a topology through the browser canvas path and save a PNG plus JSON summary.",
    )
    parser.add_argument("--family", help="Tiling family to render.")
    parser.add_argument("--profile", help="Named render-review profile to use.")
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List the available named render-review profiles and exit.",
    )
    parser.add_argument("--patch-depth", type=int, help="Patch depth for aperiodic tilings.")
    parser.add_argument("--cell-size", type=int, help="Cell size for grid-sized tilings.")
    parser.add_argument("--viewport-width", type=int, default=DEFAULT_VIEWPORT_WIDTH)
    parser.add_argument("--viewport-height", type=int, default=DEFAULT_VIEWPORT_HEIGHT)
    parser.add_argument("--theme", choices=("light", "dark"), default=DEFAULT_THEME)
    parser.add_argument("--out", type=Path, help="PNG output path.")
    parser.add_argument("--summary-out", type=Path, help="JSON summary output path.")
    parser.add_argument("--reference", type=Path, help="Optional reference image path.")
    parser.add_argument("--montage-out", type=Path, help="Optional side-by-side montage output path.")
    parser.add_argument(
        "--literature-review",
        action="store_true",
        help="Resolve a profile-owned literature reference from the local cache when no explicit --reference is provided.",
    )
    parser.add_argument(
        "--reference-cache-dir",
        type=Path,
        default=DEFAULT_REFERENCE_CACHE_DIR,
        help="Cache directory for operator-provided literature reference images.",
    )
    return parser


def _parser_error(parser: argparse.ArgumentParser, message: str) -> None:
    parser.error(message)


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_profiles:
        return args
    if args.viewport_width <= 0 or args.viewport_height <= 0:
        _parser_error(parser, "--viewport-width and --viewport-height must be positive.")
    if args.patch_depth is not None and args.cell_size is not None:
        _parser_error(parser, "--patch-depth and --cell-size are mutually exclusive.")
    if args.montage_out is not None and args.reference is None and not bool(args.literature_review):
        _parser_error(parser, "--montage-out requires --reference or --literature-review.")
    return args


def resolve_literature_reference(
    *,
    profile: RenderReviewProfile | None,
    explicit_reference: Path | None,
    literature_review: bool,
    reference_cache_dir: Path,
) -> ResolvedLiteratureReference:
    warnings: list[str] = []
    reference_path = explicit_reference
    cache_path: Path | None = None
    reference_status: str | None = None
    citation_label: str | None = None
    review_note: str | None = None
    source_urls: tuple[str, ...] = ()

    literature_reference: LiteratureReference | None = None
    if profile is not None:
        literature_reference = profile.literature_reference
    if literature_reference is not None:
        citation_label = literature_reference.citation_label
        source_urls = (
            literature_reference.primary_source_url,
            *literature_reference.secondary_source_urls,
        )
        review_note = literature_reference.review_note

    if explicit_reference is not None:
        reference_status = "explicit"
    elif literature_review:
        if literature_reference is None:
            warnings.append(
                f"Profile {profile.name!r} does not declare literature reference metadata."
                if profile is not None
                else "Literature review requested without a render-review profile."
            )
            reference_status = "missing"
        else:
            cache_path = resolve_profile_reference_cache_path(profile, cache_dir=reference_cache_dir)
            if cache_path is not None and cache_path.exists():
                reference_path = cache_path
                reference_status = "cached"
            else:
                reference_status = "missing"
                if cache_path is not None:
                    warnings.append(
                        f"Literature reference image was not found in the local cache: {cache_path}"
                    )
                else:
                    warnings.append(
                        f"Profile {profile.name!r} does not declare a default literature cache filename."
                    )

    return ResolvedLiteratureReference(
        requested=literature_review,
        citation_label=citation_label,
        source_urls=source_urls,
        review_note=review_note,
        reference_status=reference_status,
        reference_path=reference_path,
        cache_path=cache_path,
        warnings=tuple(warnings),
    )


def resolve_render_review_request(args: argparse.Namespace) -> ResolvedRenderReviewRequest:
    parser = build_parser()
    profile = None
    if args.profile is not None:
        try:
            profile = resolve_render_review_profile(str(args.profile))
        except ValueError as exc:
            _parser_error(parser, str(exc))
    if args.literature_review and profile is None:
        _parser_error(parser, "--literature-review requires --profile.")
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
    explicit_reference = args.reference
    if explicit_reference is not None and not explicit_reference.exists():
        _parser_error(parser, f"reference image does not exist: {explicit_reference}")
    literature_reference = resolve_literature_reference(
        profile=profile,
        explicit_reference=explicit_reference,
        literature_review=bool(args.literature_review),
        reference_cache_dir=Path(args.reference_cache_dir),
    )
    return ResolvedRenderReviewRequest(
        family=str(family),
        patch_depth=patch_depth,
        cell_size=cell_size,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        theme=theme,
        out=args.out,
        summary_out=args.summary_out,
        reference=literature_reference.reference_path,
        montage_out=args.montage_out,
        literature_review=bool(args.literature_review),
        reference_cache_dir=Path(args.reference_cache_dir),
        profile_name=str(args.profile) if args.profile is not None else None,
        profile=profile,
        literature_reference=literature_reference,
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


def build_literature_review_summary(
    *,
    literature_reference: ResolvedLiteratureReference,
    comparison: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "requested": literature_reference.requested,
        "citationLabel": literature_reference.citation_label,
        "sourceUrls": list(literature_reference.source_urls),
        "reviewNote": literature_reference.review_note,
        "referenceImageStatus": literature_reference.reference_status,
        "referenceImagePath": (
            str(literature_reference.reference_path)
            if literature_reference.reference_path is not None
            else None
        ),
        "referenceCachePath": (
            str(literature_reference.cache_path)
            if literature_reference.cache_path is not None
            else None
        ),
        "comparison": comparison,
        "warnings": list(literature_reference.warnings),
    }


def condense_transform_report(transform_report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(transform_report, dict):
        return None
    sample_cells = transform_report.get("sampleCells")
    condensed_sample_ids: dict[str, str | None] = {}
    if isinstance(sample_cells, dict):
        for role, payload in sample_cells.items():
            condensed_sample_ids[str(role)] = (
                str(payload.get("cellId"))
                if isinstance(payload, dict) and payload.get("cellId") is not None
                else None
            )
    render_metrics = transform_report.get("renderMetrics")
    return {
        "adapterGeometry": transform_report.get("adapterGeometry"),
        "adapterFamily": transform_report.get("adapterFamily"),
        "topologyBounds": transform_report.get("topologyBounds"),
        "renderedBounds": (
            {
                "width": render_metrics.get("cssWidth"),
                "height": render_metrics.get("cssHeight"),
                "canvasWidth": render_metrics.get("canvasWidth"),
                "canvasHeight": render_metrics.get("canvasHeight"),
            }
            if isinstance(render_metrics, dict)
            else None
        ),
        "sampleCellIds": condensed_sample_ids,
    }


def condense_overlap_hotspots(overlap_hotspots: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(overlap_hotspots, dict):
        return None
    return {
        "status": overlap_hotspots.get("status"),
        "policyMode": overlap_hotspots.get("policyMode"),
        "representativeCellCount": overlap_hotspots.get("representativeCellCount"),
        "sampledOverlapCount": overlap_hotspots.get("sampledOverlapCount"),
        "maxSampledArea": overlap_hotspots.get("maxSampledArea"),
        "transformSampleHits": overlap_hotspots.get("transformSampleHits"),
        "topKindPairs": overlap_hotspots.get("topKindPairs"),
    }


def condense_settle_diagnostics(settle_diagnostics: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(settle_diagnostics, dict):
        return None
    return {
        "settled": bool(settle_diagnostics.get("settled")),
        "stablePollCountRequired": settle_diagnostics.get("stablePollCountRequired"),
        "stablePollIntervalMs": settle_diagnostics.get("stablePollIntervalMs"),
        "settledAt": settle_diagnostics.get("settledAt"),
        "settleDurationMs": settle_diagnostics.get("settleDurationMs"),
        "finalSnapshot": settle_diagnostics.get("finalSnapshot"),
        "warnings": list(settle_diagnostics.get("warnings", [])),
    }


def build_overlap_hotspots_summary(
    *,
    family: str,
    profile: RenderReviewProfile | None,
    overlap_hotspots: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(overlap_hotspots, dict):
        return None
    policy = resolve_overlap_policy(family=family, profile=profile)
    sampled_overlap_count = int(overlap_hotspots.get("sampledOverlapCount") or 0)
    max_sampled_area = float(overlap_hotspots.get("maxSampledArea") or 0)
    status = "diagnostic-only"
    warnings: list[str] = []
    if sampled_overlap_count > 0:
        if policy.mode == "strict":
            status = "blocking"
            warnings.append(
                f"{family!r} reported {sampled_overlap_count} positive-area representative overlaps under the strict overlap policy."
            )
        else:
            max_area_threshold = float(policy.expected_to_reduce_max_sampled_area or 0)
            max_count_threshold = int(policy.expected_to_reduce_max_sampled_count or 0)
            if sampled_overlap_count <= max_count_threshold and max_sampled_area <= max_area_threshold:
                status = "expected-to-reduce"
                warnings.append(
                    f"{family!r} still reports residual positive-area overlap, but it is within the current relaxed diagnostic budget."
                )
            else:
                status = "blocking"
                warnings.append(
                    f"{family!r} reports large structural overlap: {sampled_overlap_count} sampled pairs with max area {max_sampled_area:.3f}."
                )
    return {
        **overlap_hotspots,
        "policyMode": policy.mode,
        "policyReviewNote": policy.review_note,
        "expectedToReduceMaxSampledArea": policy.expected_to_reduce_max_sampled_area,
        "expectedToReduceMaxSampledCount": policy.expected_to_reduce_max_sampled_count,
        "status": status,
        "warnings": warnings,
    }


def parse_grid_size_text(grid_size_text: str) -> dict[str, Any] | None:
    text = str(grid_size_text or "").strip()
    if not text:
        return None
    depth_match = re.match(r"^Depth\s+(?P<depth>\d+)\s+•\s+(?P<tiles>\d+)\s+tiles$", text)
    if depth_match:
        return {
            "mode": "patch_depth",
            "depth": int(depth_match.group("depth")),
            "tileCount": int(depth_match.group("tiles")),
        }
    dimensions_match = re.match(r"^(?P<width>\d+)\s*x\s*(?P<height>\d+)$", text)
    if dimensions_match:
        return {
            "mode": "grid_dimensions",
            "width": int(dimensions_match.group("width")),
            "height": int(dimensions_match.group("height")),
        }
    return None


def extract_backend_topology_facts(topology_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(topology_payload, dict):
        return None
    topology_spec = topology_payload.get("topology_spec")
    if not isinstance(topology_spec, dict):
        return None
    cells = topology_payload.get("cells")
    return {
        "tilingFamily": str(topology_spec.get("tiling_family") or "") or None,
        "patchDepth": int(topology_spec["patch_depth"]) if isinstance(topology_spec.get("patch_depth"), int) else None,
        "width": int(topology_spec["width"]) if isinstance(topology_spec.get("width"), int) else None,
        "height": int(topology_spec["height"]) if isinstance(topology_spec.get("height"), int) else None,
        "topologyCellCount": len(cells) if isinstance(cells, list) else None,
        "topologyRevision": str(topology_payload.get("topology_revision") or "") or None,
    }


def build_consistency_report(
    *,
    request: ResolvedRenderReviewRequest,
    host_kind: str,
    actual_patch_depth: int | None,
    actual_cell_size: int | None,
    grid_size_text: str,
    generation_text: str,
    backend_topology: dict[str, Any] | None,
    browser_topology: dict[str, Any] | None,
) -> dict[str, Any]:
    parsed_grid_size = parse_grid_size_text(grid_size_text)
    warnings: list[str] = []

    if backend_topology is None:
        warnings.append(f"Backend topology facts unavailable for host mode {host_kind}.")
    if browser_topology is None:
        warnings.append("Browser topology diagnostics were unavailable.")
    if grid_size_text and parsed_grid_size is None:
        warnings.append(f"Grid summary text could not be parsed: {grid_size_text!r}.")

    requested = {
        "tilingFamily": request.family,
        "patchDepth": request.patch_depth,
        "cellSize": request.cell_size,
    }
    dom_summary = {
        "gridSizeText": grid_size_text,
        "generationText": generation_text,
    }

    if browser_topology is not None:
        browser_family = browser_topology.get("tilingFamily")
        if browser_family is not None and browser_family != request.family:
            warnings.append(
                f"Requested tiling family {request.family!r} does not match browser state family {browser_family!r}."
            )
        browser_patch_depth = browser_topology.get("patchDepth")
        if actual_patch_depth is not None and browser_patch_depth is not None and browser_patch_depth != actual_patch_depth:
            warnings.append(
                f"Visible patch depth control value {actual_patch_depth} does not match browser state patch depth {browser_patch_depth}."
            )

    if backend_topology is not None:
        backend_family = backend_topology.get("tilingFamily")
        if backend_family is not None and backend_family != request.family:
            warnings.append(
                f"Requested tiling family {request.family!r} does not match backend topology family {backend_family!r}."
            )
        backend_patch_depth = backend_topology.get("patchDepth")
        if actual_patch_depth is not None and backend_patch_depth is not None and backend_patch_depth != actual_patch_depth:
            warnings.append(
                f"Visible patch depth control value {actual_patch_depth} does not match backend topology patch depth {backend_patch_depth}."
            )

    if (
        backend_topology is not None
        and browser_topology is not None
        and backend_topology.get("topologyCellCount") is not None
        and browser_topology.get("topologyCellCount") is not None
        and backend_topology["topologyCellCount"] != browser_topology["topologyCellCount"]
    ):
        warnings.append(
            "Backend topology cell count "
            f"{backend_topology['topologyCellCount']} does not match browser topology cell count "
            f"{browser_topology['topologyCellCount']}."
        )

    if parsed_grid_size is not None and parsed_grid_size.get("mode") == "patch_depth":
        parsed_depth = parsed_grid_size.get("depth")
        parsed_tile_count = parsed_grid_size.get("tileCount")
        if actual_patch_depth is not None and parsed_depth is not None and parsed_depth != actual_patch_depth:
            warnings.append(
                f"Grid summary depth {parsed_depth} does not match visible patch depth control value {actual_patch_depth}."
            )
        if browser_topology is not None and parsed_tile_count is not None:
            browser_tile_count = browser_topology.get("topologyCellCount")
            if browser_tile_count is not None and parsed_tile_count != browser_tile_count:
                warnings.append(
                    f"Grid summary tile count {parsed_tile_count} does not match browser topology cell count {browser_tile_count}."
                )
        if backend_topology is not None and parsed_tile_count is not None:
            backend_tile_count = backend_topology.get("topologyCellCount")
            if backend_tile_count is not None and parsed_tile_count != backend_tile_count:
                warnings.append(
                    f"Grid summary tile count {parsed_tile_count} does not match backend topology cell count {backend_tile_count}."
                )
    elif parsed_grid_size is not None and parsed_grid_size.get("mode") == "grid_dimensions":
        parsed_width = parsed_grid_size.get("width")
        parsed_height = parsed_grid_size.get("height")
        if browser_topology is not None:
            browser_width = browser_topology.get("width")
            browser_height = browser_topology.get("height")
            if browser_width is not None and parsed_width is not None and browser_width != parsed_width:
                warnings.append(
                    f"Grid summary width {parsed_width} does not match browser topology width {browser_width}."
                )
            if browser_height is not None and parsed_height is not None and browser_height != parsed_height:
                warnings.append(
                    f"Grid summary height {parsed_height} does not match browser topology height {browser_height}."
                )
        if backend_topology is not None:
            backend_width = backend_topology.get("width")
            backend_height = backend_topology.get("height")
            if backend_width is not None and parsed_width is not None and backend_width != parsed_width:
                warnings.append(
                    f"Grid summary width {parsed_width} does not match backend topology width {backend_width}."
                )
            if backend_height is not None and parsed_height is not None and backend_height != parsed_height:
                warnings.append(
                    f"Grid summary height {parsed_height} does not match backend topology height {backend_height}."
                )

    return {
        "requested": requested,
        "actualControlValues": {
            "patchDepth": actual_patch_depth,
            "cellSize": actual_cell_size,
        },
        "backendTopology": backend_topology,
        "browserState": browser_topology,
        "dom": dom_summary,
        "parsedGridSummary": parsed_grid_size,
        "warnings": warnings,
    }


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


def _contain_on_panel(
    image: Image.Image,
    *,
    panel_width: int,
    panel_height: int,
) -> tuple[Image.Image, dict[str, int]]:
    contained = ImageOps.contain(image, (panel_width, panel_height))
    panel = Image.new("RGBA", (panel_width, panel_height), (242, 242, 242, 255))
    offset_x = (panel_width - contained.width) // 2
    offset_y = (panel_height - contained.height) // 2
    panel.paste(contained, (offset_x, offset_y))
    return panel, {
        "width": contained.width,
        "height": contained.height,
        "offsetX": offset_x,
        "offsetY": offset_y,
    }


def build_reference_montage(
    rendered_path: Path,
    reference_path: Path,
    montage_path: Path,
) -> dict[str, Any]:
    montage_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(rendered_path) as rendered_image, Image.open(reference_path) as reference_image:
        rendered = rendered_image.convert("RGBA")
        reference = reference_image.convert("RGBA")
        panel_width = max(rendered.width, reference.width)
        panel_height = max(rendered.height, reference.height)
        rendered_panel, rendered_fit = _contain_on_panel(
            rendered,
            panel_width=panel_width,
            panel_height=panel_height,
        )
        reference_panel, reference_fit = _contain_on_panel(
            reference,
            panel_width=panel_width,
            panel_height=panel_height,
        )
        montage = Image.new(
            "RGBA",
            (panel_width * 2, panel_height),
            (230, 230, 230, 255),
        )
        montage.paste(rendered_panel, (0, 0))
        montage.paste(reference_panel, (panel_width, 0))
        montage.save(montage_path)
        return {
            "montageImagePath": str(montage_path),
            "normalizationMode": "contain",
            "panelWidth": panel_width,
            "panelHeight": panel_height,
            "outputImagePath": str(rendered_path),
            "outputImageWidth": rendered.width,
            "outputImageHeight": rendered.height,
            "outputImageFittedWidth": rendered_fit["width"],
            "outputImageFittedHeight": rendered_fit["height"],
            "outputImageOffsetX": rendered_fit["offsetX"],
            "outputImageOffsetY": rendered_fit["offsetY"],
            "referenceImagePath": str(reference_path),
            "referenceImageWidth": reference.width,
            "referenceImageHeight": reference.height,
            "referenceImageFittedWidth": reference_fit["width"],
            "referenceImageFittedHeight": reference_fit["height"],
            "referenceImageOffsetX": reference_fit["offsetX"],
            "referenceImageOffsetY": reference_fit["offsetY"],
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
    runtime_provenance = None
    provenance_warnings: tuple[str, ...] = ()
    settle_diagnostics: dict[str, Any] | None = None
    try:
        active_host.start()
        runtime_provenance = active_host.runtime_provenance()
        provenance_warnings = tuple(
            str(warning)
            for warning in runtime_provenance.get("warnings", [])
        ) if isinstance(runtime_provenance, dict) else ()
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
                    settle_diagnostics = wait_for_patch_render_complete(page)

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
                    browser_topology = browser_topology_summary(page)
                    transform_report = browser_transform_report(page)
                    raw_overlap_hotspots = browser_overlap_hotspots(page)
                    overlap_hotspots = build_overlap_hotspots_summary(
                        family=request.family,
                        profile=request.profile,
                        overlap_hotspots=raw_overlap_hotspots,
                    )
                    backend_topology = None
                    client = active_host.client()
                    if client is not None:
                        backend_topology = extract_backend_topology_facts(client.get_topology())
                    consistency_report = build_consistency_report(
                        request=request,
                        host_kind=host_kind,
                        actual_patch_depth=actual_patch_depth,
                        actual_cell_size=actual_cell_size,
                        grid_size_text=str(visual_summary["gridSizeText"]),
                        generation_text=str(visual_summary["generationText"]),
                        backend_topology=backend_topology,
                        browser_topology=browser_topology,
                    )
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
                        "transformReport": transform_report,
                        "overlapHotspots": overlap_hotspots,
                        "runtimeProvenance": runtime_provenance,
                        "provenanceWarnings": list(provenance_warnings),
                        "settleDiagnostics": settle_diagnostics,
                        "consistency": consistency_report,
                    }
                    comparison_payload = None
                    if request.reference is not None and montage_path is not None:
                        comparison_payload = build_reference_montage(
                            png_path,
                            request.reference,
                            montage_path,
                        )
                        summary_payload["comparison"] = comparison_payload
                    summary_payload["literatureReview"] = build_literature_review_summary(
                        literature_reference=request.literature_reference,
                        comparison=comparison_payload,
                    )
                    summary_path.write_text(
                        json.dumps(summary_payload, indent=2, sort_keys=True),
                        encoding="utf-8",
                    )
                    return RenderCanvasReviewResult(
                        png_path=png_path,
                        summary_path=summary_path,
                        montage_path=montage_path,
                        consistency_warnings=tuple(str(warning) for warning in consistency_report["warnings"]),
                        provenance_warnings=provenance_warnings,
                        literature_warnings=request.literature_reference.warnings,
                        literature_reference_status=request.literature_reference.reference_status,
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
                "runtimeProvenance": runtime_provenance,
                "provenanceWarnings": list(provenance_warnings),
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
    if parsed_args.list_profiles:
        for profile in iter_render_review_profiles():
            print(describe_render_review_profile(profile))
        return 0
    result = render_canvas_review(parsed_args)
    print(f"render_png={result.png_path}")
    print(f"render_summary={result.summary_path}")
    if result.montage_path is not None:
        print(f"render_montage={result.montage_path}")
    if result.literature_reference_status is not None:
        print(f"literature_reference_status={result.literature_reference_status}")
    if result.literature_warnings:
        print(f"literature_warnings={len(result.literature_warnings)}")
        for warning in result.literature_warnings:
            print(f"literature_warning={warning}")
    if result.consistency_warnings:
        print(f"consistency_warnings={len(result.consistency_warnings)}")
        for warning in result.consistency_warnings:
            print(f"consistency_warning={warning}")
    if result.provenance_warnings:
        print(f"provenance_warnings={len(result.provenance_warnings)}")
        for warning in result.provenance_warnings:
            print(f"provenance_warning={warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
