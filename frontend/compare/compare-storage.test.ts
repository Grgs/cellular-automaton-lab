import { afterEach, describe, expect, it, vi } from "vitest";

import {
    deleteSavedCompareRun,
    deleteSavedTilingSet,
    listSavedCompareRuns,
    listSavedTilingSets,
    saveCompareRun,
    saveTilingSet,
} from "./compare-storage.js";
import type { CompareRunConfig } from "./compare-run-link.js";

function config(overrides: Partial<CompareRunConfig> = {}): CompareRunConfig {
    return {
        seed: "101",
        rule: "conway",
        traversal: "bfs",
        frames: 12,
        grid_size: 8,
        geometries: ["square", "hex"],
        ...overrides,
    };
}

function memoryStorage(): Storage {
    const values = new Map<string, string>();
    return {
        get length() {
            return values.size;
        },
        clear(): void {
            values.clear();
        },
        getItem(key: string): string | null {
            return values.get(key) ?? null;
        },
        key(index: number): string | null {
            return [...values.keys()][index] ?? null;
        },
        removeItem(key: string): void {
            values.delete(key);
        },
        setItem(key: string, value: string): void {
            values.set(key, value);
        },
    };
}

describe("compare-storage", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("saves, replaces by name, lists newest first, and deletes compare runs", () => {
        const storage = memoryStorage();
        vi.spyOn(Date, "now").mockReturnValueOnce(1).mockReturnValueOnce(2).mockReturnValueOnce(3);
        vi.spyOn(Math, "random").mockReturnValue(0.123456);

        const first = saveCompareRun("Daily sweep", config({ seed: "1" }), storage);
        const second = saveCompareRun("Other", config({ seed: "2" }), storage);
        const replacement = saveCompareRun("Daily sweep", config({ seed: "3" }), storage);

        expect(listSavedCompareRuns(storage).map((run) => [run.name, run.config.seed])).toEqual([
            ["Daily sweep", "3"],
            ["Other", "2"],
        ]);

        deleteSavedCompareRun(replacement.id, storage);
        expect(listSavedCompareRuns(storage).map((run) => run.id)).toEqual([second.id]);
        expect(first.id).not.toBe(replacement.id);
    });

    it("saves deduplicated tiling sets and deletes by id", () => {
        const storage = memoryStorage();

        const saved = saveTilingSet("Regular pair", ["square", "hex", "square"], storage);

        expect(listSavedTilingSets(storage)).toMatchObject([
            { id: saved.id, name: "Regular pair", geometries: ["square", "hex"] },
        ]);
        deleteSavedTilingSet(saved.id, storage);
        expect(listSavedTilingSets(storage)).toEqual([]);
    });

    it("ignores malformed storage instead of throwing", () => {
        const storage = memoryStorage();
        storage.setItem("cellular-automaton-lab.compare.v1", "{nope");

        expect(listSavedCompareRuns(storage)).toEqual([]);
        expect(listSavedTilingSets(storage)).toEqual([]);
    });
});
