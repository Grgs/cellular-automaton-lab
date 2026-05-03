import { describe, expect, it } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

describe("controls-model/editor", () => {
    it("describes unarmed direct painting as applying the selected paint state", async () => {
        installFrontendGlobals();
        const { createAppState } = await import("../state/simulation-state.js");
        const { buildEditorViewModel } = await import("./editor.js");
        const state = createAppState();
        state.selectedEditorTool = "brush";
        state.brushSize = 1;
        state.editArmed = true;
        state.editCueVisible = true;

        const viewModel = buildEditorViewModel({
            state,
        });

        expect(viewModel.canvasEditCueText).toBe(
            "Edit mode active. Click or drag to paint. Unarmed click or drag applies the selected paint state.",
        );
    });
});
