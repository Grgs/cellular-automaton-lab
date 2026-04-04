import {
    describeTopologySpec,
    getTopologyDefinition,
} from "./topology-catalog.js";
import type { PatternPayload, ParsedPattern, TopologySpec } from "./types/domain.js";
import type { AppState } from "./types/state.js";
import { PatternValidationError, parsePatternText } from "./parsers/pattern.js";

const PATTERN_FORMAT = "cellular-automaton-lab-pattern";
const PATTERN_VERSION = 5;

export function buildPatternPayload(state: AppState): PatternPayload {
    const topology = state?.topology;
    const rule = state?.activeRule;
    if (!topology || !Array.isArray(topology.cells) || !rule?.name) {
        throw new PatternValidationError("Pattern export is only available after the simulation finishes loading.");
    }
    const topologySpec = describeTopologySpec(topology.topology_spec || state.topologySpec || {});

    const cellsById = Object.fromEntries(topology.cells.flatMap((cell, index) => {
        const stateValue = Number(state.cellStates?.[index] ?? 0);
        return stateValue === 0 ? [] : [[cell.id, stateValue]];
    }));

    const payload = {
        format: PATTERN_FORMAT,
        version: PATTERN_VERSION,
        topology_spec: {
            ...topologySpec,
            width: Number(topologySpec.width) || 0,
            height: Number(topologySpec.height) || 0,
            patch_depth: Number(topologySpec.patch_depth) || 0,
        },
        rule: rule.name,
        cells_by_id: cellsById,
    };
    return payload;
}

export function serializePatternPayload(payload: PatternPayload): string {
    return `${JSON.stringify(payload, null, 2)}\n`;
}

function slugSegment(value: string | number | null | undefined): string {
    return String(value)
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "") || "pattern";
}

export function buildPatternFilename(payload: PatternPayload): string {
    const rule = slugSegment(payload.rule);
    const topologySpec = describeTopologySpec(payload.topology_spec || {});
    const tilingFamily = slugSegment(topologySpec.tiling_family);
    const adjacencyMode = slugSegment(topologySpec.adjacency_mode);
    if (topologySpec.sizing_mode === "patch_depth") {
        return `pattern-${rule}-${tilingFamily}-${adjacencyMode}-d${Number(topologySpec.patch_depth) || 0}.json`;
    }
    const width = Number(topologySpec.width) || 0;
    const height = Number(topologySpec.height) || 0;
    return `pattern-${rule}-${tilingFamily}-${adjacencyMode}-${width}x${height}.json`;
}

export function downloadPatternFile(content: string, filename: string, {
    documentRef = document,
    urlApi = window.URL,
}: {
    documentRef?: Document;
    urlApi?: Pick<typeof URL, "createObjectURL" | "revokeObjectURL">;
} = {}): void {
    const blob = new Blob([content], { type: "application/json" });
    const url = urlApi.createObjectURL(blob);
    const link = documentRef.createElement("a");
    link.href = url;
    link.download = filename;
    link.style.display = "none";
    documentRef.body.appendChild(link);
    link.click();
    link.remove();
    urlApi.revokeObjectURL(url);
}

export async function readPatternFile(file: File | null | undefined): Promise<string> {
    if (!file) {
        throw new PatternValidationError("No pattern file was selected.");
    }
    return file.text();
}

function resolveClipboardApi<TMethod extends "writeText" | "readText">(
    clipboardRef: Pick<Clipboard, TMethod> | null,
    methodName: TMethod,
): Pick<Clipboard, TMethod> {
    if (!clipboardRef || typeof clipboardRef[methodName] !== "function") {
        throw new Error("Clipboard access is not available. Use import/export instead.");
    }
    return clipboardRef;
}

export async function writeClipboardText(text: string, {
    clipboardRef = typeof navigator !== "undefined" ? navigator.clipboard : null,
}: {
    clipboardRef?: Pick<Clipboard, "writeText"> | null;
} = {}): Promise<void> {
    const clipboard = resolveClipboardApi(clipboardRef, "writeText");
    await clipboard.writeText(String(text));
}

export async function readClipboardText({
    clipboardRef = typeof navigator !== "undefined" ? navigator.clipboard : null,
}: {
    clipboardRef?: Pick<Clipboard, "readText"> | null;
} = {}): Promise<string> {
    const clipboard = resolveClipboardApi(clipboardRef, "readText");
    return clipboard.readText();
}

export { PatternValidationError, parsePatternText };
