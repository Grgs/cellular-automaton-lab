import { afterEach, describe, expect, it, vi } from "vitest";

import type { SimulationBackend } from "../types/controller-api.js";
import type { SimulationSnapshot } from "../types/domain.js";
import { createPaneSession } from "./pane-session.js";

function snapshot(overrides: Partial<SimulationSnapshot> = {}): SimulationSnapshot {
    const topology_spec = {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 1,
        height: 1,
        patch_depth: 0,
    };
    return {
        topology_spec,
        speed: 7,
        running: false,
        generation: 0,
        state_revision: 0,
        state_epoch: 1,
        rule: {
            name: "conway",
            display_name: "Conway",
            description: "",
            default_paint_state: 1,
            supports_randomize: true,
            states: [
                { value: 0, label: "Dead", color: "#fff", paintable: true },
                { value: 1, label: "Live", color: "#000", paintable: true },
            ],
            rule_protocol: "universal-v1",
            supports_all_topologies: true,
            compatible_tiling_families: null,
        },
        topology_revision: "rev",
        topology: {
            topology_revision: "rev",
            topology_spec,
            width: 1,
            height: 1,
            cells: [{ id: "a", kind: "square", neighbors: [] }],
        },
        cell_states: [0],
        ...overrides,
    };
}

afterEach(() => {
    vi.useRealTimers();
});

describe("pane session", () => {
    it("owns polling and stops it with registered cleanup on disposal", async () => {
        vi.useFakeTimers();
        const running = snapshot({ running: true });
        const getState = vi.fn(async () => running);
        const cleanup = vi.fn();
        const session = createPaneSession({
            backend: { getState } as unknown as SimulationBackend,
            onSnapshot: vi.fn(),
            onError: vi.fn(),
        });
        session.registerCleanup(cleanup);
        session.applySnapshot(running);

        await vi.advanceTimersByTimeAsync(250);
        expect(getState).toHaveBeenCalledTimes(1);

        session.dispose();
        await vi.advanceTimersByTimeAsync(500);
        expect(getState).toHaveBeenCalledTimes(1);
        expect(cleanup).toHaveBeenCalledOnce();
    });

    it("serializes pause-write-resume through the snapshot boundary", async () => {
        const events: string[] = [];
        const running = snapshot({ running: true, state_revision: 2 });
        const paused = snapshot({ running: false, state_revision: 3 });
        const edited = snapshot({ running: false, state_revision: 4, cell_states: [1] });
        const resumed = snapshot({ running: true, state_revision: 5, cell_states: [1] });
        const postControl = vi.fn(async (path: string) => {
            events.push(path);
            return path.endsWith("pause") ? paused : resumed;
        });
        const setCells = vi.fn(async () => {
            events.push("cells");
            return edited;
        });
        const applied: SimulationSnapshot[] = [];
        const session = createPaneSession({
            backend: { postControl, setCells } as unknown as SimulationBackend,
            onSnapshot: (next) => applied.push(next),
            onError: vi.fn(),
        });
        session.applySnapshot(running);

        await session.writeCells([{ id: "a", state: 1 }]);

        expect(events).toEqual(["/api/control/pause", "cells", "/api/control/resume"]);
        expect(applied).toEqual([running, paused, edited, resumed]);
        session.dispose();
    });
});
