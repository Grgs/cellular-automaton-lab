import { getDefaultPresetId, listAvailablePresets } from "./presets.js";
import { currentTopologyVariantKey, getSelectedPresetId } from "./state/simulation-state.js";
import { currentDimensions, currentEditorRule } from "./state/selectors.js";
import type { ResolvedPresetSelection } from "./types/domain.js";
import type { AppState } from "./types/state.js";

export function buildPresetSelection(state: AppState): ResolvedPresetSelection {
    const rule = currentEditorRule(state);
    const { width, height } = currentDimensions(state);
    const ruleName = rule?.name ?? "";
    const topologyVariantKey = currentTopologyVariantKey(state);
    const presetOptions = listAvailablePresets(ruleName, topologyVariantKey, width, height);
    const defaultPresetId = getDefaultPresetId(ruleName, topologyVariantKey, width, height);
    const storedPresetId = getSelectedPresetId(state, ruleName);
    const selectedPresetId = presetOptions.some((preset) => preset.id === storedPresetId)
        ? storedPresetId
        : defaultPresetId;

    return {
        rule,
        ruleName,
        geometry: topologyVariantKey,
        width,
        height,
        presetOptions,
        defaultPresetId,
        selectedPresetId,
        presetId: selectedPresetId,
    };
}

export function resolveRequestedPresetSelection(
    state: AppState,
    requestedPresetId: string | null | undefined,
): ResolvedPresetSelection {
    const selection = buildPresetSelection(state);
    if (selection.presetOptions.length === 0) {
        return {
            ...selection,
            presetId: null,
        };
    }
    if (
        requestedPresetId
        && selection.presetOptions.some((preset) => preset.id === requestedPresetId)
    ) {
        return {
            ...selection,
            presetId: requestedPresetId,
        };
    }
    return {
        ...selection,
        presetId: selection.selectedPresetId,
    };
}
