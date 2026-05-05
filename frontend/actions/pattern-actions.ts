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
import { clearPatternStatus, setPatternStatus } from "../state/overlay-state.js";
import {
    BLOCKING_ACTIVITY_IMPORT_PATTERN,
    BLOCKING_ACTIVITY_PASTE_PATTERN,
    BLOCKING_ACTIVITY_APPLY_SHARE_LINK,
} from "../blocking-activity.js";
import { createPatternImportRuntime } from "./pattern-import-runtime.js";
import {
    buildShareUrl,
    decodeShareFragment,
    readShareBodyFromHash,
    ShareLinkDecodeError,
} from "../share-link.js";
import type {
    PatternActionOptions,
    PatternActionSet,
    PatternBuildResult,
} from "../types/actions.js";
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
}): PatternActionSet {
    const importRuntime = createPatternImportRuntime({
        state,
        elements: {
            speedInput: elements.speedInput,
        },
        interactions,
        viewportController,
        renderControlPanel,
        applySimulationState,
        postControlFn,
        setCellsRequestFn,
        onError,
        refreshState,
        simulationMutations,
        parsePatternTextFn,
        confirmImportFn,
    });

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

    async function importPatternFile(
        file: File | null | undefined,
    ): Promise<SimulationSnapshot | null> {
        if (!file) {
            return null;
        }

        return importRuntime.importPatternText(() => readPatternFileFn(file), {
            failurePrefix: "Import failed",
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
            downloadPatternFileFn(content, filename);
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
        return importRuntime.importPatternText(() => readClipboardTextFn(), {
            failurePrefix: "Paste failed",
            successMessage: "Pasted pattern from clipboard.",
            cancelMessage: "Paste canceled.",
            blockingActivity: BLOCKING_ACTIVITY_PASTE_PATTERN,
        });
    }

    async function copyShareLink(): Promise<string | null> {
        try {
            const { pattern } = buildSerializedPattern();
            const url = buildShareUrl(pattern, window.location.href);
            await writeClipboardTextFn(url);
            updatePatternStatus("Copied share link to clipboard.", "success");
            return url;
        } catch (error) {
            handlePatternError("Share link copy failed", error);
            return null;
        }
    }

    function readShareablePatternFromHash(): ParsedPattern | null {
        if (!readShareBodyFromHash(window.location.hash)) {
            return null;
        }
        try {
            return decodeShareFragment(window.location.hash);
        } catch (error) {
            const message =
                error instanceof ShareLinkDecodeError
                    ? error.message
                    : error instanceof Error
                      ? error.message
                      : String(error);
            updatePatternStatus(`Share link invalid: ${message}`, "error");
            onError(error);
            return null;
        }
    }

    async function applyShareLinkFromHash(): Promise<SimulationSnapshot | null> {
        const parsedPattern = readShareablePatternFromHash();
        if (!parsedPattern) {
            return null;
        }
        return importRuntime.applyParsedPattern(parsedPattern, {
            failurePrefix: "Share link load failed",
            successMessage: "Loaded shared board.",
            cancelMessage: "Share link load canceled.",
            blockingActivity: BLOCKING_ACTIVITY_APPLY_SHARE_LINK,
            skipConfirm: true,
        });
    }

    return {
        openPatternImport,
        importPatternFile: (file) => importPatternFile(file),
        exportPattern: () => exportPattern(),
        copyPattern: () => copyPattern(),
        pastePattern: () => pastePattern(),
        copyShareLink: () => copyShareLink(),
        applyShareLinkFromHash: () => applyShareLinkFromHash(),
    };
}
