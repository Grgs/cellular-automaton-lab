import { beforeEach, describe, expect, it, vi } from "vitest";

import { DRAG_GESTURE_FLASH_DURATION_MS } from "./constants.js";
import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type { SimulationSnapshot } from "../types/domain.js";
import type { AppState } from "../types/state.js";

function createIndexedState(currentStates: number[]): AppState {
    return {
        topologyIndex: {
            byId: new Map([
                ["c:0:0", { id: "c:0:0", index: 0 }],
                ["c:1:0", { id: "c:1:0", index: 1 }],
            ]),
        },
        cellStates: currentStates,
        undoStack: [],
        redoStack: [],
    } as unknown as AppState;
}

describe("interactions/legacy-drag", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("uses an explicit gesture target state for every cell in the drag commit", async () => {
        const { createLegacyDragController } = await import("./legacy-drag.js");
        const state = createIndexedState([7, 3]);
        const previewPaintCells = vi.fn();
        const clearPreview = vi.fn();
        const setGestureOutline = vi.fn();
        const flashGestureOutline = vi.fn();
        const clearGestureOutline = vi.fn();
        const setCellsRequest = vi.fn().mockResolvedValue({ ok: true } as unknown as SimulationSnapshot);
        const runStateMutation = vi.fn(async (task: () => Promise<SimulationSnapshot>) => task());
        const renderControlPanel = vi.fn();
        const setPointerCapture = vi.fn();
        const releasePointerCapture = vi.fn();
        const enableClickSuppression = vi.fn();

        const legacyDrag = createLegacyDragController({
            state,
            getPaintState: () => 4,
            previewPaintCells,
            clearPreview,
            setGestureOutline,
            flashGestureOutline,
            clearGestureOutline,
            setCellsRequest,
            runStateMutation,
            renderControlPanel,
            setPointerCapture,
            releasePointerCapture,
            enableClickSuppression,
        });

        legacyDrag.begin({ id: "c:0:0", x: 0, y: 0, state: 7 }, 11, 0);
        legacyDrag.update({ id: "c:1:0", x: 1, y: 0, state: 3 });
        await legacyDrag.end();

        expect(previewPaintCells).toHaveBeenCalled();
        expect(setGestureOutline).toHaveBeenCalledWith([
            { id: "c:0:0", x: 0, y: 0, state: 0 },
            { id: "c:1:0", x: 1, y: 0, state: 0 },
        ], "erase");
        expect(setCellsRequest).toHaveBeenCalledWith([
            { id: "c:0:0", x: 0, y: 0, state: 0 },
            { id: "c:1:0", x: 1, y: 0, state: 0 },
        ]);
        expect(flashGestureOutline).toHaveBeenCalledWith([
            { id: "c:0:0", x: 0, y: 0, state: 0 },
            { id: "c:1:0", x: 1, y: 0, state: 0 },
        ], "erase", DRAG_GESTURE_FLASH_DURATION_MS);
        expect(clearGestureOutline).toHaveBeenCalledTimes(1);
        expect(enableClickSuppression).toHaveBeenCalledTimes(1);
        expect(clearPreview).toHaveBeenCalledTimes(1);
        expect(state.undoStack).toEqual([
            {
                forwardCells: [
                    { id: "c:0:0", state: 0 },
                    { id: "c:1:0", state: 0 },
                ],
                inverseCells: [
                    { id: "c:0:0", state: 7 },
                    { id: "c:1:0", state: 3 },
                ],
            },
        ]);
        expect(renderControlPanel).toHaveBeenCalledTimes(1);
    });

    it("cancels without committing or flashing when the pointer is canceled", async () => {
        const { createLegacyDragController } = await import("./legacy-drag.js");
        const setCellsRequest = vi.fn().mockResolvedValue(null);
        const flashGestureOutline = vi.fn();
        const clearGestureOutline = vi.fn();
        const clearPreview = vi.fn();

        const legacyDrag = createLegacyDragController({
            getPaintState: () => 1,
            previewPaintCells: vi.fn(),
            clearPreview,
            setGestureOutline: vi.fn(),
            flashGestureOutline,
            clearGestureOutline,
            setCellsRequest,
            runStateMutation: vi.fn(async (task: () => Promise<SimulationSnapshot>) => task()),
            setPointerCapture: vi.fn(),
            releasePointerCapture: vi.fn(),
            enableClickSuppression: vi.fn(),
        });

        legacyDrag.begin({ id: "c:0:0", x: 0, y: 0 }, 12, 1);
        legacyDrag.update({ id: "c:1:0", x: 1, y: 0 });
        await legacyDrag.cancel();

        expect(setCellsRequest).not.toHaveBeenCalled();
        expect(flashGestureOutline).not.toHaveBeenCalled();
        expect(clearGestureOutline).toHaveBeenCalled();
        expect(clearPreview).toHaveBeenCalled();
    });
});
