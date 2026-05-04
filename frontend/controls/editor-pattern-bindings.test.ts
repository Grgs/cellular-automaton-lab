import { describe, expect, it, vi } from "vitest";

import { bindEditorAndPatternControls } from "./editor-pattern-bindings.js";
import type { AppActionSet } from "../types/actions.js";
import type { DomElements } from "../types/dom.js";

function createActions(): AppActionSet {
    return {
        toggleRun: vi.fn(),
        step: vi.fn(),
        reset: vi.fn(),
        randomReset: vi.fn(),
        changeSpeed: vi.fn(),
        changeRule: vi.fn(),
        changeTilingFamily: vi.fn(),
        changeAdjacencyMode: vi.fn(),
        changePatchDepth: vi.fn(),
        commitPatchDepth: vi.fn(),
        openPatternImport: vi.fn(),
        importPatternFile: vi.fn(),
        exportPattern: vi.fn(),
        copyPattern: vi.fn(),
        pastePattern: vi.fn(),
        copyShareLink: vi.fn(),
        applyShareLinkFromHash: vi.fn(),
        loadPresetSeed: vi.fn(),
        changePresetSeedSelection: vi.fn(),
        loadShowcaseDemo: vi.fn(),
        setCellSize: vi.fn(),
        commitCellSize: vi.fn(),
        setUnsafeSizingEnabled: vi.fn(),
        setTileColorsEnabled: vi.fn(),
        setPaintState: vi.fn(),
        setEditorTool: vi.fn(),
        setBrushSize: vi.fn(),
        toggleDrawer: vi.fn(),
        closeDrawer: vi.fn(),
        dismissOverlays: vi.fn(),
        handleTopBarEmptyClick: vi.fn(),
        handleInspectorEmptyClick: vi.fn(),
        handleWorkspaceEmptyClick: vi.fn(),
        setDisclosureState: vi.fn(),
        toggleTheme: vi.fn(),
        resetAllSettings: vi.fn(),
        undoEdit: vi.fn(),
        redoEdit: vi.fn(),
        cancelEditorPreview: vi.fn(),
        enterEditMode: vi.fn(),
        exitEditMode: vi.fn(),
    };
}

describe("controls/editor-pattern-bindings", () => {
    it("binds the erase button to state 0", () => {
        const eraseBtn = document.createElement("button");
        const elements = {
            presetSeedSelect: null,
            paintPalette: null,
            editorTools: null,
            brushSizeControls: null,
            eraseBtn,
            presetSeedBtn: null,
            importPatternBtn: null,
            copyPatternBtn: null,
            exportPatternBtn: null,
            pastePatternBtn: null,
            shareLinkBtn: null,
            patternImportInput: null,
            undoBtn: null,
            redoBtn: null,
        } as Partial<DomElements> as DomElements;
        const actions = createActions();

        bindEditorAndPatternControls(elements, actions);
        eraseBtn.click();

        expect(actions.setPaintState).toHaveBeenCalledWith(0);
    });
});
