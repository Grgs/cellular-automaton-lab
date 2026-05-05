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
import { createPatternActions } from "./actions/pattern-actions.js";
import { createPresetActions } from "./actions/preset-actions.js";
import { createShowcaseActions } from "./actions/showcase-actions.js";
import { createSimulationActions } from "./actions/simulation/index.js";
import { createUiActions } from "./actions/ui-actions.js";
import {
    createEditorUiActionSet,
    createPatternPresetActionSet,
    createSimulationConfigActionSet,
} from "./app-action-groups.js";
import { resetThemeToDefault } from "./theme.js";
import type { ActionMutationAdapter, AppActionOptions, AppActionSet } from "./types/actions.js";
import type { SimulationMutations } from "./types/controller.js";

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
    createSimulationActionsFn,
    createPresetActionsFn,
    createShowcaseActionsFn,
    createPatternActionsFn,
    createUiActionsFn,
    confirmImportFn = (message) => window.confirm(message),
    resetThemeToDefaultFn,
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
    const sharedSimulationMutations: ActionMutationAdapter | SimulationMutations | null =
        simulationMutations;

    const simulationActions = createSimulationConfigActionSet({
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
        simulationMutations: sharedSimulationMutations,
        createSimulationActionsFn,
    });

    const presetPatternActions = createPatternPresetActionSet({
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
        simulationMutations: sharedSimulationMutations,
        createPresetActionsFn,
        createShowcaseActionsFn,
        createPatternActionsFn,
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

    const editorUiActions = createEditorUiActionSet({
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
        simulationMutations: sharedSimulationMutations,
        createUiActionsFn,
        resetThemeToDefaultFn,
    });

    return {
        ...simulationActions,
        ...presetPatternActions,
        ...editorUiActions,
    };
}
