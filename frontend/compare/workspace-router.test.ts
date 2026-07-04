import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type { AppBootstrapData, SimulationSnapshot } from "../types/domain.js";
import type { SimulationBackend } from "../types/controller.js";

function bootstrapData(): AppBootstrapData {
    const topology = (
        tiling_family: string,
        geometry: string,
        family: string,
    ): AppBootstrapData["topology_catalog"][number] => ({
        tiling_family,
        label: tiling_family,
        picker_group: family,
        picker_order: 0,
        mode_type: "adjacency",
        mode_label: "Mode",
        mode_labels: { edge: "Edge adjacency" },
        sizing_mode: "grid",
        family,
        render_kind: "square",
        viewport_sync_mode: "frontend",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "conway" },
        geometry_keys: { edge: geometry },
        sizing_policy: { control: "cell_size", default: 16, min: 2, max: 64 },
    });
    return {
        app_defaults: {} as AppBootstrapData["app_defaults"],
        topology_catalog: [topology("Square", "square", "regular")],
        periodic_face_tilings: [],
        aperiodic_families: [],
        server_meta: { app_name: "test" },
        snapshot_version: 5,
    };
}

function fakeBackend(): SimulationBackend {
    const snapshot = {} as SimulationSnapshot;
    return {
        getState: async () => snapshot,
        getRules: async () => ({ rules: [] }),
        dispose: () => {},
        postControl: async () => snapshot,
        toggleCell: async () => snapshot,
        setCell: async () => snapshot,
        setCells: async () => snapshot,
        compareSeed: async () => ({
            rule_name: "conway",
            seed: "",
            seed_bits: 0,
            traversal: "bfs",
            steps: 1,
            grid_size: 16,
            degenerate: false,
            results: [],
        }),
        requestFilmstrip: async () => ({
            rule_name: "conway",
            seed: "",
            traversal: "bfs",
            frame_count: 0,
            grid_size: 12,
            tilings: [],
        }),
        previewTopology: async () => ({
            topology_revision: "t",
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 16,
                height: 16,
                patch_depth: 0,
            },
            cells: [],
        }),
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

function resetHash(): void {
    // Strip the hash without firing hashchange (live listeners are disposed first).
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
}

function markDemoSeenInStorage(): void {
    window.localStorage.setItem(
        "cellular-automaton-lab.compare.v1",
        JSON.stringify({ runs: [], tilingSets: [], demoSeenAt: 1 }),
    );
}

function backdrop(): HTMLElement | null {
    return document.querySelector<HTMLElement>(".compare-backdrop");
}

describe("mountWorkspaceRouter", () => {
    const handles: Array<{ dispose(): void }> = [];

    async function mount(options: { wallTrigger?: HTMLButtonElement } = {}): Promise<void> {
        const { mountWorkspaceRouter } = await import("./workspace-router.js");
        handles.push(
            mountWorkspaceRouter({
                backend: fakeBackend(),
                bootstrapData: bootstrapData(),
                ...(options.wallTrigger ? { wallTrigger: options.wallTrigger } : {}),
            }),
        );
    }

    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
        Object.defineProperty(window, "localStorage", {
            configurable: true,
            value: memoryStorage(),
        });
        // Most cases exercise routing, not the demo; mark it seen up front and
        // let the demo-specific cases clear the flag.
        markDemoSeenInStorage();
        resetHash();
    });

    afterEach(() => {
        // Dispose routers so their hashchange listeners don't leak into later tests.
        while (handles.length > 0) {
            handles.pop()?.dispose();
        }
        resetHash();
        document.body.innerHTML = "";
        document.getElementById("workspace-router-styles")?.remove();
        document.getElementById("compare-panel-styles")?.remove();
        window.localStorage.clear();
        vi.restoreAllMocks();
    });

    it("lands on the wall for a bare URL", async () => {
        await mount();

        await vi.waitFor(() => {
            expect(backdrop()).not.toBeNull();
            expect(backdrop()?.hidden).toBe(false);
        });
        expect(document.querySelector(".compare-dialog--workspace")).not.toBeNull();
        // The wall never renders a floating toggle or watch banner.
        expect(document.querySelector(".compare-toggle")).toBeNull();
        expect(document.querySelector(".compare-watch-banner")).toBeNull();
    });

    it("keeps the wall closed for a #/lab deep link", async () => {
        window.location.hash = "#/lab";
        await mount();

        // The panel chunk is never loaded for a Lab landing.
        expect(document.querySelector(".compare-backdrop")).toBeNull();
        expect(document.querySelector<HTMLElement>(".wall-loading-veil")?.hidden).toBe(true);
    });

    it("keeps the wall closed for a bare share link (share implies Lab)", async () => {
        window.location.hash = "#share=v1.abc";
        await mount();

        expect(document.querySelector(".compare-backdrop")).toBeNull();
    });

    it("opens the wall for the legacy #/compare alias", async () => {
        window.location.hash = "#/compare";
        await mount();

        await vi.waitFor(() => {
            expect(backdrop()?.hidden).toBe(false);
        });
    });

    it("writes #/lab when the wall is left via Open the Lab", async () => {
        await mount();
        await vi.waitFor(() => {
            expect(backdrop()?.hidden).toBe(false);
        });

        document.querySelector<HTMLButtonElement>(".compare-back")?.click();

        expect(backdrop()?.hidden).toBe(true);
        expect(window.location.hash).toBe("#/lab");
    });

    it("closes the wall when the hash navigates to the Lab", async () => {
        await mount();
        await vi.waitFor(() => {
            expect(backdrop()?.hidden).toBe(false);
        });

        // Simulate the back button landing on the Lab route.
        window.location.hash = "#/lab";
        window.dispatchEvent(new Event("hashchange"));
        expect(backdrop()?.hidden).toBe(true);
    });

    it("returns to the wall from the Lab via the wall trigger", async () => {
        window.location.hash = "#/lab";
        const wallTrigger = document.createElement("button");
        document.body.append(wallTrigger);
        await mount({ wallTrigger });

        expect(document.querySelector(".compare-backdrop")).toBeNull();

        // No manual hashchange: entering the wall strips the hash to empty via
        // replaceState (which fires no event), so the trigger must resolve the
        // destination itself.
        wallTrigger.click();

        await vi.waitFor(() => {
            expect(backdrop()?.hidden).toBe(false);
        });
        expect(window.location.hash).toBe("");
    });

    it("restores a run link without starting the run", async () => {
        const { encodeCompareRunFragment } = await import("./compare-run-link.js");
        window.location.hash = `#${encodeCompareRunFragment({
            seed: "101",
            rule: "conway",
            traversal: "row-major",
            frames: 12,
            grid_size: 8,
            geometries: ["square"],
        })}`;
        await mount();

        await vi.waitFor(() => {
            expect(
                document.querySelector<HTMLInputElement>('input.compare-field[type="text"]')?.value,
            ).toBe("101");
        });
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toBe(
            "Loaded run link — 1 tilings ready.",
        );
    });

    it("surfaces a status message for a run link it cannot open", async () => {
        // A newer-version run slot the current build cannot decode.
        window.location.hash = "#run=v2.bogus";
        await mount();

        await vi.waitFor(() => {
            expect(backdrop()?.hidden).toBe(false);
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "newer version",
            );
        });
    });

    it("autoplays the featured demo once on a first visit", async () => {
        window.localStorage.clear();
        await mount();

        await vi.waitFor(() => {
            expect(backdrop()?.hidden).toBe(false);
        });
        // The demo applied its curated config (shape seed) and marked itself seen.
        await vi.waitFor(() => {
            const shapeSelect = [
                ...document.querySelectorAll<HTMLSelectElement>("select.compare-field"),
            ].find((select) =>
                [...select.options].some((option) => option.value === "r-pentomino"),
            );
            expect(shapeSelect?.value).toBe("r-pentomino");
        });
        const raw = window.localStorage.getItem("cellular-automaton-lab.compare.v1") ?? "{}";
        expect(typeof JSON.parse(raw).demoSeenAt).toBe("number");
    });

    it("does not autoplay the demo when it was already seen", async () => {
        await mount();

        await vi.waitFor(() => {
            expect(backdrop()?.hidden).toBe(false);
        });
        const shapeSelect = [
            ...document.querySelectorAll<HTMLSelectElement>("select.compare-field"),
        ].find((select) => [...select.options].some((option) => option.value === "r-pentomino"));
        // Bit-seed mode is the untouched default; the demo did not apply its config.
        expect(shapeSelect?.value).toBe("");
    });

    it("does not autoplay the demo over a run link, even on a first visit", async () => {
        window.localStorage.clear();
        const { encodeCompareRunFragment } = await import("./compare-run-link.js");
        window.location.hash = `#${encodeCompareRunFragment({
            seed: "101",
            rule: "conway",
            traversal: "bfs",
            frames: 12,
            grid_size: 8,
            geometries: ["square"],
        })}`;
        await mount();

        await vi.waitFor(() => {
            expect(
                document.querySelector<HTMLInputElement>('input.compare-field[type="text"]')?.value,
            ).toBe("101");
        });
        const raw = window.localStorage.getItem("cellular-automaton-lab.compare.v1");
        expect(raw).toBeNull();
    });

    it("disposes the panel and the loading veil", async () => {
        await mount();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-backdrop")).not.toBeNull();
        });

        handles.pop()?.dispose();
        expect(document.querySelector(".compare-backdrop")).toBeNull();
        expect(document.querySelector(".wall-loading-veil")).toBeNull();
    });
});
