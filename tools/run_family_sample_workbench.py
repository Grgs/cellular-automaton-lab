from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import datetime as dt
from hashlib import sha1
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.simulation.aperiodic_shield import (
    build_shield_patch_for_window_threshold,
)
from backend.simulation.reference_verification.observation import observe_topology
from backend.simulation.topology import build_topology
from backend.simulation.topology_catalog import geometry_uses_patch_depth
from backend.simulation.topology_specialized import topology_from_aperiodic_patch
from backend.simulation.topology_types import LatticeTopology
from backend.simulation.topology_validation import validate_topology
from tools.workbench_support import (
    VALID_HOSTS,
    VALID_THEMES,
    build_candidate_manifest_record,
    format_candidate_metric_line,
    resolve_default_workbench_artifact_dir,
    run_candidate_browser_review,
    write_json,
)

DEFAULT_WORKBENCH_OUTPUT_DIR = ROOT_DIR / "output" / "family-sample-workbench"
DEFAULT_SHIELD_WINDOW_MULTIPLIERS = (0.90, 0.95, 1.00, 1.05, 1.10)
DEFAULT_VALIDATION_OVERLAP_PREVIEW = 12


@dataclass(frozen=True)
class ResolvedWorkbenchRequest:
    family: str
    patch_depth: int
    strategy: str
    values: tuple[float, ...] | None
    browser_review: bool
    host: str
    theme: str
    artifact_dir: Path


@dataclass(frozen=True)
class WorkbenchCandidate:
    index: int
    name: str
    strategy: str
    parameter_name: str | None
    parameter_value: float | None
    topology: LatticeTopology
    artifact_dir: Path


@dataclass(frozen=True)
class WorkbenchResult:
    artifact_dir: Path
    manifest_path: Path
    candidate_count: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explore candidate representative samples for patch-depth topology families.",
    )
    parser.add_argument("--family", required=True, help="Patch-depth topology family to explore.")
    parser.add_argument("--patch-depth", required=True, type=int, help="Patch depth to explore.")
    parser.add_argument("--strategy", help="Candidate generation strategy.")
    parser.add_argument("--values", help="Comma-separated candidate values for the selected strategy.")
    parser.add_argument(
        "--browser-review",
        action="store_true",
        help="Run browser-backed render review for each candidate topology.",
    )
    parser.add_argument("--host", choices=VALID_HOSTS, default="standalone")
    parser.add_argument("--theme", choices=VALID_THEMES, default="light")
    parser.add_argument("--artifact-dir", type=Path, help="Optional root artifact directory.")
    return parser


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def _parser_error(parser: argparse.ArgumentParser, message: str) -> None:
    parser.error(message)


def _resolve_default_strategy(family: str) -> str:
    if family == "shield":
        return "representative-window"
    return "baseline"


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


def default_shield_window_values(*, patch_depth: int) -> tuple[float, ...]:
    baseline_threshold = (
        json.loads((ROOT_DIR / "backend" / "simulation" / "data" / "shield_reference_patch.json").read_text(encoding="utf-8"))
        ["representative_window_thresholds"][str(max(0, int(patch_depth)))]
    )
    return tuple(round(float(baseline_threshold) * multiplier, 6) for multiplier in DEFAULT_SHIELD_WINDOW_MULTIPLIERS)


def resolve_workbench_request(args: argparse.Namespace) -> ResolvedWorkbenchRequest:
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

    strategy = str(args.strategy or _resolve_default_strategy(family))
    try:
        values = _parse_float_values(args.values, value_name="--values")
    except ValueError as exc:
        _parser_error(parser, str(exc))

    if strategy == "baseline":
        if values is not None:
            _parser_error(parser, "--values is not supported for the baseline strategy.")
        resolved_values = None
    elif strategy == "representative-window":
        if family != "shield":
            _parser_error(parser, "representative-window is supported only for 'shield' in v1.")
        resolved_values = values or default_shield_window_values(patch_depth=int(args.patch_depth))
        if any(value <= 0 for value in resolved_values):
            _parser_error(parser, "--values must contain positive threshold values.")
    else:
        _parser_error(parser, f"Unsupported strategy {strategy!r}.")

    return ResolvedWorkbenchRequest(
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


def candidate_dir_name(candidate: WorkbenchCandidate) -> str:
    return candidate.name


def _candidate_topology_revision(
    *,
    family: str,
    patch_depth: int,
    strategy: str,
    parameter_name: str | None,
    parameter_value: float | None,
    topology: LatticeTopology,
) -> str:
    digest = sha1(
        json.dumps(
            {
                "family": family,
                "patchDepth": patch_depth,
                "strategy": strategy,
                "parameterName": parameter_name,
                "parameterValue": round(parameter_value, 6) if parameter_value is not None else None,
                "width": topology.width,
                "height": topology.height,
                "cellIds": [cell.id for cell in topology.cells],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return digest[:12]


def _topology_with_revision(topology: LatticeTopology, *, topology_revision: str) -> LatticeTopology:
    return LatticeTopology(
        geometry=topology.geometry,
        width=topology.width,
        height=topology.height,
        cells=topology.cells,
        topology_revision=topology_revision,
        patch_depth=topology.patch_depth,
    )


def _build_baseline_candidate(
    *,
    family: str,
    patch_depth: int,
) -> LatticeTopology:
    return build_topology(family, 0, 0, patch_depth)


def _build_shield_window_candidate(
    *,
    patch_depth: int,
    window_threshold: float,
) -> LatticeTopology:
    patch = build_shield_patch_for_window_threshold(
        patch_depth,
        window_threshold=window_threshold,
    )
    return topology_from_aperiodic_patch("shield", patch)


def expand_candidates(request: ResolvedWorkbenchRequest) -> tuple[WorkbenchCandidate, ...]:
    candidates: list[WorkbenchCandidate] = []
    if request.strategy == "baseline":
        topology = _build_baseline_candidate(
            family=request.family,
            patch_depth=request.patch_depth,
        )
        candidates.append(
            WorkbenchCandidate(
                index=1,
                name="001-baseline",
                strategy=request.strategy,
                parameter_name=None,
                parameter_value=None,
                topology=topology,
                artifact_dir=request.artifact_dir / "001-baseline",
            )
        )
        return tuple(candidates)

    assert request.strategy == "representative-window"
    assert request.values is not None
    for index, threshold in enumerate(request.values, start=1):
        topology = _build_shield_window_candidate(
            patch_depth=request.patch_depth,
            window_threshold=threshold,
        )
        topology = _topology_with_revision(
            topology,
            topology_revision=_candidate_topology_revision(
                family=request.family,
                patch_depth=request.patch_depth,
                strategy=request.strategy,
                parameter_name="window_threshold",
                parameter_value=threshold,
                topology=topology,
            ),
        )
        candidates.append(
            WorkbenchCandidate(
                index=index,
                name=f"{index:03d}-threshold-{threshold:.6f}",
                strategy=request.strategy,
                parameter_name="window_threshold",
                parameter_value=threshold,
                topology=topology,
                artifact_dir=request.artifact_dir / f"{index:03d}-threshold-{threshold:.6f}",
            )
        )
    return tuple(candidates)


def build_structural_summary(
    *,
    candidate: WorkbenchCandidate,
    request: ResolvedWorkbenchRequest,
) -> dict[str, Any]:
    observation = observe_topology(
        geometry=request.family,
        sample_mode="candidate_workbench",
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
    graph_component_count = (
        0
        if validation.checked_cell_count == 0
        else 1 + len(validation.disconnected_components)
    )
    return {
        "family": request.family,
        "patchDepth": request.patch_depth,
        "strategy": candidate.strategy,
        "parameterName": candidate.parameter_name,
        "parameterValue": candidate.parameter_value,
        **asdict(observation),
        "validation": {
            "overlapPairCount": len(validation.overlapping_pairs),
            "overlapPairPreview": [list(pair) for pair in validation.overlapping_pairs[:DEFAULT_VALIDATION_OVERLAP_PREVIEW]],
            "polygonIssueCount": len(validation.polygon_issues),
            "graphComponentCount": graph_component_count,
            "edgeMultiplicityIssueCount": len(validation.edge_multiplicity_issues),
            "surfaceComponentCount": validation.surface_component_count,
            "holeCount": validation.hole_count,
            "isValid": validation.is_valid,
        },
    }


def run_family_sample_workbench(
    request: ResolvedWorkbenchRequest,
) -> WorkbenchResult:
    candidates = expand_candidates(request)
    manifest_path = request.artifact_dir / "workbench-manifest.json"
    manifest: dict[str, Any] = {
        "family": request.family,
        "patchDepth": request.patch_depth,
        "strategy": request.strategy,
        "requestedValues": list(request.values) if request.values is not None else None,
        "browserReview": request.browser_review,
        "host": request.host if request.browser_review else None,
        "theme": request.theme if request.browser_review else None,
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
            structural_summary = build_structural_summary(candidate=candidate, request=request)
            candidate_summary_payload = dict(structural_summary)
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
                        "totalCells": structural_summary["total_cells"],
                        "connectedComponentCount": structural_summary["connected_component_count"],
                        "holeCount": structural_summary["hole_count"],
                        "overlapPairCount": structural_summary["validation"]["overlapPairCount"],
                        "boundsAspectRatio": structural_summary["bounds_aspect_ratio"],
                        "signature": structural_summary["signature"],
                    },
                    browser_review_summary=browser_review_summary,
                )
            )
        exit_status = "success"
        return WorkbenchResult(
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
    print(
        format_candidate_metric_line(
            candidate_record["name"],
            metrics={
                "cells": candidate_record["totalCells"],
                "components": candidate_record["connectedComponentCount"],
                "holes": candidate_record["holeCount"],
                "overlaps": candidate_record["overlapPairCount"],
                "aspect": candidate_record["boundsAspectRatio"],
            },
        )
    )


def main(argv: list[str] | None = None) -> int:
    request = resolve_workbench_request(parse_cli_args(argv))
    result = run_family_sample_workbench(request)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    print(f"workbench_artifact_dir={result.artifact_dir}")
    print(f"workbench_manifest={result.manifest_path}")
    print(f"workbench_candidates={result.candidate_count}")
    for candidate_record in manifest["candidates"]:
        _print_candidate_line(candidate_record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
