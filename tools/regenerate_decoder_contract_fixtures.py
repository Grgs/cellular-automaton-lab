from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.browser_runtime import BrowserSimulationRuntime  # noqa: E402
from tools._common import write_text_lf  # noqa: E402

DEFAULT_FIXTURE_PATH = (
    ROOT / "frontend" / "test-fixtures" / "decoder-contract" / "worker-responses.json"
)

# Snapshots and deltas carry a wall-clock `state_epoch`; pin it so regeneration
# is byte-stable. The frontend contract test only needs the field present.
FIXED_STATE_EPOCH = 1_721_000_000_000_000

_COMPARE_REQUEST = {
    "seed": "01101001",
    "rule": "conway",
    "geometries": ["square", "hex"],
    "steps": 8,
    "grid_size": 8,
    "include_states": True,
}

_FILMSTRIP_REQUEST = {
    "seed": "01101001",
    "rule": "conway",
    "geometries": ["square", "hex"],
    "frames": 4,
    "grid_size": 8,
}

# A small board keeps every captured snapshot compact without losing shape
# coverage; the topology payload structure is identical at any size.
_SMALL_RESET_REQUEST = {
    "topology_spec": {
        "tiling_family": "square",
        "adjacency_mode": "edge",
        "sizing_mode": "grid",
        "width": 6,
        "height": 6,
        "patch_depth": 0,
    },
    "speed": 5,
    "rule": "conway",
    "randomize": False,
}

_OVERSIZED_RESET_REQUEST = {
    "topology_spec": {
        "tiling_family": "square",
        "adjacency_mode": "edge",
        "sizing_mode": "grid",
        "width": 201,
        "height": 100,
        "patch_depth": 0,
        "unsafe_size_override": True,
    },
    "speed": 5,
    "rule": "conway",
    "randomize": False,
}


def _normalize_state_epochs(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: FIXED_STATE_EPOCH if key == "state_epoch" else _normalize_state_epochs(entry)
            for key, entry in value.items()
        }
    if isinstance(value, list):
        return [_normalize_state_epochs(entry) for entry in value]
    return value


def _parsed(raw: str) -> dict[str, Any]:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Runtime handlers must return JSON objects.")
    return cast(dict[str, Any], payload)


def build_fixture_document() -> dict[str, Any]:
    """Drive the real standalone runtime handlers and record their responses.

    Every entry is the verbatim JSON a worker command emits (plus the
    normalized `state_epoch`), so the frontend contract test decodes exactly
    what production code would receive.
    """
    runtime = BrowserSimulationRuntime.create()
    responses: dict[str, dict[str, Any]] = {}

    def record(name: str, decoder: str, raw: str) -> dict[str, Any]:
        response = _parsed(raw)
        responses[name] = {"decoder": decoder, "response": response}
        return response

    record(
        "control-reset",
        "request",
        runtime.handle_command("/api/control/reset", _SMALL_RESET_REQUEST),
    )
    record("init", "init", runtime.get_state_response())
    record("state", "request", runtime.handle_command("/api/state"))
    record("rules", "request", runtime.handle_command("/api/rules"))

    cell_ids = [cell.id for cell in runtime.service.get_state().topology.cells[:3]]
    set_many = record(
        "cells-set-many",
        "request",
        runtime.handle_command(
            "/api/cells/set-many",
            {"cells": [{"id": cell_id, "state": 1} for cell_id in cell_ids]},
        ),
    )
    # The HTTP routes return the bare delta without the worker's `ok` wrapper.
    responses["http-cell-delta"] = {
        "decoder": "delta",
        "response": {key: value for key, value in set_many.items() if key != "ok"},
    }

    record("control-step", "request", runtime.handle_command("/api/control/step"))
    record("tick-idle", "tick", runtime.tick_running())
    runtime.service.start()
    record("tick-running", "tick", runtime.tick_running())
    runtime.service.pause()

    record("compare", "request", runtime.handle_command("/api/compare", _COMPARE_REQUEST))
    record(
        "filmstrip",
        "request",
        runtime.handle_command("/api/compare/filmstrip", _FILMSTRIP_REQUEST),
    )
    record(
        "topology-preview-square",
        "request",
        runtime.handle_command("/api/topology/preview", {"geometry": "square", "grid_size": 4}),
    )
    record(
        "topology-preview-cairo",
        "request",
        runtime.handle_command(
            "/api/topology/preview", {"geometry": "cairo-pentagonal", "grid_size": 4}
        ),
    )

    record(
        "error-topology-budget",
        "request",
        runtime.handle_command("/api/control/reset", _OVERSIZED_RESET_REQUEST),
    )
    record("error-unknown-command", "request", runtime.handle_command("/api/does-not-exist"))

    document = {
        "note": (
            "Generated by `python -m tools fixtures decoder-contract`. Verbatim standalone "
            "runtime responses (state_epoch pinned) consumed by "
            "frontend/standalone/runtime-decoders.contract.test.ts."
        ),
        "responses": responses,
    }
    return cast(dict[str, Any], _normalize_state_epochs(document))


def render_fixture_document() -> str:
    return json.dumps(build_fixture_document(), indent=2, sort_keys=True) + "\n"


def fixture_drift_detail(fixture_path: Path = DEFAULT_FIXTURE_PATH) -> str | None:
    """Return a human-readable drift description, or None when current."""
    if not fixture_path.is_file():
        return f"{fixture_path} does not exist"
    current = fixture_path.read_text(encoding="utf-8")
    if current != render_fixture_document():
        return f"{fixture_path} does not match regenerated runtime responses"
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate or check the standalone decoder contract fixture.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift against the checked-in fixture instead of writing.",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_FIXTURE_PATH,
        help="Fixture path (default: frontend/test-fixtures/decoder-contract/worker-responses.json)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fixture_path: Path = args.path
    if args.check:
        drift = fixture_drift_detail(fixture_path)
        if drift is None:
            print("decoder contract fixture is up to date")
            return 0
        print(f"decoder contract fixture drift: {drift}")
        print("Run `python -m tools fixtures decoder-contract` to regenerate.")
        return 1
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(fixture_path, render_fixture_document())
    print(f"Wrote {fixture_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
