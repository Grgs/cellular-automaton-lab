import { describe, expect, it, vi } from "vitest";

import { createCompareWorkspaceStore } from "./compare-workspace-store.js";

describe("compare workspace store", () => {
    it("publishes immutable replacements without exposing mutable config arrays", () => {
        const geometries = ["square", "hex"];
        const store = createCompareWorkspaceStore({
            seed: "1",
            rule: "conway",
            traversal: "bfs",
            grid_size: 16,
            frames: 50,
            geometries,
        });
        const listener = vi.fn();
        store.subscribe(listener);
        geometries.push("triangular");

        expect(store.getState().configuration.geometries).toEqual(["square", "hex"]);
        expect(Object.isFrozen(store.getState())).toBe(true);
        expect(Object.isFrozen(store.getState().configuration.geometries)).toBe(true);

        store.update((state) => ({
            ...state,
            selectedBoard: "hex",
            forkedBoards: ["hex"],
        }));
        expect(store.getState().selectedBoard).toBe("hex");
        expect(store.getState().forkedBoards).toEqual(["hex"]);
        expect(listener).toHaveBeenCalledOnce();
    });
});
