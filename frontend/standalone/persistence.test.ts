import { beforeEach, describe, expect, it, vi } from "vitest";

describe("standalone persistence", () => {
    beforeEach(() => {
        const storage = new Map<string, string>();
        Object.defineProperty(window, "localStorage", {
            configurable: true,
            value: {
                getItem: (key: string) => storage.get(key) ?? null,
                setItem: (key: string, value: string) => {
                    storage.set(key, value);
                },
                removeItem: (key: string) => {
                    storage.delete(key);
                },
                clear: () => {
                    storage.clear();
                },
            },
        });
        Object.defineProperty(window, "indexedDB", {
            configurable: true,
            value: undefined,
        });
        vi.restoreAllMocks();
    });

    it("falls back to localStorage when IndexedDB is unavailable", async () => {
        const { createSimulationStatePersistence } = await import("./persistence.js");
        const persistence = await createSimulationStatePersistence();
        const snapshot = {
            version: 5 as const,
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 10,
                height: 6,
                patch_depth: 0,
            },
            speed: 5,
            running: false,
            generation: 2,
            rule: "conway",
            cells_by_id: { "c:0:0": 1 },
        };

        await persistence.save(snapshot);
        await expect(persistence.load()).resolves.toEqual(snapshot);
    });
});
