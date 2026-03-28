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
});
