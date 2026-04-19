from __future__ import annotations

import datetime as dt
import io
import json
import math
import time
from collections import Counter, deque
from pathlib import Path
from typing import Any, TypedDict, cast

from playwright.sync_api import Page
from PIL import Image


class CanvasVisualSummary(TypedDict):
    canvasWidth: int
    canvasHeight: int
    coverageWidthRatio: float
    coverageHeightRatio: float
    visibleAspectRatio: float | None
    edgeDensity: float | None
    boundaryDominance: float | None
    gutterScore: float | None
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
    metricInputs: dict[str, object] | None
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
DEFAULT_ALPHA_OCCUPIED_THRESHOLD = 32
DEFAULT_ALPHA_OPAQUE_THRESHOLD = 250
DEFAULT_BOUNDARY_BAND_FRACTION = 0.15
DEFAULT_MIN_DOMINANT_FILL_COUNT = 100


class OccupiedBounds(TypedDict):
    minX: int
    maxX: int
    minY: int
    maxY: int
    width: int
    height: int


def _mask_index(width: int, x: int, y: int) -> int:
    return (y * width) + x


def occupied_bounds_from_mask(
    occupied_mask: list[bool],
    *,
    width: int,
    height: int,
) -> OccupiedBounds | None:
    min_x = width
    min_y = height
    max_x = -1
    max_y = -1
    for y in range(height):
        row_offset = y * width
        for x in range(width):
            if not occupied_mask[row_offset + x]:
                continue
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y
    if max_x < min_x or max_y < min_y:
        return None
    return {
        "minX": min_x,
        "maxX": max_x,
        "minY": min_y,
        "maxY": max_y,
        "width": (max_x - min_x) + 1,
        "height": (max_y - min_y) + 1,
    }


def visible_aspect_ratio(bounds: OccupiedBounds | None) -> float | None:
    if bounds is None or bounds["height"] <= 0:
        return None
    return bounds["width"] / bounds["height"]


def edge_density(
    occupied_mask: list[bool],
    *,
    width: int,
    height: int,
) -> float | None:
    occupied_count = 0
    edge_count = 0
    for y in range(height):
        row_offset = y * width
        for x in range(width):
            if not occupied_mask[row_offset + x]:
                continue
            occupied_count += 1
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = x + dx
                ny = y + dy
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    edge_count += 1
                    break
                if not occupied_mask[_mask_index(width, nx, ny)]:
                    edge_count += 1
                    break
    if occupied_count <= 0:
        return None
    return edge_count / occupied_count


def boundary_dominance(
    occupied_mask: list[bool],
    bounds: OccupiedBounds | None,
    *,
    width: int,
    height: int,
    band_fraction: float = DEFAULT_BOUNDARY_BAND_FRACTION,
) -> float | None:
    if bounds is None:
        return None
    occupied_count = 0
    boundary_count = 0
    horizontal_band = max(1, math.ceil(bounds["width"] * band_fraction))
    vertical_band = max(1, math.ceil(bounds["height"] * band_fraction))
    left_limit = bounds["minX"] + horizontal_band
    right_limit = bounds["maxX"] - horizontal_band
    top_limit = bounds["minY"] + vertical_band
    bottom_limit = bounds["maxY"] - vertical_band
    for y in range(height):
        row_offset = y * width
        for x in range(width):
            if not occupied_mask[row_offset + x]:
                continue
            occupied_count += 1
            if (
                x < left_limit
                or x > right_limit
                or y < top_limit
                or y > bottom_limit
            ):
                boundary_count += 1
    if occupied_count <= 0:
        return None
    return boundary_count / occupied_count


def gutter_score(
    occupied_mask: list[bool],
    bounds: OccupiedBounds | None,
    *,
    width: int,
    height: int,
) -> float | None:
    if bounds is None:
        return None
    bbox_area = bounds["width"] * bounds["height"]
    if bbox_area <= 0:
        return None
    queue: deque[tuple[int, int]] = deque()
    visited: set[int] = set()

    def enqueue_if_transparent(x: int, y: int) -> None:
        index = _mask_index(width, x, y)
        if occupied_mask[index] or index in visited:
            return
        visited.add(index)
        queue.append((x, y))

    for x in range(bounds["minX"], bounds["maxX"] + 1):
        enqueue_if_transparent(x, bounds["minY"])
        enqueue_if_transparent(x, bounds["maxY"])
    for y in range(bounds["minY"], bounds["maxY"] + 1):
        enqueue_if_transparent(bounds["minX"], y)
        enqueue_if_transparent(bounds["maxX"], y)

    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy
            if nx < bounds["minX"] or nx > bounds["maxX"] or ny < bounds["minY"] or ny > bounds["maxY"]:
                continue
            enqueue_if_transparent(nx, ny)

    enclosed_transparent_pixels = 0
    for y in range(bounds["minY"], bounds["maxY"] + 1):
        for x in range(bounds["minX"], bounds["maxX"] + 1):
            index = _mask_index(width, x, y)
            if occupied_mask[index] or index in visited:
                continue
            enclosed_transparent_pixels += 1
    return enclosed_transparent_pixels / bbox_area


def summarize_canvas_pixels(
    image: Image.Image,
    *,
    alpha_occupied_threshold: int = DEFAULT_ALPHA_OCCUPIED_THRESHOLD,
    alpha_opaque_threshold: int = DEFAULT_ALPHA_OPAQUE_THRESHOLD,
) -> dict[str, Any]:
    rgba_image = image.convert("RGBA")
    width, height = rgba_image.size
    rgba_pixels = rgba_image.load()
    occupied_mask: list[bool] = []
    dominant_fill_colors: Counter[str] = Counter()

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = rgba_pixels[x, y]
            occupied = alpha >= alpha_occupied_threshold
            occupied_mask.append(occupied)
            if (
                alpha >= alpha_opaque_threshold
                and red >= 140
                and green >= 100
                and blue >= 60
            ):
                dominant_fill_colors[f"{red},{green},{blue}"] += 1

    bounds = occupied_bounds_from_mask(occupied_mask, width=width, height=height)
    coverage_width_ratio = (bounds["width"] / width) if bounds is not None and width > 0 else 0.0
    coverage_height_ratio = (bounds["height"] / height) if bounds is not None and height > 0 else 0.0

    return {
        "canvasWidth": width,
        "canvasHeight": height,
        "coverageWidthRatio": coverage_width_ratio,
        "coverageHeightRatio": coverage_height_ratio,
        "visibleAspectRatio": visible_aspect_ratio(bounds),
        "edgeDensity": edge_density(occupied_mask, width=width, height=height),
        "boundaryDominance": boundary_dominance(
            occupied_mask,
            bounds,
            width=width,
            height=height,
        ),
        "gutterScore": gutter_score(
            occupied_mask,
            bounds,
            width=width,
            height=height,
        ),
        "dominantFillColors": [
            [key, count]
            for key, count in sorted(
                (
                    (key, count)
                    for key, count in dominant_fill_colors.items()
                    if count >= DEFAULT_MIN_DOMINANT_FILL_COUNT
                ),
                key=lambda item: item[1],
                reverse=True,
            )
        ],
    }


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


def apply_review_topology_payload(
    page: Page,
    topology_payload: dict[str, Any],
) -> None:
    page.evaluate(
        """async (payload) => {
            const applyReviewTopology = window.__applyReviewTopology;
            if (typeof applyReviewTopology !== "function") {
                throw new Error("Review topology injection hook is unavailable.");
            }
            await applyReviewTopology(payload);
        }""",
        topology_payload,
    )


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


def canvas_visual_summary(page: Page, *, png_path: Path | None = None) -> CanvasVisualSummary:
    if png_path is not None and png_path.exists():
        with Image.open(png_path) as image:
            pixel_summary = summarize_canvas_pixels(image)
    else:
        png_bytes = page.locator("#grid").screenshot(type="png")
        with Image.open(io.BytesIO(png_bytes)) as image:
            pixel_summary = summarize_canvas_pixels(image)
    text_summary = page.evaluate(
        """() => {
            const canvas = document.getElementById("grid");
            if (!(canvas instanceof HTMLCanvasElement)) {
                throw new Error("grid canvas is missing");
            }
            return {
                renderCellSize: Number(canvas.getAttribute("data-render-cell-size") || "0"),
                generationText: document.getElementById("generation-text")?.textContent?.trim() || "",
                gridSizeText: document.getElementById("grid-size-text")?.textContent?.trim() || "",
            };
        }""",
    )
    return cast(
        CanvasVisualSummary,
        {
            **pixel_summary,
            "renderCellSize": float(text_summary["renderCellSize"]),
            "generationText": str(text_summary["generationText"]),
            "gridSizeText": str(text_summary["gridSizeText"]),
        },
    )


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
