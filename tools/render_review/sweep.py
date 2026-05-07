from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.render_review.browser_support.artifacts import create_artifact_dir
from tools.render_review.review import (
    DEFAULT_REFERENCE_CACHE_DIR,
    ResolvedRenderReviewRequest,
    condense_profile_expectations,
    condense_settle_diagnostics,
    condense_overlap_hotspots,
    condense_transform_report,
    condense_visual_metrics,
    resolve_render_review_request,
)
from tools.render_review.profiles import RenderReviewProfile, resolve_render_review_profile
from tools.render_review.browser_check import ManagedRenderReviewRun, run_managed_render_review

DEFAULT_SWEEP_OUTPUT_DIR = ROOT_DIR / "output" / "render-review-sweeps"
VALID_HOSTS = ("standalone", "server")
VALID_THEMES = ("light", "dark")


@dataclass(frozen=True)
class ResolvedRenderReviewSweepRequest:
    profile: RenderReviewProfile
    hosts: tuple[str, ...]
    themes: tuple[str, ...]
    patch_depths: tuple[int, ...] | None
    cell_sizes: tuple[int, ...] | None
    literature_review: bool
    reference: Path | None
    reference_cache_dir: Path
    artifact_dir: Path
    allow_stale_standalone: bool


@dataclass(frozen=True)
class RenderReviewSweepCase:
    index: int
    host: str
    theme: str
    patch_depth: int | None
    cell_size: int | None
    name: str
    artifact_dir: Path


@dataclass(frozen=True)
class RenderReviewSweepResult:
    artifact_dir: Path
    manifest_path: Path
    case_count: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a small matrix of managed render-review cases and write a combined sweep manifest.",
    )
    parser.add_argument("--profile", required=True, help="Named render-review profile to sweep.")
    parser.add_argument("--hosts", help="Comma-separated host kinds. Default: standalone.")
    parser.add_argument("--themes", help="Comma-separated themes. Default: profile theme.")
    parser.add_argument(
        "--patch-depths", help="Comma-separated patch depths for patch-depth profiles."
    )
    parser.add_argument("--cell-sizes", help="Comma-separated cell sizes for cell-size profiles.")
    parser.add_argument(
        "--reference", type=Path, help="Optional reference image path to pass to every case."
    )
    parser.add_argument(
        "--literature-review",
        action="store_true",
        help="Resolve profile-owned literature references from the local cache when explicit --reference is not provided.",
    )
    parser.add_argument(
        "--reference-cache-dir", type=Path, help="Optional literature reference cache directory."
    )
    parser.add_argument(
        "--artifact-dir", type=Path, help="Optional root artifact directory for the sweep."
    )
    parser.add_argument(
        "--allow-stale-standalone",
        action="store_true",
        help="Skip the standalone build freshness preflight for intentional stale-bundle diagnosis.",
    )
    return parser


def _parser_error(parser: argparse.ArgumentParser, message: str) -> None:
    parser.error(message)


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def _parse_csv_values(raw: str | None, *, value_name: str) -> tuple[str, ...] | None:
    if raw is None:
        return None
    values = tuple(part.strip() for part in str(raw).split(",") if part.strip())
    if not values:
        raise ValueError(f"{value_name} must contain at least one value.")
    return values


def _parse_csv_int_values(raw: str | None, *, value_name: str) -> tuple[int, ...] | None:
    values = _parse_csv_values(raw, value_name=value_name)
    if values is None:
        return None
    parsed_values: list[int] = []
    for value in values:
        try:
            parsed_value = int(value)
        except ValueError as exc:
            raise ValueError(f"{value_name} must contain integers: {value!r}") from exc
        parsed_values.append(parsed_value)
    return tuple(parsed_values)


def resolve_default_sweep_artifact_dir(
    *,
    profile_name: str,
    artifact_dir: Path | None,
) -> Path:
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir
    timestamp = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    return create_artifact_dir(
        name=f"{timestamp}-{profile_name}",
        default_parent=DEFAULT_SWEEP_OUTPUT_DIR,
    )


def resolve_sweep_request(args: argparse.Namespace) -> ResolvedRenderReviewSweepRequest:
    parser = build_parser()
    try:
        profile = resolve_render_review_profile(str(args.profile))
    except ValueError as exc:
        _parser_error(parser, str(exc))
    hosts = _parse_csv_values(args.hosts, value_name="--hosts") or ("standalone",)
    invalid_hosts = [host for host in hosts if host not in VALID_HOSTS]
    if invalid_hosts:
        _parser_error(parser, f"--hosts contains unsupported values: {', '.join(invalid_hosts)}")
    themes = _parse_csv_values(args.themes, value_name="--themes") or (str(profile.theme),)
    invalid_themes = [theme for theme in themes if theme not in VALID_THEMES]
    if invalid_themes:
        _parser_error(parser, f"--themes contains unsupported values: {', '.join(invalid_themes)}")
    if args.reference is not None and not args.reference.exists():
        _parser_error(parser, f"reference image does not exist: {args.reference}")

    patch_depths = _parse_csv_int_values(args.patch_depths, value_name="--patch-depths")
    cell_sizes = _parse_csv_int_values(args.cell_sizes, value_name="--cell-sizes")
    if profile.patch_depth is not None:
        if cell_sizes is not None:
            _parser_error(
                parser, "--cell-sizes is not valid for patch-depth render-review profiles."
            )
        resolved_patch_depths = patch_depths or (int(profile.patch_depth),)
        if any(value < 0 for value in resolved_patch_depths):
            _parser_error(parser, "--patch-depths must be non-negative.")
        resolved_cell_sizes = None
    elif profile.cell_size is not None:
        if patch_depths is not None:
            _parser_error(
                parser, "--patch-depths is not valid for cell-size render-review profiles."
            )
        resolved_cell_sizes = cell_sizes or (int(profile.cell_size),)
        if any(value <= 0 for value in resolved_cell_sizes):
            _parser_error(parser, "--cell-sizes must be positive.")
        resolved_patch_depths = None
    else:
        _parser_error(
            parser,
            f"Render-review profile {profile.name!r} does not declare a patch depth or cell size.",
        )

    return ResolvedRenderReviewSweepRequest(
        profile=profile,
        hosts=tuple(hosts),
        themes=tuple(themes),
        patch_depths=resolved_patch_depths,
        cell_sizes=resolved_cell_sizes,
        literature_review=bool(args.literature_review),
        reference=args.reference,
        reference_cache_dir=Path(args.reference_cache_dir)
        if args.reference_cache_dir is not None
        else DEFAULT_REFERENCE_CACHE_DIR,
        artifact_dir=resolve_default_sweep_artifact_dir(
            profile_name=profile.name,
            artifact_dir=args.artifact_dir,
        ),
        allow_stale_standalone=bool(args.allow_stale_standalone),
    )


def sweep_case_dir_name(
    *,
    index: int,
    host: str,
    theme: str,
    patch_depth: int | None,
    cell_size: int | None,
) -> str:
    sizing_fragment = f"depth-{patch_depth}" if patch_depth is not None else f"size-{cell_size}"
    return f"{index:03d}-host-{host}-theme-{theme}-{sizing_fragment}"


def expand_sweep_cases(
    request: ResolvedRenderReviewSweepRequest,
) -> tuple[RenderReviewSweepCase, ...]:
    cases: list[RenderReviewSweepCase] = []
    sizing_values = request.patch_depths if request.patch_depths is not None else request.cell_sizes
    assert sizing_values is not None
    index = 1
    for host in request.hosts:
        for theme in request.themes:
            for value in sizing_values:
                patch_depth = value if request.patch_depths is not None else None
                cell_size = value if request.cell_sizes is not None else None
                name = sweep_case_dir_name(
                    index=index,
                    host=host,
                    theme=theme,
                    patch_depth=patch_depth,
                    cell_size=cell_size,
                )
                cases.append(
                    RenderReviewSweepCase(
                        index=index,
                        host=host,
                        theme=theme,
                        patch_depth=patch_depth,
                        cell_size=cell_size,
                        name=name,
                        artifact_dir=request.artifact_dir / name,
                    )
                )
                index += 1
    return tuple(cases)


def _case_output_stem(*, family: str, patch_depth: int | None, cell_size: int | None) -> str:
    if patch_depth is not None:
        return f"{family}-depth-{patch_depth}"
    return f"{family}-size-{cell_size}"


def build_case_review_request(
    request: ResolvedRenderReviewSweepRequest,
    case: RenderReviewSweepCase,
) -> ResolvedRenderReviewRequest:
    output_stem = _case_output_stem(
        family=request.profile.family,
        patch_depth=case.patch_depth,
        cell_size=case.cell_size,
    )
    args = argparse.Namespace(
        family=request.profile.family,
        profile=request.profile.name,
        list_profiles=False,
        patch_depth=case.patch_depth,
        cell_size=case.cell_size,
        viewport_width=request.profile.viewport_width,
        viewport_height=request.profile.viewport_height,
        theme=case.theme,
        out=case.artifact_dir / f"{output_stem}.png",
        summary_out=case.artifact_dir / f"{output_stem}.json",
        reference=request.reference,
        montage_out=(
            case.artifact_dir / f"{output_stem}-montage.png"
            if request.reference is not None or request.literature_review
            else None
        ),
        literature_review=request.literature_review,
        reference_cache_dir=request.reference_cache_dir,
    )
    return resolve_render_review_request(args)


def extract_sweep_case_metrics(summary_payload: dict[str, Any]) -> dict[str, Any]:
    consistency = summary_payload.get("consistency")
    browser_state = consistency.get("browserState") if isinstance(consistency, dict) else None
    backend_topology = consistency.get("backendTopology") if isinstance(consistency, dict) else None
    return {
        "gridSizeText": summary_payload.get("gridSizeText"),
        "generationText": summary_payload.get("generationText"),
        "coverageWidthRatio": summary_payload.get("coverageWidthRatio"),
        "coverageHeightRatio": summary_payload.get("coverageHeightRatio"),
        "renderCellSize": summary_payload.get("renderCellSize"),
        "browserTopologyCellCount": (
            browser_state.get("topologyCellCount") if isinstance(browser_state, dict) else None
        ),
        "backendTopologyCellCount": (
            backend_topology.get("topologyCellCount")
            if isinstance(backend_topology, dict)
            else None
        ),
    }


def write_sweep_manifest(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")
    return path


def _serialize_path(path: Path) -> str:
    return path.as_posix()


def build_sweep_case_record(
    *,
    case: RenderReviewSweepCase,
    run: ManagedRenderReviewRun,
) -> dict[str, Any]:
    summary_payload = json.loads(run.render_summary_path.read_text(encoding="utf-8"))
    literature_review = summary_payload.get("literatureReview")
    return {
        "index": case.index,
        "name": case.name,
        "host": case.host,
        "theme": case.theme,
        "patchDepth": case.patch_depth,
        "cellSize": case.cell_size,
        "artifactDir": _serialize_path(case.artifact_dir),
        "runManifest": _serialize_path(run.run_manifest_path),
        "renderPng": _serialize_path(run.render_png_path),
        "renderSummary": _serialize_path(run.render_summary_path),
        "renderMontage": _serialize_path(run.render_montage_path)
        if run.render_montage_path is not None
        else None,
        "consistencyWarnings": list(run.consistency_warnings),
        "provenanceWarnings": summary_payload.get("provenanceWarnings", []),
        "diagnosticErrors": summary_payload.get("diagnosticErrors", []),
        "runtimeProvenance": summary_payload.get("runtimeProvenance"),
        "settleDiagnostics": condense_settle_diagnostics(summary_payload.get("settleDiagnostics")),
        "transformSummary": condense_transform_report(summary_payload.get("transformReport")),
        "overlapHotspots": condense_overlap_hotspots(summary_payload.get("overlapHotspots")),
        "visualMetrics": condense_visual_metrics(summary_payload.get("visualMetrics")),
        "profileExpectations": condense_profile_expectations(
            summary_payload.get("profileExpectations")
        ),
        "literatureReview": (
            {
                "requested": literature_review.get("requested"),
                "citationLabel": literature_review.get("citationLabel"),
                "referenceImageStatus": literature_review.get("referenceImageStatus"),
                "referenceImagePath": literature_review.get("referenceImagePath"),
                "referenceCachePath": literature_review.get("referenceCachePath"),
                "warnings": literature_review.get("warnings"),
            }
            if isinstance(literature_review, dict)
            else None
        ),
        "metrics": extract_sweep_case_metrics(summary_payload),
    }


def run_render_review_sweep(
    request: ResolvedRenderReviewSweepRequest,
) -> RenderReviewSweepResult:
    cases = expand_sweep_cases(request)
    manifest_path = request.artifact_dir / "sweep-manifest.json"
    manifest: dict[str, Any] = {
        "profile": request.profile.name,
        "family": request.profile.family,
        "requestedMatrix": {
            "hosts": list(request.hosts),
            "themes": list(request.themes),
            "patchDepths": list(request.patch_depths) if request.patch_depths is not None else None,
            "cellSizes": list(request.cell_sizes) if request.cell_sizes is not None else None,
            "literatureReview": request.literature_review,
            "reference": _serialize_path(request.reference)
            if request.reference is not None
            else None,
            "referenceCacheDir": _serialize_path(request.reference_cache_dir),
            "allowStaleStandalone": request.allow_stale_standalone,
        },
        "startedAt": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "cases": [],
    }
    exit_status = "failure"
    try:
        for case in cases:
            case_review_request = build_case_review_request(request, case)
            run = run_managed_render_review(
                host_kind=case.host,
                review_args=case_review_request,
                artifact_dir=case.artifact_dir,
                allow_stale_standalone=request.allow_stale_standalone,
            )
            manifest["cases"].append(build_sweep_case_record(case=case, run=run))
        exit_status = "success"
        return RenderReviewSweepResult(
            artifact_dir=request.artifact_dir,
            manifest_path=manifest_path,
            case_count=len(cases),
        )
    except Exception as exc:
        manifest["failureReason"] = str(exc)
        raise
    finally:
        manifest["exitStatus"] = exit_status
        manifest["stoppedAt"] = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        write_sweep_manifest(manifest_path, manifest)


def main(argv: list[str] | None = None) -> int:
    parsed_args = parse_cli_args(argv)
    request = resolve_sweep_request(parsed_args)
    try:
        result = run_render_review_sweep(request)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"sweep_artifact_dir={result.artifact_dir}")
    print(f"sweep_manifest={result.manifest_path}")
    print(f"sweep_cases={result.case_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
