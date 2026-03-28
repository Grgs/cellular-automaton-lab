import { MAX_EDITOR_HISTORY } from "./editor-tools.js";
import { findTopologyCellById, regularCellId } from "./topology.js";
import type { CellStateUpdate, SimulationSnapshot } from "./types/domain.js";
import type { EditorHistoryEntry } from "./types/editor.js";
import type { AppState } from "./types/state.js";

function normalizeCellUpdate(topologyIndex: AppState["topologyIndex"], cell: unknown): CellStateUpdate | null {
    if (!cell || typeof cell !== "object") {
        return null;
    }
    const record = cell as Partial<CellStateUpdate> & { x?: number; y?: number };

    if (typeof record.id === "string" && record.id.length > 0) {
        const resolved = findTopologyCellById(topologyIndex, record.id);
        return resolved ? { id: resolved.id, state: Number(record.state) } : null;
    }

    if (Number.isFinite(record.x) && Number.isFinite(record.y)) {
        const resolved = findTopologyCellById(topologyIndex, regularCellId(record.x ?? 0, record.y ?? 0));
        return resolved ? { id: resolved.id, state: Number(record.state) } : null;
    }

    return null;
}

export function currentCellStateForId(state: AppState, cellId: string): number | null {
    const resolved = findTopologyCellById(state.topologyIndex, cellId);
    if (!resolved) {
        return null;
    }
    return Number(state.cellStates?.[resolved.index] ?? 0);
}

export function buildCommittedEdit(state: AppState, cells: unknown[]): EditorHistoryEntry | null {
    if (!state.topologyIndex || !Array.isArray(cells) || cells.length === 0) {
        return null;
    }

    const normalized = new Map<string, CellStateUpdate>();
    cells.forEach((cell) => {
        const nextCell = normalizeCellUpdate(state.topologyIndex, cell);
        if (!nextCell || !Number.isFinite(nextCell.state)) {
            return;
        }
        normalized.set(nextCell.id, nextCell);
    });

    if (normalized.size === 0) {
        return null;
    }

    const forwardCells: CellStateUpdate[] = [];
    const inverseCells: CellStateUpdate[] = [];
    normalized.forEach((cell) => {
        const previousState = currentCellStateForId(state, cell.id);
        if (previousState === null || previousState === cell.state) {
            return;
        }
        forwardCells.push({ id: cell.id, state: cell.state });
        inverseCells.push({ id: cell.id, state: previousState });
    });

    if (forwardCells.length === 0) {
        return null;
    }

    return { forwardCells, inverseCells };
}

export function clearEditorHistory(state: AppState): void {
    state.undoStack = [];
    state.redoStack = [];
}

export function pushUndoEntry(state: AppState, entry: EditorHistoryEntry | null, limit = MAX_EDITOR_HISTORY): void {
    if (!entry?.forwardCells?.length || !entry?.inverseCells?.length) {
        return;
    }
    state.undoStack = [...state.undoStack, entry].slice(-limit);
    state.redoStack = [];
}

export function hasUndoHistory(state: AppState): boolean {
    return Array.isArray(state.undoStack) && state.undoStack.length > 0;
}

export function hasRedoHistory(state: AppState): boolean {
    return Array.isArray(state.redoStack) && state.redoStack.length > 0;
}

export function peekUndoEntry(state: AppState): EditorHistoryEntry | null {
    return hasUndoHistory(state) ? (state.undoStack[state.undoStack.length - 1] ?? null) : null;
}

export function peekRedoEntry(state: AppState): EditorHistoryEntry | null {
    return hasRedoHistory(state) ? (state.redoStack[state.redoStack.length - 1] ?? null) : null;
}

export function commitUndoSuccess(state: AppState): EditorHistoryEntry | null {
    const entry = peekUndoEntry(state);
    if (!entry) {
        return null;
    }
    state.undoStack = state.undoStack.slice(0, -1);
    state.redoStack = [...state.redoStack, entry].slice(-MAX_EDITOR_HISTORY);
    return entry;
}

export function commitRedoSuccess(state: AppState): EditorHistoryEntry | null {
    const entry = peekRedoEntry(state);
    if (!entry) {
        return null;
    }
    state.redoStack = state.redoStack.slice(0, -1);
    state.undoStack = [...state.undoStack, entry].slice(-MAX_EDITOR_HISTORY);
    return entry;
}

function sameScalar(left: unknown, right: unknown): boolean {
    return left === right || (left == null && right == null);
}

function sameArray(left: number[], right: number[]): boolean {
    if (left === right) {
        return true;
    }
    if (!Array.isArray(left) || !Array.isArray(right) || left.length !== right.length) {
        return false;
    }
    for (let index = 0; index < left.length; index += 1) {
        if (left[index] !== right[index]) {
            return false;
        }
    }
    return true;
}

export function shouldClearHistoryForSimulationUpdate(
    state: AppState,
    simulationState: SimulationSnapshot,
    source = "external",
): boolean {
    if (source === "editor") {
        return false;
    }

    if (!hasUndoHistory(state) && !hasRedoHistory(state)) {
        return false;
    }

    const nextRuleName = simulationState.rule.name;
    const currentRuleName = state.activeRule?.name ?? null;
    if (!sameScalar(nextRuleName, currentRuleName)) {
        return true;
    }

    if (!sameScalar(Number(simulationState.generation), Number(state.generation))) {
        return true;
    }

    const nextTopologySpec = simulationState.topology_spec;
    if (!sameScalar(
        `${nextTopologySpec.tiling_family}:${nextTopologySpec.adjacency_mode || "edge"}`,
        state.topologySpec ? `${state.topologySpec.tiling_family}:${state.topologySpec.adjacency_mode || "edge"}` : null,
    )) {
        return true;
    }

    if (!sameScalar(Number(nextTopologySpec?.width) || 0, Number(state.width) || 0)) {
        return true;
    }

    if (!sameScalar(Number(nextTopologySpec?.height) || 0, Number(state.height) || 0)) {
        return true;
    }

    if (!sameScalar(Number(nextTopologySpec?.patch_depth) || 0, Number(state.patchDepth) || 0)) {
        return true;
    }

    if (!sameScalar(simulationState.topology_revision, state.topologyRevision ?? null)) {
        return true;
    }

    if (state.cellStates.length > 0) {
        return !sameArray(
            simulationState.cell_states.map((value) => Number(value)),
            state.cellStates.map((value) => Number(value)),
        );
    }

    return false;
}
