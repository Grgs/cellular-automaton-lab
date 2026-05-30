import { afterEach, describe, expect, it, vi } from "vitest";

import { mountComparePanel } from "./compare-panel.js";
import type {
    AppBootstrapData,
    SeedComparisonResult,
    SimulationSnapshot,
} from "../types/domain.js";
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
        topology_catalog: [
            topology("Square", "square", "regular"),
            topology("Hex", "hex", "regular"),
            topology("Spectre", "spectre", "aperiodic"),
        ],
        periodic_face_tilings: [],
        aperiodic_families: [],
        server_meta: { app_name: "test" },
        snapshot_version: 5,
    };
}

function comparisonResult(): SeedComparisonResult {
    return {
        rule_name: "conway",
        seed: "111",
        seed_bits: 3,
        traversal: "bfs",
        steps: 5,
        grid_size: 16,
        degenerate: false,
        results: [
            {
                geometry: "square",
                tiling_family: "Square",
                family: "regular",
                cell_count: 100,
                seed_bits: 3,
                seed_cells: 3,
                initial_population: 3,
                final_population: 4,
                normalized_population: 1.33,
                classification: "still-life",
                period: 1,
                steps_run: 2,
                extinction_step: null,
                note: null,
                population: [3, 4, 4],
                change_rate: [0.04, 0],
            },
        ],
    };
}

function fakeBackend(): { backend: SimulationBackend; compareSeed: ReturnType<typeof vi.fn> } {
    const snapshot = {} as SimulationSnapshot;
    const compareSeed = vi.fn(async () => comparisonResult());
    const backend: SimulationBackend = {
        getState: async () => snapshot,
        getRules: async () => ({
            rules: [
                {
                    name: "conway",
                    display_name: "Conway",
                    description: "",
                    default_paint_state: 1,
                    supports_randomize: true,
                    states: [],
                    rule_protocol: "universal-v1",
                    supports_all_topologies: true,
                },
            ],
        }),
        dispose: () => {},
        postControl: async () => snapshot,
        toggleCell: async () => snapshot,
        setCell: async () => snapshot,
        setCells: async () => snapshot,
        compareSeed,
    };
    return { backend, compareSeed };
}

describe("mountComparePanel", () => {
    afterEach(() => {
        document.body.innerHTML = "";
        document.getElementById("compare-panel-styles")?.remove();
    });

    it("mounts a toggle and a hidden dialog without throwing", () => {
        const { backend } = fakeBackend();
        const handle = mountComparePanel({ backend, bootstrapData: bootstrapData() });
        const toggle = document.querySelector(".compare-toggle");
        const backdrop = document.querySelector<HTMLElement>(".compare-backdrop");
        expect(toggle).not.toBeNull();
        expect(backdrop?.hidden).toBe(true);
        // Default representative selection: both regular grids + one aperiodic.
        expect(document.querySelectorAll(".compare-tiling input:checked")).toHaveLength(3);
        handle.dispose();
        expect(document.querySelector(".compare-toggle")).toBeNull();
    });

    it("runs a comparison and renders the portrait and grid", async () => {
        const { backend, compareSeed } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        document.querySelector<HTMLButtonElement>(".compare-run")?.click();

        await vi.waitFor(() => {
            expect(compareSeed).toHaveBeenCalledTimes(1);
            expect(document.querySelector(".compare-grid tbody tr")).not.toBeNull();
        });
        expect(document.querySelectorAll(".compare-portrait__line").length).toBeGreaterThan(0);
        const request = compareSeed.mock.calls.at(0)?.[0];
        expect(request?.geometries).toContain("square");
        expect(request?.traversal).toBe("bfs");
    });
});
