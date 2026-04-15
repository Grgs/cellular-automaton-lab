from __future__ import annotations

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


def wait_for_patch_render_complete(page: Page) -> None:
    page.wait_for_function(
        """() => {
            const grid = document.getElementById("grid");
            const overlay = document.getElementById("blocking-activity-overlay");
            const renderCellSize = Number(grid?.getAttribute("data-render-cell-size") || "0");
            const overlayHidden = overlay instanceof HTMLElement
                ? overlay.hidden || overlay.getAttribute("hidden") !== null
                : true;
            return Number.isFinite(renderCellSize) && renderCellSize > 0 && overlayHidden;
        }""",
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
