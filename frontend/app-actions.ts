import { createDefaultResetRuntime } from "./actions/default-reset.js";
import { createPatternActions } from "./actions/pattern-actions.js";
import { createPresetActions } from "./actions/preset-actions.js";
import { createShowcaseActions } from "./actions/showcase-actions.js";
import { createSimulationActions } from "./actions/simulation/index.js";
import { createUiActions } from "./actions/ui-actions.js";
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
import { dismissFirstRunHint } from "./state/overlay-state.js";
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
import type { SimulationSnapshot } from "./types/domain.js";

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
    const defaultResetRuntime = createDefaultResetRuntime({
        state,
        interactions,
        uiSessionController,
        renderCurrentGrid,
        renderControlPanel,
        refreshState,
        resetThemeToDefault: resetThemeToDefaultFn,
    });

    return {
        ...simulationActions,
        ...presetActions,
        ...showcaseActions,
        ...patternActions,
        ...uiActions,
        resetAllSettings: (): Promise<SimulationSnapshot | null> => defaultResetRuntime.resetAllSettings(),
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
