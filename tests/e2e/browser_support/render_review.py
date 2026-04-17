from __future__ import annotations

import datetime as dt
import json
import time
from typing import Any, TypedDict, cast

from playwright.sync_api import Page


class CanvasVisualSummary(TypedDict):
    canvasWidth: int
    canvasHeight: int
    coverageWidthRatio: float
    coverageHeightRatio: float
    dominantFillColors: list[list[object]]
    renderCellSize: float
    generationText: str
    gridSizeText: str


class BrowserTopologySummary(TypedDict):
    tilingFamily: str | None
    patchDepth: int | None
    topologyCellCount: int | None
    width: int | None
    height: int | None
    topologyRevision: str | None


class BrowserTransformReport(TypedDict):
    geometry: str
    adapterGeometry: str
    adapterFamily: str
    topologyBounds: dict[str, float] | None
    renderMetrics: dict[str, float | int | None]
    sampleCells: dict[str, dict[str, object] | None]
    overlapHotspots: dict[str, object] | None


class BrowserReadinessSnapshot(TypedDict):
    appReady: bool
    blockingActivityVisible: bool
    blockingActivityKind: str | None
    blockingActivityMessage: str
    blockingActivityDetail: str
    blockingActivityStartedAt: int | None
    topologyRevision: str | None
    topologyCellCount: int
    patchDepth: int | None
    renderCellSize: float | None
    gridSizeText: str
    generationText: str
    statusText: str


class RenderSettleDiagnostics(TypedDict):
    settled: bool
    stablePollCountRequired: int
    stablePollIntervalMs: int
    finalSnapshot: BrowserReadinessSnapshot | None
    settledAt: str | None
    settleDurationMs: int
    warnings: list[str]


PLACEHOLDER_GRID_SIZE_TEXT = "-- x --"
DEFAULT_SETTLE_TIMEOUT_MS = 30_000
DEFAULT_SETTLE_STABLE_POLLS = 3
DEFAULT_SETTLE_POLL_INTERVAL_MS = 150


def wait_for_page_bootstrapped(page: Page, *, timeout_ms: int = 30_000) -> None:
    page.wait_for_selector("#grid", timeout=timeout_ms)
    page.wait_for_function("() => document.readyState === 'complete'", timeout=timeout_ms)
    page.wait_for_function(
        """() => {
            const grid = document.getElementById('grid');
            const statusText = document.getElementById('status-text');
            const gridSizeText = document.getElementById('grid-size-text')?.textContent?.trim() || '';
            const renderCellSize = Number(grid?.dataset.renderCellSize || 0);
            return Boolean(grid)
                && Boolean(statusText)
                && typeof statusText.textContent === 'string'
                && statusText.textContent.trim().length > 0
                && (
                    window.__appReady === true
                    || renderCellSize > 0
                    || (gridSizeText.length > 0 && gridSizeText !== '-- x --')
                );
        }""",
        timeout=timeout_ms,
    )


def normalize_readiness_snapshot(raw: object) -> BrowserReadinessSnapshot | None:
    if not isinstance(raw, dict):
        return None
    snapshot = cast(dict[str, object], raw)

    def _as_bool(value: object) -> bool:
        return bool(value)

    def _as_string(value: object) -> str:
        return str(value).strip() if value is not None else ""

    def _as_int_or_none(value: object) -> int | None:
        numeric = int(value) if isinstance(value, bool) else int(value) if isinstance(value, int) else None
        if numeric is not None:
            return numeric
        try:
            parsed = int(str(value))
        except (TypeError, ValueError):
            return None
        return parsed

    def _as_float_or_none(value: object) -> float | None:
        try:
            numeric = float(str(value))
        except (TypeError, ValueError):
            return None
        return numeric if numeric == numeric else None

    return {
        "appReady": _as_bool(snapshot.get("appReady")),
        "blockingActivityVisible": _as_bool(snapshot.get("blockingActivityVisible")),
        "blockingActivityKind": (_as_string(snapshot.get("blockingActivityKind")) or None),
        "blockingActivityMessage": _as_string(snapshot.get("blockingActivityMessage")),
        "blockingActivityDetail": _as_string(snapshot.get("blockingActivityDetail")),
        "blockingActivityStartedAt": _as_int_or_none(snapshot.get("blockingActivityStartedAt")),
        "topologyRevision": (_as_string(snapshot.get("topologyRevision")) or None),
        "topologyCellCount": _as_int_or_none(snapshot.get("topologyCellCount")) or 0,
        "patchDepth": _as_int_or_none(snapshot.get("patchDepth")),
        "renderCellSize": _as_float_or_none(snapshot.get("renderCellSize")),
        "gridSizeText": _as_string(snapshot.get("gridSizeText")),
        "generationText": _as_string(snapshot.get("generationText")),
        "statusText": _as_string(snapshot.get("statusText")),
    }


def readiness_tuple(snapshot: BrowserReadinessSnapshot) -> tuple[object, ...]:
    return (
        snapshot["topologyRevision"],
        snapshot["topologyCellCount"],
        snapshot["patchDepth"],
        snapshot["renderCellSize"],
        snapshot["gridSizeText"],
        snapshot["generationText"],
        snapshot["statusText"],
        snapshot["blockingActivityVisible"],
        snapshot["blockingActivityKind"],
        snapshot["blockingActivityMessage"],
    )


def readiness_blockers(snapshot: BrowserReadinessSnapshot | None) -> list[str]:
    if snapshot is None:
        return ["Readiness diagnostics were unavailable."]
    blockers: list[str] = []
    if not snapshot["appReady"]:
        blockers.append("App readiness flag was false.")
    if snapshot["blockingActivityVisible"]:
        blockers.append("Blocking activity was still visible.")
    if snapshot["blockingActivityKind"]:
        blockers.append(f"Blocking activity kind was still set: {snapshot['blockingActivityKind']}.")
    if snapshot["blockingActivityMessage"]:
        blockers.append(f"Blocking activity message was still set: {snapshot['blockingActivityMessage']}.")
    if not snapshot["topologyRevision"]:
        blockers.append("Topology revision was missing.")
    if snapshot["topologyCellCount"] <= 0:
        blockers.append("Topology cell count was not positive.")
    if not snapshot["renderCellSize"] or snapshot["renderCellSize"] <= 0:
        blockers.append("Rendered cell size was not positive.")
    if not snapshot["gridSizeText"] or snapshot["gridSizeText"] == PLACEHOLDER_GRID_SIZE_TEXT:
        blockers.append("Grid summary was still missing or placeholder.")
    if not snapshot["generationText"]:
        blockers.append("Generation summary was empty.")
    return blockers


def browser_readiness_snapshot(page: Page) -> BrowserReadinessSnapshot | None:
    summary = page.evaluate(
        """() => {
            const diagnostics = window.__appDiagnostics;
            if (typeof diagnostics !== "function") {
                return null;
            }
            const snapshot = diagnostics();
            if (!snapshot || typeof snapshot !== "object" || !snapshot.readiness) {
                return null;
            }
            return snapshot.readiness;
        }""",
    )
    return normalize_readiness_snapshot(summary)


def select_tiling_family(
    page: Page,
    tiling_family: str,
    *,
    expect_reset_request: bool = False,
    timeout_ms: int = 60_000,
) -> int | None:
    if not expect_reset_request:
        page.select_option("#tiling-family-select", tiling_family)
        page.wait_for_function(
            """(nextTilingFamily) => {
                const select = document.getElementById("tiling-family-select");
                return select instanceof HTMLSelectElement && select.value === nextTilingFamily;
            }""",
            arg=tiling_family,
            timeout=timeout_ms,
        )
        return None
    with page.expect_response(
        lambda response: response.request.method == "POST" and "/api/control/reset" in response.url,
        timeout=timeout_ms,
    ) as response_info:
        page.select_option("#tiling-family-select", tiling_family)
    return int(response_info.value.status)


def set_range_value(
    page: Page,
    selector: str,
    value: int,
    *,
    timeout_ms: int = 30_000,
) -> None:
    page.wait_for_function(
        """(elementSelector) => {
            const input = document.querySelector(elementSelector);
            return input instanceof HTMLInputElement && !input.hidden;
        }""",
        arg=selector,
        timeout=timeout_ms,
    )
    page.locator(selector).evaluate(
        """(node, nextValue) => {
            if (!(node instanceof HTMLInputElement)) {
                throw new Error("expected range input");
            }
            node.value = String(nextValue);
            node.dispatchEvent(new Event("input", { bubbles: true }));
            node.dispatchEvent(new Event("change", { bubbles: true }));
        }""",
        value,
    )
    page.wait_for_function(
        """({ elementSelector, expectedValue }) => {
            const input = document.querySelector(elementSelector);
            return input instanceof HTMLInputElement && Number(input.value) === expectedValue;
        }""",
        arg={"elementSelector": selector, "expectedValue": value},
        timeout=timeout_ms,
    )


def set_patch_depth(page: Page, patch_depth: int, *, timeout_ms: int = 30_000) -> None:
    set_range_value(page, "#patch-depth-input", patch_depth, timeout_ms=timeout_ms)


def set_cell_size(page: Page, cell_size: int, *, timeout_ms: int = 30_000) -> None:
    set_range_value(page, "#cell-size-input", cell_size, timeout_ms=timeout_ms)


def wait_for_patch_render_complete(
    page: Page,
    *,
    timeout_ms: int = DEFAULT_SETTLE_TIMEOUT_MS,
    stable_poll_count: int = DEFAULT_SETTLE_STABLE_POLLS,
    stable_poll_interval_ms: int = DEFAULT_SETTLE_POLL_INTERVAL_MS,
) -> RenderSettleDiagnostics:
    started_at = time.monotonic()
    deadline = started_at + (timeout_ms / 1000)
    last_snapshot: BrowserReadinessSnapshot | None = None
    last_tuple: tuple[object, ...] | None = None
    stable_count = 0

    while time.monotonic() < deadline:
        snapshot = browser_readiness_snapshot(page)
        last_snapshot = snapshot
        blockers = readiness_blockers(snapshot)
        if blockers:
            stable_count = 0
            last_tuple = None
        else:
            current_tuple = readiness_tuple(cast(BrowserReadinessSnapshot, snapshot))
            if current_tuple == last_tuple:
                stable_count += 1
            else:
                stable_count = 1
                last_tuple = current_tuple
            if stable_count >= stable_poll_count:
                page.evaluate(
                    """() => new Promise((resolve) => {
                        requestAnimationFrame(() => requestAnimationFrame(() => resolve(null)));
                    })"""
                )
                settled_at = dt.datetime.now(tz=dt.timezone.utc).isoformat()
                return {
                    "settled": True,
                    "stablePollCountRequired": stable_poll_count,
                    "stablePollIntervalMs": stable_poll_interval_ms,
                    "finalSnapshot": cast(BrowserReadinessSnapshot, snapshot),
                    "settledAt": settled_at,
                    "settleDurationMs": int((time.monotonic() - started_at) * 1000),
                    "warnings": [],
                }
        time.sleep(stable_poll_interval_ms / 1000)

    warnings = readiness_blockers(last_snapshot)
    if last_snapshot is not None:
        if last_snapshot["blockingActivityVisible"] or last_snapshot["blockingActivityKind"] or last_snapshot["blockingActivityMessage"]:
            warnings.append("Blocking activity never cleared before timeout.")
        if not last_snapshot["gridSizeText"] or last_snapshot["gridSizeText"] == PLACEHOLDER_GRID_SIZE_TEXT:
            warnings.append("Grid summary stayed placeholder before timeout.")
    if stable_count > 0:
        warnings.append("Readiness tuple kept changing before timeout.")
    diagnostics: RenderSettleDiagnostics = {
        "settled": False,
        "stablePollCountRequired": stable_poll_count,
        "stablePollIntervalMs": stable_poll_interval_ms,
        "finalSnapshot": last_snapshot,
        "settledAt": None,
        "settleDurationMs": int((time.monotonic() - started_at) * 1000),
        "warnings": list(dict.fromkeys(warnings)),
    }
    raise AssertionError(
        "Render did not settle within "
        f"{timeout_ms}ms. Last readiness snapshot: {json.dumps(last_snapshot, sort_keys=True)}"
    )


def canvas_visual_summary(page: Page) -> CanvasVisualSummary:
    summary = page.evaluate(
        """() => {
            const canvas = document.getElementById("grid");
            if (!(canvas instanceof HTMLCanvasElement)) {
                throw new Error("grid canvas is missing");
            }
            const context = canvas.getContext("2d");
            if (!context) {
                throw new Error("2d canvas context is unavailable");
            }
            const image = context.getImageData(0, 0, canvas.width, canvas.height);
            const { data, width, height } = image;
            let minX = width;
            let minY = height;
            let maxX = -1;
            let maxY = -1;
            const dominantFillColors = new Map();

            for (let y = 0; y < height; y += 1) {
                for (let x = 0; x < width; x += 1) {
                    const index = ((y * width) + x) * 4;
                    const alpha = data[index + 3];
                    if (alpha < 32) {
                        continue;
                    }
                    if (x < minX) minX = x;
                    if (x > maxX) maxX = x;
                    if (y < minY) minY = y;
                    if (y > maxY) maxY = y;

                    if (alpha < 250) {
                        continue;
                    }
                    const r = data[index];
                    const g = data[index + 1];
                    const b = data[index + 2];
                    if (r < 140 || g < 100 || b < 60) {
                        continue;
                    }
                    const key = `${r},${g},${b}`;
                    dominantFillColors.set(key, (dominantFillColors.get(key) || 0) + 1);
                }
            }

            return {
                canvasWidth: width,
                canvasHeight: height,
                coverageWidthRatio: maxX >= minX ? (maxX - minX + 1) / width : 0,
                coverageHeightRatio: maxY >= minY ? (maxY - minY + 1) / height : 0,
                dominantFillColors: Array.from(dominantFillColors.entries())
                    .filter(([, count]) => count >= 100)
                    .sort((left, right) => right[1] - left[1]),
                renderCellSize: Number(canvas.getAttribute("data-render-cell-size") || "0"),
                generationText: document.getElementById("generation-text")?.textContent?.trim() || "",
                gridSizeText: document.getElementById("grid-size-text")?.textContent?.trim() || "",
            };
        }""",
    )
    return cast(CanvasVisualSummary, summary)


def browser_topology_summary(page: Page) -> BrowserTopologySummary | None:
    summary = page.evaluate(
        """() => {
            const diagnostics = window.__appDiagnostics;
            if (typeof diagnostics !== "function") {
                return null;
            }
            const snapshot = diagnostics();
            if (!snapshot || typeof snapshot !== "object") {
                return null;
            }
            const numericOrNull = (value) => {
                const numeric = Number(value);
                return Number.isFinite(numeric) ? numeric : null;
            };
            return {
                tilingFamily: typeof snapshot.tilingFamily === "string" ? snapshot.tilingFamily : null,
                patchDepth: numericOrNull(snapshot.patchDepth),
                topologyCellCount: numericOrNull(snapshot.topologyCellCount),
                width: numericOrNull(snapshot.width),
                height: numericOrNull(snapshot.height),
                topologyRevision: typeof snapshot.topologyRevision === "string" ? snapshot.topologyRevision : null,
            };
        }""",
    )
    if summary is None:
        return None
    cast_summary = cast(dict[str, object], summary)
    return cast(
        BrowserTopologySummary,
        {
            "tilingFamily": cast_summary.get("tilingFamily"),
            "patchDepth": cast_summary.get("patchDepth"),
            "topologyCellCount": cast_summary.get("topologyCellCount"),
            "width": cast_summary.get("width"),
            "height": cast_summary.get("height"),
            "topologyRevision": cast_summary.get("topologyRevision"),
        },
    )


def browser_transform_report(page: Page) -> BrowserTransformReport | None:
    summary = page.evaluate(
        """() => {
            const diagnostics = window.__appDiagnostics;
            if (typeof diagnostics !== "function") {
                return null;
            }
            const snapshot = diagnostics();
            if (!snapshot || typeof snapshot !== "object" || !snapshot.transformReport) {
                return null;
            }
            return snapshot.transformReport;
        }""",
    )
    if summary is None:
        return None
    return cast(BrowserTransformReport, summary)


def browser_overlap_hotspots(page: Page) -> dict[str, object] | None:
    summary = browser_transform_report(page)
    if summary is None:
        return None
    overlap_hotspots = summary.get("overlapHotspots")
    return cast(dict[str, object] | None, overlap_hotspots)


def viewport_gap_summary(page: Page) -> dict[str, float]:
    summary = page.evaluate(
        """() => {
            const viewport = document.getElementById("grid-viewport");
            const canvas = document.getElementById("grid");
            if (!(viewport instanceof HTMLElement) || !(canvas instanceof HTMLCanvasElement)) {
                throw new Error("grid viewport or canvas is missing");
            }
            const viewportRect = viewport.getBoundingClientRect();
            const canvasRect = canvas.getBoundingClientRect();
            return {
                topGap: canvasRect.top - viewportRect.top,
                bottomGap: viewportRect.bottom - canvasRect.bottom,
                leftGap: canvasRect.left - viewportRect.left,
                rightGap: viewportRect.right - canvasRect.right,
            };
        }""",
    )
    return cast(dict[str, float], summary)


def assert_canvas_centered_within_viewport(
    page: Page,
    *,
    maximum_vertical_gap_delta: float = 4.0,
    maximum_horizontal_gap_delta: float = 4.0,
) -> None:
    summary = viewport_gap_summary(page)
    if abs(summary["topGap"] - summary["bottomGap"]) > maximum_vertical_gap_delta:
        raise AssertionError(
            "canvas vertical gaps were not balanced within the viewport: "
            f"{summary!r}"
        )
    if abs(summary["leftGap"] - summary["rightGap"]) > maximum_horizontal_gap_delta:
        raise AssertionError(
            "canvas horizontal gaps were not balanced within the viewport: "
            f"{summary!r}"
        )
