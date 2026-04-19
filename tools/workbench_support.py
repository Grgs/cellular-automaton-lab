from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tests.e2e.browser_support.artifacts import create_artifact_dir
from tools.render_canvas_review import (
    DEFAULT_REFERENCE_CACHE_DIR,
    condense_overlap_hotspots,
    condense_settle_diagnostics,
    condense_transform_report,
    condense_visual_metrics,
    render_canvas_review,
    resolve_render_review_request,
    with_review_topology_payload,
)

VALID_HOSTS = ("standalone", "server")
VALID_THEMES = ("light", "dark")


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")
    return path


def resolve_default_workbench_artifact_dir(
    *,
    artifact_dir: Path | None,
    default_parent: Path,
    name: str,
) -> Path:
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir
    timestamp = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    return create_artifact_dir(
        name=f"{timestamp}-{name}",
        default_parent=default_parent,
    )


def run_candidate_browser_review(
    *,
    family: str,
    patch_depth: int,
    theme: str,
    host: str,
    artifact_dir: Path,
    topology_payload: dict[str, Any],
) -> dict[str, Any]:
    stem = f"{family}-depth-{patch_depth}"
    resolved = resolve_render_review_request(
        argparse.Namespace(
            family=family,
            profile=None,
            list_profiles=False,
            patch_depth=patch_depth,
            cell_size=None,
            viewport_width=1200,
            viewport_height=900,
            theme=theme,
            out=artifact_dir / f"{stem}.png",
            summary_out=artifact_dir / f"{stem}.json",
            reference=None,
            montage_out=None,
            literature_review=False,
            reference_cache_dir=DEFAULT_REFERENCE_CACHE_DIR,
        )
    )
    review_request = with_review_topology_payload(resolved, topology_payload)
    review_result = render_canvas_review(
        review_request,
        host_kind=host,
        artifact_dir=artifact_dir,
    )
    review_payload = json.loads(review_result.summary_path.read_text(encoding="utf-8"))
    return {
        "summaryPath": str(review_result.summary_path),
        "pngPath": str(review_result.png_path),
        "runManifestPath": None,
        "consistency": review_payload.get("consistency"),
        "transformSummary": condense_transform_report(review_payload.get("transformReport")),
        "overlapHotspots": condense_overlap_hotspots(review_payload.get("overlapHotspots")),
        "settleDiagnostics": condense_settle_diagnostics(review_payload.get("settleDiagnostics")),
        "visualMetrics": condense_visual_metrics(review_payload.get("visualMetrics")),
    }


def build_candidate_manifest_record(
    *,
    index: int,
    name: str,
    strategy: str,
    parameter_name: str | None,
    parameter_value: float | None,
    artifact_dir: Path,
    topology_path: Path,
    summary_path: Path,
    key_metrics: dict[str, Any],
    browser_review_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    record = {
        "index": index,
        "name": name,
        "strategy": strategy,
        "parameterName": parameter_name,
        "parameterValue": parameter_value,
        "artifactDir": str(artifact_dir),
        "candidateTopology": str(topology_path),
        "candidateSummary": str(summary_path),
        **key_metrics,
    }
    if browser_review_summary is not None:
        record["renderReview"] = browser_review_summary
    return record


def _format_metric_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def format_candidate_metric_line(name: str, *, metrics: dict[str, Any]) -> str:
    metric_parts = [f"{key}={_format_metric_value(value)}" for key, value in metrics.items()]
    return f"{name}: {' '.join(metric_parts)}"
