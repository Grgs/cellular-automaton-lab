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
});
