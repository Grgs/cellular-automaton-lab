import type { SeedFilmstripResult } from "../types/domain.js";
import type { CompareRunConfig } from "./compare-run-link.js";

export type CompareWallHistoryOperation = "add" | "remove" | "replace";

export interface CompareWallSnapshot {
    readonly configuration: CompareRunConfig;
    readonly orderedBoards: readonly string[];
    readonly filmstrip: SeedFilmstripResult;
    readonly resultKey: string;
    readonly selectedBoard: string | null;
    readonly focusedBoard: string | null;
    readonly frameIndex: number;
    readonly playing: boolean;
}

export interface CompareWallHistoryEntry {
    readonly operation: CompareWallHistoryOperation;
    readonly label: string;
    readonly before: CompareWallSnapshot;
    readonly after: CompareWallSnapshot;
}

export interface CompareWallHistoryState {
    readonly canUndo: boolean;
    readonly canRedo: boolean;
    readonly undoLabel: string | null;
    readonly redoLabel: string | null;
}

export interface CompareWallHistoryController {
    record(entry: CompareWallHistoryEntry): void;
    undo(): CompareWallHistoryEntry | null;
    redo(): CompareWallHistoryEntry | null;
    clear(): void;
    getState(): CompareWallHistoryState;
    subscribe(listener: (state: CompareWallHistoryState) => void): () => void;
}

interface CompareWallHistoryOptions {
    limit?: number;
}

function deepFreeze<T>(value: T, seen = new WeakSet<object>()): T {
    if (value === null || typeof value !== "object") {
        return value;
    }
    const object = value as object;
    if (seen.has(object)) {
        return value;
    }
    seen.add(object);
    for (const child of Object.values(object)) {
        deepFreeze(child, seen);
    }
    return Object.freeze(value);
}

function immutableCopy<T>(value: T): T {
    return deepFreeze(structuredClone(value));
}

export function createCompareWallSnapshot(snapshot: CompareWallSnapshot): CompareWallSnapshot {
    return immutableCopy(snapshot);
}

function immutableEntry(entry: CompareWallHistoryEntry): CompareWallHistoryEntry {
    return deepFreeze({
        operation: entry.operation,
        label: entry.label,
        before: createCompareWallSnapshot(entry.before),
        after: createCompareWallSnapshot(entry.after),
    });
}

export function createCompareWallHistory(
    options: CompareWallHistoryOptions = {},
): CompareWallHistoryController {
    const limit = Math.max(1, Math.trunc(options.limit ?? 20));
    let undoEntries: CompareWallHistoryEntry[] = [];
    let redoEntries: CompareWallHistoryEntry[] = [];
    const listeners = new Set<(state: CompareWallHistoryState) => void>();

    function state(): CompareWallHistoryState {
        return Object.freeze({
            canUndo: undoEntries.length > 0,
            canRedo: redoEntries.length > 0,
            undoLabel: undoEntries.at(-1)?.label ?? null,
            redoLabel: redoEntries.at(-1)?.label ?? null,
        });
    }

    function emit(): void {
        const snapshot = state();
        listeners.forEach((listener) => listener(snapshot));
    }

    return {
        record(entry): void {
            undoEntries = [...undoEntries, immutableEntry(entry)].slice(-limit);
            redoEntries = [];
            emit();
        },
        undo(): CompareWallHistoryEntry | null {
            const entry = undoEntries.at(-1) ?? null;
            if (!entry) {
                return null;
            }
            undoEntries = undoEntries.slice(0, -1);
            redoEntries = [...redoEntries, entry];
            emit();
            return entry;
        },
        redo(): CompareWallHistoryEntry | null {
            const entry = redoEntries.at(-1) ?? null;
            if (!entry) {
                return null;
            }
            redoEntries = redoEntries.slice(0, -1);
            undoEntries = [...undoEntries, entry].slice(-limit);
            emit();
            return entry;
        },
        clear(): void {
            if (undoEntries.length === 0 && redoEntries.length === 0) {
                return;
            }
            undoEntries = [];
            redoEntries = [];
            emit();
        },
        getState: state,
        subscribe(listener): () => void {
            listeners.add(listener);
            return () => listeners.delete(listener);
        },
    };
}
