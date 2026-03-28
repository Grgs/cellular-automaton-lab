from __future__ import annotations

import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path
from typing import Mapping, TypedDict

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.payload_types import JsonObject, TopologySpecPayload
from backend.simulation.topology import _build_topology_cached, _build_topology_uncached, empty_board
from tests.e2e.support_server import AppServer


class ViewportPayload(TypedDict):
    width: int
    height: int


class ResetRequestPayload(TypedDict):
    topology_spec: TopologySpecPayload
    speed: int
    rule: str
    randomize: bool


VIEWPORT: ViewportPayload = {"width": 1440, "height": 900}
CASES = (
    ("square", "conway", {"width": 90, "height": 60}),
    ("archimedean-3-3-3-3-6", "archlife-3-3-3-3-6", {"width": 36, "height": 24}),
    ("trihexagonal-3-6-3-6", "kagome-life", {"width": 48, "height": 32}),
)

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


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: Mapping[str, object] | None = None,
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


def median_elapsed_ms(callback, *, repeats: int = 5) -> float:
    values = [callback() for _ in range(repeats)]
    return statistics.median(values)


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


def default_reset_payload(geometry: str, rule: str, dimensions: dict[str, int]) -> ResetRequestPayload:
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


def main() -> None:
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

            for geometry, rule, dimensions in CASES:
                reset_payload = default_reset_payload(geometry, rule, dimensions)
                build_ms = benchmark_topology_build_ms(
                    geometry,
                    int(dimensions["width"]),
                    int(dimensions["height"]),
                )

                reset_payload_response, reset_bytes, reset_ms = request_json(
                    server.base_url,
                    "/api/control/reset",
                    method="POST",
                    payload=reset_payload,
                )
                if not isinstance(reset_payload_response, dict):
                    raise RuntimeError("Reset response must be a JSON object.")
                topology_payload = reset_payload_response.get("topology")
                if not isinstance(topology_payload, dict):
                    raise RuntimeError("Reset response did not include topology payload.")
                cells_payload = topology_payload.get("cells")
                if not isinstance(cells_payload, list) or not cells_payload:
                    raise RuntimeError("Reset response did not include topology cells.")
                first_cell = cells_payload[0]
                if not isinstance(first_cell, dict):
                    raise RuntimeError("Topology cell payload is invalid.")
                toggle_id = first_cell.get("id")
                if not isinstance(toggle_id, str) or not toggle_id:
                    raise RuntimeError("Topology cell payload did not include an id.")
                _, toggle_bytes, toggle_ms = request_json(
                    server.base_url,
                    "/api/cells/toggle",
                    method="POST",
                    payload={"id": toggle_id},
                )

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

            browser.close()
    finally:
        server.close()


if __name__ == "__main__":
    main()
