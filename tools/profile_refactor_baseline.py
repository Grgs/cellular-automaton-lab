from __future__ import annotations

import argparse
import json
import statistics
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from backend.simulation.seeding import compare_seed, run_seed_filmstrip
from tests.e2e.support_server import AppServer
from tools import check_bundle_size
from tools._common import ROOT_DIR, write_text_lf
from tools.profile_tiling_latency import (
    CASES,
    benchmark_topology_build_ms,
    default_reset_payload,
    post_reset,
    post_toggle,
)

DEFAULT_BUNDLE_DIR = ROOT_DIR / "output" / "standalone"


def _json_bytes(payload: object) -> int:
    return len(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def _median_payload(callback: Callable[[], object], *, repeats: int) -> tuple[object, float]:
    timings: list[float] = []
    latest: object | None = None
    for _ in range(repeats):
        started_at = time.perf_counter()
        latest = callback()
        timings.append((time.perf_counter() - started_at) * 1000)
    if latest is None:
        raise RuntimeError("baseline callback did not produce a payload")
    return latest, statistics.median(timings)


def _bundle_baseline(bundle_dir: Path) -> dict[str, object]:
    if not bundle_dir.exists():
        return {"available": False, "build_dir": str(bundle_dir)}
    budget = check_bundle_size.load_budget(check_bundle_size.DEFAULT_BUDGET_PATH)
    sizes, uncategorised = check_bundle_size.measure(bundle_dir, budget)
    violations, total = check_bundle_size.evaluate(sizes, budget)
    return {
        "available": True,
        "build_dir": str(bundle_dir),
        "raw_bytes": total.raw_bytes,
        "gzip_bytes": total.gzip_bytes,
        "uncategorised": uncategorised,
        "violations": [
            {
                "category": violation.category,
                "metric": violation.metric,
                "actual": violation.actual,
                "budget": violation.budget,
            }
            for violation in violations
        ],
    }


def collect_baseline(*, repeats: int, bundle_dir: Path) -> dict[str, object]:
    topology_cases: list[dict[str, object]] = []
    server = AppServer()
    server.start()
    try:
        for geometry, rule, dimensions in CASES:
            width = int(dimensions["width"])
            height = int(dimensions["height"])
            reset_payload = default_reset_payload(geometry, rule, dimensions)
            reset_state, reset_bytes, reset_ms = post_reset(server.base_url, reset_payload)
            cells = reset_state["topology"]["cells"]
            if not cells:
                raise RuntimeError(f"{geometry} baseline topology did not contain cells")
            toggle_id = str(cells[0]["id"])
            _, toggle_bytes, toggle_ms = post_toggle(server.base_url, toggle_id)
            topology_cases.append(
                {
                    "geometry": geometry,
                    "width": width,
                    "height": height,
                    "cell_count": len(reset_state["cell_states"]),
                    "cold_build_median_ms": benchmark_topology_build_ms(
                        geometry, width, height, repeats=repeats
                    ),
                    "reset_ms": reset_ms,
                    "reset_bytes": reset_bytes,
                    "single_toggle_ms": toggle_ms,
                    "single_toggle_bytes": toggle_bytes,
                }
            )
    finally:
        server.close()

    comparison, comparison_ms = _median_payload(
        lambda: compare_seed(
            seed="011001100001000",
            geometries=("square", "hex", "trihexagonal-3-6-3-6"),
            steps=30,
            grid_size=12,
            include_states=True,
        ).to_dict(),
        repeats=repeats,
    )
    filmstrip, filmstrip_ms = _median_payload(
        lambda: run_seed_filmstrip(
            seed="011001100001000",
            geometries=("square", "hex", "trihexagonal-3-6-3-6"),
            frame_count=30,
            grid_size=12,
        ).to_dict(),
        repeats=repeats,
    )
    return {
        "schema_version": 1,
        "repeats": repeats,
        "topology_and_mutation": topology_cases,
        "comparison": {
            "median_ms": comparison_ms,
            "payload_bytes": _json_bytes(comparison),
            "geometry_count": 3,
            "steps": 30,
        },
        "filmstrip": {
            "median_ms": filmstrip_ms,
            "payload_bytes": _json_bytes(filmstrip),
            "geometry_count": 3,
            "frame_count": 30,
        },
        "bundle": _bundle_baseline(bundle_dir),
    }


def render_summary(payload: dict[str, object]) -> str:
    lines = ["Post-hotspot refactor baseline", ""]
    for case in cast(list[dict[str, Any]], payload["topology_and_mutation"]):
        typed_case = dict(case)
        lines.append(
            "{geometry:28s} cells={cell_count:5d} build={cold_build_median_ms:7.1f}ms "
            "toggle={single_toggle_ms:7.1f}ms/{single_toggle_bytes:7d}B".format(**typed_case)
        )
    comparison = cast(dict[str, Any], payload["comparison"])
    filmstrip = cast(dict[str, Any], payload["filmstrip"])
    lines.extend(
        (
            "",
            f"comparison median={comparison['median_ms']:.1f}ms "
            f"payload={comparison['payload_bytes']}B",
            f"filmstrip  median={filmstrip['median_ms']:.1f}ms "
            f"payload={filmstrip['payload_bytes']}B",
        )
    )
    bundle = cast(dict[str, Any], payload["bundle"])
    if bundle.get("available"):
        lines.append(f"bundle     raw={bundle['raw_bytes']}B gzip={bundle['gzip_bytes']}B")
    else:
        lines.append("bundle     unavailable (build standalone to include it)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record the post-hotspot refactor performance and payload baseline."
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.repeats < 1:
        raise SystemExit("--repeats must be at least 1")
    payload = collect_baseline(repeats=args.repeats, bundle_dir=args.bundle_dir)
    rendered = (
        json.dumps(payload, indent=2, sort_keys=True)
        if args.format == "json"
        else render_summary(payload)
    )
    if args.output is not None:
        write_text_lf(args.output, rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
