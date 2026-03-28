import { bindControlShortcuts } from "./controls-shortcuts.js";
import { parseEditorTool } from "./parsers/editor.js";
import { DISCLOSURE_IDS } from "./ui-session.js";
import type { AppActionSet } from "./types/actions.js";
import type { BrowserClearTimeout, BrowserSetTimeout, BrowserTimerId } from "./types/controller.js";
import type { SimulationSnapshot } from "./types/domain.js";
import type { DomElements } from "./types/dom.js";
import type { UiDisclosureId } from "./types/session.js";

const INTERACTIVE_CHROME_SELECTOR = [
    "button",
    "input",
    "select",
    "textarea",
    "label",
    "summary",
    "a[href]",
    "[role='button']",
    "[role='link']",
    "[contenteditable='true']",
].join(", ");

function eventTargetElement(event: Event): Element | null {
    return event.target instanceof Element ? event.target : null;
}

function isInteractiveChromeClick(event: Event, container: HTMLElement | null): boolean {
    const target = eventTargetElement(event);
    if (!target || !container || !container.contains(target)) {
        return false;
    }
    return Boolean(target.closest(INTERACTIVE_CHROME_SELECTOR));
}

const LIMIT_CUE_DURATION_MS = 1800;
type MaybePromise<TResult> = TResult | Promise<TResult>;
type AsyncControlResult = MaybePromise<boolean | void | null | SimulationSnapshot>;
type AsyncButtonResult = MaybePromise<boolean | void | null | SimulationSnapshot>;

function parseNumericConstraint(value: string): number | null {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
}

function rangeLimitMessage(input: HTMLInputElement | null): string {
    if (!input) {
        return "";
    }
    const rawValue = String(input.value ?? "").trim();
    if (rawValue === "") {
        return "";
    }
    const value = Number(rawValue);
    if (!Number.isFinite(value)) {
        return "";
    }
    const minimum = parseNumericConstraint(input.min);
    const maximum = parseNumericConstraint(input.max);
    if (minimum !== null && value < minimum) {
        return maximum !== null
            ? `Allowed: ${minimum}-${maximum}.`
            : `Minimum: ${minimum}.`;
    }
    if (maximum !== null && value > maximum) {
        return minimum !== null
            ? `Allowed: ${minimum}-${maximum}.`
            : `Maximum: ${maximum}.`;
    }
    return "";
}

function stepBoundaryLimitMessage(
    input: HTMLInputElement | null,
    direction: "up" | "down" | null,
): string {
    if (!input || (direction !== "up" && direction !== "down")) {
        return "";
    }
    const rawValue = String(input.value ?? "").trim();
    if (rawValue === "") {
        return "";
    }
    const value = Number(rawValue);
    if (!Number.isFinite(value)) {
        return "";
    }
    const minimum = parseNumericConstraint(input.min);
    const maximum = parseNumericConstraint(input.max);
    if (direction === "up" && maximum !== null && value >= maximum) {
        return minimum !== null
            ? `Allowed: ${minimum}-${maximum}.`
            : `Maximum: ${maximum}.`;
    }
    if (direction === "down" && minimum !== null && value <= minimum) {
        return maximum !== null
            ? `Allowed: ${minimum}-${maximum}.`
            : `Minimum: ${minimum}.`;
    }
    return "";
}

function stepDirectionFromPointer(
    input: HTMLInputElement | null,
    event: PointerEvent,
): "up" | "down" | null {
    if (!input || typeof input.getBoundingClientRect !== "function") {
        return null;
    }
    const rect = input.getBoundingClientRect();
    const spinnerWidth = Math.min(24, Math.max(16, rect.width * 0.3));
    if (event.clientX < rect.right - spinnerWidth) {
        return null;
    }
    return event.clientY <= rect.top + rect.height / 2 ? "up" : "down";
}

function ensureLimitCue(field: HTMLElement | null): HTMLSpanElement | null {
    if (!field) {
        return null;
    }
    let cue = field.querySelector(".top-control-limit-cue") as HTMLSpanElement | null;
    if (cue) {
        return cue;
    }
    cue = document.createElement("span");
    cue.className = "top-control-limit-cue";
    cue.hidden = true;
    cue.setAttribute("aria-live", "polite");
    field.appendChild(cue);
    return cue;
}

function clearLimitCue(
    field: HTMLElement | null,
    input: HTMLInputElement | null,
    _label: HTMLElement | null,
    cueTimeouts: WeakMap<HTMLInputElement, BrowserTimerId>,
    clearTimeoutFn: BrowserClearTimeout,
): void {
    if (!field || !input) {
        return;
    }
    const timeoutId = cueTimeouts.get(input);
    if (timeoutId !== undefined) {
        clearTimeoutFn(timeoutId);
        cueTimeouts.delete(input);
    }
    field.classList.remove("has-limit-cue");
    delete field.dataset.limitCueText;
    input.classList.remove("is-limit-cue");
    input.removeAttribute("aria-invalid");
    const cue = field.querySelector(".top-control-limit-cue") as HTMLSpanElement | null;
    if (cue) {
        cue.hidden = true;
        cue.textContent = "";
    }
}

function showLimitCue(
    field: HTMLElement | null,
    input: HTMLInputElement | null,
    label: HTMLElement | null,
    message: string,
    cueTimeouts: WeakMap<HTMLInputElement, BrowserTimerId>,
    setTimeoutFn: BrowserSetTimeout,
    clearTimeoutFn: BrowserClearTimeout,
): void {
    if (!field || !input || !message) {
        return;
    }
    clearLimitCue(field, input, label, cueTimeouts, clearTimeoutFn);
    const cue = ensureLimitCue(field);
    field.classList.add("has-limit-cue");
    field.dataset.limitCueText = message;
    input.classList.add("is-limit-cue");
    input.setAttribute("aria-invalid", "true");
    if (cue) {
        cue.hidden = false;
        cue.textContent = message;
    }
    const timeoutId = setTimeoutFn(() => {
        clearLimitCue(field, input, label, cueTimeouts, clearTimeoutFn);
    }, LIMIT_CUE_DURATION_MS);
    cueTimeouts.set(input, timeoutId);
}

function bindConstrainedNumericControl({
    input,
    field,
    label,
    onInput,
    onChange,
    cueTimeouts,
    setTimeoutFn,
    clearTimeoutFn,
}: {
    input: HTMLInputElement | null;
    field: HTMLElement | null;
    label: HTMLElement | null;
    onInput?: (value: number) => AsyncControlResult;
    onChange?: (value: number) => AsyncControlResult;
    cueTimeouts: WeakMap<HTMLInputElement, BrowserTimerId>;
    setTimeoutFn: BrowserSetTimeout;
    clearTimeoutFn: BrowserClearTimeout;
}): void {
    if (!input) {
        return;
    }
    const maybeShowCue = () => {
        const message = rangeLimitMessage(input);
        if (message) {
            showLimitCue(field, input, label, message, cueTimeouts, setTimeoutFn, clearTimeoutFn);
            return;
        }
        clearLimitCue(field, input, label, cueTimeouts, clearTimeoutFn);
    };
    if (onInput) {
        input.addEventListener("input", () => {
            const message = rangeLimitMessage(input);
            onInput(Number(input.value));
            if (message) {
                showLimitCue(field, input, label, message, cueTimeouts, setTimeoutFn, clearTimeoutFn);
                return;
            }
            clearLimitCue(field, input, label, cueTimeouts, clearTimeoutFn);
        });
    }
    if (onChange) {
        input.addEventListener("change", () => {
            onChange(Number(input.value));
        });
    }
    input.addEventListener("keydown", (event) => {
        const direction = event.key === "ArrowUp"
            ? "up"
            : (event.key === "ArrowDown" ? "down" : null);
        if (!direction) {
            return;
        }
        const message = stepBoundaryLimitMessage(input, direction);
        if (!message) {
            return;
        }
        showLimitCue(field, input, label, message, cueTimeouts, setTimeoutFn, clearTimeoutFn);
    });
    input.addEventListener("pointerdown", (event) => {
        const direction = stepDirectionFromPointer(input, event);
        if (!direction) {
            return;
        }
        const message = stepBoundaryLimitMessage(input, direction);
        if (!message) {
            return;
        }
        showLimitCue(field, input, label, message, cueTimeouts, setTimeoutFn, clearTimeoutFn);
    });
}

function bindInputControl<TValue>(
    element: HTMLElement | null,
    eventName: "input" | "change",
    valueFactory: () => TValue,
    handler: ((value: TValue) => AsyncControlResult) | undefined,
): void {
    if (!element || !handler) {
        return;
    }
    element.addEventListener(eventName, () => {
        void handler(valueFactory());
    });
}

function bindButtonControl(
    element: HTMLButtonElement | null,
    handler: (() => AsyncButtonResult) | undefined,
): void {
    if (!element || !handler) {
        return;
    }
    element.addEventListener("click", () => {
        void handler();
    });
}

function bindDelegatedControl(
    container: HTMLElement | null,
    selector: string,
    handler: ((button: HTMLElement) => AsyncControlResult) | undefined,
): void {
    if (!container || !handler) {
        return;
    }
    container.addEventListener("click", (event) => {
        if (!(event.target instanceof Element)) {
            return;
        }
        const button = event.target.closest(selector);
        if (!(button instanceof HTMLElement)) {
            return;
        }
        void handler(button);
    });
}

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
        label: elements.cellSizeLabel,
        onInput: actions.setCellSize,
        onChange: actions.commitCellSize,
        cueTimeouts,
        setTimeoutFn,
        clearTimeoutFn,
    });

    bindConstrainedNumericControl({
        input: elements.patchDepthInput,
        field: elements.patchDepthField,
        label: elements.patchDepthLabel,
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
