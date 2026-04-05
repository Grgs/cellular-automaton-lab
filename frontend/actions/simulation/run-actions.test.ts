import { describe, expect, it, vi } from "vitest";

import { createRunActions } from "./run-actions.js";

function createRuntime() {
    const interactions = {
        clearSelection: vi.fn(),
        sendControl: vi.fn().mockResolvedValue(null),
    };

    const runtime = {
        state: {
            isRunning: false,
            generation: 0,
        },
        interactions,
        dismissHintsAndStatus: vi.fn(),
        applyOverlayIntentAndRender: vi.fn(),
        buildResetPayload: vi.fn((randomize: boolean) => ({ randomize })),
        applySpeedSelection: vi.fn(),
        resetRuleSelectionOrigin: vi.fn(),
    } as unknown as Parameters<typeof createRunActions>[0];

    return { runtime, interactions };
}

describe("actions/simulation/run-actions", () => {
    it("clears the persistent selection before reset", async () => {
        const { runtime, interactions } = createRuntime();

        await createRunActions(runtime).reset();

        expect(interactions.clearSelection).toHaveBeenCalledTimes(1);
        expect(interactions.sendControl).toHaveBeenCalledWith(
            "/api/control/reset",
            { randomize: false },
            expect.any(Object),
        );
    });

    it("clears the persistent selection before random reset", async () => {
        const { runtime, interactions } = createRuntime();

        await createRunActions(runtime).randomReset();

        expect(interactions.clearSelection).toHaveBeenCalledTimes(1);
        expect(interactions.sendControl).toHaveBeenCalledWith(
            "/api/control/reset",
            { randomize: true },
            expect.any(Object),
        );
    });
});
