import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("overlay-policy", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("clears the running restore flag when a board rebuild is applied", async () => {
        const { createAppState } = await import("./state/simulation-state.js");
        const {
            applyOverlayIntent,
            OVERLAY_INTENT_BOARD_REBUILT,
        } = await import("./overlay-policy.js");

        const state = createAppState();
        state.overlaysDismissed = true;
        state.inspectorTemporarilyHidden = true;
        state.overlayRunPending = true;
        state.runningOverlayRestoreActive = true;

        const changed = applyOverlayIntent(state, OVERLAY_INTENT_BOARD_REBUILT);

        expect(changed).toBe(true);
        expect(state.overlaysDismissed).toBe(false);
        expect(state.inspectorTemporarilyHidden).toBe(false);
        expect(state.overlayRunPending).toBe(false);
        expect(state.runningOverlayRestoreActive).toBe(false);
    });
});
