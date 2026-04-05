import { describe, expect, it, vi } from "vitest";

import { createLegacyDragController } from "./legacy-drag.js";
import type { SimulationSnapshot } from "../types/domain.js";

describe("interactions/legacy-drag", () => {
    it("uses an explicit gesture target state for every cell in the drag commit", async () => {
        const previewPaintCells = vi.fn();
        const clearPreview = vi.fn();
        const setCellsRequest = vi.fn().mockResolvedValue(null);
        const runStateMutation = vi.fn(async (task: () => Promise<SimulationSnapshot>) => task());
        const setPointerCapture = vi.fn();
        const releasePointerCapture = vi.fn();
        const enableClickSuppression = vi.fn();

        const legacyDrag = createLegacyDragController({
            getPaintState: () => 4,
            previewPaintCells,
            clearPreview,
            setCellsRequest,
            runStateMutation,
            setPointerCapture,
            releasePointerCapture,
            enableClickSuppression,
        });

        legacyDrag.begin({ id: "c:0:0", x: 0, y: 0, state: 7 }, 11, 0);
        legacyDrag.update({ id: "c:1:0", x: 1, y: 0, state: 3 });
        await legacyDrag.end();

        expect(previewPaintCells).toHaveBeenCalled();
        expect(setCellsRequest).toHaveBeenCalledWith([
            { id: "c:0:0", x: 0, y: 0, state: 0 },
            { id: "c:1:0", x: 1, y: 0, state: 0 },
        ]);
        expect(enableClickSuppression).toHaveBeenCalledTimes(1);
        expect(clearPreview).toHaveBeenCalledTimes(1);
    });
});
