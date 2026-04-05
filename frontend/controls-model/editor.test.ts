import { describe, expect, it } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

describe("controls-model/editor", () => {
    it("describes the split between unarmed first-cell paint or erase and armed painting", async () => {
        installFrontendGlobals();
        const { buildEditorViewModel } = await import("./editor.js");

        const viewModel = buildEditorViewModel({
            state: {
                selectedEditorTool: "brush",
                brushSize: 1,
                isRunning: false,
                overlayRunPending: false,
                editArmed: true,
                editCueVisible: true,
                undoStack: [],
                redoStack: [],
            } as never,
        });

        expect(viewModel.canvasEditCueText).toBe(
            "Edit mode active. Click or drag to paint. Unarmed click or drag paints or erases based on the first cell.",
        );
    });
});
