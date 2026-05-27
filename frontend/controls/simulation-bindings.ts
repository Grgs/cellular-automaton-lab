import { bindButtonControl, bindInputControl } from "./binding-primitives.js";
import { bindConstrainedNumericControl } from "./limit-cues.js";
import { bindTilingPreviewPicker } from "./tiling-picker-bindings.js";
import type { AppActionSet } from "../types/actions.js";
import type { DomElements } from "../types/dom.js";
import type { BrowserTimerId } from "../types/controller.js";
import type { ControlBindingTimerOptions } from "./binding-options.js";

export function bindSimulationControls(
    elements: DomElements,
    actions: AppActionSet,
    {
        setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
        clearTimeoutFn = (timeoutId) => window.clearTimeout(timeoutId),
    }: ControlBindingTimerOptions = {},
): void {
    const cueTimeouts = new WeakMap<HTMLInputElement, BrowserTimerId>();

    bindConstrainedNumericControl({
        input: elements.speedInput,
        field: elements.speedField,
        onInput: actions.changeSpeed,
        cueTimeouts,
        setTimeoutFn,
        clearTimeoutFn,
    });
    bindButtonControl(elements.speedDownBtn, () => {
        const input = elements.speedInput;
        if (!input) {
            return;
        }
        const current = Number(input.value);
        const minimum = Number(input.min);
        actions.changeSpeed(Math.max(minimum, (Number.isFinite(current) ? current : minimum) - 1));
    });
    bindButtonControl(elements.speedUpBtn, () => {
        const input = elements.speedInput;
        if (!input) {
            return;
        }
        const current = Number(input.value);
        const maximum = Number(input.max);
        actions.changeSpeed(Math.min(maximum, (Number.isFinite(current) ? current : maximum) + 1));
    });
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
    bindInputControl(
        elements.ruleSelect,
        "change",
        () => elements.ruleSelect!.value,
        actions.changeRule,
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

    bindInputControl(
        elements.unsafeSizingToggle,
        "change",
        () => Boolean(elements.unsafeSizingToggle?.checked),
        actions.setUnsafeSizingEnabled,
    );
    bindInputControl(
        elements.tileColorsToggle,
        "change",
        () => Boolean(elements.tileColorsToggle?.checked),
        actions.setTileColorsEnabled,
    );
    bindTilingPreviewPicker(elements, actions);

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
}
