import type { SeedComparisonResult, SeedFilmstripResult } from "../types/domain.js";
import type { CompareRunConfig } from "./compare-run-link.js";
import type { SavedCompareRun, SavedTilingSet } from "./compare-storage.js";

export type CompareOperationKind = "analysis" | "filmstrip";
export type CompareOperationStatus = "idle" | "updating" | "failed";

export interface CompareWorkspaceState {
    readonly configuration: CompareRunConfig;
    readonly orderedBoards: readonly string[];
    readonly selectedBoard: string | null;
    readonly results: {
        readonly filmstrip: SeedFilmstripResult | null;
        readonly analysis: SeedComparisonResult | null;
        readonly analysisKey: string | null;
    };
    readonly playback: {
        readonly frameIndex: number;
        readonly playing: boolean;
    };
    readonly saved: {
        readonly runs: readonly SavedCompareRun[];
        readonly tilingSets: readonly SavedTilingSet[];
    };
    readonly operation: {
        readonly kind: CompareOperationKind | null;
        readonly status: CompareOperationStatus;
        readonly error: string | null;
    };
    readonly forkedBoards: readonly string[];
}

export interface CompareWorkspaceStore {
    getState(): CompareWorkspaceState;
    update(updater: (state: CompareWorkspaceState) => CompareWorkspaceState): CompareWorkspaceState;
    subscribe(listener: (state: CompareWorkspaceState) => void): () => void;
}

function copyConfig(config: CompareRunConfig): CompareRunConfig {
    return Object.freeze({ ...config, geometries: Object.freeze([...config.geometries]) });
}

function freezeState(state: CompareWorkspaceState): CompareWorkspaceState {
    return Object.freeze({
        ...state,
        configuration: copyConfig(state.configuration),
        orderedBoards: Object.freeze([...state.orderedBoards]),
        results: Object.freeze({ ...state.results }),
        playback: Object.freeze({ ...state.playback }),
        saved: Object.freeze({
            runs: Object.freeze([...state.saved.runs]),
            tilingSets: Object.freeze([...state.saved.tilingSets]),
        }),
        operation: Object.freeze({ ...state.operation }),
        forkedBoards: Object.freeze([...state.forkedBoards]),
    });
}

export function createCompareWorkspaceStore(
    configuration: CompareRunConfig,
): CompareWorkspaceStore {
    let state = freezeState({
        configuration,
        orderedBoards: configuration.geometries,
        selectedBoard: null,
        results: { filmstrip: null, analysis: null, analysisKey: null },
        playback: { frameIndex: 0, playing: false },
        saved: { runs: [], tilingSets: [] },
        operation: { kind: null, status: "idle", error: null },
        forkedBoards: [],
    });
    const listeners = new Set<(state: CompareWorkspaceState) => void>();

    return {
        getState: () => state,
        update(updater): CompareWorkspaceState {
            const next = freezeState(updater(state));
            if (next === state) {
                return state;
            }
            state = next;
            listeners.forEach((listener) => listener(state));
            return state;
        },
        subscribe(listener): () => void {
            listeners.add(listener);
            return () => listeners.delete(listener);
        },
    };
}
