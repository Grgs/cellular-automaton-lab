import { beforeEach, describe, expect, it } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type { SimulationSnapshot } from "../types/domain.js";

describe("snapshot reducer revisions", () => {
    beforeEach(() => installFrontendGlobals());

    it("keeps the authoritative state revision with the applied snapshot", async () => {
        const { applySimulationSnapshot } = await import("./snapshot-reducer.js");
        const { createAppState } = await import("./simulation-state.js");
        const topologySpec = {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 1,
            height: 1,
            patch_depth: 0,
        };
        const snapshot: SimulationSnapshot = {
            topology_spec: topologySpec,
            speed: 5,
            running: false,
            generation: 3,
            state_revision: 17,
            state_epoch: 1,
            rule: {
                name: "conway",
                display_name: "Conway",
                description: "Life",
                default_paint_state: 1,
                supports_randomize: true,
                states: [
                    { value: 0, label: "Dead", color: "#fff", paintable: false },
                    { value: 1, label: "Alive", color: "#000", paintable: true },
                ],
                rule_protocol: "universal-v1",
                supports_all_topologies: true,
                compatible_tiling_families: null,
            },
            topology_revision: "square:1x1",
            topology: {
                topology_spec: topologySpec,
                topology_revision: "square:1x1",
                cells: [{ id: "c:0:0", kind: "square", neighbors: [] }],
            },
            cell_states: [1],
        };
        const state = createAppState();

        applySimulationSnapshot(state, snapshot);

        expect(state.stateRevision).toBe(17);
    });
});
