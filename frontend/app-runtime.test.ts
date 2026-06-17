import { afterEach, describe, expect, it, vi } from "vitest";
import type { AppBootstrapData, SimulationSnapshot } from "./types/domain.js";

const bootstrapData: AppBootstrapData = {
    app_defaults: {
        simulation: {
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 10,
                height: 6,
                patch_depth: 0,
            },
            speed: 5,
            rule: "life",
            min_grid_size: 4,
            max_grid_size: 200,
            min_patch_depth: 0,
            max_patch_depth: 6,
            min_speed: 1,
            max_speed: 30,
        },
        ui: {
            cell_size: 12,
            min_cell_size: 8,
            max_cell_size: 24,
            storage_key: "ui-key",
        },
        theme: {
            default: "light",
            storage_key: "theme-key",
        },
    },
    topology_catalog: [
        {
            tiling_family: "square",
            label: "Square",
            picker_group: "Regular",
            picker_order: 1,
            sizing_mode: "grid",
            family: "regular",
            render_kind: "regular_grid",
            viewport_sync_mode: "grid",
            supported_adjacency_modes: ["edge"],
            default_adjacency_mode: "edge",
            default_rules: { edge: "life" },
            geometry_keys: { edge: "square" },
            sizing_policy: {
                control: "cell_size",
                default: 12,
                min: 4,
                max: 48,
            },
        },
    ],
    periodic_face_tilings: [],
    aperiodic_families: [],
    server_meta: { app_name: "Cellular Automaton Lab" },
    snapshot_version: 5,
};

function snapshot(): SimulationSnapshot {
    return {
        topology_spec: bootstrapData.app_defaults.simulation.topology_spec,
        speed: 5,
        running: false,
        generation: 0,
        rule: {
            name: "life",
            display_name: "Life",
            description: "",
            default_paint_state: 1,
            supports_randomize: true,
            states: [
                { value: 0, label: "Dead", color: "#fff", paintable: true },
                { value: 1, label: "Live", color: "#000", paintable: true },
            ],
            rule_protocol: "binary",
            supports_all_topologies: true,
            compatible_tiling_families: null,
        },
        topology_revision: "rev",
        topology: {
            topology_revision: "rev",
            topology_spec: bootstrapData.app_defaults.simulation.topology_spec,
            width: 1,
            height: 1,
            cells: [{ id: "c:0:0", kind: "cell", neighbors: [] }],
        },
        cell_states: [0],
    };
}

function installAppShell(): HTMLButtonElement {
    document.body.innerHTML = `
        <main id="main-stage">
            <section id="grid-panel">
                <canvas id="grid"></canvas>
            </section>
            <button id="split-view-toggle-btn" type="button">Split View</button>
            <button id="run-toggle-btn" type="button">Run</button>
            <button id="step-btn" type="button">Step</button>
            <button id="reset-btn" type="button">Reset</button>
            <button id="random-btn" type="button">Random</button>
            <select id="tiling-family-select"></select>
            <button id="tiling-picker-toggle" type="button"></button>
            <div id="tiling-picker-menu"></div>
            <span id="tiling-picker-current-label"></span>
            <span id="status-text"></span>
            <span id="generation-text"></span>
        </main>
    `;
    const trigger = document.getElementById("split-view-toggle-btn");
    if (!(trigger instanceof HTMLButtonElement)) {
        throw new Error("missing split trigger");
    }
    return trigger;
}

function fakeBackend() {
    return {
        getState: vi.fn(async () => snapshot()),
        getRules: vi.fn(async () => ({ rules: [snapshot().rule] })),
        dispose: vi.fn(),
        postControl: vi.fn(async () => snapshot()),
        toggleCell: vi.fn(async () => snapshot()),
        setCell: vi.fn(async () => snapshot()),
        setCells: vi.fn(async () => snapshot()),
        compareSeed: vi.fn(),
        requestFilmstrip: vi.fn(),
        previewTopology: vi.fn(),
    };
}

afterEach(() => {
    document.body.replaceChildren();
    vi.resetModules();
    vi.restoreAllMocks();
});

describe("app runtime", () => {
    it("loads the live split workspace only after the split trigger is clicked", async () => {
        const trigger = installAppShell();
        const backend = fakeBackend();
        const controller = {
            init: vi.fn(async () => {}),
            dispose: vi.fn(),
            refreshState: vi.fn(async () => {}),
            loadRules: vi.fn(async () => {}),
            applySimulationState: vi.fn(),
            applyCellSize: vi.fn(),
            applyPaintState: vi.fn(),
            loadPattern: vi.fn(),
            getState: vi.fn(),
            getInteractions: vi.fn(),
            getViewportController: vi.fn(),
            getConfigSyncController: vi.fn(),
            getUiSessionController: vi.fn(),
        };
        let liveCompareModuleLoaded = false;
        const mountLiveCompareWorkspace = vi.fn(() => ({
            dispose: vi.fn(),
            isOpen: vi.fn(() => false),
        }));

        vi.doMock("./canvas-view.js", () => ({
            createCanvasGridView: vi.fn(() => ({})),
        }));
        vi.doMock("./api.js", () => ({
            createHttpSimulationBackend: vi.fn(() => backend),
        }));
        vi.doMock("./bootstrap-data.js", () => ({
            bootstrapDataFromWindow: vi.fn(() => bootstrapData),
        }));
        vi.doMock("./editor-operations.js", () => ({
            buildEditorToolCells: vi.fn(),
        }));
        vi.doMock("./app-controller.js", () => ({
            createAppController: vi.fn(() => controller),
        }));
        vi.doMock("./compare/compare-launcher.js", () => ({
            mountCompareLauncher: vi.fn(() => ({ dispose: vi.fn() })),
        }));
        vi.doMock("./geometry/registry.js", () => ({
            getGeometryAdapter: vi.fn(() => ({})),
        }));
        vi.doMock("./review-api.js", () => ({
            installReviewApi: vi.fn(() => vi.fn()),
        }));
        vi.doMock("./live-compare/live-compare.js", () => {
            liveCompareModuleLoaded = true;
            return { mountLiveCompareWorkspace };
        });

        const { initApp } = await import("./app-runtime.js");
        await initApp({
            backend,
            bootstrapData,
            liveCompareBaseSessionId: "s-runtime",
        });

        expect(liveCompareModuleLoaded).toBe(false);
        expect(mountLiveCompareWorkspace).not.toHaveBeenCalled();

        trigger.click();

        await vi.waitFor(() => {
            expect(liveCompareModuleLoaded).toBe(true);
            expect(mountLiveCompareWorkspace).toHaveBeenCalledOnce();
        });
        expect(mountLiveCompareWorkspace).toHaveBeenCalledWith(
            expect.objectContaining({
                baseSessionId: "s-runtime",
                disposeBackendsOnClose: false,
            }),
        );
    });
});
