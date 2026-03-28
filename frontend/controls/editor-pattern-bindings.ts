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

    bindDelegatedControl(
        elements.paintPalette,
        "[data-state-value]",
        (button) => actions.setPaintState(Number(button.dataset.stateValue)),
    );
    bindDelegatedControl(
        elements.editorTools,
        "[data-editor-tool]",
        (button) => {
            const editorTool = button.dataset.editorTool;
            if (editorTool) {
                actions.setEditorTool(parseEditorTool(editorTool));
            }
        },
    );
    bindDelegatedControl(
        elements.brushSizeControls,
        "[data-brush-size]",
        (button) => actions.setBrushSize(Number(button.dataset.brushSize)),
    );

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
}
