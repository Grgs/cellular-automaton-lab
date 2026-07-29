import { describe, expect, it, vi } from "vitest";

import type { SeedFilmstripResult } from "../types/domain.js";
import type { CompareRunConfig } from "./compare-run-link.js";
import {
    createCompareWallHistory,
    createCompareWallSnapshot,
    type CompareWallHistoryEntry,
} from "./compare-wall-history.js";

function config(geometries: string[]): CompareRunConfig {
    return {
        seed: "01",
        rule: "conway",
        traversal: "bfs",
        frames: 8,
        grid_size: 12,
        geometries,
    };
}

function filmstrip(geometries: string[]): SeedFilmstripResult {
    return {
        rule_name: "conway",
        seed: "01",
        traversal: "bfs",
        frame_count: 2,
        grid_size: 12,
        tilings: geometries.map((geometry) => ({
            geometry,
            tiling_family: "regular",
            family: "regular",
            label: geometry,
            cell_count: 2,
            topology_spec: {
                tiling_family: geometry,
                adjacency_mode: "edge",
                sizing_mode: "cell_size",
                width: 12,
                height: 12,
                patch_depth: 0,
            },
            frames: [{ a: 1 }, { b: 1 }],
            extinction_step: null,
            period: null,
            note: null,
            seed_order: ["a", "b"],
        })),
    };
}

function entry(index: number): CompareWallHistoryEntry {
    const beforeGeometries = ["square", `before-${index}`];
    const afterGeometries = ["square", `after-${index}`];
    return {
        operation: "replace",
        label: `Replace ${index}`,
        before: createCompareWallSnapshot({
            configuration: config(beforeGeometries),
            orderedBoards: beforeGeometries,
            filmstrip: filmstrip(beforeGeometries),
            resultKey: `before-${index}`,
            selectedBoard: beforeGeometries[1]!,
            focusedBoard: null,
            frameIndex: index,
            playing: false,
        }),
        after: createCompareWallSnapshot({
            configuration: config(afterGeometries),
            orderedBoards: afterGeometries,
            filmstrip: filmstrip(afterGeometries),
            resultKey: `after-${index}`,
            selectedBoard: afterGeometries[1]!,
            focusedBoard: null,
            frameIndex: index + 1,
            playing: true,
        }),
    };
}

describe("compare wall history", () => {
    it("copies and deeply freezes snapshots", () => {
        const sourceGeometries = ["square", "hex"];
        const sourceConfig = config(sourceGeometries);
        const sourceFilmstrip = filmstrip(["square", "hex"]);
        const snapshot = createCompareWallSnapshot({
            configuration: sourceConfig,
            orderedBoards: sourceGeometries,
            filmstrip: sourceFilmstrip,
            resultKey: "result",
            selectedBoard: "hex",
            focusedBoard: null,
            frameIndex: 3,
            playing: true,
        });

        sourceGeometries[0] = "mutated";
        sourceFilmstrip.tilings[0]!.frames[0]!.a = 0;

        expect(snapshot.configuration.geometries).toEqual(["square", "hex"]);
        expect(snapshot.filmstrip.tilings[0]!.frames[0]).toEqual({ a: 1 });
        expect(Object.isFrozen(snapshot)).toBe(true);
        expect(Object.isFrozen(snapshot.filmstrip.tilings[0]!.frames[0])).toBe(true);
    });

    it("walks undo and redo entries and clears redo after a new record", () => {
        const history = createCompareWallHistory();
        const listener = vi.fn();
        history.subscribe(listener);
        history.record(entry(1));
        history.record(entry(2));

        expect(history.getState()).toEqual({
            canUndo: true,
            canRedo: false,
            undoLabel: "Replace 2",
            redoLabel: null,
        });
        expect(history.undo()?.label).toBe("Replace 2");
        expect(history.undo()?.label).toBe("Replace 1");
        expect(history.undo()).toBeNull();
        expect(history.redo()?.label).toBe("Replace 1");

        history.record(entry(3));
        expect(history.getState().redoLabel).toBeNull();
        expect(history.redo()).toBeNull();
        expect(listener).toHaveBeenCalled();
    });

    it("keeps only the newest 20 entries", () => {
        const history = createCompareWallHistory();
        for (let index = 0; index < 24; index += 1) {
            history.record(entry(index));
        }

        const labels: string[] = [];
        let current: CompareWallHistoryEntry | null;
        while ((current = history.undo()) !== null) {
            labels.push(current.label);
        }

        expect(labels).toHaveLength(20);
        expect(labels[0]).toBe("Replace 23");
        expect(labels.at(-1)).toBe("Replace 4");
    });

    it("clears both stacks without notifying for an already-empty history", () => {
        const history = createCompareWallHistory();
        const listener = vi.fn();
        history.subscribe(listener);
        history.clear();
        expect(listener).not.toHaveBeenCalled();

        history.record(entry(1));
        history.undo();
        history.clear();

        expect(history.getState()).toEqual({
            canUndo: false,
            canRedo: false,
            undoLabel: null,
            redoLabel: null,
        });
    });
});
