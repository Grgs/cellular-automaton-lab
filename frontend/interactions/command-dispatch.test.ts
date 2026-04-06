import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type { PaintableCell } from "../types/editor.js";
import type { SimulationSnapshot } from "../types/domain.js";
import type { AppState } from "../types/state.js";

function createMutationRuntime() {
    return {
        runStateMutation: vi.fn(async (task: () => Promise<SimulationSnapshot>) => task()),
        runSerialized: vi.fn(),
    };
}

function createIndexedState(currentState = 0): AppState {
    return {
        topologyIndex: {
            byId: new Map([
                ["cell:1", { id: "cell:1", index: 0 }],
            ]),
        },
        cellStates: [currentState],
        undoStack: [],
        redoStack: [],
    } as unknown as AppState;
}

describe("interactions/command-dispatch", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("resolves dead cells to the selected paint state for direct gestures", async () => {
        const { createInteractionCommandDispatch } = await import("./command-dispatch.js");
        const setCellRequest = vi.fn().mockResolvedValue(null);
        const toggleCellRequest = vi.fn().mockResolvedValue(null);
        const mutations = createMutationRuntime();

        const dispatch = createInteractionCommandDispatch({
            mutations,
            toggleCellRequest,
            setCellRequest,
            postControl: vi.fn(),
            getPaintState: () => 2,
            getCellState: () => 0,
        });

        expect(dispatch.resolveDirectGestureTargetState({ id: "cell:1" })).toBe(2);

        expect(setCellRequest).not.toHaveBeenCalled();
        expect(toggleCellRequest).not.toHaveBeenCalled();
    });

    it("resolves the selected paint state back to dead for direct gestures", async () => {
        const { createInteractionCommandDispatch } = await import("./command-dispatch.js");
        const setCellRequest = vi.fn().mockResolvedValue(null);

        const dispatch = createInteractionCommandDispatch({
            mutations: createMutationRuntime(),
            toggleCellRequest: vi.fn().mockResolvedValue(null),
            setCellRequest,
            postControl: vi.fn(),
            getPaintState: () => 2,
            getCellState: () => 2,
        });

        expect(dispatch.resolveDirectGestureTargetState({ id: "cell:1" })).toBe(0);
        expect(setCellRequest).not.toHaveBeenCalled();
    });

    it("treats any other nonzero state as erase for direct gestures", async () => {
        const { createInteractionCommandDispatch } = await import("./command-dispatch.js");
        const setCellRequest = vi.fn().mockResolvedValue(null);
        const cell: PaintableCell = { id: "cell:1", state: 1 };

        const dispatch = createInteractionCommandDispatch({
            mutations: createMutationRuntime(),
            toggleCellRequest: vi.fn().mockResolvedValue(null),
            setCellRequest,
            postControl: vi.fn(),
            getPaintState: () => 3,
            getCellState: (nextCell) => nextCell.state ?? 0,
        });

        expect(dispatch.resolveDirectGestureTargetState(cell)).toBe(0);
        expect(setCellRequest).not.toHaveBeenCalled();
    });

    it("paints a cell through setCellRequest when a target state is supplied", async () => {
        const { createInteractionCommandDispatch } = await import("./command-dispatch.js");
        const setCellRequest = vi.fn().mockResolvedValue({ ok: true } as unknown as SimulationSnapshot);
        const toggleCellRequest = vi.fn().mockResolvedValue(null);
        const cell: PaintableCell = { id: "cell:1" };
        const state = createIndexedState(0);
        const renderControlPanel = vi.fn();

        const dispatch = createInteractionCommandDispatch({
            state,
            mutations: createMutationRuntime(),
            toggleCellRequest,
            setCellRequest,
            postControl: vi.fn(),
            getPaintState: () => 2,
            getCellState: () => 0,
            renderControlPanel,
        });

        await dispatch.paintCell(cell, 4);

        expect(setCellRequest).toHaveBeenCalledWith(cell, 4);
        expect(toggleCellRequest).not.toHaveBeenCalled();
        expect(state.undoStack).toEqual([
            {
                forwardCells: [{ id: "cell:1", state: 4 }],
                inverseCells: [{ id: "cell:1", state: 0 }],
            },
        ]);
        expect(renderControlPanel).toHaveBeenCalledTimes(1);
    });
});
