import { afterEach, describe, expect, it, vi } from "vitest";

import { createHttpSimulationBackend, request } from "./api.js";
import type { SimulationSnapshot } from "./types/domain.js";

function stubFetch(response: Response): void {
    vi.stubGlobal(
        "fetch",
        vi.fn(() => Promise.resolve(response)),
    );
}

function snapshot(revision = 0): SimulationSnapshot {
    const topologySpec = {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 1,
        height: 1,
        patch_depth: 0,
    };
    return {
        topology_spec: topologySpec,
        speed: 5,
        running: false,
        generation: 0,
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
        topology_revision: "rev-1",
        topology: {
            topology_spec: topologySpec,
            topology_revision: "rev-1",
            cells: [{ id: "c:0:0", kind: "square", neighbors: [] }],
        },
        cell_states: [0],
    };
}

function jsonResponse(value: unknown): Response {
    return new Response(JSON.stringify(value), { status: 200 });
}

describe("request", () => {
    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("returns the parsed body on success", async () => {
        stubFetch(new Response(JSON.stringify({ ok: true }), { status: 200 }));

        await expect(request<{ ok: boolean }>("/api/state")).resolves.toEqual({ ok: true });
    });

    it("surfaces the server's error detail so callers can classify failures", async () => {
        stubFetch(
            new Response(
                JSON.stringify({ error: "Topology has 60984 cells; preview limit is 10000." }),
                { status: 400 },
            ),
        );

        await expect(request("/api/topology/preview")).rejects.toThrow(
            "Request failed: 400 — Topology has 60984 cells; preview limit is 10000.",
        );
    });

    it("falls back to the status code when the error body is not JSON", async () => {
        stubFetch(new Response("<html>boom</html>", { status: 502 }));

        await expect(request("/api/state")).rejects.toThrow("Request failed: 502");
    });
});

describe("HTTP simulation backend cell deltas", () => {
    afterEach(() => vi.unstubAllGlobals());

    it("applies a matching delta without fetching another full snapshot", async () => {
        const fetchMock = vi
            .fn<typeof fetch>()
            .mockResolvedValueOnce(jsonResponse(snapshot()))
            .mockResolvedValueOnce(
                jsonResponse({
                    base_state_revision: 0,
                    state_revision: 1,
                    topology_revision: "rev-1",
                    generation: 0,
                    cell_updates: [{ id: "c:0:0", state: 1 }],
                }),
            );
        vi.stubGlobal("fetch", fetchMock);
        const backend = createHttpSimulationBackend();
        await backend.getState();

        await expect(backend.setCell({ id: "c:0:0" }, 1)).resolves.toMatchObject({
            state_revision: 1,
            cell_states: [1],
        });
        expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it("fetches and installs a full snapshot when a delta is stale", async () => {
        const refreshed = { ...snapshot(2), cell_states: [1] };
        const fetchMock = vi
            .fn<typeof fetch>()
            .mockResolvedValueOnce(jsonResponse(snapshot()))
            .mockResolvedValueOnce(
                jsonResponse({
                    base_state_revision: 9,
                    state_revision: 10,
                    topology_revision: "rev-1",
                    generation: 0,
                    cell_updates: [{ id: "c:0:0", state: 1 }],
                }),
            )
            .mockResolvedValueOnce(jsonResponse(refreshed));
        vi.stubGlobal("fetch", fetchMock);
        const backend = createHttpSimulationBackend();
        await backend.getState();

        await expect(backend.setCell({ id: "c:0:0" }, 1)).resolves.toEqual(refreshed);
        expect(fetchMock).toHaveBeenCalledTimes(3);
    });

    it("rejects malformed mutation contracts without coercion", async () => {
        const fetchMock = vi
            .fn<typeof fetch>()
            .mockResolvedValueOnce(jsonResponse(snapshot()))
            .mockResolvedValueOnce(
                jsonResponse({
                    base_state_revision: 0,
                    state_revision: "1",
                    topology_revision: "rev-1",
                    generation: 0,
                    cell_updates: [{ id: "c:0:0", state: 1 }],
                }),
            );
        vi.stubGlobal("fetch", fetchMock);
        const backend = createHttpSimulationBackend();
        await backend.getState();

        await expect(backend.setCell({ id: "c:0:0" }, 1)).rejects.toThrow(
            "cell delta.state_revision",
        );
    });
});
