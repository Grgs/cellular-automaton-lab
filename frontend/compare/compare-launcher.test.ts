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

function resetHash(): void {
    // Strip the hash without firing hashchange (live listeners are disposed first).
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
}

describe("mountCompareLauncher", () => {
    const handles: Array<{ dispose(): void }> = [];

    async function mount(): Promise<void> {
        const { mountCompareLauncher } = await import("./compare-launcher.js");
        handles.push(
            mountCompareLauncher({ backend: fakeBackend(), bootstrapData: bootstrapData() }),
        );
    }

    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
        resetHash();
    });

    afterEach(() => {
        // Dispose launchers so their hashchange listeners don't leak into later tests.
        while (handles.length > 0) {
            handles.pop()?.dispose();
        }
        resetHash();
        document.body.innerHTML = "";
        document.getElementById("compare-toggle-styles")?.remove();
        document.getElementById("compare-panel-styles")?.remove();
        vi.restoreAllMocks();
    });

    it("renders the toggle eagerly without loading the panel module", async () => {
        await mount();

        const toggle = document.querySelector<HTMLButtonElement>(".compare-toggle");
        expect(toggle).not.toBeNull();
        expect(document.getElementById("compare-toggle-styles")).not.toBeNull();
        // The heavy panel (its dialog/backdrop) is not mounted until first click.
        expect(document.querySelector(".compare-backdrop")).toBeNull();
    });

    it("lazily mounts and opens the panel on first click", async () => {
        await mount();

        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();

        await vi.waitFor(() => {
            const backdrop = document.querySelector<HTMLElement>(".compare-backdrop");
            expect(backdrop).not.toBeNull();
            // openOnMount means the dialog is visible right after the lazy load.
            expect(backdrop?.hidden).toBe(false);
        });
        // The lazy load reuses the existing toggle rather than adding a second one.
        expect(document.querySelectorAll(".compare-toggle")).toHaveLength(1);
    });

    it("renders the watch-demo banner eagerly", async () => {
        await mount();

        expect(document.querySelector(".compare-watch-banner")).not.toBeNull();
        expect(document.querySelector(".compare-backdrop")).toBeNull();
    });

    it("opens the workspace from the watch-demo banner", async () => {
        await mount();

        document.querySelector<HTMLButtonElement>(".compare-watch-banner")?.click();

        await vi.waitFor(() => {
            const backdrop = document.querySelector<HTMLElement>(".compare-backdrop");
            expect(backdrop).not.toBeNull();
            expect(backdrop?.hidden).toBe(false);
        });
    });

    it("disposes the lazily-mounted panel and removes the toggle", async () => {
        await mount();
        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-backdrop")).not.toBeNull();
        });

        handles.pop()?.dispose();
        expect(document.querySelector(".compare-toggle")).toBeNull();
        expect(document.querySelector(".compare-backdrop")).toBeNull();
    });

    it("opens via a #/compare deep link present on first load", async () => {
        window.location.hash = "#/compare";
        await mount();

        await vi.waitFor(() => {
            const backdrop = document.querySelector<HTMLElement>(".compare-backdrop");
            expect(backdrop).not.toBeNull();
            expect(backdrop?.hidden).toBe(false);
        });
        expect(document.querySelector(".compare-dialog--workspace")).not.toBeNull();
        expect(document.querySelector(".compare-back")?.textContent).toBe("← Back to build");
    });

    it("restores a run link without starting the run", async () => {
        const { encodeCompareRunFragment } = await import("./compare-run-link.js");
        window.location.hash = `#/compare&${encodeCompareRunFragment({
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
        window.location.hash = "#/compare&run=v2.bogus";
        await mount();

        await vi.waitFor(() => {
            const backdrop = document.querySelector<HTMLElement>(".compare-backdrop");
            expect(backdrop?.hidden).toBe(false);
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "newer version",
            );
        });
    });

    it("mirrors the route into the hash on open and clears it on close", async () => {
        await mount();
        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        await vi.waitFor(() => {
            expect(document.querySelector<HTMLElement>(".compare-backdrop")?.hidden).toBe(false);
        });
        expect(window.location.hash).toBe("#/compare");

        document.querySelector<HTMLButtonElement>(".compare-close")?.click();
        expect(document.querySelector<HTMLElement>(".compare-backdrop")?.hidden).toBe(true);
        expect(window.location.hash).toBe("");
    });

    it("closes the panel when the hash navigates away from compare", async () => {
        await mount();
        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        await vi.waitFor(() => {
            expect(document.querySelector<HTMLElement>(".compare-backdrop")?.hidden).toBe(false);
        });

        // Simulate the back button leaving the compare route.
        window.location.hash = "";
        window.dispatchEvent(new Event("hashchange"));
        expect(document.querySelector<HTMLElement>(".compare-backdrop")?.hidden).toBe(true);
    });
});
