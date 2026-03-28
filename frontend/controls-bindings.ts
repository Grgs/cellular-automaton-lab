import { bindChromeControls } from "./controls/chrome-bindings.js";
import { bindDisclosureAndShortcutControls } from "./controls/disclosure-bindings.js";
import { bindEditorAndPatternControls } from "./controls/editor-pattern-bindings.js";
import { bindSimulationControls } from "./controls/simulation-bindings.js";
import type { AppActionSet } from "./types/actions.js";
import type { DomElements } from "./types/dom.js";
import type { ControlBindingTimerOptions } from "./controls/binding-options.js";

export function bindControls(
    elements: DomElements,
    actions: AppActionSet,
    timerOptions: ControlBindingTimerOptions = {},
): void {
    bindSimulationControls(elements, actions, timerOptions);
    bindEditorAndPatternControls(elements, actions);
    bindChromeControls(elements, actions);
    bindDisclosureAndShortcutControls(elements, actions);
}
