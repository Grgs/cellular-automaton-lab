import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
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
                tiling_family: "square",
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
                topology_spec: {
                    tiling_family: "square",
                    adjacency_mode: "edge",
                    sizing_mode: "grid",
                    width: 16,
                    height: 16,
                    patch_depth: 0,
                },
                initial_cells_by_id: { "c:1:1": 1, "c:2:1": 1, "c:1:2": 1 },
                final_cells_by_id: { "c:1:1": 1, "c:2:1": 1 },
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
        previewTopology: async () => ({
            topology_revision: "t",
            cells: [
                {
                    id: "c:1:1",
                    kind: "square",
                    center: { x: 0.5, y: 0.5 },
                    vertices: [
                        { x: 0, y: 0 },
                        { x: 1, y: 0 },
                        { x: 1, y: 1 },
                        { x: 0, y: 1 },
                    ],
                },
            ],
        }),
    };
    return { backend, compareSeed };
}

describe("mountComparePanel", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    afterEach(() => {
        document.body.innerHTML = "";
        document.getElementById("compare-panel-styles")?.remove();
        vi.restoreAllMocks();
    });

    it("mounts a toggle and a hidden dialog without throwing", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
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
        const { mountComparePanel } = await import("./compare-panel.js");
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
        expect(request?.include_states).toBe(true);
    });

    it("renders open/share links and opens a share URL in a new tab", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        document.querySelector<HTMLButtonElement>(".compare-run")?.click();

        await vi.waitFor(() => {
            expect(document.querySelector(".compare-row-actions")).not.toBeNull();
        });
        const buttons = [...document.querySelectorAll<HTMLButtonElement>(".compare-link")];
        const labels = buttons.map((button) => button.textContent);
        expect(labels).toEqual(["begin ↗", "end ↗", "⧉ link", "▸ preview"]);

        buttons[0]?.click();
        expect(openSpy).toHaveBeenCalledTimes(1);
        const openedUrl = String(openSpy.mock.calls.at(0)?.[0] ?? "");
        expect(openedUrl).toContain("#share=v1.");
    });

    it("renders a seed pad wired to the seed field", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        expect(document.querySelector(".compare-seedpad")).not.toBeNull();
        const seedField = document.querySelector<HTMLInputElement>(
            'input.compare-field[type="text"]',
        );
        const before = seedField?.value;
        const offCell = document.querySelector<HTMLButtonElement>(
            ".compare-seedpad-cell:not(.is-on)",
        );
        const row = offCell?.getAttribute("data-row");
        const col = offCell?.getAttribute("data-col");
        offCell?.dispatchEvent(new Event("pointerdown", { bubbles: true }));
        expect(seedField?.value).not.toBe(before);
        // the pad re-renders, so re-query the same position
        const painted = document.querySelector<HTMLButtonElement>(
            `.compare-seedpad-cell[data-row="${row}"][data-col="${col}"]`,
        );
        expect(painted?.classList.contains("is-on")).toBe(true);
    });

    it("expands a row preview into begin/end thumbnails", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        document.querySelector<HTMLButtonElement>(".compare-run")?.click();

        await vi.waitFor(() => {
            expect(document.querySelector(".compare-row-actions")).not.toBeNull();
        });
        const previewButton = [
            ...document.querySelectorAll<HTMLButtonElement>(".compare-link"),
        ].find((button) => button.textContent?.includes("preview"));
        expect(previewButton).toBeTruthy();
        previewButton?.click();

        await vi.waitFor(() => {
            // scope to the expanded detail row (the seed-preview strip also renders thumbnails)
            expect(document.querySelectorAll(".compare-detail .compare-thumb")).toHaveLength(2);
        });
        const labels = [...document.querySelectorAll(".compare-thumb-label")].map(
            (n) => n.textContent,
        );
        expect(labels).toEqual(["Begin", "End"]);

        // toggling again collapses the detail row
        previewButton?.click();
        expect(document.querySelector(".compare-detail")).toBeNull();
    });
});
