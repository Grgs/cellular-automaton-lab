import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import { buildControlsModelState, EMPTY_SYNC_STATE } from "./test-support.js";

describe("controls-model/drawer selection inspector", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("builds an empty-state selection inspector when no cells are selected", async () => {
        const { buildControlsViewModel } = await import("../controls-model.js");
        const state = await buildControlsModelState();

        const viewModel = buildControlsViewModel({
            state,
            syncState: EMPTY_SYNC_STATE,
            theme: "light",
            selectionInspectorSource: { selectedCells: [] },
        });

        expect(viewModel.selectionInspector).toMatchObject({
            mode: "empty",
            title: "No Cells Selected",
            hintText: "Right-click a cell to inspect it. Right-drag to summarize a selection.",
            summaryRows: [],
            advancedVisible: false,
        });
    });

    it("builds detailed metadata for a single selected cell", async () => {
        const { buildControlsViewModel } = await import("../controls-model.js");
        const state = await buildControlsModelState();

        const viewModel = buildControlsViewModel({
            state,
            syncState: EMPTY_SYNC_STATE,
            theme: "light",
            selectionInspectorSource: { selectedCells: [{ id: "cell:a" }] },
        });

        expect(viewModel.selectionInspector.mode).toBe("single");
        expect(viewModel.selectionInspector.subtitle).toBe("square | Dead (0)");
        expect(viewModel.selectionInspector.summaryRows).toEqual([
            { label: "State", value: "Dead (0)" },
            { label: "Cell ID", value: "cell:a" },
            { label: "Kind", value: "square" },
            { label: "Neighbor Count", value: "2" },
            { label: "Tile Family", value: "family-a" },
            { label: "Orientation", value: "north" },
            { label: "Chirality", value: "left" },
            { label: "Decorations", value: "dot, stripe" },
            { label: "Center", value: "(0.000, 0.000)" },
            { label: "Vertex Count", value: "4" },
            { label: "Slot", value: "alpha" },
        ]);
        expect(viewModel.selectionInspector.advancedRows).toEqual([
            { label: "Neighbor IDs", value: "cell:b, cell:c" },
            { label: "Vertices", value: "(0.000, 0.000), (1.000, 0.000), (1.000, 1.000), (0.000, 1.000)" },
        ]);
    });

    it("builds aggregate metadata for a multi-cell selection", async () => {
        const { buildControlsViewModel } = await import("../controls-model.js");
        const state = await buildControlsModelState();

        const viewModel = buildControlsViewModel({
            state,
            syncState: EMPTY_SYNC_STATE,
            theme: "light",
            selectionInspectorSource: {
                selectedCells: [{ id: "cell:a" }, { id: "cell:b" }, { id: "cell:c" }],
            },
        });

        expect(viewModel.selectionInspector.mode).toBe("multi");
        expect(viewModel.selectionInspector.title).toBe("3 Cells Selected");
        expect(viewModel.selectionInspector.summaryRows).toEqual([
            { label: "Selected Cells", value: "3" },
            { label: "State Mix", value: "Signal (2): 2, Dead (0): 1" },
            { label: "Kind Mix", value: "triangle: 2, square: 1" },
            { label: "Tile Family Mix", value: "family-a: 2, family-b: 1" },
            { label: "Orientation Mix", value: "north: 1, south: 1" },
            { label: "Chirality Mix", value: "left: 1, right: 1" },
            { label: "Decoration Mix", value: "dot: 2, stripe: 1" },
        ]);
        expect(viewModel.selectionInspector.advancedRows).toEqual([
            { label: "Neighbor Count Distribution", value: "2: 2, 1: 1" },
            { label: "Vertex Count Distribution", value: "3: 2, 4: 1" },
            { label: "Center Bounds", value: "x 0.000-2.000, y 0.000-3.000" },
            { label: "Selected Cell IDs", value: "cell:a, cell:b, cell:c" },
        ]);
    });

    it("surfaces backend-owned experimental blocker text for aperiodic families", async () => {
        const { buildControlsViewModel } = await import("../controls-model.js");
        const state = await buildControlsModelState();
        state.topologySpec = {
            ...state.topologySpec,
            tiling_family: "pinwheel",
            sizing_mode: "patch_depth",
            patch_depth: 3,
        };

        const viewModel = buildControlsViewModel({
            state,
            syncState: EMPTY_SYNC_STATE,
            theme: "light",
            selectionInspectorSource: { selectedCells: [] },
        });

        expect(viewModel.topologyStatusVisible).toBe(true);
        expect(viewModel.topologyStatusTone).toBe("warning");
        expect(viewModel.topologyStatusLabel).toContain("Experimental");
        expect(viewModel.topologyStatusDetail).toContain("manual visual review");
    });
});
