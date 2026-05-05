import { beforeEach, describe, expect, it, vi } from "vitest";

import { DRAG_GESTURE_FLASH_DURATION_MS } from "./constants.js";
import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type { SimulationSnapshot } from "../types/domain.js";

let createAppStateFn: typeof import("../state/simulation-state.js").createAppState;

function editorStateStub() {
    const state = createAppStateFn();
    state.topology = {
        topology_revision: "rev-test",
        topology_spec: state.topologySpec,
        cells: [],
    };
    state.topologyIndex = { byId: new Map() };
    state.cellStates = [];
    state.isRunning = false;
    return state;
}

describe("interactions/editor-session", () => {
    beforeEach(async () => {
        vi.resetModules();
        installFrontendGlobals();
        ({ createAppState: createAppStateFn } = await import("../state/simulation-state.js"));
    });

    it("shows and flashes a paint outline for armed brush drags", async () => {
        const previewCells = [
            { id: "c:0:0", x: 0, y: 0, state: 1 },
            { id: "c:1:0", x: 1, y: 0, state: 1 },
        ];
        const commitEditorCells = vi.fn(async () => null as SimulationSnapshot | null);

        vi.doMock("../editor-operations.js", () => ({
            buildBrushCells: vi.fn(() => previewCells),
            buildEditorToolCells: vi.fn(() => previewCells),
        }));
        vi.doMock("./editor-session-commit.js", () => ({
            createEditorCommitRuntime: () => ({
                ensurePausedForEditing: vi.fn(async () => true),
                commitEditorCells,
            }),
        }));

        const { createEditorSessionController } = await import("./editor-session.js");
        const previewPaintCells = vi.fn();
        const setGestureOutline = vi.fn();
        const flashGestureOutline = vi.fn();
        const clearGestureOutline = vi.fn();

        const controller = createEditorSessionController({
            state: editorStateStub(),
            getPaintState: () => 1,
            getEditorTool: () => "brush",
            getBrushSize: () => 1,
            previewPaintCells,
            clearPreview: vi.fn(),
            setGestureOutline,
            flashGestureOutline,
            clearGestureOutline,
            setCellsRequest: vi.fn(),
            postControl: vi.fn(),
            renderControlPanel: vi.fn(),
            setPointerCapture: vi.fn(),
            releasePointerCapture: vi.fn(),
            runStateMutation: vi.fn(async (task: () => Promise<SimulationSnapshot>) => task()),
        });

        await controller.beginPointerSession({ id: "c:0:0", x: 0, y: 0 }, 1);
        controller.handlePointerMove({ id: "c:1:0", x: 1, y: 0 });
        await controller.handlePointerUp();

        expect(previewPaintCells).toHaveBeenCalledWith(previewCells);
        expect(setGestureOutline).toHaveBeenCalledWith(previewCells, "paint");
        expect(commitEditorCells).toHaveBeenCalledWith(previewCells);
        expect(flashGestureOutline).toHaveBeenCalledWith(
            previewCells,
            "paint",
            DRAG_GESTURE_FLASH_DURATION_MS,
        );
        expect(clearGestureOutline).toHaveBeenCalled();
    });

    it("shows and flashes a paint outline for armed line drags", async () => {
        const previewCells = [
            { id: "c:0:0", x: 0, y: 0, state: 1 },
            { id: "c:1:0", x: 1, y: 0, state: 1 },
            { id: "c:2:0", x: 2, y: 0, state: 1 },
        ];
        const commitEditorCells = vi.fn(async () => null as SimulationSnapshot | null);

        vi.doMock("../editor-operations.js", () => ({
            buildBrushCells: vi.fn(() => previewCells),
            buildEditorToolCells: vi.fn(() => previewCells),
        }));
        vi.doMock("./editor-session-commit.js", () => ({
            createEditorCommitRuntime: () => ({
                ensurePausedForEditing: vi.fn(async () => true),
                commitEditorCells,
            }),
        }));

        const { createEditorSessionController } = await import("./editor-session.js");
        const previewPaintCells = vi.fn();
        const setGestureOutline = vi.fn();
        const flashGestureOutline = vi.fn();
        const clearGestureOutline = vi.fn();

        const controller = createEditorSessionController({
            state: editorStateStub(),
            getPaintState: () => 1,
            getEditorTool: () => "line",
            getBrushSize: () => 1,
            previewPaintCells,
            clearPreview: vi.fn(),
            setGestureOutline,
            flashGestureOutline,
            clearGestureOutline,
            setCellsRequest: vi.fn(),
            postControl: vi.fn(),
            renderControlPanel: vi.fn(),
            setPointerCapture: vi.fn(),
            releasePointerCapture: vi.fn(),
            runStateMutation: vi.fn(async (task: () => Promise<SimulationSnapshot>) => task()),
        });

        await controller.beginPointerSession({ id: "c:0:0", x: 0, y: 0 }, 1);
        controller.handlePointerMove({ id: "c:2:0", x: 2, y: 0 });
        await controller.handlePointerUp();

        expect(previewPaintCells).toHaveBeenCalledWith(previewCells);
        expect(setGestureOutline).not.toHaveBeenCalled();
        expect(commitEditorCells).toHaveBeenCalledWith(previewCells);
        expect(flashGestureOutline).toHaveBeenCalledWith(
            previewCells,
            "paint",
            DRAG_GESTURE_FLASH_DURATION_MS,
        );
        expect(clearGestureOutline).toHaveBeenCalled();
    });

    it("keeps fill clicks free of drag outline behavior", async () => {
        const commitEditorCells = vi.fn(async () => null as SimulationSnapshot | null);
        const fillCells = [{ id: "c:0:0", x: 0, y: 0, state: 1 }];

        vi.doMock("../editor-operations.js", () => ({
            buildBrushCells: vi.fn(() => fillCells),
            buildEditorToolCells: vi.fn(() => fillCells),
        }));
        vi.doMock("./editor-session-commit.js", () => ({
            createEditorCommitRuntime: () => ({
                ensurePausedForEditing: vi.fn(async () => true),
                commitEditorCells,
            }),
        }));

        const { createEditorSessionController } = await import("./editor-session.js");
        const setGestureOutline = vi.fn();
        const flashGestureOutline = vi.fn();

        const controller = createEditorSessionController({
            state: editorStateStub(),
            getPaintState: () => 1,
            getEditorTool: () => "fill",
            getBrushSize: () => 1,
            previewPaintCells: vi.fn(),
            clearPreview: vi.fn(),
            setGestureOutline,
            flashGestureOutline,
            clearGestureOutline: vi.fn(),
            setCellsRequest: vi.fn(),
            postControl: vi.fn(),
            renderControlPanel: vi.fn(),
            setPointerCapture: vi.fn(),
            releasePointerCapture: vi.fn(),
            runStateMutation: vi.fn(async (task: () => Promise<SimulationSnapshot>) => task()),
        });

        await controller.handleClick({ id: "c:0:0", x: 0, y: 0 });

        expect(commitEditorCells).toHaveBeenCalledWith(fillCells);
        expect(setGestureOutline).not.toHaveBeenCalled();
        expect(flashGestureOutline).not.toHaveBeenCalled();
    });

    it("skips rebuilding shape previews while the pointer remains on the same cell", async () => {
        const previewCells = [{ id: "c:1:0", x: 1, y: 0, state: 1 }];
        const buildEditorToolCells = vi.fn(() => previewCells);

        vi.doMock("../editor-operations.js", () => ({
            buildBrushCells: vi.fn(() => previewCells),
            buildEditorToolCells,
        }));
        vi.doMock("./editor-session-commit.js", () => ({
            createEditorCommitRuntime: () => ({
                ensurePausedForEditing: vi.fn(async () => true),
                commitEditorCells: vi.fn(async () => null as SimulationSnapshot | null),
            }),
        }));

        const { createEditorSessionController } = await import("./editor-session.js");
        const previewPaintCells = vi.fn();

        const controller = createEditorSessionController({
            state: editorStateStub(),
            getPaintState: () => 1,
            getEditorTool: () => "rectangle",
            getBrushSize: () => 1,
            previewPaintCells,
            clearPreview: vi.fn(),
            setGestureOutline: vi.fn(),
            flashGestureOutline: vi.fn(),
            clearGestureOutline: vi.fn(),
            setCellsRequest: vi.fn(),
            postControl: vi.fn(),
            renderControlPanel: vi.fn(),
            setPointerCapture: vi.fn(),
            releasePointerCapture: vi.fn(),
            runStateMutation: vi.fn(async (task: () => Promise<SimulationSnapshot>) => task()),
        });

        await controller.beginPointerSession({ id: "c:0:0", x: 0, y: 0 }, 1);
        controller.handlePointerMove({ id: "c:1:0", x: 1, y: 0 });
        controller.handlePointerMove({ id: "c:1:0", x: 1, y: 0 });

        expect(buildEditorToolCells).toHaveBeenCalledTimes(1);
        expect(previewPaintCells).toHaveBeenCalledTimes(1);
    });
});
