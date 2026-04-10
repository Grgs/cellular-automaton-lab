import { describe, expect, it, vi } from "vitest";

import { createTransientOverlayController } from "./transient-overlays.js";
import { DRAG_GESTURE_FLASH_DURATION_MS } from "../interactions/constants.js";
import type { TopologyPayload } from "../types/domain.js";

function topology(cellIds: string[], revision = "rev-1"): TopologyPayload {
    return {
        topology_revision: revision,
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 1,
            height: 1,
            patch_depth: 0,
        },
        cells: cellIds.map((id) => ({ id, kind: "cell", neighbors: [] })),
        width: 1,
        height: 1,
    };
}

describe("canvas/transient-overlays", () => {
    it("no-ops repeated hover, selection, and gesture outline updates", () => {
        const onChange = vi.fn();
        const overlays = createTransientOverlayController({
            onChange,
            setTimeoutFn: vi.fn(() => 1),
            clearTimeoutFn: vi.fn(),
        });

        overlays.setHoveredCell({ id: "cell:a" });
        overlays.setHoveredCell({ id: "cell:a" });
        overlays.setSelectedCells([{ id: "cell:a" }]);
        overlays.setSelectedCells([{ id: "cell:a" }]);
        overlays.setGestureOutline([{ id: "cell:a" }], "paint");
        overlays.setGestureOutline([{ id: "cell:a" }], "paint");

        expect(onChange).toHaveBeenCalledTimes(3);
    });

    it("returns selected cell copies instead of mutable internal state", () => {
        const overlays = createTransientOverlayController({
            onChange: vi.fn(),
            setTimeoutFn: vi.fn(() => 1),
            clearTimeoutFn: vi.fn(),
        });

        overlays.setSelectedCells([{ id: "cell:a", x: 1 }]);
        const selectedCells = overlays.getSelectedCells();
        selectedCells[0]!.x = 99;

        expect(overlays.getSelectedCells()).toEqual([{ id: "cell:a", x: 1 }]);
    });

    it("hides hover for the currently selected cell", () => {
        const overlays = createTransientOverlayController({
            onChange: vi.fn(),
            setTimeoutFn: vi.fn(() => 1),
            clearTimeoutFn: vi.fn(),
        });

        overlays.setSelectedCells([{ id: "cell:a" }]);
        overlays.setHoveredCell({ id: "cell:a" });

        expect(overlays.snapshot().hoveredCell).toBeNull();
    });

    it("clears flashed gesture outlines after the configured duration", () => {
        vi.useFakeTimers();
        const onChange = vi.fn();
        const overlays = createTransientOverlayController({
            onChange,
            setTimeoutFn: (callback, delay) => window.setTimeout(callback, delay),
            clearTimeoutFn: (timerId) => window.clearTimeout(timerId),
        });

        overlays.flashGestureOutline([{ id: "cell:a" }], "erase", DRAG_GESTURE_FLASH_DURATION_MS);

        expect(overlays.snapshot().gestureOutlineCells).toEqual([{ id: "cell:a" }]);

        vi.advanceTimersByTime(DRAG_GESTURE_FLASH_DURATION_MS + 1);

        expect(overlays.snapshot().gestureOutlineCells).toEqual([]);
        expect(overlays.snapshot().gestureOutlineTone).toBeNull();
        expect(onChange).toHaveBeenCalledTimes(2);
        vi.useRealTimers();
    });

    it("clears selection and gesture outline when topology revision changes", () => {
        const overlays = createTransientOverlayController({
            onChange: vi.fn(),
            setTimeoutFn: vi.fn(() => 1),
            clearTimeoutFn: vi.fn(),
        });

        overlays.reconcileForRender(topology(["cell:a"], "rev-1"));
        overlays.setSelectedCells([{ id: "cell:a" }]);
        overlays.setGestureOutline([{ id: "cell:a" }], "paint");

        overlays.reconcileForRender(topology(["cell:a"], "rev-2"));

        expect(overlays.getSelectedCells()).toEqual([]);
        expect(overlays.snapshot().gestureOutlineCells).toEqual([]);
    });

    it("filters selected cells and clears outlines that disappear from the topology", () => {
        const overlays = createTransientOverlayController({
            onChange: vi.fn(),
            setTimeoutFn: vi.fn(() => 1),
            clearTimeoutFn: vi.fn(),
        });

        overlays.reconcileForRender(topology(["cell:a", "cell:b"], "rev-1"));
        overlays.setSelectedCells([{ id: "cell:a" }, { id: "cell:b" }]);
        overlays.setGestureOutline([{ id: "cell:b" }], "paint");

        overlays.reconcileForRender(topology(["cell:a"], "rev-1"));

        expect(overlays.getSelectedCells()).toEqual([{ id: "cell:a" }]);
        expect(overlays.snapshot().gestureOutlineCells).toEqual([]);
    });
});
