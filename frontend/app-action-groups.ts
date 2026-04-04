import { createDefaultResetRuntime } from "./actions/default-reset.js";
import { createPatternActions } from "./actions/pattern-actions.js";
import { createPresetActions } from "./actions/preset-actions.js";
import { createShowcaseActions } from "./actions/showcase-actions.js";
import { createSimulationActions } from "./actions/simulation/index.js";
import { createUiActions } from "./actions/ui-actions.js";
import { dismissFirstRunHint } from "./state/overlay-state.js";
import { resetThemeToDefault } from "./theme.js";
import type {
    ActionMutationAdapter,
    AppActionOptions,
    PatternActionSet,
    PresetActionSet,
    ShowcaseActionSet,
    SimulationActionSet,
    UiActionSet,
} from "./types/actions.js";
import type { SimulationSnapshot } from "./types/domain.js";

export function createSimulationConfigActionSet(
    options: AppActionOptions & { createSimulationActionsFn?: typeof createSimulationActions | undefined },
): SimulationActionSet {
    const { createSimulationActionsFn = createSimulationActions } = options;
    return createSimulationActionsFn({
        state: options.state,
        interactions: options.interactions,
        viewportController: options.viewportController,
        configSyncController: options.configSyncController,
        uiSessionController: options.uiSessionController,
        renderControlPanel: options.renderControlPanel,
        getViewportDimensions: options.getViewportDimensions,
    });
}

export function createPatternPresetActionSet(
    options: AppActionOptions & {
        simulationMutations: ActionMutationAdapter | null;
        createPresetActionsFn?: typeof createPresetActions | undefined;
        createShowcaseActionsFn?: typeof createShowcaseActions | undefined;
        createPatternActionsFn?: typeof createPatternActions | undefined;
        confirmImportFn?: ((message: string) => boolean) | undefined;
        buildPatternPayloadFn?: typeof import("./pattern-io.js").buildPatternPayload | undefined;
        serializePatternPayloadFn?: typeof import("./pattern-io.js").serializePatternPayload | undefined;
        buildPatternFilenameFn?: typeof import("./pattern-io.js").buildPatternFilename | undefined;
        downloadPatternFileFn?: typeof import("./pattern-io.js").downloadPatternFile | undefined;
        readPatternFileFn?: typeof import("./pattern-io.js").readPatternFile | undefined;
        parsePatternTextFn?: typeof import("./pattern-io.js").parsePatternText | undefined;
        readClipboardTextFn?: typeof import("./pattern-io.js").readClipboardText | undefined;
        writeClipboardTextFn?: typeof import("./pattern-io.js").writeClipboardText | undefined;
    },
): PatternActionSet & PresetActionSet & ShowcaseActionSet {
    const {
        createPresetActionsFn = createPresetActions,
        createShowcaseActionsFn = createShowcaseActions,
        createPatternActionsFn = createPatternActions,
        confirmImportFn = (message) => window.confirm(message),
        buildPatternPayloadFn,
        serializePatternPayloadFn,
        buildPatternFilenameFn,
        downloadPatternFileFn,
        readPatternFileFn,
        parsePatternTextFn,
        readClipboardTextFn,
        writeClipboardTextFn,
    } = options;

    const presetActions = createPresetActionsFn({
        state: options.state,
        elements: options.elements,
        interactions: options.interactions,
        applySimulationState: options.applySimulationState,
        postControlFn: options.postControlFn,
        setCellsRequestFn: options.setCellsRequestFn,
        onError: options.onError,
        refreshState: options.refreshState,
        renderControlPanel: options.renderControlPanel,
        simulationMutations: options.simulationMutations,
    });

    const patternActions = createPatternActionsFn({
        state: options.state,
        elements: options.elements,
        interactions: options.interactions,
        viewportController: options.viewportController,
        renderControlPanel: options.renderControlPanel,
        applySimulationState: options.applySimulationState,
        postControlFn: options.postControlFn,
        setCellsRequestFn: options.setCellsRequestFn,
        onError: options.onError,
        refreshState: options.refreshState,
        simulationMutations: options.simulationMutations,
        confirmImportFn,
        ...(buildPatternPayloadFn ? { buildPatternPayloadFn } : {}),
        ...(serializePatternPayloadFn ? { serializePatternPayloadFn } : {}),
        ...(buildPatternFilenameFn ? { buildPatternFilenameFn } : {}),
        ...(downloadPatternFileFn ? { downloadPatternFileFn } : {}),
        ...(readPatternFileFn ? { readPatternFileFn } : {}),
        ...(parsePatternTextFn ? { parsePatternTextFn } : {}),
        ...(readClipboardTextFn ? { readClipboardTextFn } : {}),
        ...(writeClipboardTextFn ? { writeClipboardTextFn } : {}),
    });

    const showcaseActions = createShowcaseActionsFn({
        state: options.state,
        elements: options.elements,
        interactions: options.interactions,
        applySimulationState: options.applySimulationState,
        postControlFn: options.postControlFn,
        setCellsRequestFn: options.setCellsRequestFn,
        renderControlPanel: options.renderControlPanel,
        refreshState: options.refreshState,
        onError: options.onError,
        getViewportDimensions: options.getViewportDimensions,
        simulationMutations: options.simulationMutations,
    });

    return {
        ...presetActions,
        ...patternActions,
        ...showcaseActions,
    };
}

export function createEditorUiActionSet(
    options: AppActionOptions & {
        createUiActionsFn?: typeof createUiActions | undefined;
        resetThemeToDefaultFn?: typeof resetThemeToDefault | undefined;
    },
): UiActionSet & {
    resetAllSettings(): Promise<SimulationSnapshot | null>;
    undoEdit(): Promise<SimulationSnapshot | null> | undefined;
    redoEdit(): Promise<SimulationSnapshot | null> | undefined;
    cancelEditorPreview(): Promise<void> | undefined;
} {
    const {
        createUiActionsFn = createUiActions,
        resetThemeToDefaultFn = resetThemeToDefault,
    } = options;

    const uiActions = createUiActionsFn({
        state: options.state,
        uiSessionController: options.uiSessionController,
        renderCurrentGrid: options.renderCurrentGrid,
        renderControlPanel: options.renderControlPanel,
        viewportController: options.viewportController,
    });
    const defaultResetRuntime = createDefaultResetRuntime({
        state: options.state,
        interactions: options.interactions,
        uiSessionController: options.uiSessionController,
        renderCurrentGrid: options.renderCurrentGrid,
        renderControlPanel: options.renderControlPanel,
        refreshState: options.refreshState,
        resetThemeToDefault: resetThemeToDefaultFn,
    });

    return {
        ...uiActions,
        resetAllSettings: (): Promise<SimulationSnapshot | null> => defaultResetRuntime.resetAllSettings(),
        undoEdit: () => {
            dismissFirstRunHint(options.state);
            return options.interactions.undo?.();
        },
        redoEdit: () => {
            dismissFirstRunHint(options.state);
            return options.interactions.redo?.();
        },
        cancelEditorPreview: () => options.interactions.cancelActivePreview?.(),
    };
}
