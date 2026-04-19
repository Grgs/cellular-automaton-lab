from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import datetime as dt
from hashlib import sha1
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.simulation.aperiodic_shield import (
    build_shield_patch_for_cleanup_scale,
    default_shield_trace_geometry_cleanup_scale,
)
from backend.simulation.reference_verification.observation import observe_topology
from backend.simulation.topology_catalog import geometry_uses_patch_depth
from backend.simulation.topology_specialized import topology_from_aperiodic_patch
from backend.simulation.topology_types import LatticeTopology
from backend.simulation.topology_validation import (
    analyze_topology_overlap_areas,
    validate_topology,
)
from tools.render_review.workbench_support import (
    VALID_HOSTS,
    VALID_THEMES,
    build_candidate_manifest_record,
    format_candidate_metric_line,
    resolve_default_workbench_artifact_dir,
    run_candidate_browser_review,
    write_json,
)

DEFAULT_WORKBENCH_OUTPUT_DIR = ROOT_DIR / "output" / "geometry-cleanup-workbench"
DEFAULT_SHIELD_CLEANUP_OFFSETS = (-0.02, -0.01, 0.0, 0.01, 0.02)
DEFAULT_OVERLAP_PAIR_PREVIEW = 10
LARGE_BOUNDS_DRIFT_RATIO_DELTA = 0.03
LARGE_BOUNDS_ASPECT_DELTA = 0.03


@dataclass(frozen=True)
class ResolvedCleanupWorkbenchRequest:
    family: str
    patch_depth: int
    strategy: str
    values: tuple[float, ...] | None
    browser_review: bool
    host: str
    theme: str
    artifact_dir: Path


@dataclass(frozen=True)
class CleanupWorkbenchCandidate:
    index: int
    name: str
    strategy: str
    parameter_name: str
    parameter_value: float
    topology: LatticeTopology
    artifact_dir: Path
    is_baseline: bool


@dataclass(frozen=True)
class CleanupWorkbenchResult:
    artifact_dir: Path
    manifest_path: Path
    candidate_count: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explore topology cleanup factors for image-derived patch-depth topology families.",
    )
    parser.add_argument("--family", required=True, help="Patch-depth topology family to explore.")
    parser.add_argument("--patch-depth", required=True, type=int, help="Patch depth to explore.")
    parser.add_argument("--strategy", help="Cleanup strategy.")
    parser.add_argument("--values", help="Comma-separated raw cleanup scales.")
    parser.add_argument(
        "--browser-review",
        action="store_true",
        help="Run browser-backed render review for each cleanup candidate.",
    )
    parser.add_argument("--host", choices=VALID_HOSTS, default="standalone")
    parser.add_argument("--theme", choices=VALID_THEMES, default="light")
    parser.add_argument("--artifact-dir", type=Path, help="Optional root artifact directory.")
    return parser


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def _parser_error(parser: argparse.ArgumentParser, message: str) -> None:
    parser.error(message)


def _parse_float_values(raw: str | None, *, value_name: str) -> tuple[float, ...] | None:
    if raw is None:
        return None
    values = tuple(part.strip() for part in str(raw).split(",") if part.strip())
    if not values:
        raise ValueError(f"{value_name} must contain at least one value.")
    parsed: list[float] = []
    for value in values:
        try:
            parsed_value = float(value)
        except ValueError as exc:
            raise ValueError(f"{value_name} must contain numeric values: {value!r}") from exc
        parsed.append(parsed_value)
    return tuple(parsed)


def _normalize_cleanup_scale(scale: float) -> float:
    return round(min(1.0, max(scale, 1e-6)), 6)


def default_shield_cleanup_scales() -> tuple[float, ...]:
    baseline_scale = default_shield_trace_geometry_cleanup_scale()
    normalized = {
        _normalize_cleanup_scale(baseline_scale + offset)
        for offset in DEFAULT_SHIELD_CLEANUP_OFFSETS
    }
    normalized.add(_normalize_cleanup_scale(baseline_scale))
    return tuple(sorted(normalized))


def resolve_cleanup_workbench_request(args: argparse.Namespace) -> ResolvedCleanupWorkbenchRequest:
    parser = build_parser()
    family = str(args.family)
    try:
        uses_patch_depth = geometry_uses_patch_depth(family)
    except KeyError:
        _parser_error(parser, f"Unsupported topology family {family!r}.")
    if not uses_patch_depth:
        _parser_error(parser, f"Topology family {family!r} does not use patch depth.")
    if int(args.patch_depth) < 0:
        _parser_error(parser, "--patch-depth must be non-negative.")

    strategy = str(args.strategy or "trace-cleanup-scale")
    if strategy != "trace-cleanup-scale":
        _parser_error(parser, f"Unsupported strategy {strategy!r}.")
    if family != "shield":
        _parser_error(parser, "trace-cleanup-scale is supported only for 'shield' in v1.")

    try:
        parsed_values = _parse_float_values(args.values, value_name="--values")
    except ValueError as exc:
        _parser_error(parser, str(exc))

    baseline_scale = _normalize_cleanup_scale(default_shield_trace_geometry_cleanup_scale())
    if parsed_values is None:
        resolved_values = default_shield_cleanup_scales()
    else:
        normalized_values: set[float] = {baseline_scale}
        for value in parsed_values:
            if value <= 0 or value > 1:
                _parser_error(
                    parser, "--values must contain cleanup scales in the interval (0, 1]."
                )
            normalized_values.add(_normalize_cleanup_scale(value))
        resolved_values = tuple(sorted(normalized_values))

    return ResolvedCleanupWorkbenchRequest(
        family=family,
        patch_depth=int(args.patch_depth),
        strategy=strategy,
        values=resolved_values,
        browser_review=bool(args.browser_review),
        host=str(args.host),
        theme=str(args.theme),
        artifact_dir=resolve_default_workbench_artifact_dir(
            artifact_dir=args.artifact_dir,
            default_parent=DEFAULT_WORKBENCH_OUTPUT_DIR,
            name=f"{family}-depth-{int(args.patch_depth)}",
        ),
    )


def _candidate_topology_revision(
    *,
    family: str,
    patch_depth: int,
    strategy: str,
    cleanup_scale: float,
    topology: LatticeTopology,
) -> str:
    digest = sha1(
        json.dumps(
            {
                "family": family,
                "patchDepth": patch_depth,
                "strategy": strategy,
                "cleanupScale": round(cleanup_scale, 6),
                "width": topology.width,
                "height": topology.height,
                "cellIds": [cell.id for cell in topology.cells],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return digest[:12]


def _topology_with_revision(
    topology: LatticeTopology, *, topology_revision: str
) -> LatticeTopology:
    return LatticeTopology(
        geometry=topology.geometry,
        width=topology.width,
        height=topology.height,
        cells=topology.cells,
        topology_revision=topology_revision,
        patch_depth=topology.patch_depth,
    )


def expand_cleanup_candidates(
    request: ResolvedCleanupWorkbenchRequest,
) -> tuple[CleanupWorkbenchCandidate, ...]:
    assert request.values is not None
    baseline_scale = _normalize_cleanup_scale(default_shield_trace_geometry_cleanup_scale())
    candidates: list[CleanupWorkbenchCandidate] = []
    for index, cleanup_scale in enumerate(request.values, start=1):
        patch = build_shield_patch_for_cleanup_scale(
            request.patch_depth,
            cleanup_scale=cleanup_scale,
        )
        topology = topology_from_aperiodic_patch("shield", patch)
        topology = _topology_with_revision(
            topology,
            topology_revision=_candidate_topology_revision(
                family=request.family,
                patch_depth=request.patch_depth,
                strategy=request.strategy,
                cleanup_scale=cleanup_scale,
                topology=topology,
            ),
        )
        is_baseline = abs(cleanup_scale - baseline_scale) < 1e-9
        name = f"{index:03d}-scale-{cleanup_scale:.6f}"
        candidates.append(
            CleanupWorkbenchCandidate(
                index=index,
                name=name,
                strategy=request.strategy,
                parameter_name="cleanup_scale",
                parameter_value=cleanup_scale,
                topology=topology,
                artifact_dir=request.artifact_dir / name,
                is_baseline=is_baseline,
            )
        )
    return tuple(candidates)


def _graph_component_count(validation_result: Any) -> int:
    return (
        0
        if validation_result.checked_cell_count == 0
        else 1 + len(validation_result.disconnected_components)
    )


def _bounds_drift(
    *,
    baseline_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
) -> dict[str, float | None]:
    baseline_width = float(baseline_summary["bounds_width"])
    baseline_height = float(baseline_summary["bounds_height"])
    baseline_aspect = float(baseline_summary["bounds_aspect_ratio"])
    candidate_width = float(candidate_summary["bounds_width"])
    candidate_height = float(candidate_summary["bounds_height"])
    candidate_aspect = float(candidate_summary["bounds_aspect_ratio"])
    return {
        "widthRatio": (candidate_width / baseline_width) if baseline_width > 0 else None,
        "heightRatio": (candidate_height / baseline_height) if baseline_height > 0 else None,
        "aspectRatioDelta": candidate_aspect - baseline_aspect,
    }


def _visual_comparison_summary(
    browser_review_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    visual_metrics = (
        browser_review_summary.get("visualMetrics")
        if isinstance(browser_review_summary, dict)
        else None
    )
    if not isinstance(visual_metrics, dict):
        return {
            "gutterScore": None,
            "boundaryDominance": None,
            "visibleAspectRatio": None,
            "radialSymmetryScore": None,
        }
    return {
        "gutterScore": visual_metrics.get("gutterScore"),
        "boundaryDominance": visual_metrics.get("boundaryDominance"),
        "visibleAspectRatio": visual_metrics.get("visibleAspectRatio"),
        "radialSymmetryScore": visual_metrics.get("radialSymmetryScore"),
    }


def _cleanup_warnings(
    *,
    cleanup_scale: float,
    baseline_scale: float,
    overlap_pair_count: int,
    bounds_drift: dict[str, float | None],
    browser_review_summary: dict[str, Any] | None,
) -> list[str]:
    warnings: list[str] = []
    width_ratio = bounds_drift["widthRatio"]
    height_ratio = bounds_drift["heightRatio"]
    aspect_delta = bounds_drift["aspectRatioDelta"]
    if overlap_pair_count == 0 and (
        (width_ratio is not None and abs(width_ratio - 1.0) > LARGE_BOUNDS_DRIFT_RATIO_DELTA)
        or (height_ratio is not None and abs(height_ratio - 1.0) > LARGE_BOUNDS_DRIFT_RATIO_DELTA)
        or (aspect_delta is not None and abs(aspect_delta) > LARGE_BOUNDS_ASPECT_DELTA)
    ):
        warnings.append(
            "Cleanup removed overlap but introduced comparatively large bounds drift versus the shipped baseline."
        )
    if cleanup_scale > baseline_scale:
        warnings.append("Cleanup scale exceeds the current shipped baseline scale.")
    if browser_review_summary is None:
        warnings.append("Visible gutter risk is unavailable without browser review.")
    else:
        visual_metrics = browser_review_summary.get("visualMetrics")
        if not isinstance(visual_metrics, dict) or visual_metrics.get("gutterScore") is None:
            warnings.append(
                "Visible gutter risk could not be derived from the browser review metrics."
            )
    return warnings


def build_cleanup_structural_summary(
    *,
    candidate: CleanupWorkbenchCandidate,
    request: ResolvedCleanupWorkbenchRequest,
    baseline_summary: dict[str, Any],
    browser_review_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    observation = observe_topology(
        geometry=request.family,
        sample_mode="cleanup_workbench",
        depth=request.patch_depth,
        topology=candidate.topology,
    )
    validation = validate_topology(
        candidate.topology,
        check_surface=True,
        check_overlaps=True,
        check_edge_multiplicity=True,
        check_graph_connectivity=True,
    )
    overlap_diagnostics = analyze_topology_overlap_areas(
        candidate.topology,
        top_limit=DEFAULT_OVERLAP_PAIR_PREVIEW,
    )
    observation_summary = asdict(observation)
    bounds_drift = _bounds_drift(
        baseline_summary=baseline_summary,
        candidate_summary=observation_summary,
    )
    baseline_scale = _normalize_cleanup_scale(default_shield_trace_geometry_cleanup_scale())
    visual_comparison = _visual_comparison_summary(browser_review_summary)
    cleanup_diagnostics = {
        "isBaseline": candidate.is_baseline,
        "baselineCleanupScale": baseline_scale,
        "overlapPairCount": overlap_diagnostics.pair_count,
        "maxOverlapArea": overlap_diagnostics.max_area,
        "topOverlapPairs": [
            {
                "leftId": pair.left_id,
                "rightId": pair.right_id,
                "area": round(pair.area, 6),
            }
            for pair in overlap_diagnostics.top_pairs
        ],
        "boundsDrift": bounds_drift,
        "visualComparison": visual_comparison,
        "warnings": _cleanup_warnings(
            cleanup_scale=candidate.parameter_value,
            baseline_scale=baseline_scale,
            overlap_pair_count=overlap_diagnostics.pair_count,
            bounds_drift=bounds_drift,
            browser_review_summary=browser_review_summary,
        ),
    }
    return {
        "family": request.family,
        "patchDepth": request.patch_depth,
        "strategy": candidate.strategy,
        "parameterName": candidate.parameter_name,
        "parameterValue": candidate.parameter_value,
        **observation_summary,
        "validation": {
            "polygonIssueCount": len(validation.polygon_issues),
            "graphComponentCount": _graph_component_count(validation),
            "edgeMultiplicityIssueCount": len(validation.edge_multiplicity_issues),
            "surfaceComponentCount": validation.surface_component_count,
            "holeCount": validation.hole_count,
            "isValid": validation.is_valid,
        },
        "cleanupDiagnostics": cleanup_diagnostics,
    }


def run_geometry_cleanup_workbench(
    request: ResolvedCleanupWorkbenchRequest,
) -> CleanupWorkbenchResult:
    candidates = expand_cleanup_candidates(request)
    manifest_path = request.artifact_dir / "workbench-manifest.json"
    baseline_candidate = next(candidate for candidate in candidates if candidate.is_baseline)
    baseline_observation = asdict(
        observe_topology(
            geometry=request.family,
            sample_mode="cleanup_workbench_baseline",
            depth=request.patch_depth,
            topology=baseline_candidate.topology,
        )
    )
    manifest: dict[str, Any] = {
        "family": request.family,
        "patchDepth": request.patch_depth,
        "strategy": request.strategy,
        "requestedValues": list(request.values) if request.values is not None else None,
        "resolvedValues": [candidate.parameter_value for candidate in candidates],
        "browserReview": request.browser_review,
        "host": request.host if request.browser_review else None,
        "theme": request.theme if request.browser_review else None,
        "baselineCleanupScale": baseline_candidate.parameter_value,
        "startedAt": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "candidates": [],
    }
    exit_status = "failure"
    try:
        for candidate in candidates:
            candidate.artifact_dir.mkdir(parents=True, exist_ok=True)
            topology_path = write_json(
                candidate.artifact_dir / "candidate-topology.json",
                candidate.topology.to_dict(),
            )
            browser_review_summary: dict[str, Any] | None = None
            if request.browser_review:
                browser_review_summary = run_candidate_browser_review(
                    family=request.family,
                    patch_depth=request.patch_depth,
                    theme=request.theme,
                    host=request.host,
                    artifact_dir=candidate.artifact_dir,
                    topology_payload=candidate.topology.to_dict(),
                )
            structural_summary = build_cleanup_structural_summary(
                candidate=candidate,
                request=request,
                baseline_summary=baseline_observation,
                browser_review_summary=browser_review_summary,
            )
            candidate_summary_payload = dict(structural_summary)
            if browser_review_summary is not None:
                candidate_summary_payload["renderReview"] = browser_review_summary
            summary_path = write_json(
                candidate.artifact_dir / "candidate-summary.json",
                candidate_summary_payload,
            )
            manifest["candidates"].append(
                build_candidate_manifest_record(
                    index=candidate.index,
                    name=candidate.name,
                    strategy=candidate.strategy,
                    parameter_name=candidate.parameter_name,
                    parameter_value=candidate.parameter_value,
                    artifact_dir=candidate.artifact_dir,
                    topology_path=topology_path,
                    summary_path=summary_path,
                    key_metrics={
                        "isBaseline": candidate.is_baseline,
                        "totalCells": structural_summary["total_cells"],
                        "connectedComponentCount": structural_summary["connected_component_count"],
                        "holeCount": structural_summary["hole_count"],
                        "overlapPairCount": structural_summary["cleanupDiagnostics"][
                            "overlapPairCount"
                        ],
                        "maxOverlapArea": structural_summary["cleanupDiagnostics"][
                            "maxOverlapArea"
                        ],
                        "boundsAspectRatio": structural_summary["bounds_aspect_ratio"],
                        "boundsDrift": structural_summary["cleanupDiagnostics"]["boundsDrift"],
                        "signature": structural_summary["signature"],
                    },
                    browser_review_summary=browser_review_summary,
                )
            )
        exit_status = "success"
        return CleanupWorkbenchResult(
            artifact_dir=request.artifact_dir,
            manifest_path=manifest_path,
            candidate_count=len(candidates),
        )
    except Exception as exc:
        manifest["failureReason"] = str(exc)
        raise
    finally:
        manifest["exitStatus"] = exit_status
        manifest["stoppedAt"] = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        write_json(manifest_path, manifest)


def _print_candidate_line(candidate_record: dict[str, Any]) -> None:
    bounds_drift = candidate_record.get("boundsDrift") or {}
    render_review = candidate_record.get("renderReview") or {}
    visual_metrics = render_review.get("visualMetrics") if isinstance(render_review, dict) else None
    gutter_score = visual_metrics.get("gutterScore") if isinstance(visual_metrics, dict) else None
    print(
        format_candidate_metric_line(
            candidate_record["name"],
            metrics={
                "baseline": candidate_record.get("isBaseline"),
                "cells": candidate_record.get("totalCells"),
                "overlaps": candidate_record.get("overlapPairCount"),
                "maxArea": candidate_record.get("maxOverlapArea"),
                "widthRatio": bounds_drift.get("widthRatio"),
                "heightRatio": bounds_drift.get("heightRatio"),
                "gutter": gutter_score,
            },
        )
    )


def main(argv: list[str] | None = None) -> int:
    request = resolve_cleanup_workbench_request(parse_cli_args(argv))
    result = run_geometry_cleanup_workbench(request)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    print(f"workbench_artifact_dir={result.artifact_dir}")
    print(f"workbench_manifest={result.manifest_path}")
    print(f"workbench_candidates={result.candidate_count}")
    for candidate_record in manifest["candidates"]:
        _print_candidate_line(candidate_record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
