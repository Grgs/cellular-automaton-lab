import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("simulation-reconciler", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("clears edit mode and restores overlays on topology rebuilds", async () => {
        const { createSimulationReconciler } = await import("./simulation-reconciler.js");
        const { createAppState } = await import("./state/simulation-state.js");

        const state = createAppState();
        state.topologySpec = {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 30,
            height: 20,
            patch_depth: 0,
        };
        state.topologyRevision = "old-revision";
        state.editArmed = true;
        state.editCueVisible = true;
        state.overlaysDismissed = true;
        state.inspectorTemporarilyHidden = true;

        const applySimulationSnapshot = vi.fn((nextState, snapshot) => {
            nextState.topologyRevision = snapshot.topology_revision ?? null;
            nextState.topologySpec = {
                tiling_family: "hex",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 24,
                height: 18,
                patch_depth: 0,
            };
            nextState.isRunning = false;
        });
        const clearEditorHistory = vi.fn();
        const setEditorRule = vi.fn();
        const syncPolling = vi.fn();
        const renderAll = vi.fn();
        const clearEditModeFn = vi.fn((nextState) => {
            nextState.editArmed = false;
            nextState.editCueVisible = false;
            return true;
        });

        const reconciler = createSimulationReconciler({
            state,
            applySimulationSnapshot,
            shouldClearHistoryForSimulationUpdate: () => false,
            clearEditorHistory,
            setEditorRule,
            syncPolling,
            renderAll,
            clearEditModeFn,
        });

        reconciler.apply({
            topology_spec: {
                tiling_family: "hex",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 24,
                height: 18,
                patch_depth: 0,
            },
            speed: 5,
            running: false,
            generation: 0,
            rule: {
                name: "conway",
                display_name: "Life: Conway",
                description: "Classic Life.",
                states: [
                    { value: 0, label: "Dead", color: "#000000", paintable: false },
                    { value: 1, label: "Alive", color: "#ffffff", paintable: true },
                ],
                default_paint_state: 1,
                supports_randomize: true,
                rule_protocol: "universal-v1",
                supports_all_topologies: true,
            },
            topology_revision: "new-revision",
            topology: {
                topology_revision: "new-revision",
                topology_spec: {
                    tiling_family: "hex",
                    adjacency_mode: "edge",
                    sizing_mode: "grid",
                    width: 24,
                    height: 18,
                    patch_depth: 0,
                },
                cells: [],
            },
            cell_states: [],
        });

        expect(applySimulationSnapshot).toHaveBeenCalled();
        expect(clearEditorHistory).not.toHaveBeenCalled();
        expect(clearEditModeFn).toHaveBeenCalledWith(state);
        expect(state.overlaysDismissed).toBe(false);
        expect(state.inspectorTemporarilyHidden).toBe(false);
        expect(renderAll).toHaveBeenCalled();
        expect(syncPolling).toHaveBeenCalled();
        expect(setEditorRule).not.toHaveBeenCalled();
    });
});
