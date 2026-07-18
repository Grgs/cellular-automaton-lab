import { describe, expect, it } from "vitest";

import {
    decodeInitResponse,
    decodeRequestResponse,
    decodeTickResponse,
} from "./runtime-decoders.js";

function topologySpec() {
    return {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 2,
        height: 2,
        patch_depth: 0,
    };
}

function rule() {
    return {
        name: "conway",
        display_name: "Conway's Life",
        description: "Life",
        default_paint_state: 1,
        supports_randomize: true,
        states: [
            { value: 0, label: "Dead", color: "#fff", paintable: true },
            { value: 1, label: "Alive", color: "#000", paintable: true },
        ],
        rule_protocol: "life_like",
        supports_all_topologies: true,
        compatible_tiling_families: null,
    };
}

function snapshot() {
    return {
        topology_spec: topologySpec(),
        speed: 5,
        running: false,
        generation: 0,
        state_revision: 0,
        state_epoch: 1,
        rule: rule(),
        topology_revision: "square:2x2",
        topology: {
            topology_spec: topologySpec(),
            topology_revision: "square:2x2",
            width: 2,
            height: 2,
            cells: [
                { id: "c:0:0", kind: "cell", neighbors: [] },
                { id: "c:1:0", kind: "cell", neighbors: [] },
            ],
        },
        cell_states: [0, 1],
    };
}

describe("standalone runtime decoders", () => {
    it("decodes valid init and tick snapshots without coercion", () => {
        expect(
            decodeInitResponse(
                JSON.stringify({
                    snapshot: snapshot(),
                    persisted_snapshot: null,
                }),
            ),
        ).toMatchObject({ snapshot: { topology_revision: "square:2x2" } });

        expect(
            decodeTickResponse(
                JSON.stringify({
                    ok: true,
                    stepped: true,
                    snapshot: snapshot(),
                }),
            ),
        ).toMatchObject({ ok: true, stepped: true });
    });

    it("preserves structured topology-budget errors", () => {
        expect(
            decodeRequestResponse(
                JSON.stringify({
                    ok: false,
                    error: "too many cells",
                    code: "topology_cell_budget_exceeded",
                    limit: 20_000,
                    estimated_cells: 20_100,
                }),
            ),
        ).toEqual({
            ok: false,
            error: "too many cells",
            code: "topology_cell_budget_exceeded",
            limit: 20_000,
            estimated_cells: 20_100,
        });
    });

    it("decodes strict revisioned cell deltas", () => {
        expect(
            decodeRequestResponse(
                JSON.stringify({
                    ok: true,
                    base_state_revision: 2,
                    state_revision: 3,
                    state_epoch: 1,
                    topology_revision: "square:2x2",
                    generation: 1,
                    cell_updates: [{ id: "c:0:0", state: 1 }],
                }),
            ).cellDelta,
        ).toEqual({
            base_state_revision: 2,
            state_revision: 3,
            state_epoch: 1,
            topology_revision: "square:2x2",
            generation: 1,
            cell_updates: [{ id: "c:0:0", state: 1 }],
        });

        expect(() =>
            decodeRequestResponse(
                JSON.stringify({
                    ok: true,
                    base_state_revision: 2,
                    state_revision: 3,
                    state_epoch: 1,
                    topology_revision: "square:2x2",
                    generation: 1,
                    cell_updates: [{ id: "c:0:0", state: 1.5 }],
                }),
            ),
        ).toThrow("cell delta update.state");
    });

    it("rejects values the previous decoder silently coerced", () => {
        expect(() =>
            decodeRequestResponse(
                JSON.stringify({
                    ok: true,
                    filmstrip: {
                        rule_name: "conway",
                        seed: "1",
                        traversal: "bfs",
                        frame_count: "30",
                        grid_size: 12,
                        tilings: [],
                    },
                }),
            ),
        ).toThrow("filmstrip.frame_count");

        expect(() =>
            decodeInitResponse(
                JSON.stringify({
                    snapshot: snapshot(),
                    persisted_snapshot: {
                        version: 5,
                        topology_spec: topologySpec(),
                        speed: 5,
                        running: false,
                        generation: 0,
                        rule: "conway",
                        cells_by_id: { "c:0:0": "1" },
                    },
                }),
            ),
        ).toThrow("persisted snapshot.cells_by_id.c:0:0");
    });
});
