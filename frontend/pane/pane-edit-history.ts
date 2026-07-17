import { indexTopology } from "../topology-index.js";
import type { PreviewPaintCell } from "../types/editor.js";
import type { PaneSession } from "./pane-session.js";

interface PaneCellDiff {
    id: string;
    prevState: number;
    nextState: number;
}

export interface PaneEditHistory {
    commit(cells: PreviewPaintCell[]): Promise<void>;
    canUndo(): boolean;
    canRedo(): boolean;
    undo(): Promise<void>;
    redo(): Promise<void>;
    clear(): void;
}

/** Cell-level history: simulation steps between a paint and its undo are kept. */
export function createPaneEditHistory(session: PaneSession): PaneEditHistory {
    const undoStack: PaneCellDiff[][] = [];
    const redoStack: PaneCellDiff[][] = [];

    async function commit(cells: PreviewPaintCell[]): Promise<void> {
        const current = await session.ensureSnapshot();
        const topologyIndex = indexTopology(current.topology);
        const diffs = cells.flatMap((cell) => {
            const resolved = topologyIndex.byId.get(cell.id);
            if (!resolved) {
                return [];
            }
            const nextState = Number(cell.state);
            const prevState = Number(current.cell_states[resolved.index] ?? 0);
            if (prevState === nextState) {
                return [];
            }
            return [{ id: resolved.id, prevState, nextState }];
        });
        if (diffs.length === 0) {
            return;
        }
        undoStack.push(diffs);
        redoStack.length = 0;
        try {
            await session.writeCells(diffs.map(({ id, nextState }) => ({ id, state: nextState })));
        } catch (error) {
            undoStack.pop();
            throw error;
        }
    }

    return {
        commit,
        canUndo: () => undoStack.length > 0,
        canRedo: () => redoStack.length > 0,
        async undo(): Promise<void> {
            const diffs = undoStack.pop();
            if (!diffs) {
                return;
            }
            redoStack.push(diffs);
            try {
                await session.writeCells(
                    diffs.map(({ id, prevState }) => ({ id, state: prevState })),
                );
            } catch (error) {
                redoStack.pop();
                undoStack.push(diffs);
                throw error;
            }
        },
        async redo(): Promise<void> {
            const diffs = redoStack.pop();
            if (!diffs) {
                return;
            }
            undoStack.push(diffs);
            try {
                await session.writeCells(
                    diffs.map(({ id, nextState }) => ({ id, state: nextState })),
                );
            } catch (error) {
                undoStack.pop();
                redoStack.push(diffs);
                throw error;
            }
        },
        clear(): void {
            undoStack.length = 0;
            redoStack.length = 0;
        },
    };
}
