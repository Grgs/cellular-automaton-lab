import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import { buildSingleVariantBootstrappedTopologyDefinition } from "../test-helpers/topology-catalog-fixtures.js";

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
            buildSingleVariantBootstrappedTopologyDefinition("chair", {
                geometryKey: "chair",
                renderKind: "polygon_aperiodic",
                defaultRule: "life-b2-s23",
                sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 5 },
            }),
            buildSingleVariantBootstrappedTopologyDefinition("deltoidal-hexagonal", {
                geometryKey: "deltoidal-hexagonal",
                renderKind: "polygon_periodic",
                defaultRule: "life-b2-s23",
                sizingPolicy: { control: "cell_size", default: 12, min: 8, max: 20 },
            }),
            buildSingleVariantBootstrappedTopologyDefinition("hat-monotile", {
                geometryKey: "hat-monotile",
                renderKind: "polygon_aperiodic",
                defaultRule: "life-b2-s23",
                sizingPolicy: { control: "patch_depth", default: 2, min: 0, max: 3 },
            }),
            buildSingleVariantBootstrappedTopologyDefinition("tuebingen-triangle", {
                geometryKey: "tuebingen-triangle",
                renderKind: "polygon_aperiodic",
                defaultRule: "life-b2-s23",
                sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 5 },
            }),
            buildSingleVariantBootstrappedTopologyDefinition("dodecagonal-square-triangle", {
                geometryKey: "dodecagonal-square-triangle",
                renderKind: "polygon_aperiodic",
                defaultRule: "life-b2-s23",
                sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 4 },
            }),
            buildSingleVariantBootstrappedTopologyDefinition("shield", {
                geometryKey: "shield",
                renderKind: "polygon_aperiodic",
                defaultRule: "life-b2-s23",
                sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 5 },
            }),
            buildSingleVariantBootstrappedTopologyDefinition("pinwheel", {
                geometryKey: "pinwheel",
                renderKind: "polygon_aperiodic",
                defaultRule: "life-b2-s23",
                sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 4 },
            }),
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
            patchDepthMax: 5,
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
