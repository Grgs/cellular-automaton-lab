import { describe, expect, it, vi } from "vitest";

import { createCompareWorkspaceStore, inspectedBoard } from "./compare-workspace-store.js";

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

    it("derives the inspected board from focus with a selection fallback", () => {
        const store = createCompareWorkspaceStore({
            seed: "1",
            rule: "conway",
            traversal: "bfs",
            grid_size: 16,
            frames: 50,
            geometries: ["square", "hex"],
        });

        expect(store.getState().focusedBoard).toBeNull();
        expect(inspectedBoard(store.getState())).toBeNull();

        // A filmstrip install defaults the selection while the gallery stays
        // unfocused: the inspector describes the selection.
        store.update((state) => ({ ...state, selectedBoard: "square" }));
        expect(inspectedBoard(store.getState())).toBe("square");

        // Speaker view: an active focus wins over the selection default.
        store.update((state) => ({ ...state, focusedBoard: "hex" }));
        expect(inspectedBoard(store.getState())).toBe("hex");

        // Leaving speaker view falls back to the selection.
        store.update((state) => ({ ...state, focusedBoard: null }));
        expect(inspectedBoard(store.getState())).toBe("square");
    });
});
