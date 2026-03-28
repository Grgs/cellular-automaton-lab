import {
    buildPatternFilename,
    buildPatternPayload,
    downloadPatternFile,
    parsePatternText,
    readClipboardText,
    readPatternFile,
    serializePatternPayload,
    writeClipboardText,
} from "../pattern-io.js";
import { applyOverlayIntent, OVERLAY_INTENT_BOARD_REBUILT } from "../overlay-policy.js";
import {
    clearEditMode,
    clearPatternStatus,
    dismissFirstRunHint,
    hasPatternCells,
    setPatternStatus,
} from "../state/overlay-state.js";
import {
    RULE_SELECTION_ORIGIN_DEFAULT,
} from "../state/constants.js";
import { setRuleSelectionOrigin } from "../state/simulation-state.js";
import {
    BLOCKING_ACTIVITY_IMPORT_PATTERN,
    BLOCKING_ACTIVITY_PASTE_PATTERN,
} from "../blocking-activity.js";
import { createActionMutationAdapter } from "./shared/mutation-adapter.js";
import type {
    ActionMutationAdapter,
    PatternActionOptions,
    PatternActionSet,
    PatternBuildResult,
    PatternImportOptions,
} from "../types/actions.js";
import type { SimulationMutations } from "../types/controller.js";
import type { ParsedPattern, PatternPayload, SimulationSnapshot } from "../types/domain.js";

export function createPatternActions({
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
    buildPatternPayloadFn = buildPatternPayload,
    serializePatternPayloadFn = serializePatternPayload,
    buildPatternFilenameFn = buildPatternFilename,
    downloadPatternFileFn = downloadPatternFile,
    readPatternFileFn = readPatternFile,
    parsePatternTextFn = parsePatternText,
    readClipboardTextFn = readClipboardText,
    writeClipboardTextFn = writeClipboardText,
    confirmImportFn = (message) => window.confirm(message),
    applyOverlayIntentFn = applyOverlayIntent,
    dismissFirstRunHintFn = dismissFirstRunHint,
    clearEditModeFn = clearEditMode,
    setRuleSelectionOriginFn = setRuleSelectionOrigin,
}: PatternActionOptions & {
    buildPatternPayloadFn?: typeof buildPatternPayload;
    serializePatternPayloadFn?: typeof serializePatternPayload;
    buildPatternFilenameFn?: typeof buildPatternFilename;
    downloadPatternFileFn?: typeof downloadPatternFile;
    readPatternFileFn?: typeof readPatternFile;
    parsePatternTextFn?: typeof parsePatternText;
    readClipboardTextFn?: typeof readClipboardText;
    writeClipboardTextFn?: typeof writeClipboardText;
    confirmImportFn?: (message: string) => boolean;
    applyOverlayIntentFn?: typeof applyOverlayIntent;
    dismissFirstRunHintFn?: typeof dismissFirstRunHint;
    clearEditModeFn?: typeof clearEditMode;
    setRuleSelectionOriginFn?: typeof setRuleSelectionOrigin;
}): PatternActionSet {
    const mutations: ActionMutationAdapter | SimulationMutations = simulationMutations
        || createActionMutationAdapter({ interactions, applySimulationState });

    function updatePatternStatus(message = "", tone = "info"): void {
        if (!message) {
            clearPatternStatus(state);
        } else {
            setPatternStatus(state, message, tone);
        }
        renderControlPanel();
    }

    function handlePatternError(prefix: string, error: unknown): void {
        const message = error instanceof Error ? error.message : String(error);
        updatePatternStatus(`${prefix}: ${message}`, "error");
        onError(error);
    }

    function openPatternImport(): void {
        if (!elements.patternImportInput) {
            return;
        }
        elements.patternImportInput.value = "";
        elements.patternImportInput.click();
    }

    function buildSerializedPattern(): PatternBuildResult {
        const pattern: PatternPayload = buildPatternPayloadFn(state);
        return {
            pattern,
            filename: buildPatternFilenameFn(pattern),
            content: serializePatternPayloadFn(pattern),
        };
    }

    async function parseImportedPattern(
        readTextTask: () => Promise<string>,
        failurePrefix: string,
    ): Promise<ParsedPattern | null> {
        try {
            return parsePatternTextFn(await readTextTask());
        } catch (error) {
            handlePatternError(failurePrefix, error);
            return null;
        }
    }

    async function importParsedPattern(
        parsedPattern: ParsedPattern | null,
        {
        successMessage,
        cancelMessage,
        blockingActivity = null,
        onSuccess = () => {},
    }: PatternImportOptions = {
        successMessage: "",
        cancelMessage: "",
    }): Promise<SimulationSnapshot | null> {
        if (!parsedPattern) {
            return null;
        }
        if (
            (state.generation > 0 || hasPatternCells(state))
            && !confirmImportFn("Importing a pattern will replace the current board. Continue?")
        ) {
            updatePatternStatus(cancelMessage, "info");
            return null;
        }

        const requestedSpeed = Number(elements.speedInput?.value);
        const speed = Number.isFinite(requestedSpeed) ? requestedSpeed : Number(state.speed);
        viewportController.suppressAutoSync?.();

        const resetRequest = {
            topology_spec: {
                ...parsedPattern.topologySpec,
                width: parsedPattern.width,
                height: parsedPattern.height,
                patch_depth: parsedPattern.patchDepth,
            },
            speed,
            rule: parsedPattern.rule,
            randomize: false,
        };

        return mutations.runSerialized(
            async () => {
                const resetState = await postControlFn("/api/control/reset", resetRequest);
                const resolvedResetState = await mutations.applyRemoteState(
                    resetState,
                    { source: "external" },
                );

                const importedCells = Object.entries(parsedPattern.cellsById).map(([id, state]) => ({
                    id,
                    state,
                }));
                if (importedCells.length === 0) {
                    return resolvedResetState;
                }

                const availableCellIds = new Set(resolvedResetState.topology.cells.map((cell) => cell.id));
                const unknownCellId = importedCells.find((cell) => !availableCellIds.has(cell.id))?.id;
                if (unknownCellId) {
                    throw new Error(`Pattern references an unknown cell id '${unknownCellId}'.`);
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
        ).then((result) => {
            viewportController.suppressAutoSync?.();
            dismissFirstRunHintFn(state);
            setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_DEFAULT);
            const overlaysRestored = applyOverlayIntentFn(state, OVERLAY_INTENT_BOARD_REBUILT);
            const editChanged = clearEditModeFn(state);
            if (overlaysRestored || editChanged) {
                renderControlPanel();
            }
            onSuccess();
            updatePatternStatus(successMessage, "success");
            return result;
        }).catch(() => null);
    }

    async function importPatternFile(file: File | null | undefined): Promise<SimulationSnapshot | null> {
        if (!file) {
            return null;
        }

        const parsedPattern = await parseImportedPattern(
            () => readPatternFileFn(file),
            "Import failed",
        );
        return importParsedPattern(parsedPattern, {
            successMessage: `Imported pattern from ${file.name}.`,
            cancelMessage: "Import canceled.",
            blockingActivity: BLOCKING_ACTIVITY_IMPORT_PATTERN,
            onSuccess: () => {
                if (elements.patternImportInput) {
                    elements.patternImportInput.value = "";
                }
            },
        });
    }

    async function exportPattern(): Promise<PatternPayload | null> {
        try {
            const { pattern, filename, content } = buildSerializedPattern();
            downloadPatternFileFn(
                content,
                filename,
            );
            updatePatternStatus(`Exported pattern to ${filename}.`, "success");
            return pattern;
        } catch (error) {
            handlePatternError("Export failed", error);
            return null;
        }
    }

    async function copyPattern(): Promise<PatternPayload | null> {
        try {
            const { pattern, content } = buildSerializedPattern();
            await writeClipboardTextFn(content);
            updatePatternStatus("Copied pattern to clipboard.", "success");
            return pattern;
        } catch (error) {
            handlePatternError("Copy failed", error);
            return null;
        }
    }

    async function pastePattern(): Promise<SimulationSnapshot | null> {
        const parsedPattern = await parseImportedPattern(
            () => readClipboardTextFn(),
            "Paste failed",
        );
        return importParsedPattern(parsedPattern, {
            successMessage: "Pasted pattern from clipboard.",
            cancelMessage: "Paste canceled.",
            blockingActivity: BLOCKING_ACTIVITY_PASTE_PATTERN,
        });
    }

    return {
        openPatternImport,
        importPatternFile: (file) => importPatternFile(file),
        exportPattern: () => exportPattern(),
        copyPattern: () => copyPattern(),
        pastePattern: () => pastePattern(),
    };
}
