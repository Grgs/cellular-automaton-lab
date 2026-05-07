from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, ClassVar, Protocol, cast

from playwright.sync_api import Response, ViewportSize, expect

try:
    from tests.e2e.browser_support.bootstrap import WaitUntilState
    from tests.e2e.support_runtime_host import BrowserRuntimeHost
    from tests.e2e.support_server import JsonApiClient
    from tools.render_review.browser_support.diagnostics import GridSummary, parse_grid_summary_text
    from tools.render_review.browser_support.palette_regression import PaletteFixtureCase
    from tools.render_review.browser_support.render_review import (
        apply_review_cell_states,
        apply_review_topology_payload,
        assert_canvas_centered_within_viewport,
        canvas_visual_summary,
        reset_review_state,
        sample_review_cell_pixel,
        select_tiling_family,
        wait_for_patch_render_complete,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.browser_support.bootstrap import WaitUntilState
    from tests.e2e.support_runtime_host import BrowserRuntimeHost
    from tests.e2e.support_server import JsonApiClient
    from tools.render_review.browser_support.diagnostics import GridSummary, parse_grid_summary_text
    from tools.render_review.browser_support.palette_regression import PaletteFixtureCase
    from tools.render_review.browser_support.render_review import (
        apply_review_cell_states,
        apply_review_topology_payload,
        assert_canvas_centered_within_viewport,
        canvas_visual_summary,
        reset_review_state,
        sample_review_cell_pixel,
        select_tiling_family,
        wait_for_patch_render_complete,
    )


class SharedUiFlowCase(Protocol):
    page_viewport: ClassVar[ViewportSize | None]
    page: Any
    host: BrowserRuntimeHost
    api: JsonApiClient | None

    def goto_page(
        self,
        url: str,
        *,
        wait_until: WaitUntilState | None = None,
        timeout: float | None = None,
    ) -> Response | None: ...

    def reload_page(
        self,
        *,
        wait_until: WaitUntilState | None = None,
        timeout: float | None = None,
    ) -> Response | None: ...

    def addCleanup(self, function: Any, /, *args: Any, **kwargs: Any) -> None: ...
    def assertEqual(self, first: Any, second: Any, msg: str | None = None) -> None: ...
    def assertNotEqual(self, first: Any, second: Any, msg: str | None = None) -> None: ...
    def assertTrue(self, expr: Any, msg: str | None = None) -> None: ...
    def assertGreater(self, first: Any, second: Any, msg: str | None = None) -> None: ...
    def assertGreaterEqual(self, first: Any, second: Any, msg: str | None = None) -> None: ...
    def assertLessEqual(self, first: Any, second: Any, msg: str | None = None) -> None: ...


class SharedUiFlowHelpers:
    def _case(self) -> SharedUiFlowCase:
        return cast(SharedUiFlowCase, self)

    def initialize_shared_ui_flow(self) -> None:
        case = self._case()
        case.goto_page(f"{case.host.base_url}/", wait_until="load")
        self._ensure_drawer_open()

    def _expect(self, selector: str) -> Any:
        case = self._case()
        return cast(Any, expect(case.page.locator(selector)))

    def _ensure_drawer_open(self) -> None:
        case = self._case()
        if case.page.locator("#control-drawer").get_attribute("data-open") != "true":
            case.page.click("#drawer-toggle-btn")
            self._expect("#control-drawer").to_have_attribute("data-open", "true")

    def _read_generation(self) -> int:
        case = self._case()
        return int((case.page.locator("#generation-text").text_content() or "0").strip())

    def _grid_summary(self) -> GridSummary:
        case = self._case()
        return parse_grid_summary_text(case.page.locator("#grid-size-text").text_content())

    def _click_canvas_center(self) -> None:
        case = self._case()
        canvas = case.page.locator("#grid")
        case.page.wait_for_function(
            """() => {
                const value = Number(document.getElementById("grid")?.getAttribute("data-render-cell-size") || "0");
                return Number.isFinite(value) && value > 0;
            }""",
        )
        render_cell_size_text = canvas.get_attribute("data-render-cell-size")
        if render_cell_size_text is None:
            raise AssertionError("canvas did not report a rendered cell size")
        render_cell_size = float(render_cell_size_text)
        if render_cell_size <= 0:
            raise AssertionError(
                f"canvas reported an invalid rendered cell size: {render_cell_size_text!r}"
            )

        grid_summary = self._grid_summary()
        if (
            grid_summary.kind != "regular"
            or grid_summary.width is None
            or grid_summary.height is None
        ):
            raise AssertionError(f"grid summary did not describe a regular board: {grid_summary!r}")

        gap = 0 if render_cell_size <= 6 else 1
        pitch = render_cell_size + gap
        target_x = gap + ((grid_summary.width // 2) * pitch) + (render_cell_size / 2)
        target_y = gap + ((grid_summary.height // 2) * pitch) + (render_cell_size / 2)
        canvas.click(position={"x": target_x, "y": target_y})

    def _paint_canvas_center(self) -> None:
        self._click_canvas_center()
        self._expect("#canvas-toolbar-undo-btn").to_be_enabled()

    def _wait_for_standalone_persisted_snapshot(
        self,
        *,
        expected_rule: str,
        expected_cells_by_id: dict[str, int],
    ) -> None:
        case = self._case()
        case.page.wait_for_function(
            """async ({ expectedRule, expectedCellsById, databaseName, objectStoreName, snapshotKey, localStorageKey }) => {
                const matchesSnapshot = (value) => {
                    if (!value || typeof value !== "object") {
                        return false;
                    }
                    const cellsById = value.cells_by_id;
                    if (!cellsById || typeof cellsById !== "object") {
                        return false;
                    }
                    return (
                        value.rule === expectedRule &&
                        JSON.stringify(cellsById) === JSON.stringify(expectedCellsById)
                    );
                };

                const localStorageRaw = window.localStorage.getItem(localStorageKey);
                if (localStorageRaw) {
                    try {
                        if (matchesSnapshot(JSON.parse(localStorageRaw))) {
                            return true;
                        }
                    } catch {
                        // Ignore malformed localStorage payloads while waiting for persistence.
                    }
                }

                if (typeof window.indexedDB === "undefined") {
                    return false;
                }

                const indexedDbValue = await new Promise((resolve) => {
                    const openRequest = window.indexedDB.open(databaseName, 1);
                    openRequest.onerror = () => resolve(null);
                    openRequest.onsuccess = () => {
                        const database = openRequest.result;
                        if (!database.objectStoreNames.contains(objectStoreName)) {
                            resolve(null);
                            return;
                        }
                        const transaction = database.transaction(objectStoreName, "readonly");
                        const store = transaction.objectStore(objectStoreName);
                        const getRequest = store.get(snapshotKey);
                        getRequest.onerror = () => resolve(null);
                        getRequest.onsuccess = () => resolve(getRequest.result ?? null);
                    };
                });

                return matchesSnapshot(indexedDbValue);
            }""",
            arg={
                "expectedRule": expected_rule,
                "expectedCellsById": expected_cells_by_id,
                "databaseName": "cellular-automaton-lab-standalone",
                "objectStoreName": "runtime",
                "snapshotKey": "snapshot-v5",
                "localStorageKey": "cellular-automaton-lab-standalone-state-v5",
            },
        )

    def _canvas_visual_summary(self) -> dict[str, object]:
        case = self._case()
        return cast(dict[str, object], canvas_visual_summary(case.page))

    def _assert_canvas_centered_within_viewport(
        self,
        *,
        maximum_vertical_gap_delta: float = 4.0,
        maximum_horizontal_gap_delta: float = 4.0,
    ) -> None:
        case = self._case()
        assert_canvas_centered_within_viewport(
            case.page,
            maximum_vertical_gap_delta=maximum_vertical_gap_delta,
            maximum_horizontal_gap_delta=maximum_horizontal_gap_delta,
        )

    def _wait_for_patch_render_complete(self) -> None:
        case = self._case()
        wait_for_patch_render_complete(case.page)

    def _apply_review_topology(self, topology_payload: dict[str, object]) -> None:
        case = self._case()
        apply_review_topology_payload(case.page, topology_payload)
        wait_for_patch_render_complete(case.page)

    def _apply_review_cell_states(
        self, review_cell_states: dict[str, int] | list[dict[str, object]]
    ) -> None:
        case = self._case()
        apply_review_cell_states(case.page, review_cell_states)
        case.page.wait_for_timeout(75)

    def _reset_review_state(self) -> None:
        case = self._case()
        reset_review_state(case.page)
        wait_for_patch_render_complete(case.page)

    def _sample_review_cell_pixel(self, cell_id: str) -> tuple[int, int, int, int] | None:
        case = self._case()
        return sample_review_cell_pixel(case.page, cell_id)

    def _sample_canvas_pixel_rgba(
        self, canvas_x: float, canvas_y: float
    ) -> tuple[int, int, int, int]:
        case = self._case()
        rgba = case.page.evaluate(
            """([x, y]) => {
                const canvas = document.getElementById("grid");
                if (!(canvas instanceof HTMLCanvasElement)) {
                    throw new Error("grid canvas is missing");
                }
                const context = canvas.getContext("2d");
                if (!context) {
                    throw new Error("grid context is missing");
                }
                const data = context.getImageData(Math.round(x), Math.round(y), 1, 1).data;
                return Array.from(data);
            }""",
            [canvas_x, canvas_y],
        )
        if not isinstance(rgba, list) or len(rgba) != 4:
            raise AssertionError(
                f"canvas pixel sampling returned an invalid RGBA payload: {rgba!r}"
            )
        red, green, blue, alpha = (int(channel) for channel in rgba)
        return (red, green, blue, alpha)

    def _click_canvas_position(self, canvas_x: float, canvas_y: float) -> None:
        case = self._case()
        bbox = case.page.locator("#grid").bounding_box()
        if bbox is None:
            raise AssertionError("grid canvas bounding box was unavailable")
        canvas_metrics = case.page.evaluate(
            """() => {
                const canvas = document.getElementById("grid");
                if (!(canvas instanceof HTMLCanvasElement)) {
                    throw new Error("grid canvas is missing");
                }
                return { width: canvas.width, height: canvas.height };
            }""",
        )
        if not isinstance(canvas_metrics, dict):
            raise AssertionError("grid canvas metrics were unavailable")
        canvas_width = float(canvas_metrics.get("width") or 0)
        canvas_height = float(canvas_metrics.get("height") or 0)
        if canvas_width <= 0 or canvas_height <= 0:
            raise AssertionError(f"grid canvas metrics were invalid: {canvas_metrics!r}")
        css_x = bbox["x"] + (canvas_x * (bbox["width"] / canvas_width))
        css_y = bbox["y"] + (canvas_y * (bbox["height"] / canvas_height))
        case.page.mouse.click(css_x, css_y)

    def _set_paint_state(self, state_value: int) -> None:
        case = self._case()
        case.page.locator(f'.paint-state-button[data-state-value="{state_value}"]').click()

    def _set_editor_tool(self, editor_tool: str) -> None:
        case = self._case()
        case.page.locator(f'[data-editor-tool="{editor_tool}"]').click()

    def _patch_depth_input_state(self) -> dict[str, str | None]:
        case = self._case()
        state = case.page.evaluate(
            """() => {
                const input = document.getElementById("patch-depth-input");
                if (!(input instanceof HTMLInputElement)) {
                    throw new Error("patch depth input is missing");
                }
                return {
                    min: input.min,
                    max: input.max,
                    value: input.value,
                };
            }""",
        )
        if not isinstance(state, dict):
            raise AssertionError(f"patch depth input state was invalid: {state!r}")
        return cast(dict[str, str | None], state)

    def _select_tiling_family_and_wait_for_reset(
        self,
        tiling_family: str,
        *,
        timeout_ms: int = 60_000,
    ) -> None:
        case = self._case()
        status_code = select_tiling_family(
            case.page,
            tiling_family,
            expect_reset_request=case.api is not None,
            timeout_ms=timeout_ms,
        )
        if status_code is not None:
            case.assertEqual(status_code, 200)

    def _wait_for_canvas_visual_patch(
        self,
        *,
        minimum_fill_colors: int,
        minimum_coverage_width_ratio: float,
        minimum_coverage_height_ratio: float,
    ) -> None:
        case = self._case()
        case.page.wait_for_function(
            """({ minimumFillColors, minimumCoverageWidthRatio, minimumCoverageHeightRatio }) => {
                const canvas = document.getElementById("grid");
                if (!(canvas instanceof HTMLCanvasElement)) {
                    return false;
                }
                const context = canvas.getContext("2d");
                if (!context) {
                    return false;
                }
                const overlay = document.getElementById("blocking-activity-overlay");
                if (overlay instanceof HTMLElement && !overlay.hidden) {
                    return false;
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

                const dominantCount = Array.from(dominantFillColors.values()).filter((count) => count >= 100).length;
                const coverageWidthRatio = maxX >= minX ? (maxX - minX + 1) / width : 0;
                const coverageHeightRatio = maxY >= minY ? (maxY - minY + 1) / height : 0;
                return dominantCount >= minimumFillColors
                    && coverageWidthRatio > minimumCoverageWidthRatio
                    && coverageHeightRatio > minimumCoverageHeightRatio;
            }""",
            arg={
                "minimumFillColors": minimum_fill_colors,
                "minimumCoverageWidthRatio": minimum_coverage_width_ratio,
                "minimumCoverageHeightRatio": minimum_coverage_height_ratio,
            },
        )

    def _assert_browser_visible_aperiodic_patch(
        self,
        *,
        minimum_fill_colors: int,
        minimum_coverage_width_ratio: float = 0.75,
        minimum_coverage_height_ratio: float = 0.75,
    ) -> None:
        self._wait_for_patch_render_complete()
        self._wait_for_canvas_visual_patch(
            minimum_fill_colors=minimum_fill_colors,
            minimum_coverage_width_ratio=minimum_coverage_width_ratio,
            minimum_coverage_height_ratio=minimum_coverage_height_ratio,
        )
        case = self._case()
        summary = self._canvas_visual_summary()
        dominant_fill_colors = cast(list[list[object]], summary["dominantFillColors"])
        coverage_width_ratio = cast(float, summary["coverageWidthRatio"])
        coverage_height_ratio = cast(float, summary["coverageHeightRatio"])
        case.assertGreater(coverage_width_ratio, minimum_coverage_width_ratio)
        case.assertGreater(coverage_height_ratio, minimum_coverage_height_ratio)
        case.assertGreaterEqual(len(dominant_fill_colors), minimum_fill_colors)

    def _assert_fixture_dead_cells_do_not_alias_live_canvas_color(
        self,
        fixture_case: PaletteFixtureCase,
    ) -> None:
        case = self._case()
        topology = cast(dict[str, object], fixture_case["topology"])
        cells = cast(list[dict[str, object]], topology["cells"])
        selector_fields = fixture_case["selector_fields"]

        self._select_tiling_family_and_wait_for_reset(fixture_case["family"])
        self._expect("#tiling-family-select").to_have_value(fixture_case["family"])
        self._apply_review_topology(topology)

        try:

            def _coerce_center_coordinate(center: dict[str, object], axis: str) -> float:
                value = center.get(axis)
                if isinstance(value, (int, float)):
                    return float(value)
                raise AssertionError(f"cell center axis {axis!r} was not numeric: {center!r}")

            centers = [
                (
                    _coerce_center_coordinate(cast(dict[str, object], cell["center"]), "x"),
                    _coerce_center_coordinate(cast(dict[str, object], cell["center"]), "y"),
                )
                for cell in cells
                if isinstance(cell.get("center"), dict)
            ]
            mean_x = sum(point[0] for point in centers) / len(centers)
            mean_y = sum(point[1] for point in centers) / len(centers)

            grouped_candidates: dict[str, list[dict[str, object]]] = {}
            for cell in cells:
                center = cell.get("center")
                if not isinstance(center, dict):
                    continue
                signature_parts = []
                for field in selector_fields:
                    value = cell.get(field)
                    signature_parts.append(str(value or "<missing>"))
                signature = ":".join(signature_parts) if signature_parts else "__default__"
                grouped_candidates.setdefault(signature, []).append(cell)

            representative_cells: dict[str, dict[str, object]] = {}
            for signature, candidates in grouped_candidates.items():
                candidates.sort(
                    key=lambda cell: (
                        (
                            _coerce_center_coordinate(cast(dict[str, object], cell["center"]), "x")
                            - mean_x
                        )
                        ** 2
                        + (
                            _coerce_center_coordinate(cast(dict[str, object], cell["center"]), "y")
                            - mean_y
                        )
                        ** 2
                    ),
                )
                for candidate in candidates:
                    sampled_pixel = self._sample_review_cell_pixel(str(candidate["id"]))
                    if sampled_pixel is None:
                        continue
                    representative_cells[signature] = candidate
                    break

            case.assertTrue(
                representative_cells,
                f"{fixture_case['family']} fixture did not yield any representative palette samples",
            )

            dead_samples: dict[str, tuple[int, int, int, int]] = {}
            for signature, cell in representative_cells.items():
                sampled_pixel = self._sample_review_cell_pixel(str(cell["id"]))
                if sampled_pixel is None:
                    raise AssertionError(
                        f"{fixture_case['family']} sample {signature} did not resolve to a rendered pixel"
                    )
                dead_samples[signature] = sampled_pixel

            self._apply_review_cell_states(
                [{"id": str(cell["id"]), "state": 1} for cell in representative_cells.values()],
            )

            live_samples: dict[str, tuple[int, int, int, int]] = {}
            for signature, cell in representative_cells.items():
                sampled_pixel = self._sample_review_cell_pixel(str(cell["id"]))
                if sampled_pixel is None:
                    raise AssertionError(
                        f"{fixture_case['family']} sample {signature} did not resolve to a rendered pixel after live-state injection",
                    )
                live_samples[signature] = sampled_pixel

            canonical_live_sample = next(iter(live_samples.values()))
            for signature in sorted(representative_cells):
                case.assertEqual(
                    live_samples[signature],
                    canonical_live_sample,
                    f"{fixture_case['family']} sample {signature} did not paint to the canonical live canvas color",
                )
                case.assertNotEqual(
                    dead_samples[signature],
                    canonical_live_sample,
                    f"{fixture_case['family']} sample {signature} dead-state canvas color aliased the live canvas color",
                )
        finally:
            self._reset_review_state()

    def _export_pattern_payload(self) -> dict[str, object]:
        case = self._case()
        with case.page.expect_download() as download_info:
            case.page.locator("#export-pattern-btn").evaluate("(node) => node.click()")
        download = download_info.value
        download_path = download.path()
        if download_path is None:
            raise AssertionError("pattern export did not produce a readable download")
        return json.loads(Path(download_path).read_text(encoding="utf-8"))

    def _write_clipboard_text(self, text: str) -> None:
        case = self._case()
        case.page.evaluate("(nextText) => navigator.clipboard.writeText(nextText)", text)

    def _read_clipboard_text(self) -> str:
        case = self._case()
        return str(case.page.evaluate("() => navigator.clipboard.readText()"))
