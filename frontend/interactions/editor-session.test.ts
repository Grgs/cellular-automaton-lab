import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type { SimulationSnapshot } from "../types/domain.js";

function editorStateStub() {
    return {
        topology: { cells: [] },
        topologyIndex: { byId: new Map() },
        cellStates: [],
        isRunning: false,
    } as never;
}

describe("interactions/editor-session", () => {
    beforeEach(() => {
        vi.resetModules();
        installFrontendGlobals();
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
        expect(flashGestureOutline).toHaveBeenCalledWith(previewCells, "paint", 150);
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
        expect(setGestureOutline).toHaveBeenCalledWith(previewCells, "paint");
        expect(commitEditorCells).toHaveBeenCalledWith(previewCells);
        expect(flashGestureOutline).toHaveBeenCalledWith(previewCells, "paint", 150);
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
});
