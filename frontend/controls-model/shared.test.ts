import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

describe("controls-model/shared", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("hides HUD and occluding inspector while running until manually restored", async () => {
        const { createAppState } = await import("../state/simulation-state.js");
        const { buildOverlayVisibilityState, buildDrawerToggleState } = await import("./shared.js");

        const state = createAppState();
        state.drawerOpen = true;
        state.isRunning = true;
        state.inspectorOccludesGrid = true;

        expect(buildOverlayVisibilityState(state)).toEqual({
            overlaysVisible: false,
            hudVisible: false,
            drawerVisible: false,
            backdropVisible: false,
        });
        expect(buildDrawerToggleState(state).drawerToggleLabel).toBe("Show Overlays");

        state.runningOverlayRestoreActive = true;
        expect(buildOverlayVisibilityState(state)).toEqual({
            overlaysVisible: true,
            hudVisible: true,
            drawerVisible: true,
            backdropVisible: true,
        });
    });

    it("widens viewport sizing ranges when unsafe sizing is enabled", async () => {
        const { createAppState } = await import("../state/simulation-state.js");
        const { resolveViewportSizingState } = await import("./shared.js");

        const state = createAppState();
        state.unsafeSizingEnabled = true;
        state.topologySpec = {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 30,
            height: 20,
            patch_depth: 0,
        };

        expect(resolveViewportSizingState(state)).toMatchObject({
            cellSizeMin: 1,
            cellSizeMax: 240,
        });
    });

    it("uses patch-depth sizing for new aperiodic tilings and cell-size sizing for new periodic mixed tilings", async () => {
        window.APP_TOPOLOGIES = [
            ...window.APP_TOPOLOGIES,
            {
                tiling_family: "chair",
                label: "Chair",
                picker_group: "Experimental",
                picker_order: 290,
                sizing_mode: "patch_depth",
                family: "aperiodic",
                render_kind: "polygon_aperiodic",
                viewport_sync_mode: "presentation-only",
                supported_adjacency_modes: ["edge"],
                default_adjacency_mode: "edge",
                default_rules: { edge: "life-b2-s23" },
                geometry_keys: { edge: "chair" },
                sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 5 },
            },
            {
                tiling_family: "deltoidal-hexagonal",
                label: "Deltoidal Hexagonal",
                picker_group: "Periodic Mixed",
                picker_order: 215,
                sizing_mode: "grid",
                family: "mixed",
                render_kind: "polygon_periodic",
                viewport_sync_mode: "backend-sync",
                supported_adjacency_modes: ["edge"],
                default_adjacency_mode: "edge",
                default_rules: { edge: "life-b2-s23" },
                geometry_keys: { edge: "deltoidal-hexagonal" },
                sizing_policy: { control: "cell_size", default: 12, min: 8, max: 20 },
            },
            {
                tiling_family: "hat-monotile",
                label: "Hat",
                picker_group: "Aperiodic",
                picker_order: 250,
                sizing_mode: "patch_depth",
                family: "aperiodic",
                render_kind: "polygon_aperiodic",
                viewport_sync_mode: "presentation-only",
                supported_adjacency_modes: ["edge"],
                default_adjacency_mode: "edge",
                default_rules: { edge: "life-b2-s23" },
                geometry_keys: { edge: "hat-monotile" },
                sizing_policy: { control: "patch_depth", default: 2, min: 0, max: 3 },
            },
            {
                tiling_family: "tuebingen-triangle",
                label: "Tuebingen Triangle",
                picker_group: "Aperiodic",
                picker_order: 310,
                sizing_mode: "patch_depth",
                family: "aperiodic",
                render_kind: "polygon_aperiodic",
                viewport_sync_mode: "presentation-only",
                supported_adjacency_modes: ["edge"],
                default_adjacency_mode: "edge",
                default_rules: { edge: "life-b2-s23" },
                geometry_keys: { edge: "tuebingen-triangle" },
                sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 5 },
            },
            {
                tiling_family: "square-triangle",
                label: "Square-Triangle",
                picker_group: "Experimental",
                picker_order: 320,
                sizing_mode: "patch_depth",
                family: "aperiodic",
                render_kind: "polygon_aperiodic",
                viewport_sync_mode: "presentation-only",
                supported_adjacency_modes: ["edge"],
                default_adjacency_mode: "edge",
                default_rules: { edge: "life-b2-s23" },
                geometry_keys: { edge: "square-triangle" },
                sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 4 },
            },
            {
                tiling_family: "shield",
                label: "Shield",
                picker_group: "Experimental",
                picker_order: 330,
                sizing_mode: "patch_depth",
                family: "aperiodic",
                render_kind: "polygon_aperiodic",
                viewport_sync_mode: "presentation-only",
                supported_adjacency_modes: ["edge"],
                default_adjacency_mode: "edge",
                default_rules: { edge: "life-b2-s23" },
                geometry_keys: { edge: "shield" },
                sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 4 },
            },
            {
                tiling_family: "pinwheel",
                label: "Pinwheel",
                picker_group: "Experimental",
                picker_order: 340,
                sizing_mode: "patch_depth",
                family: "aperiodic",
                render_kind: "polygon_aperiodic",
                viewport_sync_mode: "presentation-only",
                supported_adjacency_modes: ["edge"],
                default_adjacency_mode: "edge",
                default_rules: { edge: "life-b2-s23" },
                geometry_keys: { edge: "pinwheel" },
                sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 4 },
            },
        ];

        const { createAppState } = await import("../state/simulation-state.js");
        const { resolveViewportSizingState } = await import("./shared.js");

        const chairState = createAppState();
        chairState.topologySpec = {
            tiling_family: "chair",
            adjacency_mode: "edge",
            sizing_mode: "patch_depth",
            width: 0,
            height: 0,
            patch_depth: 3,
        };

        const periodicState = createAppState();
        periodicState.topologySpec = {
            tiling_family: "deltoidal-hexagonal",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 4,
            height: 4,
            patch_depth: 0,
        };
        const hatState = createAppState();
        hatState.topologySpec = {
            tiling_family: "hat-monotile",
            adjacency_mode: "edge",
            sizing_mode: "patch_depth",
            width: 0,
            height: 0,
            patch_depth: 2,
        };
        const tuebingenState = createAppState();
        tuebingenState.topologySpec = {
            tiling_family: "tuebingen-triangle",
            adjacency_mode: "edge",
            sizing_mode: "patch_depth",
            width: 0,
            height: 0,
            patch_depth: 3,
        };
        const squareTriangleState = createAppState();
        squareTriangleState.topologySpec = {
            tiling_family: "square-triangle",
            adjacency_mode: "edge",
            sizing_mode: "patch_depth",
            width: 0,
            height: 0,
            patch_depth: 3,
        };
        const shieldState = createAppState();
        shieldState.topologySpec = {
            tiling_family: "shield",
            adjacency_mode: "edge",
            sizing_mode: "patch_depth",
            width: 0,
            height: 0,
            patch_depth: 3,
        };
        const pinwheelState = createAppState();
        pinwheelState.topologySpec = {
            tiling_family: "pinwheel",
            adjacency_mode: "edge",
            sizing_mode: "patch_depth",
            width: 0,
            height: 0,
            patch_depth: 3,
        };

        expect(resolveViewportSizingState(chairState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: 0,
            patchDepthMax: 5,
        });
        expect(resolveViewportSizingState(hatState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: 0,
            patchDepthMax: 3,
        });
        expect(resolveViewportSizingState(tuebingenState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: 0,
            patchDepthMax: 5,
        });
        expect(resolveViewportSizingState(squareTriangleState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: 0,
            patchDepthMax: 4,
        });
        expect(resolveViewportSizingState(shieldState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: 0,
            patchDepthMax: 4,
        });
        expect(resolveViewportSizingState(pinwheelState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: 0,
            patchDepthMax: 4,
        });
        expect(resolveViewportSizingState(periodicState)).toMatchObject({
            usesPatchDepth: false,
            cellSizeMin: 8,
            cellSizeMax: 20,
        });
    });
});
