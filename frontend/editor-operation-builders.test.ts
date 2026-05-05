import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";
import type { AppState } from "./types/state.js";
import type { TopologyPayload } from "./types/domain.js";

let buildRectangleCellsFn: typeof import("./editor-operation-builders.js").buildRectangleCells;
let createAppStateFn: typeof import("./state/simulation-state.js").createAppState;
let indexTopologyFn: typeof import("./topology.js").indexTopology;

function regularCellId(x: number, y: number): string {
    return `c:${x}:${y}`;
}

function squareState(width: number, height: number): AppState {
    const state = createAppStateFn();
    const topology: TopologyPayload = {
        topology_revision: "test-square",
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width,
            height,
            patch_depth: 0,
        },
        cells: Array.from({ length: width * height }, (_, index) => {
            const x = index % width;
            const y = Math.floor(index / width);
            return {
                id: regularCellId(x, y),
                kind: "cell",
                neighbors: [],
            };
        }),
    };
    state.width = width;
    state.height = height;
    state.cellSize = 10;
    state.renderCellSize = 10;
    state.topologySpec = topology.topology_spec;
    state.topology = topology;
    state.topologyIndex = indexTopologyFn(topology);
    state.cellStates = Array(width * height).fill(0);
    return state;
}

describe("editor-operation-builders", () => {
    beforeEach(async () => {
        vi.resetModules();
        installFrontendGlobals();
        ({ buildRectangleCells: buildRectangleCellsFn } =
            await import("./editor-operation-builders.js"));
        ({ createAppState: createAppStateFn } = await import("./state/simulation-state.js"));
        ({ indexTopology: indexTopologyFn } = await import("./topology.js"));
    });

    it("builds regular-grid rectangles from bounded topology lookups", () => {
        const state = squareState(10, 10);

        const cells = buildRectangleCellsFn(
            state,
            { id: "c:1:1", x: 1, y: 1 },
            { id: "c:4:3", x: 4, y: 3 },
            2,
            1,
        );

        expect(cells.map((cell) => cell.id).sort()).toEqual([
            "c:1:1",
            "c:1:2",
            "c:1:3",
            "c:2:1",
            "c:2:3",
            "c:3:1",
            "c:3:3",
            "c:4:1",
            "c:4:2",
            "c:4:3",
        ]);
        expect(cells.every((cell) => cell.state === 2)).toBe(true);
    });
});
