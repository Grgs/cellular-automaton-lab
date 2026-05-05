import { applyOverlayIntent, OVERLAY_INTENT_BOARD_REBUILT } from "../overlay-policy.js";
import {
    clearEditMode,
    clearPatternStatus,
    dismissFirstRunHint,
    setPatternStatus,
} from "../state/overlay-state.js";
import { RULE_SELECTION_ORIGIN_DEFAULT } from "../state/constants.js";
import { setRuleSelectionOrigin } from "../state/simulation-state.js";
import { parsePatternText } from "../pattern-io.js";
import { createActionMutationAdapter } from "./shared/mutation-adapter.js";
import {
    buildPatternImportResetRequest,
    normalizeImportedCellUpdates,
    shouldConfirmPatternImport,
} from "./pattern-import-plan.js";
import type { ActionMutationAdapter, PatternImportOptions } from "../types/actions.js";
import type {
    InteractionController,
    PostControlFunction,
    SetCellsRequestFunction,
    SimulationMutations,
    ViewportController,
} from "../types/controller.js";
import type { ParsedPattern, SimulationSnapshot } from "../types/domain.js";
import type { AppState } from "../types/state.js";

interface PatternImportElements {
    speedInput: HTMLInputElement | null;
}

export interface PatternTextImportOptions extends PatternImportOptions {
    failurePrefix: string;
}

interface CreatePatternImportRuntimeOptions {
    state: AppState;
    elements: PatternImportElements;
    interactions: Pick<InteractionController, "runSerialized">;
    viewportController: Pick<ViewportController, "suppressAutoSync">;
    renderControlPanel: () => void;
    applySimulationState: (
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ) => void;
    postControlFn: PostControlFunction;
    setCellsRequestFn: SetCellsRequestFunction;
    onError: (error: unknown) => void;
    refreshState: () => Promise<void>;
    simulationMutations?: ActionMutationAdapter | SimulationMutations | null;
    parsePatternTextFn?: typeof parsePatternText;
    confirmImportFn?: (message: string) => boolean;
    applyOverlayIntentFn?: typeof applyOverlayIntent;
    dismissFirstRunHintFn?: typeof dismissFirstRunHint;
    clearEditModeFn?: typeof clearEditMode;
    setRuleSelectionOriginFn?: typeof setRuleSelectionOrigin;
    setPatternStatusFn?: typeof setPatternStatus;
    clearPatternStatusFn?: typeof clearPatternStatus;
}

export interface PatternImportRuntime {
    importPatternText(
        readTextTask: () => Promise<string>,
        options: PatternTextImportOptions,
    ): Promise<SimulationSnapshot | null>;
    applyParsedPattern(
        parsedPattern: ParsedPattern,
        options: PatternTextImportOptions & { skipConfirm?: boolean },
    ): Promise<SimulationSnapshot | null>;
}

export function createPatternImportRuntime({
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
    simulationMutations = null,
    parsePatternTextFn = parsePatternText,
    confirmImportFn = (message) => window.confirm(message),
    applyOverlayIntentFn = applyOverlayIntent,
    dismissFirstRunHintFn = dismissFirstRunHint,
    clearEditModeFn = clearEditMode,
    setRuleSelectionOriginFn = setRuleSelectionOrigin,
    setPatternStatusFn = setPatternStatus,
    clearPatternStatusFn = clearPatternStatus,
}: CreatePatternImportRuntimeOptions): PatternImportRuntime {
    const mutations: ActionMutationAdapter | SimulationMutations =
        simulationMutations || createActionMutationAdapter({ interactions, applySimulationState });

    function updatePatternStatus(message = "", tone = "info"): void {
        if (!message) {
            clearPatternStatusFn(state);
        } else {
            setPatternStatusFn(state, message, tone);
        }
        renderControlPanel();
    }

    function handleImportParseFailure(prefix: string, error: unknown): void {
        const message = error instanceof Error ? error.message : String(error);
        updatePatternStatus(`${prefix}: ${message}`, "error");
        onError(error);
    }

    async function parseImportedPattern(
        readTextTask: () => Promise<string>,
        failurePrefix: string,
    ): Promise<ParsedPattern | null> {
        try {
            return parsePatternTextFn(await readTextTask());
        } catch (error) {
            handleImportParseFailure(failurePrefix, error);
            return null;
        }
    }

    async function applyParsedPattern(
        parsedPattern: ParsedPattern,
        {
            successMessage,
            cancelMessage,
            blockingActivity = null,
            onSuccess = () => {},
            skipConfirm = false,
        }: PatternTextImportOptions & { skipConfirm?: boolean },
    ): Promise<SimulationSnapshot | null> {
        if (
            !skipConfirm &&
            shouldConfirmPatternImport(state) &&
            !confirmImportFn("Importing a pattern will replace the current board. Continue?")
        ) {
            updatePatternStatus(cancelMessage, "info");
            return null;
        }

        const requestedSpeed = Number(elements.speedInput?.value);
        const speed = Number.isFinite(requestedSpeed) ? requestedSpeed : Number(state.speed);
        viewportController.suppressAutoSync?.();

        return mutations
            .runSerialized(
                async () => {
                    const resetState = await postControlFn(
                        "/api/control/reset",
                        buildPatternImportResetRequest(parsedPattern, speed),
                    );
                    const resolvedResetState = await mutations.applyRemoteState(resetState, {
                        source: "external",
                    });

                    const importedCells = normalizeImportedCellUpdates(parsedPattern);
                    if (importedCells.length === 0) {
                        return resolvedResetState;
                    }

                    const availableCellIds = new Set(
                        resolvedResetState.topology.cells.map((cell) => cell.id),
                    );
                    const unknownCellId = importedCells.find(
                        (cell) => !availableCellIds.has(cell.id),
                    )?.id;
                    if (unknownCellId) {
                        throw new Error(
                            `Pattern references an unknown cell id '${unknownCellId}'.`,
                        );
                    }

                    const importedState = await setCellsRequestFn(importedCells);
                    await mutations.applyRemoteState(importedState, { source: "external" });
                    return importedState;
                },
                {
                    blockingActivity,
                    onError: (error) => {
                        const message = error instanceof Error ? error.message : String(error);
                        updatePatternStatus(`Import failed: ${message}`, "error");
                        onError(error);
                    },
                    onRecover: refreshState,
                },
            )
            .then(async (result) => {
                viewportController.suppressAutoSync?.();
                dismissFirstRunHintFn(state);
                setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_DEFAULT);
                const overlaysRestored = applyOverlayIntentFn(state, OVERLAY_INTENT_BOARD_REBUILT);
                const editChanged = clearEditModeFn(state);
                if (overlaysRestored || editChanged) {
                    renderControlPanel();
                }
                await onSuccess();
                updatePatternStatus(successMessage, "success");
                return result;
            })
            .catch(() => null);
    }

    async function importPatternText(
        readTextTask: () => Promise<string>,
        options: PatternTextImportOptions,
    ): Promise<SimulationSnapshot | null> {
        const parsedPattern = await parseImportedPattern(readTextTask, options.failurePrefix);
        if (!parsedPattern) {
            return null;
        }
        return applyParsedPattern(parsedPattern, options);
    }

    return {
        importPatternText,
        applyParsedPattern,
    };
}
