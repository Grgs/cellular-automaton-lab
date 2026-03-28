import { bindControlShortcuts } from "./controls-shortcuts.js";
import { bindButtonControl, bindDelegatedControl, bindInputControl } from "./controls/binding-primitives.js";
import { bindConstrainedNumericControl } from "./controls/limit-cues.js";
import { eventTargetElement, isInteractiveChromeClick } from "./controls/shell-clicks.js";
import { parseEditorTool } from "./parsers/editor.js";
import { DISCLOSURE_IDS } from "./ui-session.js";
import type { AppActionSet } from "./types/actions.js";
import type { BrowserClearTimeout, BrowserSetTimeout, BrowserTimerId } from "./types/controller.js";
import type { DomElements } from "./types/dom.js";
import type { UiDisclosureId } from "./types/session.js";

export function bindControls(
    elements: DomElements,
    actions: AppActionSet,
    {
        setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
        clearTimeoutFn = (timeoutId) => window.clearTimeout(timeoutId),
    }: {
        setTimeoutFn?: BrowserSetTimeout;
        clearTimeoutFn?: BrowserClearTimeout;
    } = {},
): void {
    const cueTimeouts = new WeakMap<HTMLInputElement, BrowserTimerId>();
    bindInputControl(elements.speedInput, "input", () => Number(elements.speedInput!.value), actions.changeSpeed);
    bindInputControl(
        elements.tilingFamilySelect,
        "change",
        () => elements.tilingFamilySelect!.value,
        actions.changeTilingFamily,
    );
    bindInputControl(
        elements.adjacencyModeSelect,
        "change",
        () => elements.adjacencyModeSelect!.value,
        actions.changeAdjacencyMode,
    );
    bindInputControl(elements.ruleSelect, "change", () => elements.ruleSelect!.value, actions.changeRule);
    bindInputControl(
        elements.presetSeedSelect,
        "change",
        () => elements.presetSeedSelect!.value,
        actions.changePresetSeedSelection,
    );

    bindConstrainedNumericControl({
        input: elements.cellSizeInput,
        field: elements.cellSizeField,
        onInput: actions.setCellSize,
        onChange: actions.commitCellSize,
        cueTimeouts,
        setTimeoutFn,
        clearTimeoutFn,
    });

    bindConstrainedNumericControl({
        input: elements.patchDepthInput,
        field: elements.patchDepthField,
        onInput: actions.changePatchDepth,
        onChange: actions.commitPatchDepth,
        cueTimeouts,
        setTimeoutFn,
        clearTimeoutFn,
    });

    bindButtonControl(elements.themeToggleBtn, actions.toggleTheme);
    bindButtonControl(elements.drawerToggleBtn, actions.toggleDrawer);
    bindButtonControl(elements.runToggleBtn, actions.toggleRun);
    bindButtonControl(elements.stepBtn, actions.step);
    bindButtonControl(elements.resetBtn, actions.reset);
    bindButtonControl(elements.randomBtn, actions.randomReset);
    bindButtonControl(elements.resetAllSettingsBtn, actions.resetAllSettings);

    const showcaseBindings: Array<[HTMLButtonElement | null, string]> = [
        [elements.showcaseWhirlpoolBtn, "whirlpool"],
        [elements.showcaseWireworldBtn, "wireworld"],
        [elements.showcasePenroseBtn, "penrose"],
    ];
    showcaseBindings.forEach(([element, demoId]) => {
        if (!element || !actions.loadShowcaseDemo) {
            return;
        }
        element.addEventListener("click", () => {
            void actions.loadShowcaseDemo(demoId);
        });
    });

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

    if (actions.setDisclosureState) {
        DISCLOSURE_IDS.forEach((id) => {
            const disclosure = elements[id];
            if (!disclosure) {
                return;
            }
            disclosure.addEventListener("toggle", () => {
                actions.setDisclosureState(id as UiDisclosureId, disclosure.open);
            });
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
    if (elements.drawerBackdrop && actions.closeDrawer) {
        elements.drawerBackdrop.addEventListener("click", () => {
            void actions.closeDrawer();
        });
    }
    if (elements.redoBtn && actions.redoEdit) {
        elements.redoBtn.addEventListener("click", () => {
            void actions.redoEdit();
        });
    }

    if (elements.topBar && actions.handleTopBarEmptyClick) {
        elements.topBar.addEventListener("click", (event) => {
            if (isInteractiveChromeClick(event, elements.topBar)) {
                return;
            }
            void actions.handleTopBarEmptyClick();
        });
    }

    if (elements.controlDrawer && actions.handleInspectorEmptyClick) {
        const controlDrawer = elements.controlDrawer;
        controlDrawer.addEventListener("click", (event) => {
            if (controlDrawer.dataset.open !== "true" || controlDrawer.getAttribute("aria-hidden") === "true") {
                return;
            }
            if (isInteractiveChromeClick(event, controlDrawer)) {
                return;
            }
            void actions.handleInspectorEmptyClick();
        });
    }

    if (elements.mainStage && actions.handleWorkspaceEmptyClick) {
        const mainStage = elements.mainStage;
        mainStage.addEventListener("click", (event) => {
            const target = eventTargetElement(event);
            if (!target || !mainStage.contains(target)) {
                return;
            }
            if (elements.controlDrawer?.contains(target)) {
                return;
            }
            if (elements.grid?.contains?.(target) || target === elements.grid) {
                return;
            }
            if (isInteractiveChromeClick(event, mainStage)) {
                return;
            }
            void actions.handleWorkspaceEmptyClick();
        });
    }

    bindControlShortcuts(actions);
}
