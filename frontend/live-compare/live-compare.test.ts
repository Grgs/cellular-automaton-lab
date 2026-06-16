import { afterEach, describe, expect, it, vi } from "vitest";
import { mountLiveCompareWorkspace } from "./live-compare.js";
import type { SimulationBackend } from "../types/controller-api.js";
import type { GridView } from "../types/controller-view.js";
import type {
    AppBootstrapData,
    BootstrappedTopologyDefinition,
    SimulationSnapshot,
} from "../types/domain.js";

function topologyDefinition(
    tilingFamily: string,
    label: string,
    order: number,
): BootstrappedTopologyDefinition {
    return {
        tiling_family: tilingFamily,
        label,
        picker_group: "Regular",
        picker_order: order,
        sizing_mode: "grid",
        family: "regular",
        render_kind: "regular_grid",
        viewport_sync_mode: "grid",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "life" },
        geometry_keys: { edge: tilingFamily },
        sizing_policy: {
            control: "cell_size",
            default: 18,
            min: 4,
            max: 48,
        },
    };
}

const bootstrapData: AppBootstrapData = {
    app_defaults: {
        simulation: {
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 12,
                height: 10,
                patch_depth: 3,
            },
            speed: 5,
            rule: "life",
            min_grid_size: 2,
            max_grid_size: 64,
            min_patch_depth: 1,
            max_patch_depth: 6,
            min_speed: 1,
            max_speed: 60,
        },
        ui: {
            cell_size: 18,
            min_cell_size: 4,
            max_cell_size: 48,
            storage_key: "test-ui",
        },
        theme: {
            default: "light",
            storage_key: "test-theme",
        },
    },
    topology_catalog: [
        topologyDefinition("square", "Square", 1),
        topologyDefinition("hex", "Hexagonal", 2),
    ],
    periodic_face_tilings: [],
    aperiodic_families: [],
    server_meta: { app_name: "Cellular Automaton Lab" },
    snapshot_version: 5,
};

function snapshot(tilingFamily = "square", running = false, generation = 0): SimulationSnapshot {
    return {
        topology_spec: {
            tiling_family: tilingFamily,
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 1,
            height: 1,
            patch_depth: 3,
        },
        speed: 5,
        running,
        generation,
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
        topology_revision: `${tilingFamily}-rev`,
        topology: {
            topology_revision: `${tilingFamily}-rev`,
            topology_spec: {
                tiling_family: tilingFamily,
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 1,
                height: 1,
                patch_depth: 3,
            },
            cells: [{ id: "c:0:0", kind: "cell", neighbors: [] }],
        },
        cell_states: [0],
    };
}

class FakeBackend implements SimulationBackend {
    state = snapshot();
    readonly calls: string[] = [];

    constructor(readonly sessionId: string) {}

    getState = vi.fn(async () => this.state);
    getRules = vi.fn(async () => ({ rules: [this.state.rule] }));
    dispose = vi.fn();
    compareSeed = vi.fn();
    requestFilmstrip = vi.fn();
    previewTopology = vi.fn();

    postControl = vi.fn(async (path: string, body?: unknown) => {
        this.calls.push(path);
        if (path === "/api/control/reset") {
            const resetBody = body as { topology_spec: { tiling_family: string } };
            this.state = snapshot(resetBody.topology_spec.tiling_family);
        } else if (path === "/api/control/start" || path === "/api/control/resume") {
            this.state = { ...this.state, running: true };
        } else if (path === "/api/control/pause") {
            this.state = { ...this.state, running: false };
        } else if (path === "/api/control/step") {
            this.state = { ...this.state, generation: this.state.generation + 1 };
        }
        return this.state;
    }) as SimulationBackend["postControl"];

    toggleCell = vi.fn(async () => {
        this.state = {
            ...this.state,
            cell_states: [this.state.cell_states[0] === 0 ? 1 : 0],
        };
        return this.state;
    });

    setCell = vi.fn(async () => this.state);
    setCells = vi.fn(async (cells) => {
        const nextStates = [...this.state.cell_states];
        for (const cell of cells) {
            const index = this.state.topology.cells.findIndex(
                (candidate) => candidate.id === cell.id,
            );
            if (index >= 0) {
                nextStates[index] = cell.state;
            }
        }
        this.state = { ...this.state, cell_states: nextStates };
        return this.state;
    });
}

function createGridView(): GridView {
    return {
        render: vi.fn(),
        getCellFromPointerEvent: vi.fn(() => ({ id: "c:0:0" })),
        setPreviewCells: vi.fn(),
        clearPreview: vi.fn(),
        setHoveredCell: vi.fn(),
        setSelectedCells: vi.fn(),
        getSelectedCells: vi.fn(() => []),
        setGestureOutline: vi.fn(),
        flashGestureOutline: vi.fn(),
        clearGestureOutline: vi.fn(),
    };
}

afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
});

describe("live compare workspace", () => {
    it("disables the trigger when no server session id is available", () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: null,
        });

        expect(trigger.disabled).toBe(true);
        expect(trigger.title).toContain("server sessions");
    });

    it("opens two independent session-backed panes", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        document.body.append(trigger, gridPanel);
        const backends = new Map<string, FakeBackend>();

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-test",
            backendFactory: (sessionId) => {
                const backend = new FakeBackend(sessionId);
                backends.set(sessionId, backend);
                return backend;
            },
            createGridView,
            storage: null,
        });

        trigger.click();

        await vi.waitFor(() => {
            expect(gridPanel.querySelectorAll(".live-compare-pane")).toHaveLength(2);
            expect(backends.get("s-test-left")?.calls).toContain("/api/control/reset");
            expect(backends.get("s-test-right")?.calls).toContain("/api/control/reset");
        });
        expect(gridPanel.classList.contains("is-live-compare")).toBe(true);
        expect(trigger.textContent).toBe("Single View");
    });

    it("drawing mutates only the pane under the pointer", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        document.body.append(trigger, gridPanel);
        const backends = new Map<string, FakeBackend>();

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-edit",
            backendFactory: (sessionId) => {
                const backend = new FakeBackend(sessionId);
                backends.set(sessionId, backend);
                return backend;
            },
            createGridView,
            storage: null,
        });

        trigger.click();
        await vi.waitFor(() => {
            expect(gridPanel.querySelectorAll(".live-compare-canvas")).toHaveLength(2);
        });

        const rightCanvas = gridPanel.querySelectorAll(".live-compare-canvas")[1]!;
        rightCanvas.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, pointerId: 1 }));
        rightCanvas.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, pointerId: 1 }));

        await vi.waitFor(() => {
            expect(backends.get("s-edit-right")?.setCells).toHaveBeenCalledWith([
                { id: "c:0:0", state: 1 },
            ]);
        });
        expect(backends.get("s-edit-left")?.setCells).not.toHaveBeenCalled();
    });

    it("supports click-only canvas editing", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        document.body.append(trigger, gridPanel);
        const backends = new Map<string, FakeBackend>();

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-click-edit",
            backendFactory: (sessionId) => {
                const backend = new FakeBackend(sessionId);
                backends.set(sessionId, backend);
                return backend;
            },
            createGridView,
            storage: null,
        });

        trigger.click();
        await vi.waitFor(() => {
            expect(gridPanel.querySelectorAll(".live-compare-canvas")).toHaveLength(2);
        });

        const leftCanvas = gridPanel.querySelector(".live-compare-canvas")!;
        leftCanvas.dispatchEvent(new MouseEvent("click", { bubbles: true }));

        await vi.waitFor(() => {
            expect(backends.get("s-click-edit-left")?.setCells).toHaveBeenCalledWith([
                { id: "c:0:0", state: 1 },
            ]);
        });
    });

    it("routes top-row run controls to both panes", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        const stepBtn = document.createElement("button");
        const statusText = document.createElement("strong");
        const generationText = document.createElement("strong");
        document.body.append(trigger, stepBtn, statusText, generationText, gridPanel);
        const backends = new Map<string, FakeBackend>();

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-top",
            controls: { stepBtn, statusText, generationText },
            backendFactory: (sessionId) => {
                const backend = new FakeBackend(sessionId);
                backends.set(sessionId, backend);
                return backend;
            },
            createGridView,
            storage: null,
        });

        trigger.click();
        await vi.waitFor(() => {
            expect(gridPanel.querySelectorAll(".live-compare-pane")).toHaveLength(2);
        });

        stepBtn.click();

        await vi.waitFor(() => {
            expect(backends.get("s-top-left")?.state.generation).toBe(1);
            expect(backends.get("s-top-right")?.state.generation).toBe(1);
            expect(generationText.textContent).toBe("1");
        });
        expect(statusText.textContent).toContain("Split");
    });

    it("does not route top-row tiling picker choices to split panes", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        const tilingFamilySelect = document.createElement("select");
        const tilingPickerMenu = document.createElement("div");
        const tilingPickerToggle = document.createElement("button");
        const tilingPickerCurrentLabel = document.createElement("span");
        const squareOption = document.createElement("option");
        squareOption.value = "square";
        const hexOption = document.createElement("option");
        hexOption.value = "hex";
        tilingFamilySelect.append(squareOption, hexOption);
        const squareCard = document.createElement("button");
        squareCard.className = "tiling-preview-card";
        squareCard.dataset.tilingFamily = "square";
        tilingPickerMenu.append(squareCard);
        document.body.append(
            trigger,
            tilingFamilySelect,
            tilingPickerMenu,
            tilingPickerToggle,
            tilingPickerCurrentLabel,
            gridPanel,
        );
        const backends = new Map<string, FakeBackend>();

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-picker",
            controls: {
                tilingFamilySelect,
                tilingPickerMenu,
                tilingPickerToggle,
                tilingPickerCurrentLabel,
            },
            backendFactory: (sessionId) => {
                const backend = new FakeBackend(sessionId);
                backends.set(sessionId, backend);
                return backend;
            },
            createGridView,
            storage: null,
        });

        trigger.click();
        await vi.waitFor(() => {
            expect(gridPanel.querySelectorAll(".live-compare-pane")).toHaveLength(2);
        });

        squareCard.click();

        expect(tilingPickerToggle.disabled).toBe(true);
        expect(backends.get("s-picker-left")?.state.topology_spec.tiling_family).toBe("square");
        expect(backends.get("s-picker-right")?.state.topology_spec.tiling_family).toBe("hex");
    });
});
