import { describe, expect, it } from "vitest";

import {
    applyCellMutationDelta,
    persistedSnapshotFrom,
    SimulationSnapshotCache,
} from "./simulation-snapshot-cache.js";
import type { CellMutationDelta, SimulationSnapshot } from "./types/domain.js";

function snapshot(revision = 0, generation = 0): SimulationSnapshot {
    const topologySpec = {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 2,
        height: 1,
        patch_depth: 0,
    };
    return {
        topology_spec: topologySpec,
        speed: 5,
        running: false,
        generation,
        state_revision: revision,
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
        topology_revision: "square:2x1",
        topology: {
            topology_spec: topologySpec,
            topology_revision: "square:2x1",
            cells: [
                { id: "c:0:0", kind: "square", neighbors: [] },
                { id: "c:1:0", kind: "square", neighbors: [] },
            ],
        },
        cell_states: [0, 0],
    };
}

function delta(overrides: Partial<CellMutationDelta> = {}): CellMutationDelta {
    return {
        base_state_revision: 0,
        state_revision: 1,
        topology_revision: "square:2x1",
        generation: 0,
        cell_updates: [{ id: "c:1:0", state: 1 }],
        ...overrides,
    };
}

describe("cell mutation deltas", () => {
    it("applies changed cells without replacing topology identity", () => {
        const current = snapshot();

        const applied = applyCellMutationDelta(current, delta());

        expect(applied).toMatchObject({ state_revision: 1, cell_states: [0, 1] });
        expect(applied?.topology).toBe(current.topology);
    });

    it("accepts no-op deltas and rejects mismatched or malformed patches", () => {
        const current = snapshot();
        expect(
            applyCellMutationDelta(current, delta({ state_revision: 0, cell_updates: [] })),
        ).toMatchObject({ state_revision: 0, cell_states: [0, 0] });
        expect(applyCellMutationDelta(current, delta({ base_state_revision: 2 }))).toBeNull();
        expect(applyCellMutationDelta(current, delta({ generation: 1 }))).toBeNull();
        expect(
            applyCellMutationDelta(current, delta({ topology_revision: "replacement" })),
        ).toBeNull();
        expect(
            applyCellMutationDelta(current, delta({ cell_updates: [{ id: "missing", state: 1 }] })),
        ).toBeNull();
    });

    it("resynchronizes stale patches and never installs an older in-flight refresh", async () => {
        const cache = new SimulationSnapshotCache();
        cache.install(snapshot(), null);
        let resolveRefresh!: (value: SimulationSnapshot) => void;
        const refresh = new Promise<SimulationSnapshot>((resolve) => {
            resolveRefresh = resolve;
        });

        const reconciliation = cache.reconcileDelta(
            delta({ base_state_revision: 9 }),
            () => refresh,
        );
        const beforeNewerInstall = cache.current();
        const newer = { ...snapshot(3), cell_states: [1, 1] };
        cache.install(newer, beforeNewerInstall);
        resolveRefresh({ ...snapshot(2), cell_states: [1, 0] });

        await expect(reconciliation).resolves.toBe(newer);
        expect(cache.current()).toBe(newer);
    });

    it("allows an authoritative lower revision after a runtime restore when no request races", () => {
        const cache = new SimulationSnapshotCache();
        cache.install(snapshot(8), null);
        const requestBase = cache.current();

        const restored = snapshot(0);

        expect(cache.install(restored, requestBase)).toBe(restored);
    });

    it("serializes accepted snapshots without persisting the ephemeral revision", () => {
        const current = { ...snapshot(4, 2), cell_states: [0, 1] };

        expect(persistedSnapshotFrom(current)).toEqual({
            version: 5,
            topology_spec: current.topology_spec,
            speed: 5,
            running: false,
            generation: 2,
            rule: "conway",
            cells_by_id: { "c:1:0": 1 },
        });
    });
});
