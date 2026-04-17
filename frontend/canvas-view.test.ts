import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DRAG_GESTURE_FLASH_DURATION_MS } from "./interactions/constants.js";
import { installFrontendGlobals } from "./test-helpers/bootstrap.js";
import type { TopologyPayload } from "./types/domain.js";

const BASE_METRICS = {
    geometry: "square",
    width: 1,
    height: 1,
    cellSize: 12,
    gap: 0,
    cssWidth: 12,
    cssHeight: 12,
    xInset: 0,
    yInset: 0,
    pixelWidth: 12,
    pixelHeight: 12,
    dpr: 1,
};

function topologyPayload(): TopologyPayload {
    return {
        cells: [{
            id: "square:0:0",
            kind: "cell",
            neighbors: [],
        } as TopologyPayload["cells"][number]],
        topology_revision: "test:topology",
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 1,
            height: 1,
            patch_depth: 0,
        },
        width: 1,
        height: 1,
    };
}

function polygonTopologyPayload(): TopologyPayload {
    return {
        cells: [
            {
                id: "shield:a",
                kind: "kite",
                orientation_token: "0",
                neighbors: ["shield:b"],
                center: { x: 0, y: 0 },
                vertices: [
                    { x: -1, y: -1 },
                    { x: 1, y: -1 },
                    { x: 1, y: 1 },
                    { x: -1, y: 1 },
                ],
            },
            {
                id: "shield:b",
                kind: "dart",
                orientation_token: "120",
                neighbors: ["shield:a", "shield:c"],
                center: { x: 3, y: 0 },
                vertices: [
                    { x: 2, y: -1 },
                    { x: 4, y: -1 },
                    { x: 4, y: 1 },
                    { x: 2, y: 1 },
                ],
            },
            {
                id: "shield:c",
                kind: "kite",
                orientation_token: "240",
                neighbors: ["shield:b"],
                center: { x: 7, y: 0 },
                vertices: [
                    { x: 6, y: -1 },
                    { x: 8, y: -1 },
                    { x: 8, y: 1 },
                    { x: 6, y: 1 },
                ],
            },
        ],
        topology_revision: "test:shield:topology",
        topology_spec: {
            tiling_family: "shield",
            adjacency_mode: "edge",
            sizing_mode: "patch_depth",
            width: 3,
            height: 1,
            patch_depth: 3,
        },
        width: 3,
        height: 1,
    };
}

describe("canvas-view", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installFrontendGlobals();
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it("redraws transient layers for hover changes without redrawing the committed layer", async () => {
        const drawCommittedLayer = vi.fn();
        const drawHoverLayer = vi.fn();
        const drawSelectionLayer = vi.fn();
        const drawPreviewLayer = vi.fn();
        const drawGestureOutlineLayer = vi.fn();
        const restoreCommittedSurface = vi.fn();

        vi.doMock("./canvas/surface.js", () => ({
            createCanvasSurface: () => ({
                context: {} as CanvasRenderingContext2D,
                committedCanvas: document.createElement("canvas"),
                committedContext: {} as CanvasRenderingContext2D,
                resize: () => ({ ...BASE_METRICS }),
                restoreCommittedSurface,
            }),
        }));
        vi.doMock("./canvas/render-layers.js", () => ({
            drawCommittedLayer,
            drawHoverLayer,
            drawSelectionLayer,
            drawPreviewLayer,
            drawGestureOutlineLayer,
        }));
        vi.doMock("./geometry/registry.js", () => ({
            getGeometryAdapter: () => ({
                buildMetrics: () => ({ ...BASE_METRICS }),
                family: "regular",
            }),
            isSupportedGeometry: () => true,
        }));
        vi.doMock("./canvas/cache.js", () => ({
            resolveGeometryCache: () => ({ cacheKey: "cache", geometryCache: null }),
        }));
        vi.doMock("./canvas/render-style.js", () => ({
            DEFAULT_COLORS: {
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
            },
            buildStateColorLookup: () => new Map([[0, "#f8f1e5"]]),
            readCanvasColors: () => ({
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
            }),
            resolveCanvasRenderStyle: () => ({
                mode: "standard",
                geometry: "square",
                lineColorToken: "lineSoft",
                triangleStrokeEnabled: false,
                lineColor: "rgba(31, 36, 48, 0.10)",
                aperiodicLineColor: "rgba(31, 36, 48, 0.24)",
                hoverTintColor: "rgba(31, 36, 48, 0.20)",
                hoverStrokeColor: "#1f2430",
                selectionTintColor: "rgba(191, 90, 54, 0.16)",
                selectionStrokeColor: "#8a3d20",
                gesturePaintStrokeColor: "#8a3d20",
                gestureEraseStrokeColor: "rgba(31, 36, 48, 0.24)",
            }),
            resolveDeadCellColor: vi.fn(),
            resolveRenderedCellColor: () => "#f8f1e5",
            resolveRenderDetailLevel: vi.fn(),
            resolveRenderStyle: vi.fn(),
            resolveStateColor: vi.fn(),
        }));

        const { createCanvasGridView } = await import("./canvas-view.js");
        const canvas = document.createElement("canvas");
        const view = createCanvasGridView({ canvas });

        view.render(
            {
                topology: topologyPayload(),
                cellStates: [0],
                previewCellStatesById: null,
            },
            12,
            [],
            "square",
        );

        expect(drawCommittedLayer).toHaveBeenCalledTimes(1);
        expect(drawHoverLayer).not.toHaveBeenCalled();

        const restoreCallsAfterRender = restoreCommittedSurface.mock.calls.length;
        view.setHoveredCell({ id: "square:0:0", x: 0, y: 0 });

        expect(drawCommittedLayer).toHaveBeenCalledTimes(1);
        expect(restoreCommittedSurface).toHaveBeenCalledTimes(restoreCallsAfterRender + 1);
        expect(drawHoverLayer).toHaveBeenCalledTimes(1);

        view.setHoveredCell({ id: "square:0:0", x: 0, y: 0 });

        expect(drawHoverLayer).toHaveBeenCalledTimes(1);

        view.setPreviewCells([{ id: "square:0:0", x: 0, y: 0, state: 1 }]);

        expect(drawHoverLayer).toHaveBeenCalledTimes(2);
        expect(drawHoverLayer.mock.invocationCallOrder.at(-1)).toBeLessThan(
            drawPreviewLayer.mock.invocationCallOrder.at(-1) ?? Number.POSITIVE_INFINITY,
        );

        view.setGestureOutline([{ id: "square:0:0", x: 0, y: 0 }], "paint");

        expect(drawGestureOutlineLayer).toHaveBeenCalledTimes(1);
        expect(drawPreviewLayer.mock.invocationCallOrder.at(-1)).toBeLessThan(
            drawGestureOutlineLayer.mock.invocationCallOrder.at(-1) ?? Number.POSITIVE_INFINITY,
        );

        const restoreCallsBeforeClear = restoreCommittedSurface.mock.calls.length;
        view.setHoveredCell(null);

        expect(restoreCommittedSurface).toHaveBeenCalledTimes(restoreCallsBeforeClear + 1);
        expect(drawHoverLayer).toHaveBeenCalledTimes(3);

        view.setSelectedCells([{ id: "square:0:0", x: 0, y: 0 }]);

        expect(drawCommittedLayer).toHaveBeenCalledTimes(1);
        expect(drawSelectionLayer).toHaveBeenCalledTimes(1);
        expect(view.getSelectedCells()).toEqual([{ id: "square:0:0", x: 0, y: 0 }]);

        view.setSelectedCells([{ id: "square:0:0", x: 0, y: 0 }]);

        expect(drawSelectionLayer).toHaveBeenCalledTimes(1);

        view.flashGestureOutline(
            [{ id: "square:0:0", x: 0, y: 0 }],
            "erase",
            DRAG_GESTURE_FLASH_DURATION_MS,
        );

        expect(drawGestureOutlineLayer.mock.calls.length).toBeGreaterThanOrEqual(2);

        vi.advanceTimersByTime(DRAG_GESTURE_FLASH_DURATION_MS + 1);

        expect(restoreCommittedSurface.mock.calls.length).toBeGreaterThan(restoreCallsBeforeClear);
        const gestureCallsBeforeRevisionChange = drawGestureOutlineLayer.mock.calls.length;

        view.render(
            {
                topology: {
                    ...topologyPayload(),
                    topology_revision: "test:topology:next",
                },
                cellStates: [0],
                previewCellStatesById: null,
            },
            12,
            [],
            "square",
        );

        expect(view.getSelectedCells()).toEqual([]);
        expect(drawGestureOutlineLayer).toHaveBeenCalledTimes(gestureCallsBeforeRevisionChange);
    });

    it("centers presentation-only canvases inside larger viewports without centering backend-synced grids", async () => {
        const resize = vi.fn(() => ({ ...BASE_METRICS, cssWidth: 120, cssHeight: 60 }));

        vi.doMock("./canvas/surface.js", () => ({
            createCanvasSurface: () => ({
                context: {} as CanvasRenderingContext2D,
                committedCanvas: document.createElement("canvas"),
                committedContext: {} as CanvasRenderingContext2D,
                resize,
                restoreCommittedSurface: vi.fn(),
            }),
        }));
        vi.doMock("./canvas/render-layers.js", () => ({
            drawCommittedLayer: vi.fn(),
            drawHoverLayer: vi.fn(),
            drawSelectionLayer: vi.fn(),
            drawPreviewLayer: vi.fn(),
            drawGestureOutlineLayer: vi.fn(),
        }));
        vi.doMock("./geometry/registry.js", () => ({
            getGeometryAdapter: () => ({
                buildMetrics: () => ({ ...BASE_METRICS, cssWidth: 120, cssHeight: 60 }),
                family: "mixed",
            }),
            isSupportedGeometry: () => true,
        }));
        vi.doMock("./canvas/cache.js", () => ({
            resolveGeometryCache: () => ({ cacheKey: "cache", geometryCache: null }),
        }));
        vi.doMock("./topology-catalog.js", async () => {
            const actual = await vi.importActual<typeof import("./topology-catalog.js")>("./topology-catalog.js");
            return {
                ...actual,
                topologyUsesBackendViewportSync: (spec: { tiling_family?: string } | null | undefined) => (
                    String(spec?.tiling_family) === "square"
                ),
            };
        });
        vi.doMock("./canvas/render-style.js", () => ({
            DEFAULT_COLORS: {
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
            },
            buildStateColorLookup: () => new Map([[0, "#f8f1e5"]]),
            readCanvasColors: () => ({
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
            }),
            resolveCanvasRenderStyle: () => ({
                mode: "standard",
                geometry: "square",
                lineColorToken: "lineSoft",
                triangleStrokeEnabled: false,
                lineColor: "rgba(31, 36, 48, 0.10)",
                aperiodicLineColor: "rgba(31, 36, 48, 0.24)",
                hoverTintColor: "rgba(31, 36, 48, 0.20)",
                hoverStrokeColor: "#1f2430",
                selectionTintColor: "rgba(191, 90, 54, 0.16)",
                selectionStrokeColor: "#8a3d20",
                gesturePaintStrokeColor: "#8a3d20",
                gestureEraseStrokeColor: "rgba(31, 36, 48, 0.24)",
            }),
            resolveDeadCellColor: vi.fn(),
            resolveRenderedCellColor: () => "#f8f1e5",
            resolveRenderDetailLevel: vi.fn(),
            resolveRenderStyle: vi.fn(),
            resolveStateColor: vi.fn(),
        }));

        const { createCanvasGridView } = await import("./canvas-view.js");
        const viewport = document.createElement("div");
        const canvas = document.createElement("canvas");
        viewport.append(canvas);
        document.body.append(viewport);
        Object.defineProperty(viewport, "clientWidth", { configurable: true, value: 220 });
        Object.defineProperty(viewport, "clientHeight", { configurable: true, value: 160 });

        const view = createCanvasGridView({ canvas });

        view.render(
            {
                topology: {
                    ...topologyPayload(),
                    topology_spec: {
                        ...topologyPayload().topology_spec,
                        tiling_family: "pinwheel",
                    },
                },
                cellStates: [0],
                previewCellStatesById: null,
            },
            12,
            [],
            "pinwheel",
        );

        expect(canvas.style.margin).toBe("50px");

        view.render(
            {
                topology: topologyPayload(),
                cellStates: [0],
                previewCellStatesById: null,
            },
            12,
            [],
            "square",
        );

        expect(canvas.style.margin).toBe("0px");
    });

    it("exposes deterministic render diagnostics for polygon topologies", async () => {
        const topology = polygonTopologyPayload();
        const cellsById = new Map(
            topology.cells.map((cell, index) => [
                cell.id,
                {
                    cell,
                    vertices: [],
                    centerX: 20 + (index * 30),
                    centerY: 70,
                    minX: 10 + (index * 30),
                    maxX: 30 + (index * 30),
                    minY: 60,
                    maxY: 80,
                },
            ]),
        );

        vi.doMock("./canvas/surface.js", () => ({
            createCanvasSurface: () => ({
                context: {} as CanvasRenderingContext2D,
                committedCanvas: document.createElement("canvas"),
                committedContext: {} as CanvasRenderingContext2D,
                resize: () => ({
                    ...BASE_METRICS,
                    geometry: "shield",
                    width: 3,
                    height: 1,
                    cssWidth: 300,
                    cssHeight: 140,
                    xInset: 20,
                    yInset: 70,
                    pixelWidth: 300,
                    pixelHeight: 140,
                    scale: 10,
                    coordinateScale: 0.35,
                }),
                restoreCommittedSurface: vi.fn(),
            }),
        }));
        vi.doMock("./canvas/render-layers.js", () => ({
            drawCommittedLayer: vi.fn(),
            drawHoverLayer: vi.fn(),
            drawSelectionLayer: vi.fn(),
            drawPreviewLayer: vi.fn(),
            drawGestureOutlineLayer: vi.fn(),
        }));
        vi.doMock("./geometry/registry.js", () => ({
            getGeometryAdapter: () => ({
                geometry: "shield",
                buildMetrics: () => ({
                    ...BASE_METRICS,
                    geometry: "shield",
                    width: 3,
                    height: 1,
                    cssWidth: 300,
                    cssHeight: 140,
                    xInset: 20,
                    yInset: 70,
                    scale: 10,
                    coordinateScale: 0.35,
                }),
                family: "mixed",
            }),
            isSupportedGeometry: () => true,
        }));
        vi.doMock("./canvas/cache.js", () => ({
            resolveGeometryCache: () => ({
                cacheKey: "polygon-cache",
                geometryCache: {
                    type: "shield",
                    strokePath: null,
                    cells: [],
                    cellsById,
                },
            }),
        }));
        vi.doMock("./canvas/render-style.js", () => ({
            DEFAULT_COLORS: {
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
            },
            buildStateColorLookup: () => new Map([[0, "#f8f1e5"]]),
            readCanvasColors: () => ({
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
            }),
            resolveCanvasRenderStyle: () => ({
                mode: "standard",
                geometry: "shield",
                lineColorToken: "lineSoft",
                triangleStrokeEnabled: false,
                lineColor: "rgba(31, 36, 48, 0.10)",
                aperiodicLineColor: "rgba(31, 36, 48, 0.24)",
                hoverTintColor: "rgba(31, 36, 48, 0.20)",
                hoverStrokeColor: "#1f2430",
                selectionTintColor: "rgba(191, 90, 54, 0.16)",
                selectionStrokeColor: "#8a3d20",
                gesturePaintStrokeColor: "#8a3d20",
                gestureEraseStrokeColor: "rgba(31, 36, 48, 0.24)",
            }),
            resolveDeadCellColor: vi.fn(),
            resolveRenderedCellColor: () => "#f8f1e5",
            resolveRenderDetailLevel: vi.fn(),
            resolveRenderStyle: vi.fn(),
            resolveStateColor: vi.fn(),
        }));

        const { createCanvasGridView } = await import("./canvas-view.js");
        const canvas = document.createElement("canvas");
        const view = createCanvasGridView({ canvas });

        view.render(
            {
                topology,
                cellStates: [0, 0, 0],
                previewCellStatesById: null,
            },
            12,
            [],
            "shield",
        );

        const diagnostics = view.getRenderDiagnostics();
        expect(diagnostics?.adapterFamily).toBe("mixed");
        expect(diagnostics?.renderMetrics.coordinateScale).toBe(0.35);
        expect(diagnostics?.sampleCells.lexicographicFirst?.cellId).toBe("shield:a");
        expect(diagnostics?.sampleCells.centerNearest?.cellId).toBe("shield:b");
        expect(diagnostics?.sampleCells.boundaryFurthest?.cellId).toBe("shield:c");
        expect(diagnostics?.topologyBounds?.width).toBe(9);
        expect(diagnostics?.metricInputs.renderedCellCount).toBe(3);
        expect(diagnostics?.metricInputs.orientationTokenCounts).toEqual({
            "0": 1,
            "120": 1,
            "240": 1,
        });
        expect(diagnostics?.metricInputs.angularSectorCounts).toEqual([2, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]);
        expect(diagnostics?.overlapHotspots?.sampledOverlapCount).toBe(0);
    });
});
