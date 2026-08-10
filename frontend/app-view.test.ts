import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("app-view selection inspector integration", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
        vi.restoreAllMocks();
    });

    it("passes selected cells from the grid view into the controls view model", async () => {
        const buildControlsViewModel = vi.fn(() => ({}));
        const renderControls = vi.fn();

        vi.doMock("./controls-model.js", () => ({
            buildControlsViewModel,
        }));
        vi.doMock("./controls-view.js", () => ({
            renderControls,
        }));

        const { createAppState } = await import("./state/simulation-state.js");
        const { createAppView } = await import("./app-view.js");

        const state = createAppState();
        const selectedCells = [{ id: "cell:a" }, { id: "cell:b" }];
        const gridView = {
            render: vi.fn(),
            setPreviewCells: vi.fn(),
            clearPreview: vi.fn(),
            setHoveredCell: vi.fn(),
            setSelectedCells: vi.fn(),
            getSelectedCells: vi.fn(() => selectedCells),
            setGestureOutline: vi.fn(),
            flashGestureOutline: vi.fn(),
            clearGestureOutline: vi.fn(),
        } as Parameters<typeof createAppView>[0]["gridView"];

        const appView = createAppView({
            state,
            elements: {
                mainStage: null,
                grid: null,
                controlDrawer: null,
            } as Parameters<typeof createAppView>[0]["elements"],
            gridView,
        });

        appView.renderControlsPanel();

        expect(buildControlsViewModel).toHaveBeenCalledWith(
            expect.objectContaining({
                selectionInspectorSource: { selectedCells },
            }),
        );
        expect(renderControls).toHaveBeenCalledTimes(1);
    });

    it("keeps the current presentation scale while a pointer gesture is active", async () => {
        const { createAppState } = await import("./state/simulation-state.js");
        const { createAppView } = await import("./app-view.js");

        const state = createAppState();
        state.width = 10;
        state.height = 10;
        state.cellSize = 12;
        state.renderCellSize = 12;
        const viewport = document.createElement("div");
        Object.defineProperties(viewport, {
            clientWidth: { configurable: true, value: 200 },
            clientHeight: { configurable: true, value: 200 },
        });
        const gridView = {
            render: vi.fn(),
            setPreviewCells: vi.fn(),
            clearPreview: vi.fn(),
            setHoveredCell: vi.fn(),
            setSelectedCells: vi.fn(),
            getSelectedCells: vi.fn(() => []),
            setGestureOutline: vi.fn(),
            flashGestureOutline: vi.fn(),
            clearGestureOutline: vi.fn(),
        } as Parameters<typeof createAppView>[0]["gridView"];
        const appView = createAppView({
            state,
            elements: {
                gridViewport: viewport,
            } as unknown as Parameters<typeof createAppView>[0]["elements"],
            gridView,
        });

        appView.setPointerGestureActiveResolver(() => true);
        appView.renderGrid();
        expect(state.renderCellSize).toBe(12);

        appView.setPointerGestureActiveResolver(() => false);
        appView.renderGrid();
        expect(state.renderCellSize).toBeGreaterThan(12);
    });

    it("preserves drawer occlusion while running has auto-hidden the drawer", async () => {
        const renderControls = vi.fn();
        vi.doMock("./controls-view.js", () => ({
            renderControls,
        }));

        const { createAppState } = await import("./state/simulation-state.js");
        const { createAppView } = await import("./app-view.js");

        const state = createAppState();
        state.drawerOpen = true;
        state.inspectorOccludesGrid = true;
        state.isRunning = true;

        const mainStage = document.createElement("main");
        const grid = document.createElement("canvas");
        const controlDrawer = document.createElement("aside");
        controlDrawer.dataset.open = "false";

        const appView = createAppView({
            state,
            elements: {
                mainStage,
                grid,
                controlDrawer,
            } as Parameters<typeof createAppView>[0]["elements"],
            gridView: null,
        });

        appView.renderControlsPanel();

        expect(state.inspectorOccludesGrid).toBe(true);
        expect(renderControls).toHaveBeenCalledTimes(1);
    });
});
