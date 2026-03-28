import { createPatternActions } from "./actions/pattern-actions.js";
import { createPresetActions } from "./actions/preset-actions.js";
import { createShowcaseActions } from "./actions/showcase-actions.js";
import { createSimulationActions } from "./actions/simulation/index.js";
import { createUiActions } from "./actions/ui-actions.js";
import { BLOCKING_ACTIVITY_RESTORE_DEFAULTS } from "./blocking-activity.js";
import { FRONTEND_DEFAULTS } from "./defaults.js";
import {
    buildPatternFilename,
    buildPatternPayload,
    downloadPatternFile,
    parsePatternText,
    readClipboardText,
    readPatternFile,
    serializePatternPayload,
    writeClipboardText,
} from "./pattern-io.js";
import { RULE_SELECTION_ORIGIN_DEFAULT } from "./state/constants.js";
import {
    clearPendingPatchDepth,
    rememberedCellSizeForTilingFamily,
    setCellSize,
    setPatchDepth,
} from "./state/sizing-state.js";
import { dismissFirstRunHint } from "./state/overlay-state.js";
import {
    findRule,
    setActiveRule,
    setEditorRule,
    setRuleSelectionOrigin,
    setSpeed,
    setTopologySpec,
} from "./state/simulation-state.js";
import { resetThemeToDefault } from "./theme.js";
import type {
    ActionMutationAdapter,
    AppActionOptions,
    AppActionSet,
    PatternActionSet,
    PresetActionSet,
    ShowcaseActionSet,
    SimulationActionSet,
    UiActionSet,
} from "./types/actions.js";
import type { SimulationMutations } from "./types/controller.js";
import type { SimulationSnapshot, TopologySpec } from "./types/domain.js";

interface DefaultResetPayload {
    topology_spec: TopologySpec;
    speed: number;
    rule: string;
    randomize: boolean;
}

export function createAppActions({
    state,
    elements,
    interactions,
    viewportController,
    configSyncController,
    uiSessionController,
    renderCurrentGrid,
    renderControlPanel,
    applySimulationState,
    getViewportDimensions,
    postControlFn,
    setCellsRequestFn,
    onError,
    refreshState,
    simulationMutations = null,
    buildPatternPayloadFn = buildPatternPayload,
    serializePatternPayloadFn = serializePatternPayload,
    buildPatternFilenameFn = buildPatternFilename,
    downloadPatternFileFn = downloadPatternFile,
    readPatternFileFn = readPatternFile,
    parsePatternTextFn = parsePatternText,
    readClipboardTextFn = readClipboardText,
    writeClipboardTextFn = writeClipboardText,
    createSimulationActionsFn = createSimulationActions,
    createPresetActionsFn = createPresetActions,
    createShowcaseActionsFn = createShowcaseActions,
    createPatternActionsFn = createPatternActions,
    createUiActionsFn = createUiActions,
    confirmImportFn = (message) => window.confirm(message),
    resetThemeToDefaultFn = resetThemeToDefault,
}: AppActionOptions & {
    buildPatternPayloadFn?: typeof buildPatternPayload;
    serializePatternPayloadFn?: typeof serializePatternPayload;
    buildPatternFilenameFn?: typeof buildPatternFilename;
    downloadPatternFileFn?: typeof downloadPatternFile;
    readPatternFileFn?: typeof readPatternFile;
    parsePatternTextFn?: typeof parsePatternText;
    readClipboardTextFn?: typeof readClipboardText;
    writeClipboardTextFn?: typeof writeClipboardText;
    createSimulationActionsFn?: typeof createSimulationActions;
    createPresetActionsFn?: typeof createPresetActions;
    createShowcaseActionsFn?: typeof createShowcaseActions;
    createPatternActionsFn?: typeof createPatternActions;
    createUiActionsFn?: typeof createUiActions;
    confirmImportFn?: (message: string) => boolean;
    resetThemeToDefaultFn?: typeof resetThemeToDefault;
}): AppActionSet {
    const sharedSimulationMutations: ActionMutationAdapter | SimulationMutations | null = simulationMutations;

    const simulationActions: SimulationActionSet = createSimulationActionsFn({
        state,
        interactions,
        viewportController,
        configSyncController,
        uiSessionController,
        renderControlPanel,
        getViewportDimensions,
    });

    const presetActions: PresetActionSet = createPresetActionsFn({
        state,
        elements,
        interactions,
        applySimulationState,
        postControlFn,
        setCellsRequestFn,
        onError,
        refreshState,
        renderControlPanel,
        simulationMutations: sharedSimulationMutations,
    });

    const patternActions: PatternActionSet = createPatternActionsFn({
        state,
        elements,
        interactions,
        viewportController,
        renderControlPanel,
        applySimulationState,
        postControlFn,
        setCellsRequestFn,
        onError,
        refreshState,
        simulationMutations: sharedSimulationMutations,
        confirmImportFn,
        buildPatternPayloadFn,
        serializePatternPayloadFn,
        buildPatternFilenameFn,
        downloadPatternFileFn,
        readPatternFileFn,
        parsePatternTextFn,
        readClipboardTextFn,
        writeClipboardTextFn,
    });

    const showcaseActions: ShowcaseActionSet = createShowcaseActionsFn({
        state,
        elements,
        interactions,
        applySimulationState,
        postControlFn,
        setCellsRequestFn,
        renderControlPanel,
        refreshState,
        onError,
        getViewportDimensions,
        simulationMutations: sharedSimulationMutations,
    });

    const uiActions: UiActionSet = createUiActionsFn({
        state,
        uiSessionController,
        renderCurrentGrid,
        renderControlPanel,
        viewportController,
    });

    function buildDefaultResetPayload(): DefaultResetPayload {
        return {
            topology_spec: FRONTEND_DEFAULTS.simulation.topology_spec,
            speed: FRONTEND_DEFAULTS.simulation.speed,
            rule: FRONTEND_DEFAULTS.simulation.rule,
            randomize: false,
        };
    }

    function applyDefaultBoardPreview(): void {
        const defaultTopologySpec = FRONTEND_DEFAULTS.simulation.topology_spec;
        const defaultRule = findRule(state, FRONTEND_DEFAULTS.simulation.rule) || null;

        setTopologySpec(state, defaultTopologySpec);
        state.width = Number(defaultTopologySpec.width) || 0;
        state.height = Number(defaultTopologySpec.height) || 0;
        setPatchDepth(state, defaultTopologySpec.patch_depth, defaultTopologySpec.tiling_family);
        clearPendingPatchDepth(state);
        setCellSize(
            state,
            rememberedCellSizeForTilingFamily(state, defaultTopologySpec.tiling_family),
            defaultTopologySpec.tiling_family,
        );
        setSpeed(state, FRONTEND_DEFAULTS.simulation.speed);
        setRuleSelectionOrigin(state, RULE_SELECTION_ORIGIN_DEFAULT);
        if (defaultRule) {
            setActiveRule(state, defaultRule);
            setEditorRule(state, defaultRule.name, { resetPaintState: true });
        }
    }

    return {
        ...simulationActions,
        ...presetActions,
        ...showcaseActions,
        ...patternActions,
        ...uiActions,
        resetAllSettings: (): Promise<SimulationSnapshot | null> => {
            dismissFirstRunHint(state);
            uiSessionController.resetSessionPreferences?.();
            resetThemeToDefaultFn();
            renderCurrentGrid();
            applyDefaultBoardPreview();
            renderControlPanel();
            return interactions.sendControl("/api/control/reset", buildDefaultResetPayload(), {
                blockingActivity: BLOCKING_ACTIVITY_RESTORE_DEFAULTS,
            }).then(async (simulationState) => {
                if (!simulationState) {
                    await refreshState();
                }
                return simulationState ?? null;
            });
        },
        undoEdit: () => {
            dismissFirstRunHint(state);
            return interactions.undo?.();
        },
        redoEdit: () => {
            dismissFirstRunHint(state);
            return interactions.redo?.();
        },
        cancelEditorPreview: () => interactions.cancelActivePreview?.(),
    };
}
