import { describe, expect, it, vi } from "vitest";

import type { SeedFilmstripResult } from "../types/domain.js";
import {
    createCompareWorkspaceStore,
    inspectedBoard,
    removeWorkspaceBoard,
} from "./compare-workspace-store.js";

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

        const current = store.getState();
        expect(store.update((state) => state)).toBe(current);
        expect(listener).toHaveBeenCalledOnce();
    });

    it("copies nested saved configuration and tiling arrays", () => {
        const store = createCompareWorkspaceStore({
            seed: "1",
            rule: "conway",
            traversal: "bfs",
            grid_size: 16,
            frames: 50,
            geometries: ["square"],
        });
        const runGeometries = ["square"];
        const setGeometries = ["hex"];
        store.update((state) => ({
            ...state,
            saved: {
                runs: [
                    {
                        id: "run-1",
                        name: "Run",
                        config: { ...state.configuration, geometries: runGeometries },
                        updatedAt: 1,
                    },
                ],
                tilingSets: [{ id: "set-1", name: "Set", geometries: setGeometries, updatedAt: 1 }],
            },
        }));

        runGeometries.push("tri");
        setGeometries.push("kagome");
        expect(store.getState().saved.runs[0]?.config.geometries).toEqual(["square"]);
        expect(store.getState().saved.tilingSets[0]?.geometries).toEqual(["hex"]);
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

    it("removes a board from every canonical workspace representation atomically", () => {
        const configuration = {
            seed: "1",
            rule: "conway",
            traversal: "bfs",
            grid_size: 16,
            frames: 50,
            geometries: ["square", "hex", "tri"],
        };
        const store = createCompareWorkspaceStore(configuration);
        const filmstrip = {
            rule_name: "conway",
            seed: "1",
            traversal: "bfs",
            frame_count: 1,
            grid_size: 16,
            tilings: configuration.geometries.map((geometry) => ({ geometry })),
        } as SeedFilmstripResult;
        store.update((state) => ({
            ...state,
            focusedBoard: "hex",
            selectedBoard: "hex",
            results: { ...state.results, filmstrip, filmstripKey: "three" },
        }));

        const nextConfiguration = { ...configuration, geometries: ["square", "tri"] };
        store.update((state) =>
            removeWorkspaceBoard(state, {
                geometry: "hex",
                configuration: nextConfiguration,
                filmstripKey: "two",
            }),
        );

        const state = store.getState();
        expect(state.configuration.geometries).toEqual(["square", "tri"]);
        expect(state.orderedBoards).toEqual(state.configuration.geometries);
        expect(state.results.filmstrip?.tilings.map((tiling) => tiling.geometry)).toEqual([
            "square",
            "tri",
        ]);
        expect(state.results.filmstripKey).toBe("two");
        expect(state.focusedBoard).toBeNull();
        expect(state.selectedBoard).toBe("tri");
    });
});
