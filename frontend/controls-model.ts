import { buildPresetSelection } from "./preset-selection.js";
import { currentEditorRule } from "./state/selectors.js";
import { buildDrawerViewModel } from "./controls-model/drawer.js";
import { buildEditorViewModel } from "./controls-model/editor.js";
import { buildTopBarViewModel } from "./controls-model/top-bar.js";
import type { ControlsViewModel, ControlsViewModelInput } from "./types/ui.js";

export function collectConfig(elements: {
    speedInput: HTMLInputElement | null;
    ruleSelect: HTMLSelectElement | null;
}): { speed: number; rule: string } {
    return {
        speed: Number(elements.speedInput?.value ?? 0),
        rule: String(elements.ruleSelect?.value ?? ""),
    };
}

export function buildControlsViewModel({
    state,
    syncState,
    theme,
    selectionInspectorSource,
}: ControlsViewModelInput): ControlsViewModel {
    const activeRule = state.activeRule;
    const paletteRule = currentEditorRule(state) || activeRule;
    const presetSelection = buildPresetSelection(state);

    return {
        ...buildTopBarViewModel({
            state,
            syncState,
            activeRule,
            paletteRule,
        }),
        ...buildDrawerViewModel({
            state,
            syncState,
            activeRule,
            paletteRule,
            presetSelection,
            selectionInspectorSource,
        }),
        ...buildEditorViewModel({ state }),
        theme,
    };
}
