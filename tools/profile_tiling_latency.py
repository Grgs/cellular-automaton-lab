from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.request
from pathlib import Path
from typing import TypedDict

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.payload_types import (
    CellMutationDeltaPayload,
    CellTargetPayload,
    SimulationStatePayload,
    TopologySpecPayload,
)
from backend.simulation import periodic_face_tilings
from backend.simulation.topology import _build_topology_cached, _build_topology_uncached
from backend.simulation.topology_builders import INTERNAL_ALLOW_OVERSIZED_TOPOLOGIES_ENV
from backend.simulation.topology_types import LatticeCell, LatticeTopology, topology_revision
from tests.e2e.support_server import AppServer
from tests.typed_payloads import (
    require_cell_mutation_delta_payload,
    require_simulation_state_payload,
)


class ViewportPayload(TypedDict):
    width: int
    height: int


class ResetRequestPayload(TypedDict):
    topology_spec: TopologySpecPayload
    speed: int
    rule: str
    randomize: bool


class PeriodicBuildStageMedians(TypedDict):
    descriptor_loading_ms: float
    cell_realization_ms: float
    adjacency_ms: float
    normalization_ms: float
    serialization_ms: float
    cell_count: int


VIEWPORT: ViewportPayload = {"width": 1440, "height": 900}
CASES = (
    ("square", "conway", {"width": 90, "height": 60}),
    ("trihexagonal-3-6-3-6", "kagome-life", {"width": 48, "height": 32}),
)
STRESS_CASES = (("archimedean-3-3-3-3-6", "archlife-3-3-3-3-6", {"width": 36, "height": 24}),)

BROWSER_TRANSPORT_SCRIPT = """
async ({ resetPayload, toggleId }) => {
    const encoder = new TextEncoder();
    async function request(path, body) {
        const startedAt = performance.now();
        const response = await fetch(path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const text = await response.text();
        JSON.parse(text);
        return {
            elapsedMs: performance.now() - startedAt,
            bytes: encoder.encode(text).length,
        };
    }

    const reset = await request('/api/control/reset', resetPayload);
    const toggle = await request('/api/cells/toggle', { id: toggleId });
    return {
        resetMs: reset.elapsedMs,
        toggleMs: toggle.elapsedMs,
        resetBytes: reset.bytes,
        toggleBytes: toggle.bytes,
    };
}
"""


def _request_json_bytes(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: ResetRequestPayload | CellTargetPayload | None = None,
) -> tuple[object | None, int, float]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    started_at = time.perf_counter()
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read()
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    return json.loads(raw.decode("utf-8")) if raw else None, len(raw), elapsed_ms


def post_reset(
    base_url: str,
    payload: ResetRequestPayload,
) -> tuple[SimulationStatePayload, int, float]:
    raw_payload, payload_bytes, elapsed_ms = _request_json_bytes(
        base_url,
        "/api/control/reset",
        method="POST",
        payload=payload,
    )
    return (
        require_simulation_state_payload(raw_payload, context="latency profile reset response"),
        payload_bytes,
        elapsed_ms,
    )


def post_toggle(
    base_url: str,
    cell_id: str,
) -> tuple[CellMutationDeltaPayload, int, float]:
    raw_payload, payload_bytes, elapsed_ms = _request_json_bytes(
        base_url,
        "/api/cells/toggle",
        method="POST",
        payload={"id": cell_id},
    )
    return (
        require_cell_mutation_delta_payload(raw_payload, context="latency profile toggle response"),
        payload_bytes,
        elapsed_ms,
    )


def benchmark_topology_build_ms(
    geometry: str,
    width: int,
    height: int,
    *,
    patch_depth: int = 0,
    repeats: int = 7,
) -> float:
    times: list[float] = []
    for _ in range(repeats):
        _build_topology_cached.cache_clear()
        started_at = time.perf_counter()
        _build_topology_uncached(geometry, width, height, patch_depth=patch_depth)
        times.append((time.perf_counter() - started_at) * 1000)
    return statistics.median(times)


def benchmark_periodic_build_stages(
    geometry: str,
    width: int,
    height: int,
    *,
    repeats: int = 7,
) -> PeriodicBuildStageMedians:
    timings: dict[str, list[float]] = {
        "descriptor_loading_ms": [],
        "cell_realization_ms": [],
        "adjacency_ms": [],
        "normalization_ms": [],
        "serialization_ms": [],
    }
    cell_count = 0
    for _ in range(repeats):
        periodic_face_tilings._descriptor_registry.cache_clear()
        periodic_face_tilings._loaded_pattern_descriptors.cache_clear()
        started_at = time.perf_counter()
        descriptor = periodic_face_tilings.get_periodic_face_tiling_descriptor(geometry)
        timings["descriptor_loading_ms"].append((time.perf_counter() - started_at) * 1000)

        started_at = time.perf_counter()
        realized = descriptor.realize_faces(width, height)
        timings["cell_realization_ms"].append((time.perf_counter() - started_at) * 1000)

        started_at = time.perf_counter()
        attached = periodic_face_tilings._attach_neighbors(
            realized, neighbor_mode=descriptor.neighbor_mode
        )
        timings["adjacency_ms"].append((time.perf_counter() - started_at) * 1000)

        started_at = time.perf_counter()
        normalized = tuple(
            LatticeCell(
                id=cell.id,
                kind=cell.kind,
                neighbors=cell.neighbors,
                slot=cell.slot,
                center=cell.center,
                vertices=cell.vertices,
            )
            for cell in attached
        )
        topology = LatticeTopology(
            geometry=geometry,
            width=width,
            height=height,
            cells=normalized,
            topology_revision=topology_revision(geometry, width, height, 0),
            patch_depth=0,
        )
        timings["normalization_ms"].append((time.perf_counter() - started_at) * 1000)

        started_at = time.perf_counter()
        topology.to_dict()
        timings["serialization_ms"].append((time.perf_counter() - started_at) * 1000)
        cell_count = len(normalized)

    return {
        "descriptor_loading_ms": statistics.median(timings["descriptor_loading_ms"]),
        "cell_realization_ms": statistics.median(timings["cell_realization_ms"]),
        "adjacency_ms": statistics.median(timings["adjacency_ms"]),
        "normalization_ms": statistics.median(timings["normalization_ms"]),
        "serialization_ms": statistics.median(timings["serialization_ms"]),
        "cell_count": cell_count,
    }


def default_reset_payload(
    geometry: str, rule: str, dimensions: dict[str, int]
) -> ResetRequestPayload:
    return {
        "topology_spec": {
            "tiling_family": geometry,
            "adjacency_mode": "edge",
            "sizing_mode": "grid",
            "width": int(dimensions["width"]),
            "height": int(dimensions["height"]),
            "patch_depth": 0,
        },
        "speed": 5,
        "rule": rule,
        "randomize": False,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile topology build and interaction latency.")
    parser.add_argument(
        "--allow-oversize",
        action="store_true",
        help="include intentionally oversized stress cases and bypass the interactive cell budget",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int | None:
    args = parse_args(argv)
    if args.allow_oversize:
        os.environ[INTERNAL_ALLOW_OVERSIZED_TOPOLOGIES_ENV] = "1"
    cases = (*CASES, *STRESS_CASES) if args.allow_oversize else CASES
    server = AppServer()
    server.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport=VIEWPORT)
            page.goto(f"{server.base_url}/", wait_until="load")

            print("Mixed-tiling latency profile")
            print("viewport = {width}x{height}".format(**VIEWPORT))
            print("")
            print(
                "geometry".ljust(28),
                "dims".ljust(12),
                "cells".rjust(8),
                "build".rjust(10),
                "reset".rjust(10),
                "toggle".rjust(10),
                "reset KB".rjust(10),
                "toggle KB".rjust(10),
                "browser reset".rjust(14),
                "browser toggle".rjust(15),
            )

            for geometry, rule, dimensions in cases:
                reset_payload = default_reset_payload(geometry, rule, dimensions)
                build_ms = benchmark_topology_build_ms(
                    geometry,
                    int(dimensions["width"]),
                    int(dimensions["height"]),
                )

                reset_payload_response, reset_bytes, reset_ms = post_reset(
                    server.base_url, reset_payload
                )
                cells_payload = reset_payload_response["topology"]["cells"]
                if not cells_payload:
                    raise RuntimeError("Reset response did not include topology cells.")
                first_cell = cells_payload[0]
                toggle_id = first_cell["id"]
                if not toggle_id:
                    raise RuntimeError("Topology cell payload did not include an id.")
                _, toggle_bytes, toggle_ms = post_toggle(server.base_url, toggle_id)

                browser_transport = page.evaluate(
                    BROWSER_TRANSPORT_SCRIPT,
                    {
                        "resetPayload": reset_payload,
                        "toggleId": toggle_id,
                    },
                )

                cell_count = len(reset_payload_response["cell_states"])
                print(
                    geometry.ljust(28),
                    f"{dimensions['width']}x{dimensions['height']}".ljust(12),
                    str(cell_count).rjust(8),
                    f"{build_ms:8.1f}ms".rjust(10),
                    f"{reset_ms:8.1f}ms".rjust(10),
                    f"{toggle_ms:8.1f}ms".rjust(10),
                    f"{reset_bytes / 1024:8.1f}".rjust(10),
                    f"{toggle_bytes / 1024:8.1f}".rjust(10),
                    f"{browser_transport['resetMs']:10.1f}ms".rjust(14),
                    f"{browser_transport['toggleMs']:11.1f}ms".rjust(15),
                )
                if periodic_face_tilings.is_periodic_face_tiling(geometry):
                    stages = benchmark_periodic_build_stages(
                        geometry,
                        int(dimensions["width"]),
                        int(dimensions["height"]),
                    )
                    print(
                        " " * 4,
                        "stages",
                        f"load={stages['descriptor_loading_ms']:.1f}ms",
                        f"realize={stages['cell_realization_ms']:.1f}ms",
                        f"adjacency={stages['adjacency_ms']:.1f}ms",
                        f"normalize={stages['normalization_ms']:.1f}ms",
                        f"serialize={stages['serialization_ms']:.1f}ms",
                    )

            browser.close()
    finally:
        server.close()
    return None


if __name__ == "__main__":
    raise SystemExit(main() or 0)
