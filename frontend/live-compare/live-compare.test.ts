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
    overrides: Partial<BootstrappedTopologyDefinition> = {},
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
        ...overrides,
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
        topologyDefinition("archimedean-3-3-3-3-6", "Snub Trihexagonal", 3, {
            picker_group: "Periodic Mixed",
            family: "mixed",
            render_kind: "polygon_periodic",
            viewport_sync_mode: "backend-sync",
            default_rules: { edge: "kagome-life" },
            geometry_keys: { edge: "archimedean-3-3-3-3-6" },
            sizing_policy: {
                control: "cell_size",
                default: 16,
                min: 14,
                max: 20,
            },
        }),
        topologyDefinition("ammann-beenker", "Ammann-Beenker", 4, {
            picker_group: "Aperiodic",
            sizing_mode: "patch_depth",
            family: "aperiodic",
            render_kind: "polygon_aperiodic",
            viewport_sync_mode: "presentation-only",
            default_rules: { edge: "life-b2-s23" },
            geometry_keys: { edge: "ammann-beenker" },
            sizing_policy: {
                control: "patch_depth",
                default: 4,
                min: 0,
                max: 4,
            },
        }),
    ],
    periodic_face_tilings: [],
    aperiodic_families: [],
    server_meta: { app_name: "Cellular Automaton Lab" },
    snapshot_version: 5,
};

function snapshot(
    tilingFamily = "square",
    running = false,
    generation = 0,
    width = 1,
    patchDepth = 3,
): SimulationSnapshot {
    const cells = Array.from({ length: width }, (_, x) => ({
        id: `c:${x}:0`,
        kind: "cell",
        x,
        y: 0,
        neighbors: [],
    }));
    return {
        topology_spec: {
            tiling_family: tilingFamily,
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width,
            height: 1,
            patch_depth: patchDepth,
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
                width,
                height: 1,
                patch_depth: patchDepth,
            },
            width,
            height: 1,
            cells,
        },
        cell_states: Array.from({ length: width }, () => 0),
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
            const resetBody = body as {
                topology_spec: { tiling_family: string; width: number; patch_depth?: number };
            };
            this.state = snapshot(
                resetBody.topology_spec.tiling_family,
                false,
                0,
                resetBody.topology_spec.width,
                resetBody.topology_spec.patch_depth ?? 3,
            );
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

function createCoordinateGridView(): GridView {
    return {
        ...createGridView(),
        getCellFromPointerEvent: vi.fn((event: Event) => {
            const rect = (event.currentTarget as HTMLElement | null)?.getBoundingClientRect();
            if (!rect) {
                return null;
            }
            const clientX = (event as MouseEvent).clientX;
            const x = clientX - rect.left < rect.width / 2 ? 0 : 1;
            return { id: `c:${x}:0`, x, y: 0 };
        }),
    };
}

function setCanvasRect(canvas: Element): void {
    canvas.getBoundingClientRect = () =>
        ({
            left: 20,
            top: 10,
            right: 120,
            bottom: 60,
            width: 100,
            height: 50,
            x: 20,
            y: 10,
            toJSON: () => ({}),
        }) as DOMRect;
}

function createCanvasPointerEvent(type: string, clientX: number): PointerEvent {
    const event = new MouseEvent(type, { bubbles: true, clientX });
    Object.defineProperty(event, "pointerId", { value: 1 });
    return event as PointerEvent;
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

    it("disposes and recreates pane backends on close when configured", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        document.body.append(trigger, gridPanel);
        const backends: FakeBackend[] = [];

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-dispose",
            backendFactory: (sessionId) => {
                const backend = new FakeBackend(sessionId);
                backends.push(backend);
                return backend;
            },
            disposeBackendsOnClose: true,
            createGridView,
            storage: null,
        });

        trigger.click();
        await vi.waitFor(() => {
            expect(backends).toHaveLength(2);
            expect(backends[0]?.calls).toContain("/api/control/reset");
            expect(backends[1]?.calls).toContain("/api/control/reset");
        });

        trigger.click();

        await vi.waitFor(() => {
            expect(backends).toHaveLength(4);
            expect(backends[0]?.dispose).toHaveBeenCalledOnce();
            expect(backends[1]?.dispose).toHaveBeenCalledOnce();
        });
        expect(gridPanel.classList.contains("is-live-compare")).toBe(false);

        trigger.click();

        await vi.waitFor(() => {
            expect(backends[2]?.calls).toContain("/api/control/reset");
            expect(backends[3]?.calls).toContain("/api/control/reset");
        });
        expect(backends[2]?.sessionId).toBe("s-dispose-left");
        expect(backends[3]?.sessionId).toBe("s-dispose-right");
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

    it("click editing uses the cell resolved from scaled canvas coordinates", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        document.body.append(trigger, gridPanel);
        const backends = new Map<string, FakeBackend>();

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-scaled-click",
            backendFactory: (sessionId) => {
                const backend = new FakeBackend(sessionId);
                backends.set(sessionId, backend);
                return backend;
            },
            createGridView: createCoordinateGridView,
            storage: null,
        });

        trigger.click();
        await vi.waitFor(() => {
            expect(gridPanel.querySelectorAll(".live-compare-canvas")).toHaveLength(2);
        });

        const leftCanvas = gridPanel.querySelector(".live-compare-canvas")!;
        setCanvasRect(leftCanvas);
        leftCanvas.dispatchEvent(new MouseEvent("click", { bubbles: true, clientX: 95 }));

        await vi.waitFor(() => {
            expect(backends.get("s-scaled-click-left")?.setCells).toHaveBeenCalledWith([
                { id: "c:1:0", state: 1 },
            ]);
        });
    });

    it("brush editing follows the cells resolved from scaled canvas coordinates", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        document.body.append(trigger, gridPanel);
        const backends = new Map<string, FakeBackend>();
        const buildEditorToolCells = vi.fn((_state, _tool, startCell, endCell, paintState) =>
            [startCell, endCell ?? startCell].map((cell) => ({ id: cell.id, state: paintState })),
        );

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-scaled-brush",
            backendFactory: (sessionId) => {
                const backend = new FakeBackend(sessionId);
                backends.set(sessionId, backend);
                return backend;
            },
            createGridView: createCoordinateGridView,
            buildEditorToolCells,
            storage: null,
        });

        trigger.click();
        await vi.waitFor(() => {
            expect(gridPanel.querySelectorAll(".live-compare-canvas")).toHaveLength(2);
        });

        const leftCanvas = gridPanel.querySelector(".live-compare-canvas")!;
        setCanvasRect(leftCanvas);
        leftCanvas.dispatchEvent(createCanvasPointerEvent("pointerdown", 30));
        leftCanvas.dispatchEvent(createCanvasPointerEvent("pointermove", 95));
        leftCanvas.dispatchEvent(createCanvasPointerEvent("pointerup", 95));

        await vi.waitFor(() => {
            expect(backends.get("s-scaled-brush-left")?.setCells).toHaveBeenCalledWith([
                { id: "c:0:0", state: 1 },
                { id: "c:1:0", state: 1 },
            ]);
        });
    });

    it("fits heavy mixed tiling resets to the split pane viewport", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        document.body.append(trigger, gridPanel);
        const backends = new Map<string, FakeBackend>();
        const resolveViewportDimensions = vi.fn(() => ({ width: 6, height: 5 }));

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-heavy-mixed",
            backendFactory: (sessionId) => {
                const backend = new FakeBackend(sessionId);
                backends.set(sessionId, backend);
                return backend;
            },
            createGridView,
            resolveViewportDimensions,
            storage: null,
        });

        trigger.click();
        await vi.waitFor(() => {
            expect(gridPanel.querySelectorAll(".live-compare-pane")).toHaveLength(2);
        });

        const leftPane = gridPanel.querySelector('.live-compare-pane[data-pane="left"]')!;
        const leftViewport = leftPane.querySelector(".live-compare-pane-viewport")!;
        Object.defineProperty(leftViewport, "clientWidth", { configurable: true, value: 360 });
        Object.defineProperty(leftViewport, "clientHeight", { configurable: true, value: 260 });
        const leftSelect = leftPane.querySelector<HTMLSelectElement>(
            ".live-compare-tiling-select",
        )!;
        resolveViewportDimensions.mockClear();

        leftSelect.value = "archimedean-3-3-3-3-6";
        leftSelect.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(backends.get("s-heavy-mixed-left")?.state.topology_spec.tiling_family).toBe(
                "archimedean-3-3-3-3-6",
            );
        });
        expect(resolveViewportDimensions).toHaveBeenCalledWith({
            viewportWidth: 360,
            viewportHeight: 260,
            geometry: "archimedean-3-3-3-3-6",
            cellSize: 16,
            fallbackDimensions: { width: 12, height: 10 },
            maxCellCount: 1800,
        });
        expect(backends.get("s-heavy-mixed-left")?.postControl).toHaveBeenLastCalledWith(
            "/api/control/reset",
            expect.objectContaining({
                rule: "kagome-life",
                topology_spec: expect.objectContaining({
                    tiling_family: "archimedean-3-3-3-3-6",
                    width: 6,
                    height: 5,
                }),
            }),
        );
    });

    it("uses a shallower Ammann-Beenker patch in split view", async () => {
        const trigger = document.createElement("button");
        const gridPanel = document.createElement("section");
        document.body.append(trigger, gridPanel);
        const backends = new Map<string, FakeBackend>();

        mountLiveCompareWorkspace({
            trigger,
            gridPanel,
            bootstrapData,
            baseSessionId: "s-ammann",
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

        const leftPane = gridPanel.querySelector('.live-compare-pane[data-pane="left"]')!;
        const leftSelect = leftPane.querySelector<HTMLSelectElement>(
            ".live-compare-tiling-select",
        )!;

        leftSelect.value = "ammann-beenker";
        leftSelect.dispatchEvent(new Event("change"));

        await vi.waitFor(() => {
            expect(backends.get("s-ammann-left")?.state.topology_spec.tiling_family).toBe(
                "ammann-beenker",
            );
        });
        expect(backends.get("s-ammann-left")?.state.topology_spec.patch_depth).toBe(3);
        expect(backends.get("s-ammann-left")?.postControl).toHaveBeenLastCalledWith(
            "/api/control/reset",
            expect.objectContaining({
                rule: "life-b2-s23",
                topology_spec: expect.objectContaining({
                    tiling_family: "ammann-beenker",
                    sizing_mode: "patch_depth",
                    patch_depth: 3,
                }),
            }),
        );
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
