import { collectConfig } from "../controls-model.js";
import { applyOverlayIntent, OVERLAY_INTENT_BOARD_REBUILT } from "../overlay-policy.js";
import { describeTopologySpec, resolveTopologyVariantKey } from "../topology-catalog.js";
import { buildPresetSelection, resolveRequestedPresetSelection } from "../preset-selection.js";
import { buildPresetSeed } from "../presets.js";
import { createActionMutationAdapter } from "./shared/mutation-adapter.js";
import {
    clearEditMode,
    setPatternStatus,
    dismissFirstRunHint,
} from "../state/overlay-state.js";
import {
    RULE_SELECTION_ORIGIN_DEFAULT,
} from "../state/constants.js";
import {
    setRuleSelectionOrigin,
    setSelectedPresetId,
} from "../state/simulation-state.js";
import { BLOCKING_ACTIVITY_APPLY_PRESET } from "../blocking-activity.js";
import { indexTopology, presetCellsToTopologyUpdates } from "../topology.js";
import type {
    ActionMutationAdapter,
    PresetActionOptions,
    PresetActionSet,
    PresetSeedBuildRequest,
} from "../types/actions.js";
import type { SimulationMutations } from "../types/controller.js";
import type { CartesianSeedCell, CellStateUpdate, ResolvedPresetSelection, SimulationSnapshot } from "../types/domain.js";

export function createPresetActions({
    state,
    elements,
    interactions,
    applySimulationState,
    postControlFn,
    setCellsRequestFn,
    onError,
    refreshState,
    renderControlPanel,
    simulationMutations = null,
    setSelectedPresetIdFn = setSelectedPresetId,
    setRuleSelectionOriginFn = setRuleSelectionOrigin,
    setPatternStatusFn = setPatternStatus,
    dismissFirstRunHintFn = dismissFirstRunHint,
    buildPresetSelectionFn = buildPresetSelection,
    resolveRequestedPresetSelectionFn = resolveRequestedPresetSelection,
    buildPresetSeedFn = buildPresetSeed,
    presetCellsToTopologyUpdatesFn = presetCellsToTopologyUpdates,
    applyOverlayIntentFn = applyOverlayIntent,
    clearEditModeFn = clearEditMode,
}: PresetActionOptions & {
    setSelectedPresetIdFn?: typeof setSelectedPresetId;
    setRuleSelectionOriginFn?: typeof setRuleSelectionOrigin;
    setPatternStatusFn?: typeof setPatternStatus;
    dismissFirstRunHintFn?: typeof dismissFirstRunHint;
    buildPresetSelectionFn?: typeof buildPresetSelection;
    resolveRequestedPresetSelectionFn?: typeof resolveRequestedPresetSelection;
    buildPresetSeedFn?: (options: PresetSeedBuildRequest) => CartesianSeedCell[];
    presetCellsToTopologyUpdatesFn?: typeof presetCellsToTopologyUpdates;
    applyOverlayIntentFn?: typeof applyOverlayIntent;
    clearEditModeFn?: typeof clearEditMode;
}): PresetActionSet {
    const mutations: ActionMutationAdapter | SimulationMutations = simulationMutations
        || createActionMutationAdapter({ interactions, applySimulationState });

    function applyPresetSelection(nextPresetId: string | null | undefined): void {
        const selection = buildPresetSelectionFn(state);
        if (!selection.rule) {
            return;
        }
        setSelectedPresetIdFn(state, selection.rule.name, nextPresetId ?? null);
        renderControlPanel();
    }

    function loadPresetSeed(
        requestedPresetId: string | null | undefined,
    ): Promise<SimulationSnapshot | null | void> {
        const selection: ResolvedPresetSelection = resolveRequestedPresetSelectionFn(state, requestedPresetId);
        if (!selection.rule || !selection.presetId) {
            return Promise.resolve();
        }
        const selectedRule = selection.rule;
        const presetId = selection.presetId;
        setSelectedPresetIdFn(state, selectedRule.name, presetId);
        dismissFirstRunHintFn(state);
        const overlaysRestored = applyOverlayIntentFn(state, OVERLAY_INTENT_BOARD_REBUILT);
        const editChanged = clearEditModeFn(state);
        if (overlaysRestored || editChanged) {
            renderControlPanel();
        }

        const nextConfig = collectConfig(elements);
        return mutations.runSerialized(
            async () => {
                const resetTopologySpec = describeTopologySpec({
                    ...state.topologySpec,
                    width: selection.width,
                    height: selection.height,
                    patch_depth: state.patchDepth,
                });
                const resetState = await postControlFn("/api/control/reset", {
                    topology_spec: resetTopologySpec,
                    speed: nextConfig.speed,
                    rule: selectedRule.name,
                    randomize: false,
                });
                const resolvedResetState = await mutations.applyRemoteState(
                    resetState,
                    { source: "external" },
                );

                const seededTopologySpec = describeTopologySpec(
                    resolvedResetState.topology_spec || resetTopologySpec,
                );
                const seededGeometry = resolveTopologyVariantKey(
                    seededTopologySpec.tiling_family,
                    seededTopologySpec.adjacency_mode,
                );

                const seedCells = buildPresetSeedFn({
                    ruleName: selectedRule.name,
                    geometry: seededGeometry,
                    width: Number(seededTopologySpec.width) || selection.width,
                    height: Number(seededTopologySpec.height) || selection.height,
                    presetId,
                });
                const resetTopologyIndex = indexTopology(resolvedResetState.topology);
                const topologyUpdates = presetCellsToTopologyUpdatesFn(resetTopologyIndex, seedCells);
                const nextCells: CellStateUpdate[] = topologyUpdates.length > 0 ? topologyUpdates : [];
                if (nextCells.length === 0) {
                    return resolvedResetState;
                }

                const seededState = await setCellsRequestFn(nextCells);
                await mutations.applyRemoteState(seededState, { source: "external" });
                return seededState;
            },
            {
                blockingActivity: BLOCKING_ACTIVITY_APPLY_PRESET,
                onError,
                onRecover: refreshState,
            },
        ).then((result) => {
            const presetLabel = selection.presetOptions.find((preset) => preset.id === presetId)?.label
                || presetId;
            setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_DEFAULT);
            setPatternStatusFn(state, `Loaded ${presetLabel} preset.`, "success");
            renderControlPanel();
            return result;
        }).catch(() => null);
    }

    return {
        loadPresetSeed: (presetId) => loadPresetSeed(presetId),
        changePresetSeedSelection: (presetId) => applyPresetSelection(presetId),
    };
}
