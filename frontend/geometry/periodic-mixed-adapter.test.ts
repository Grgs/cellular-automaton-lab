import { beforeEach, describe, expect, it, vi } from "vitest";

import type { PeriodicFaceTilingDescriptor } from "../types/rendering.js";
import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

const SNUB_SQUARE_GEOMETRY = "archimedean-3-3-4-3-4";

function installPeriodicMixedTestGlobals(): void {
    installFrontendGlobals();
    window.APP_PERIODIC_FACE_TILINGS = [
        {
            geometry: SNUB_SQUARE_GEOMETRY,
            label: "Snub Square (3.3.4.3.4)",
            metric_model: "pattern",
            base_edge: 52,
            unit_width: 142,
            unit_height: 142,
            min_dimension: 1,
            min_x: -26,
            min_y: -26,
            max_x: 142,
            max_y: 168,
            cell_count_per_unit: 12,
            row_offset_x: 0,
        },
    ] satisfies PeriodicFaceTilingDescriptor[];
}

function createContextStub() {
    const context: Partial<CanvasRenderingContext2D> = {
        beginPath: vi.fn(),
        moveTo: vi.fn(),
        lineTo: vi.fn(),
        closePath: vi.fn(),
        fill: vi.fn(),
        stroke: vi.fn(),
        fillStyle: "",
        strokeStyle: "",
        lineWidth: 0,
    };
    return context as CanvasRenderingContext2D;
}

describe("geometry/periodic-mixed-adapter", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installPeriodicMixedTestGlobals();
    });

    it("strokes the cached polygon boundary path during overlay rendering", async () => {
        const { createPeriodicMixedGeometryAdapter } = await import("./periodic-mixed-adapter.js");
        const adapter = createPeriodicMixedGeometryAdapter(SNUB_SQUARE_GEOMETRY);
        const context = createContextStub();
        const strokePath = {} as Path2D;

        adapter.drawOverlay?.({
            context,
            width: 0,
            height: 0,
            metrics: {
                geometry: SNUB_SQUARE_GEOMETRY,
                width: 1,
                height: 1,
                cellSize: 10,
                gap: 0,
                cssWidth: 10,
                cssHeight: 10,
                xInset: 1,
                yInset: 1,
            },
            cache: {
                type: SNUB_SQUARE_GEOMETRY,
                cells: [],
                cellsById: new Map(),
                strokePath,
            },
            renderStyle: {
                mode: "standard",
                geometry: SNUB_SQUARE_GEOMETRY,
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
            },
            cellSize: 10,
        });

        expect(context.strokeStyle).toBe("rgba(31, 36, 48, 0.10)");
        expect(context.lineWidth).toBe(1.25);
        expect(context.stroke).toHaveBeenCalledWith(strokePath);
    });

    it("strokes preview cells immediately while keeping committed cell draws fill-only", async () => {
        const { createPeriodicMixedGeometryAdapter } = await import("./periodic-mixed-adapter.js");
        const adapter = createPeriodicMixedGeometryAdapter(SNUB_SQUARE_GEOMETRY);
        const cell = {
            id: "t:0:0",
            kind: "triangle",
            neighbors: [],
            center: { x: 71, y: 15 },
            vertices: [
                { x: 45, y: 0 },
                { x: 71, y: 45 },
                { x: 97, y: 0 },
            ],
        };

        const previewContext = createContextStub();
        adapter.drawCell({
            context: previewContext,
            cell,
            stateValue: 0,
            metrics: {
                geometry: SNUB_SQUARE_GEOMETRY,
                width: 1,
                height: 1,
                cellSize: 10,
                gap: 0,
                cssWidth: 10,
                cssHeight: 10,
                xInset: 1,
                yInset: 1,
                scale: 1,
                baseMinX: 0,
                baseMinY: 0,
                unitWidth: 142,
                unitHeight: 142,
                rowOffsetX: 0,
            },
            cache: null,
            colors: {
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
                toneCream: "#f8f1e5",
                toneLinen: "#ead6b6",
                toneSand: "#efe4d0",
                toneFlax: "#e1cdac",
                toneTan: "#e5c089",
                toneStone: "#d5bb8f",
                toneRose: "#dbc1b2",
                toneClay: "#c88d4b",
                toneShadow: "#b89a6e",
            },
            colorLookup: new Map([[0, "#f8f1e5"], [1, "#1f2430"]]),
            renderStyle: {
                mode: "standard",
                geometry: SNUB_SQUARE_GEOMETRY,
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
            },
            renderLayer: "preview",
            resolveRenderedCellColor: () => "#f8f1e5",
        });

        expect(previewContext.fill).toHaveBeenCalledTimes(1);
        expect(previewContext.stroke).toHaveBeenCalledTimes(1);
        expect(previewContext.strokeStyle).toBe("rgba(31, 36, 48, 0.10)");

        const committedContext = createContextStub();
        adapter.drawCell({
            context: committedContext,
            cell,
            stateValue: 0,
            metrics: {
                geometry: SNUB_SQUARE_GEOMETRY,
                width: 1,
                height: 1,
                cellSize: 10,
                gap: 0,
                cssWidth: 10,
                cssHeight: 10,
                xInset: 1,
                yInset: 1,
                scale: 1,
                baseMinX: 0,
                baseMinY: 0,
                unitWidth: 142,
                unitHeight: 142,
                rowOffsetX: 0,
            },
            cache: null,
            colors: {
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
                toneCream: "#f8f1e5",
                toneLinen: "#ead6b6",
                toneSand: "#efe4d0",
                toneFlax: "#e1cdac",
                toneTan: "#e5c089",
                toneStone: "#d5bb8f",
                toneRose: "#dbc1b2",
                toneClay: "#c88d4b",
                toneShadow: "#b89a6e",
            },
            colorLookup: new Map([[0, "#f8f1e5"], [1, "#1f2430"]]),
            renderStyle: {
                mode: "standard",
                geometry: SNUB_SQUARE_GEOMETRY,
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
            },
            renderLayer: "committed",
            resolveRenderedCellColor: () => "#f8f1e5",
        });

        expect(committedContext.fill).toHaveBeenCalledTimes(1);
        expect(committedContext.stroke).not.toHaveBeenCalled();
    });

    it("applies a tint and stronger stroke for hovered polygon cells", async () => {
        const { createPeriodicMixedGeometryAdapter } = await import("./periodic-mixed-adapter.js");
        const adapter = createPeriodicMixedGeometryAdapter(SNUB_SQUARE_GEOMETRY);
        const context = createContextStub();
        const cell = {
            id: "t:0:0",
            kind: "triangle",
            neighbors: [],
            center: { x: 71, y: 15 },
            vertices: [
                { x: 45, y: 0 },
                { x: 71, y: 45 },
                { x: 97, y: 0 },
            ],
        };

        adapter.drawCell({
            context,
            cell,
            stateValue: 0,
            metrics: {
                geometry: SNUB_SQUARE_GEOMETRY,
                width: 1,
                height: 1,
                cellSize: 10,
                gap: 0,
                cssWidth: 10,
                cssHeight: 10,
                xInset: 1,
                yInset: 1,
                scale: 1,
                baseMinX: 0,
                baseMinY: 0,
                unitWidth: 142,
                unitHeight: 142,
                rowOffsetX: 0,
            },
            cache: null,
            colors: {
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
                toneCream: "#f8f1e5",
                toneLinen: "#ead6b6",
                toneSand: "#efe4d0",
                toneFlax: "#e1cdac",
                toneTan: "#e5c089",
                toneStone: "#d5bb8f",
                toneRose: "#dbc1b2",
                toneClay: "#c88d4b",
                toneShadow: "#b89a6e",
            },
            colorLookup: new Map([[0, "#f8f1e5"], [1, "#1f2430"]]),
            renderStyle: {
                mode: "standard",
                geometry: SNUB_SQUARE_GEOMETRY,
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
            },
            renderLayer: "hover",
            resolveRenderedCellColor: () => "#f8f1e5",
        });

        expect(context.fill).toHaveBeenCalledTimes(2);
        expect(context.stroke).toHaveBeenCalledTimes(1);
        expect(context.strokeStyle).toBe("#1f2430");
        expect(context.fillStyle).toBe("rgba(31, 36, 48, 0.20)");
    });

    it("adds a stronger tint and outline for selected mixed polygons", async () => {
        const { createPeriodicMixedGeometryAdapter } = await import("./periodic-mixed-adapter.js");
        const adapter = createPeriodicMixedGeometryAdapter(SNUB_SQUARE_GEOMETRY);
        const context = createContextStub();
        const cell = {
            id: "triangle:0",
            kind: "triangle",
            center: { x: 71, y: 15 },
            vertices: [
                { x: 45, y: 0 },
                { x: 71, y: 45 },
                { x: 97, y: 0 },
            ],
        };

        adapter.drawCell({
            context,
            cell,
            stateValue: 0,
            metrics: {
                geometry: SNUB_SQUARE_GEOMETRY,
                width: 1,
                height: 1,
                cellSize: 10,
                gap: 0,
                cssWidth: 10,
                cssHeight: 10,
                xInset: 1,
                yInset: 1,
                scale: 1,
                baseMinX: 0,
                baseMinY: 0,
                unitWidth: 142,
                unitHeight: 142,
                rowOffsetX: 0,
            },
            cache: null,
            colors: {
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
                toneCream: "#f8f1e5",
                toneLinen: "#ead6b6",
                toneSand: "#efe4d0",
                toneFlax: "#e1cdac",
                toneTan: "#e5c089",
                toneStone: "#d5bb8f",
                toneRose: "#dbc1b2",
                toneClay: "#c88d4b",
                toneShadow: "#b89a6e",
            },
            colorLookup: new Map([[0, "#f8f1e5"], [1, "#1f2430"]]),
            renderStyle: {
                mode: "standard",
                geometry: SNUB_SQUARE_GEOMETRY,
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
            },
            renderLayer: "selected",
            resolveRenderedCellColor: () => "#f8f1e5",
        });

        expect(context.fill).toHaveBeenCalledTimes(2);
        expect(context.stroke).toHaveBeenCalledTimes(1);
        expect(context.strokeStyle).toBe("#8a3d20");
        expect(context.fillStyle).toBe("rgba(191, 90, 54, 0.16)");
        expect(context.lineWidth).toBe(2.5);
    });

    it("draws a stroke-only outline for erase gesture polygons", async () => {
        const { createPeriodicMixedGeometryAdapter } = await import("./periodic-mixed-adapter.js");
        const adapter = createPeriodicMixedGeometryAdapter(SNUB_SQUARE_GEOMETRY);
        const context = createContextStub();
        const cell = {
            id: "triangle:0",
            kind: "triangle",
            center: { x: 71, y: 15 },
            vertices: [
                { x: 45, y: 0 },
                { x: 71, y: 45 },
                { x: 97, y: 0 },
            ],
        };

        adapter.drawCell({
            context,
            cell,
            stateValue: 1,
            metrics: {
                geometry: SNUB_SQUARE_GEOMETRY,
                width: 1,
                height: 1,
                cellSize: 10,
                gap: 0,
                cssWidth: 10,
                cssHeight: 10,
                xInset: 1,
                yInset: 1,
                scale: 1,
                baseMinX: 0,
                baseMinY: 0,
                unitWidth: 142,
                unitHeight: 142,
                rowOffsetX: 0,
            },
            cache: null,
            colors: {
                line: "rgba(31, 36, 48, 0.16)",
                dead: "#f8f1e5",
                deadAlt: "#d5bb8f",
                lineSoft: "rgba(31, 36, 48, 0.10)",
                lineStrong: "rgba(31, 36, 48, 0.20)",
                lineAperiodic: "rgba(31, 36, 48, 0.24)",
                live: "#1f2430",
                accent: "#bf5a36",
                accentStrong: "#8a3d20",
                toneCream: "#f8f1e5",
                toneLinen: "#ead6b6",
                toneSand: "#efe4d0",
                toneFlax: "#e1cdac",
                toneTan: "#e5c089",
                toneStone: "#d5bb8f",
                toneRose: "#dbc1b2",
                toneClay: "#c88d4b",
                toneShadow: "#b89a6e",
            },
            colorLookup: new Map([[0, "#f8f1e5"], [1, "#1f2430"]]),
            renderStyle: {
                mode: "standard",
                geometry: SNUB_SQUARE_GEOMETRY,
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
            },
            renderLayer: "gesture-erase",
            resolveRenderedCellColor: () => "#1f2430",
        });

        expect(context.fill).not.toHaveBeenCalled();
        expect(context.stroke).toHaveBeenCalledTimes(1);
        expect(context.strokeStyle).toBe("rgba(31, 36, 48, 0.24)");
        expect(context.lineWidth).toBe(2.25);
    });

    it("falls back to transformed bounds when a periodic polygon omits center metadata", async () => {
        const { createPeriodicMixedGeometryAdapter } = await import("./periodic-mixed-adapter.js");
        const adapter = createPeriodicMixedGeometryAdapter(SNUB_SQUARE_GEOMETRY);
        const center = adapter.resolveCellCenter({
            cell: {
                id: "triangle:missing-center",
                kind: "triangle",
                neighbors: [],
                vertices: [
                    { x: 45, y: 0 },
                    { x: 71, y: 45 },
                    { x: 97, y: 0 },
                ],
            },
            width: 1,
            height: 1,
            cellSize: 10,
            topology: null,
            metrics: {
                geometry: SNUB_SQUARE_GEOMETRY,
                width: 1,
                height: 1,
                cellSize: 10,
                gap: 0,
                cssWidth: 10,
                cssHeight: 10,
                xInset: 1,
                yInset: 1,
                scale: 1,
                baseMinX: 0,
                baseMinY: 0,
                unitWidth: 142,
                unitHeight: 142,
                rowOffsetX: 0,
            },
            cache: null,
        });

        expect(center).toEqual({ x: 72, y: 23.5 });
    });
});
