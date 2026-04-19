import { beforeEach, describe, expect, it, vi } from "vitest";

import {
    getFixtureTopologyDefinition,
    installFrontendGlobals,
} from "../test-helpers/bootstrap.js";

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
        const { createAppState } = await import("../state/simulation-state.js");
        const { resolveViewportSizingState } = await import("./shared.js");
        const chairPolicy = getFixtureTopologyDefinition("chair").sizing_policy;
        const hatPolicy = getFixtureTopologyDefinition("hat-monotile").sizing_policy;
        const tuebingenPolicy = getFixtureTopologyDefinition("tuebingen-triangle").sizing_policy;
        const squareTrianglePolicy = getFixtureTopologyDefinition("dodecagonal-square-triangle").sizing_policy;
        const shieldPolicy = getFixtureTopologyDefinition("shield").sizing_policy;
        const pinwheelPolicy = getFixtureTopologyDefinition("pinwheel").sizing_policy;
        const periodicPolicy = getFixtureTopologyDefinition("deltoidal-hexagonal").sizing_policy;

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
            tiling_family: "dodecagonal-square-triangle",
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
            patchDepthMin: chairPolicy.min,
            patchDepthMax: chairPolicy.max,
        });
        expect(resolveViewportSizingState(hatState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: hatPolicy.min,
            patchDepthMax: hatPolicy.max,
        });
        expect(resolveViewportSizingState(tuebingenState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: tuebingenPolicy.min,
            patchDepthMax: tuebingenPolicy.max,
        });
        expect(resolveViewportSizingState(squareTriangleState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: squareTrianglePolicy.min,
            patchDepthMax: squareTrianglePolicy.max,
        });
        expect(resolveViewportSizingState(shieldState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: shieldPolicy.min,
            patchDepthMax: shieldPolicy.max,
        });
        expect(resolveViewportSizingState(pinwheelState)).toMatchObject({
            usesPatchDepth: true,
            patchDepthMin: pinwheelPolicy.min,
            patchDepthMax: pinwheelPolicy.max,
        });
        expect(resolveViewportSizingState(periodicState)).toMatchObject({
            usesPatchDepth: false,
            cellSizeMin: periodicPolicy.min,
            cellSizeMax: periodicPolicy.max,
        });
    });
});
