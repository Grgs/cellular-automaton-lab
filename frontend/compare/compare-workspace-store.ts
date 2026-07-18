import type { SeedComparisonResult, SeedFilmstripResult } from "../types/domain.js";
import type { CompareRunConfig } from "./compare-run-link.js";
import type { SavedCompareRun, SavedTilingSet } from "./compare-storage.js";

export type CompareOperationKind = "analysis" | "filmstrip";
/** Mirrors the scheduler lifecycle: pending = accepted but not yet executing. */
export type CompareOperationStatus = "idle" | "pending" | "updating" | "failed";

export interface CompareWorkspaceState {
    readonly configuration: CompareRunConfig;
    readonly orderedBoards: readonly string[];
    /**
     * Speaker-view focus. Null in the gallery. Distinct from `selectedBoard`:
     * a board can be selected for inspection without being focused.
     */
    readonly focusedBoard: string | null;
    /**
     * The board under inspection. Follows focus changes, and a filmstrip
     * install defaults it to the first board when the previous one left the
     * wall. Read it through `inspectedBoard`, which lets an active focus win.
     */
    readonly selectedBoard: string | null;
    readonly results: {
        readonly filmstrip: SeedFilmstripResult | null;
        /** Run-config key the filmstrip was produced from (staleness checks). */
        readonly filmstripKey: string | null;
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
        /**
         * True while a backend request bracket is open. Narrower than
         * `status === "updating"`: a cache hit or an aborted launch updates
         * without ever opening the bracket.
         */
        readonly executing: boolean;
        /** The last wall rebuild failed and stale boards are still showing. */
        readonly wallUpdateFailed: boolean;
    };
    readonly forkedBoards: readonly string[];
}

/** The board the inspector should describe: an active focus wins. */
export function inspectedBoard(state: CompareWorkspaceState): string | null {
    return state.focusedBoard ?? state.selectedBoard;
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
        focusedBoard: null,
        selectedBoard: null,
        results: { filmstrip: null, filmstripKey: null, analysis: null, analysisKey: null },
        playback: { frameIndex: 0, playing: false },
        saved: { runs: [], tilingSets: [] },
        operation: {
            kind: null,
            status: "idle",
            error: null,
            executing: false,
            wallUpdateFailed: false,
        },
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
