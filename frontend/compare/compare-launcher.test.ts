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

describe("mountCompareLauncher", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    afterEach(() => {
        document.body.innerHTML = "";
        document.getElementById("compare-toggle-styles")?.remove();
        document.getElementById("compare-panel-styles")?.remove();
        vi.restoreAllMocks();
    });

    it("renders the toggle eagerly without loading the panel module", async () => {
        const { mountCompareLauncher } = await import("./compare-launcher.js");
        mountCompareLauncher({ backend: fakeBackend(), bootstrapData: bootstrapData() });

        const toggle = document.querySelector<HTMLButtonElement>(".compare-toggle");
        expect(toggle).not.toBeNull();
        expect(document.getElementById("compare-toggle-styles")).not.toBeNull();
        // The heavy panel (its dialog/backdrop) is not mounted until first click.
        expect(document.querySelector(".compare-backdrop")).toBeNull();
    });

    it("lazily mounts and opens the panel on first click", async () => {
        const { mountCompareLauncher } = await import("./compare-launcher.js");
        mountCompareLauncher({ backend: fakeBackend(), bootstrapData: bootstrapData() });

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

    it("disposes the lazily-mounted panel and removes the toggle", async () => {
        const { mountCompareLauncher } = await import("./compare-launcher.js");
        const handle = mountCompareLauncher({
            backend: fakeBackend(),
            bootstrapData: bootstrapData(),
        });
        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-backdrop")).not.toBeNull();
        });

        handle.dispose();
        expect(document.querySelector(".compare-toggle")).toBeNull();
        expect(document.querySelector(".compare-backdrop")).toBeNull();
    });
});
