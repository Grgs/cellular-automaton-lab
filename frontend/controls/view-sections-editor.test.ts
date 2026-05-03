import { describe, expect, it } from "vitest";

import { renderEditorAndPatternSections } from "./view-sections.js";
import type { DomElements } from "../types/dom.js";
import type { ControlsViewModel } from "../types/ui.js";

function createElements(): DomElements {
    return {
        unsafeSizingField: document.createElement("div"),
        unsafeSizingToggle: document.createElement("input"),
        editorTools: document.createElement("div"),
        brushSizeControls: document.createElement("div"),
        eraseBtn: document.createElement("button"),
        undoBtn: document.createElement("button"),
        redoBtn: document.createElement("button"),
        editorShortcutHint: document.createElement("p"),
        importPatternBtn: document.createElement("button"),
        copyPatternBtn: document.createElement("button"),
        exportPatternBtn: document.createElement("button"),
        pastePatternBtn: document.createElement("button"),
        patternStatus: document.createElement("p"),
        paintPalette: document.createElement("div"),
        themeToggleBtn: null,
    } as Partial<DomElements> as DomElements;
}

function createViewModel(selectedPaintState: number | null): ControlsViewModel {
    return {
        unsafeSizingEnabled: false,
        editorTools: [{ value: "brush", label: "Brush" }],
        selectedEditorTool: "brush",
        brushSizeOptions: [{ value: 1, label: "1" }],
        selectedBrushSize: 1,
        undoDisabled: true,
        redoDisabled: true,
        editorShortcutHint: "hint",
        gridEditMode: "idle",
        canvasEditCueVisible: false,
        canvasEditCueText: "",
        importPatternLabel: "Import Pattern",
        importPatternTitle: "Import",
        copyPatternLabel: "Copy Pattern",
        copyPatternDisabled: false,
        copyPatternTitle: "Copy",
        exportPatternLabel: "Export Pattern",
        exportPatternDisabled: false,
        exportPatternTitle: "Export",
        pastePatternLabel: "Paste Pattern",
        pastePatternDisabled: false,
        pastePatternTitle: "Paste",
        patternStatusText: "",
        patternStatusTone: "info",
        paletteStates: [
            { value: 0, label: "Dead", color: "#000000" },
            { value: 1, label: "Live", color: "#ffffff" },
        ],
        selectedPaintState,
        theme: "dark",
    } as Partial<ControlsViewModel> as ControlsViewModel;
}

describe("controls/view-sections editor", () => {
    it("marks erase as selected when state 0 is active", () => {
        const elements = createElements();

        renderEditorAndPatternSections(elements, createViewModel(0));

        expect(elements.eraseBtn?.hidden).toBe(false);
        expect(elements.eraseBtn?.textContent).toBe("Erase");
        expect(elements.eraseBtn?.getAttribute("aria-pressed")).toBe("true");
        expect(elements.eraseBtn?.classList.contains("is-selected")).toBe(true);
        expect(elements.eraseBtn?.title).toBe("Select Dead for erasing.");
    });

    it("hides erase until a paint state is available", () => {
        const elements = createElements();

        renderEditorAndPatternSections(elements, createViewModel(null));

        expect(elements.eraseBtn?.hidden).toBe(true);
        expect(elements.eraseBtn?.disabled).toBe(true);
    });
});
