import { describe, expect, it, vi } from "vitest";

import { createRunActions } from "./run-actions.js";
import type { ResetControlBody } from "../../types/controller-api.js";
import type { InteractionController } from "../../types/controller-view.js";
import type { TopologySpec } from "../../types/domain.js";
import type { AppState } from "../../types/state.js";

function createState(): AppState {
    const state: Partial<AppState> = {
        isRunning: false,
        generation: 0,
    };
    return state as AppState;
}

function createInteractions(): InteractionController {
    const interactions: Partial<InteractionController> = {
        clearSelection: vi.fn(),
        sendControl: vi.fn().mockResolvedValue(null),
    };
    return interactions as InteractionController;
}

function createResetPayload(randomize: boolean): ResetControlBody {
    const topologySpec: TopologySpec = {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid_dimensions",
        width: 1,
        height: 1,
        patch_depth: 0,
    };
    return {
        topology_spec: topologySpec,
        speed: 8,
        rule: "life",
        randomize,
    };
}

function createRuntime() {
    const interactions = createInteractions();

    const runtime: Partial<Parameters<typeof createRunActions>[0]> = {
        state: createState(),
        interactions,
        dismissHintsAndStatus: vi.fn(),
        applyOverlayIntentAndRender: vi.fn(),
        buildResetPayload: vi.fn(createResetPayload),
        applySpeedSelection: vi.fn(),
        resetRuleSelectionOrigin: vi.fn(),
    };

    return { runtime: runtime as Parameters<typeof createRunActions>[0], interactions };
}

describe("actions/simulation/run-actions", () => {
    it("clears the persistent selection before reset", async () => {
        const { runtime, interactions } = createRuntime();

        await createRunActions(runtime).reset();

        expect(interactions.clearSelection).toHaveBeenCalledTimes(1);
        expect(interactions.sendControl).toHaveBeenCalledWith(
            "/api/control/reset",
            createResetPayload(false),
            expect.objectContaining({
                blockingActivity: expect.objectContaining({
                    kind: "reset-board",
                }),
            }),
        );
    });

    it("clears the persistent selection before random reset", async () => {
        const { runtime, interactions } = createRuntime();

        await createRunActions(runtime).randomReset();

        expect(interactions.clearSelection).toHaveBeenCalledTimes(1);
        expect(interactions.sendControl).toHaveBeenCalledWith(
            "/api/control/reset",
            createResetPayload(true),
            expect.objectContaining({
                blockingActivity: expect.objectContaining({
                    kind: "reset-board",
                }),
            }),
        );
    });
});
