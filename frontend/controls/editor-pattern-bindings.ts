import { bindDelegatedControl, bindInputControl } from "./binding-primitives.js";
import { parseEditorTool } from "../parsers/editor.js";
import type { AppActionSet } from "../types/actions.js";
import type { DomElements } from "../types/dom.js";

export function bindEditorAndPatternControls(elements: DomElements, actions: AppActionSet): void {
    bindInputControl(
        elements.presetSeedSelect,
        "change",
        () => elements.presetSeedSelect!.value,
        actions.changePresetSeedSelection,
    );

    bindDelegatedControl(elements.paintPalette, "[data-state-value]", (button) =>
        actions.setPaintState(Number(button.dataset.stateValue)),
    );
    bindDelegatedControl(elements.editorTools, "[data-editor-tool]", (button) => {
        const editorTool = button.dataset.editorTool;
        if (editorTool) {
            actions.setEditorTool(parseEditorTool(editorTool));
        }
    });
    bindDelegatedControl(elements.brushSizeControls, "[data-brush-size]", (button) =>
        actions.setBrushSize(Number(button.dataset.brushSize)),
    );
    if (elements.eraseBtn && actions.setPaintState) {
        elements.eraseBtn.addEventListener("click", () => {
            actions.setPaintState(0);
        });
    }

    if (elements.presetSeedBtn && actions.loadPresetSeed) {
        elements.presetSeedBtn.addEventListener("click", () => {
            actions.loadPresetSeed(elements.presetSeedSelect?.value || undefined);
        });
    }
    if (elements.importPatternBtn && actions.openPatternImport) {
        elements.importPatternBtn.addEventListener("click", () => {
            actions.openPatternImport();
        });
    }
    if (elements.copyPatternBtn && actions.copyPattern) {
        elements.copyPatternBtn.addEventListener("click", () => {
            void actions.copyPattern();
        });
    }
    if (elements.exportPatternBtn && actions.exportPattern) {
        elements.exportPatternBtn.addEventListener("click", () => {
            void actions.exportPattern();
        });
    }
    if (elements.pastePatternBtn && actions.pastePattern) {
        elements.pastePatternBtn.addEventListener("click", () => {
            void actions.pastePattern();
        });
    }
    if (elements.shareLinkBtn && actions.copyShareLink) {
        elements.shareLinkBtn.addEventListener("click", () => {
            void actions.copyShareLink();
        });
    }
    if (elements.patternImportInput && actions.importPatternFile) {
        const patternImportInput = elements.patternImportInput;
        patternImportInput.addEventListener("change", () => {
            const [file] = Array.from(patternImportInput.files || []);
            if (!file) {
                return;
            }
            void actions.importPatternFile(file);
        });
    }
    if (elements.undoBtn && actions.undoEdit) {
        elements.undoBtn.addEventListener("click", () => {
            void actions.undoEdit();
        });
    }
    if (elements.redoBtn && actions.redoEdit) {
        elements.redoBtn.addEventListener("click", () => {
            void actions.redoEdit();
        });
    }

    if (elements.canvasToolbarHelpBtn && elements.canvasToolbarShortcuts) {
        const helpBtn = elements.canvasToolbarHelpBtn;
        const shortcuts = elements.canvasToolbarShortcuts;
        helpBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const open = shortcuts.hidden;
            shortcuts.hidden = !open;
            helpBtn.setAttribute("aria-expanded", open ? "true" : "false");
            helpBtn.classList.toggle("is-active", open);
        });
        document.addEventListener("click", () => {
            if (!shortcuts.hidden) {
                shortcuts.hidden = true;
                helpBtn.setAttribute("aria-expanded", "false");
                helpBtn.classList.remove("is-active");
            }
        });
    }

    if (elements.canvasToolbarArmBtn && actions.enterEditMode) {
        elements.canvasToolbarArmBtn.addEventListener("click", () => {
            actions.enterEditMode();
        });
    }
    if (elements.canvasToolbarDismissBtn && actions.exitEditMode) {
        elements.canvasToolbarDismissBtn.addEventListener("click", () => {
            actions.exitEditMode();
        });
    }

    bindDelegatedControl(elements.canvasToolbarPalette, "[data-state-value]", (button) =>
        actions.setPaintState(Number(button.dataset.stateValue)),
    );
    bindDelegatedControl(elements.canvasToolbarTools, "[data-editor-tool]", (button) => {
        const editorTool = button.dataset.editorTool;
        if (editorTool) {
            actions.setEditorTool(parseEditorTool(editorTool));
        }
    });
    bindDelegatedControl(elements.canvasToolbarBrush, "[data-brush-size]", (button) =>
        actions.setBrushSize(Number(button.dataset.brushSize)),
    );
    if (elements.canvasToolbarUndoBtn && actions.undoEdit) {
        elements.canvasToolbarUndoBtn.addEventListener("click", () => {
            void actions.undoEdit();
        });
    }
    if (elements.canvasToolbarRedoBtn && actions.redoEdit) {
        elements.canvasToolbarRedoBtn.addEventListener("click", () => {
            void actions.redoEdit();
        });
    }
}
