import { describe, expect, it, vi } from "vitest";

import { bindControlShortcuts } from "./controls-shortcuts.js";
import type { AppActionSet } from "./types/actions.js";

function createActions(overrides: Partial<AppActionSet> = {}): AppActionSet {
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
        ...overrides,
    };
}

describe("controls-shortcuts", () => {
    it("maps E to erase by selecting state 0", () => {
        const actions = createActions();
        const documentNode = document.implementation.createHTMLDocument();

        bindControlShortcuts(actions, { documentNode });
        documentNode.dispatchEvent(new KeyboardEvent("keydown", { key: "e", bubbles: true }));

        expect(actions.setPaintState).toHaveBeenCalledWith(0);
    });
});
