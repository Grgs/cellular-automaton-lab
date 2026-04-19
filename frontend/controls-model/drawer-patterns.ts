import type { ResolvedPresetSelection, RuleDefinition } from "../types/domain.js";
import type { AppState } from "../types/state.js";
import type { DrawerPatternViewModel } from "../types/ui.js";

export function buildDrawerPatternViewModel({
    state,
    activeRule,
    paletteRule,
    presetSelection,
}: {
    state: AppState;
    activeRule: RuleDefinition | null;
    paletteRule: RuleDefinition | null;
    presetSelection: ResolvedPresetSelection;
}): DrawerPatternViewModel {
    const supportsRandomize = Boolean(paletteRule && paletteRule.supports_randomize);
    const presetOptions = presetSelection.presetOptions;
    const presetSeedAvailable = presetOptions.length > 0;
    const exportPatternDisabled = !activeRule || !state.topology;
    const presetHelperText = presetSeedAvailable
        ? "Loads a curated seed for this rule and board."
        : "No curated preset is available for this rule/topology yet.";

    return {
        randomResetVisible: supportsRandomize,
        randomResetDisabled: !supportsRandomize,
        randomResetTitle: supportsRandomize
            ? ""
            : "Random reset is only available for rules that define random state weights.",
        presetSeedLabel: "Preset Seed",
        presetSeedDisabled: !presetSeedAvailable,
        presetSeedTitle: presetSeedAvailable
            ? "Reset the grid and load a curated preset seed for the selected rule."
            : "No preset seed is available for the selected rule at the current grid size.",
        presetHelperText,
        presetSeedOptions: presetOptions,
        presetSeedValue: presetSelection.selectedPresetId,
        presetSeedSelectVisible: presetOptions.length > 1,
        importPatternLabel: "Import Pattern",
        importPatternTitle: "Load a saved JSON pattern file into the simulation.",
        copyPatternLabel: "Copy Pattern",
        copyPatternDisabled: exportPatternDisabled,
        copyPatternTitle: exportPatternDisabled
            ? "Patterns can be copied after the simulation finishes loading. If clipboard access fails, use Export Pattern."
            : "Copy a JSON pattern for the current board to the clipboard. If clipboard access fails, use Export Pattern.",
        exportPatternLabel: "Export Pattern",
        exportPatternDisabled,
        exportPatternTitle: exportPatternDisabled
            ? "Patterns can be exported after the simulation finishes loading."
            : "Download a JSON pattern file for the current board.",
        pastePatternLabel: "Paste Pattern",
        pastePatternDisabled: false,
        pastePatternTitle: "Read a JSON pattern from the clipboard and load it into the simulation. If clipboard access fails, use Import Pattern.",
    };
}
