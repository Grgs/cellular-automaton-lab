import type { CompareRunConfig } from "./compare-run-link.js";

const STORAGE_KEY = "cellular-automaton-lab.compare.v1";

export interface SavedCompareRun {
    id: string;
    name: string;
    config: CompareRunConfig;
    updatedAt: number;
}

export interface SavedTilingSet {
    id: string;
    name: string;
    geometries: readonly string[];
    updatedAt: number;
}

interface CompareStorageState {
    runs: SavedCompareRun[];
    tilingSets: SavedTilingSet[];
}

function emptyState(): CompareStorageState {
    return { runs: [], tilingSets: [] };
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readRawState(storage: Storage | null = safeStorage()): CompareStorageState {
    if (!storage) {
        return emptyState();
    }
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) {
        return emptyState();
    }
    try {
        const parsed: unknown = JSON.parse(raw);
        if (!isRecord(parsed)) {
            return emptyState();
        }
        return {
            runs: Array.isArray(parsed.runs) ? parsed.runs.filter(isSavedCompareRun) : [],
            tilingSets: Array.isArray(parsed.tilingSets)
                ? parsed.tilingSets.filter(isSavedTilingSet)
                : [],
        };
    } catch {
        return emptyState();
    }
}

function writeRawState(state: CompareStorageState, storage: Storage | null = safeStorage()): void {
    if (!storage) {
        return;
    }
    storage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function safeStorage(): Storage | null {
    try {
        return typeof window === "undefined" ? null : window.localStorage;
    } catch {
        return null;
    }
}

function isCompareRunConfig(value: unknown): value is CompareRunConfig {
    if (!isRecord(value)) {
        return false;
    }
    return (
        typeof value.seed === "string" &&
        typeof value.rule === "string" &&
        typeof value.traversal === "string" &&
        typeof value.grid_size === "number" &&
        typeof value.frames === "number" &&
        Array.isArray(value.geometries) &&
        value.geometries.every((geometry) => typeof geometry === "string") &&
        (value.pattern === undefined || typeof value.pattern === "string")
    );
}

function isSavedCompareRun(value: unknown): value is SavedCompareRun {
    return (
        isRecord(value) &&
        typeof value.id === "string" &&
        typeof value.name === "string" &&
        typeof value.updatedAt === "number" &&
        isCompareRunConfig(value.config)
    );
}

function isSavedTilingSet(value: unknown): value is SavedTilingSet {
    return (
        isRecord(value) &&
        typeof value.id === "string" &&
        typeof value.name === "string" &&
        typeof value.updatedAt === "number" &&
        Array.isArray(value.geometries) &&
        value.geometries.every((geometry) => typeof geometry === "string")
    );
}

function makeId(prefix: string): string {
    return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function sortByUpdatedAt<T extends { updatedAt: number }>(items: T[]): T[] {
    return [...items].sort((left, right) => right.updatedAt - left.updatedAt);
}

export function listSavedCompareRuns(storage?: Storage | null): SavedCompareRun[] {
    return sortByUpdatedAt(readRawState(storage).runs);
}

export function listSavedTilingSets(storage?: Storage | null): SavedTilingSet[] {
    return sortByUpdatedAt(readRawState(storage).tilingSets);
}

export function saveCompareRun(
    name: string,
    config: CompareRunConfig,
    storage?: Storage | null,
): SavedCompareRun {
    const state = readRawState(storage);
    const trimmedName = name.trim();
    const saved: SavedCompareRun = {
        id: makeId("run"),
        name: trimmedName.length > 0 ? trimmedName : "Untitled run",
        config,
        updatedAt: Date.now(),
    };
    state.runs = [saved, ...state.runs.filter((run) => run.name !== saved.name)];
    writeRawState(state, storage);
    return saved;
}

export function deleteSavedCompareRun(id: string, storage?: Storage | null): void {
    const state = readRawState(storage);
    state.runs = state.runs.filter((run) => run.id !== id);
    writeRawState(state, storage);
}

export function saveTilingSet(
    name: string,
    geometries: readonly string[],
    storage?: Storage | null,
): SavedTilingSet {
    const state = readRawState(storage);
    const trimmedName = name.trim();
    const saved: SavedTilingSet = {
        id: makeId("tilings"),
        name: trimmedName.length > 0 ? trimmedName : "Untitled tiling set",
        geometries: [...new Set(geometries)],
        updatedAt: Date.now(),
    };
    state.tilingSets = [saved, ...state.tilingSets.filter((set) => set.name !== saved.name)];
    writeRawState(state, storage);
    return saved;
}

export function deleteSavedTilingSet(id: string, storage?: Storage | null): void {
    const state = readRawState(storage);
    state.tilingSets = state.tilingSets.filter((set) => set.id !== id);
    writeRawState(state, storage);
}
