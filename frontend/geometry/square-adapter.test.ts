import { describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

function createContextStub() {
    const context: Partial<CanvasRenderingContext2D> = {
        fillRect: vi.fn(),
        strokeRect: vi.fn(),
        fillStyle: "",
        strokeStyle: "",
        lineWidth: 0,
    };
    return context as CanvasRenderingContext2D;
}

describe("geometry/square-adapter", () => {
    it("adds a tint and outline for hovered square cells while preserving the base fill", async () => {
        installFrontendGlobals();
        const { squareGeometryAdapter } = await import("./square-adapter.js");
        const context = createContextStub();

        squareGeometryAdapter.drawCell({
            context,
            cell: { id: "square:0:0", x: 0, y: 0 },
            stateValue: 0,
            metrics: {
                geometry: "square",
                width: 1,
                height: 1,
                cellSize: 12,
                gap: 1,
                cssWidth: 14,
                cssHeight: 14,
                xInset: 0,
                yInset: 0,
                pitch: 13,
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
            },
            colorLookup: new Map([[0, "#f8f1e5"], [1, "#1f2430"]]),
            renderStyle: {
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
            },
            renderLayer: "hover",
            resolveRenderedCellColor: () => "#f8f1e5",
        });

        expect(context.fillRect).toHaveBeenCalledTimes(2);
        expect(context.strokeRect).toHaveBeenCalledTimes(1);
        expect(context.strokeStyle).toBe("#1f2430");
        expect(context.fillStyle).toBe("rgba(31, 36, 48, 0.20)");
    });

    it("adds a stronger tint and outline for selected square cells", async () => {
        installFrontendGlobals();
        const { squareGeometryAdapter } = await import("./square-adapter.js");
        const context = createContextStub();

        squareGeometryAdapter.drawCell({
            context,
            cell: { id: "square:0:0", x: 0, y: 0 },
            stateValue: 0,
            metrics: {
                geometry: "square",
                width: 1,
                height: 1,
                cellSize: 12,
                gap: 1,
                cssWidth: 14,
                cssHeight: 14,
                xInset: 0,
                yInset: 0,
                pitch: 13,
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
            },
            colorLookup: new Map([[0, "#f8f1e5"], [1, "#1f2430"]]),
            renderStyle: {
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
            },
            renderLayer: "selected",
            resolveRenderedCellColor: () => "#f8f1e5",
        });

        expect(context.fillRect).toHaveBeenCalledTimes(2);
        expect(context.strokeRect).toHaveBeenCalledTimes(1);
        expect(context.strokeStyle).toBe("#8a3d20");
        expect(context.fillStyle).toBe("rgba(191, 90, 54, 0.16)");
        expect(context.lineWidth).toBe(2.5);
    });

    it("draws a stroke-only outline for gesture paint cells", async () => {
        installFrontendGlobals();
        const { squareGeometryAdapter } = await import("./square-adapter.js");
        const context = createContextStub();

        squareGeometryAdapter.drawCell({
            context,
            cell: { id: "square:0:0", x: 0, y: 0 },
            stateValue: 1,
            metrics: {
                geometry: "square",
                width: 1,
                height: 1,
                cellSize: 12,
                gap: 1,
                cssWidth: 14,
                cssHeight: 14,
                xInset: 0,
                yInset: 0,
                pitch: 13,
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
            },
            colorLookup: new Map([[0, "#f8f1e5"], [1, "#1f2430"]]),
            renderStyle: {
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
            },
            renderLayer: "gesture-paint",
            resolveRenderedCellColor: () => "#1f2430",
        });

        expect(context.fillRect).not.toHaveBeenCalled();
        expect(context.strokeRect).toHaveBeenCalledTimes(1);
        expect(context.strokeStyle).toBe("#8a3d20");
        expect(context.lineWidth).toBe(2.25);
    });
});
