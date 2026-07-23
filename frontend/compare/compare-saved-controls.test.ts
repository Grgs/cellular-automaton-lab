import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { CompareRunConfig } from "./compare-run-link.js";
import { createCompareSavedControls } from "./compare-saved-controls.js";
import { createCompareWorkspaceStore } from "./compare-workspace-store.js";

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

function button(root: HTMLElement, label: string): HTMLButtonElement {
    const match = [...root.querySelectorAll<HTMLButtonElement>("button")].find(
        (candidate) => candidate.textContent === label,
    );
    if (!match) {
        throw new Error(`Missing ${label} button`);
    }
    return match;
}

describe("compare saved controls", () => {
    beforeEach(() => {
        Object.defineProperty(window, "localStorage", {
            configurable: true,
            value: memoryStorage(),
        });
    });

    afterEach(() => {
        document.body.innerHTML = "";
        window.localStorage.clear();
        vi.restoreAllMocks();
    });

    it("publishes empty saved state and disables unavailable actions", () => {
        const workspaceStore = createCompareWorkspaceStore(config());
        const statusElement = document.createElement("div");
        const controls = createCompareSavedControls({
            workspaceStore,
            currentRunConfig: () => config(),
            selectedGeometries: () => ["square", "hex"],
            applyRunConfig: vi.fn(async () => undefined),
            applyTilingSet: vi.fn(() => ""),
            statusElement,
        });
        document.body.append(controls.element);

        controls.refresh();

        expect(workspaceStore.getState().saved).toEqual({ runs: [], tilingSets: [] });
        expect(
            [...controls.element.querySelectorAll<HTMLElement>(".compare-saved-empty")].map(
                (hint) => hint.textContent,
            ),
        ).toEqual([
            "No saved runs yet. Name the current setup and choose Save run.",
            "No saved tiling sets yet. Select tilings, name the set, and choose Save set.",
        ]);
        expect(button(controls.element, "Load run").disabled).toBe(true);
        expect(button(controls.element, "Delete set").disabled).toBe(true);
    });

    it("owns save, load, replacement, and delete state for runs and tiling sets", async () => {
        const workspaceStore = createCompareWorkspaceStore(config());
        const applyRunConfig = vi.fn(async () => undefined);
        const applyTilingSet = vi.fn((saved) => `Applied ${saved.name}.`);
        const statusElement = document.createElement("div");
        let currentConfig = config();
        let geometries = ["square", "hex"];
        const controls = createCompareSavedControls({
            workspaceStore,
            currentRunConfig: () => currentConfig,
            selectedGeometries: () => geometries,
            applyRunConfig,
            applyTilingSet,
            statusElement,
        });
        document.body.append(controls.element);
        controls.refresh();

        const runName = controls.element.querySelector<HTMLInputElement>(
            'input[aria-label="Saved run name"]',
        )!;
        const setName = controls.element.querySelector<HTMLInputElement>(
            'input[aria-label="Saved tiling set name"]',
        )!;
        runName.value = "Regular run";
        setName.value = "Regular pair";
        button(controls.element, "Save run").click();
        button(controls.element, "Save set").click();

        expect(workspaceStore.getState().saved.runs).toMatchObject([
            { name: "Regular run", config: currentConfig },
        ]);
        expect(workspaceStore.getState().saved.tilingSets).toMatchObject([
            { name: "Regular pair", geometries },
        ]);
        expect(statusElement.textContent).toBe('Saved tiling set "Regular pair".');

        currentConfig = config({ seed: "111" });
        geometries = ["square"];
        button(controls.element, "Save run").click();
        button(controls.element, "Save set").click();
        expect(workspaceStore.getState().saved.runs).toHaveLength(1);
        expect(workspaceStore.getState().saved.runs[0]?.config.seed).toBe("111");
        expect(workspaceStore.getState().saved.tilingSets).toHaveLength(1);
        expect(workspaceStore.getState().saved.tilingSets[0]?.geometries).toEqual(["square"]);

        button(controls.element, "Load run").click();
        await vi.waitFor(() => expect(applyRunConfig).toHaveBeenCalledWith(currentConfig));
        button(controls.element, "Load set").click();
        expect(applyTilingSet).toHaveBeenCalledWith(
            expect.objectContaining({ name: "Regular pair", geometries: ["square"] }),
        );
        expect(statusElement.textContent).toBe("Applied Regular pair.");

        button(controls.element, "Delete run").click();
        button(controls.element, "Delete set").click();
        expect(workspaceStore.getState().saved).toEqual({ runs: [], tilingSets: [] });
        expect(button(controls.element, "Load run").disabled).toBe(true);
        expect(button(controls.element, "Load set").disabled).toBe(true);
    });
});
