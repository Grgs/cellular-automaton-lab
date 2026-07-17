import { afterEach, describe, expect, it, vi } from "vitest";

import { createEditablePane, geometryForSpec, paneSessionId } from "./pane-core.js";
import type { SimulationBackend } from "../types/controller-api.js";
import type { GridView } from "../types/controller-view.js";
import type {
    AppBootstrapData,
    BootstrappedTopologyDefinition,
    PatternPayload,
    SimulationSnapshot,
} from "../types/domain.js";

function squareDefinition(): BootstrappedTopologyDefinition {
    return {
        tiling_family: "square",
        label: "Square",
        picker_group: "Regular",
        picker_order: 0,
        mode_type: "adjacency",
        mode_label: "Mode",
        mode_labels: { edge: "Edge adjacency" },
        sizing_mode: "grid",
        family: "regular",
        render_kind: "regular_grid",
        viewport_sync_mode: "grid",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "conway" },
        geometry_keys: { edge: "square" },
        sizing_policy: { control: "cell_size", default: 12, min: 4, max: 48 },
    };
}

function bootstrapData(): AppBootstrapData {
    return {
        app_defaults: {
            simulation: {
                topology_spec: {
                    tiling_family: "square",
                    adjacency_mode: "edge",
                    sizing_mode: "grid",
                    width: 2,
                    height: 2,
                    patch_depth: 0,
                },
                speed: 7,
                rule: "conway",
                min_grid_size: 2,
                max_grid_size: 64,
                min_patch_depth: 0,
                max_patch_depth: 6,
                min_speed: 1,
                max_speed: 30,
            },
            ui: { cell_size: 12, min_cell_size: 8, max_cell_size: 24, storage_key: "ui" },
            theme: { default: "light", storage_key: "theme" },
        },
        topology_catalog: [squareDefinition()],
        periodic_face_tilings: [],
        aperiodic_families: [],
        server_meta: { app_name: "test" },
        snapshot_version: 5,
    };
}

function snapshot(overrides: Partial<SimulationSnapshot> = {}): SimulationSnapshot {
    const topology_spec = {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 2,
        height: 2,
        patch_depth: 0,
    };
    return {
        topology_spec,
        speed: 7,
        running: false,
        generation: 0,
        state_revision: 0,
        rule: {
            name: "conway",
            display_name: "Conway",
            description: "",
            default_paint_state: 1,
            supports_randomize: true,
            states: [
                { value: 0, label: "Dead", color: "#fff", paintable: true },
                { value: 1, label: "Live", color: "#000", paintable: true },
            ],
            rule_protocol: "universal-v1",
            supports_all_topologies: true,
            compatible_tiling_families: null,
        },
        topology_revision: "rev",
        topology: {
            topology_revision: "rev",
            topology_spec,
            width: 2,
            height: 2,
            cells: [
                { id: "a", kind: "square", neighbors: [] },
                { id: "b", kind: "square", neighbors: [] },
                { id: "c", kind: "square", neighbors: [] },
                { id: "d", kind: "square", neighbors: [] },
            ],
        },
        cell_states: [0, 0, 0, 0],
        ...overrides,
    };
}

interface FakeBackend {
    backend: SimulationBackend;
    postControl: ReturnType<typeof vi.fn>;
    setCells: ReturnType<typeof vi.fn>;
    getState: ReturnType<typeof vi.fn>;
    dispose: ReturnType<typeof vi.fn>;
}

function fakeBackend(initial: SimulationSnapshot = snapshot()): FakeBackend {
    const getState = vi.fn(async () => initial);
    const postControl = vi.fn(async (_path: string, _body?: unknown) => initial);
    const setCells = vi.fn(async (_cells: unknown) => initial);
    const dispose = vi.fn();
    const backend: SimulationBackend = {
        getState,
        getRules: async () => ({ rules: [] }),
        dispose,
        postControl: postControl as unknown as SimulationBackend["postControl"],
        toggleCell: async () => initial,
        setCell: async () => initial,
        setCells: setCells as unknown as SimulationBackend["setCells"],
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
            topology_revision: "rev",
            topology_spec: snapshot().topology_spec,
            cells: [],
        }),
    };
    return { backend, postControl, setCells, getState, dispose };
}

function fakeGridView(cell: { id: string } | null = { id: "a" }): GridView {
    return {
        render: vi.fn(),
        getCellFromPointerEvent: () => cell,
        setPreviewCells: vi.fn(),
        clearPreview: vi.fn(),
        setHoveredCell: vi.fn(),
        setSelectedCells: vi.fn(),
        getSelectedCells: () => [],
        setGestureOutline: vi.fn(),
        flashGestureOutline: vi.fn(),
        clearGestureOutline: vi.fn(),
    };
}

function mountPane(fake: FakeBackend, gridView: GridView = fakeGridView()) {
    const canvas = document.createElement("canvas");
    const viewport = document.createElement("div");
    viewport.append(canvas);
    document.body.append(viewport);
    const pane = createEditablePane({
        canvas,
        viewport,
        backend: fake.backend,
        gridView,
        bootstrapData: bootstrapData(),
        definitions: [squareDefinition()],
        getPaintState: () => 1,
    });
    return { pane, canvas };
}

describe("pane-core helpers", () => {
    it("sanitizes session id parts", () => {
        expect(paneSessionId("Base Session!", "focus")).toBe("Base-Session--focus");
    });

    it("resolves a geometry from a spec's tiling family", () => {
        expect(geometryForSpec([squareDefinition()], snapshot().topology_spec)).toBe("square");
    });
});

describe("createEditablePane", () => {
    afterEach(() => {
        document.body.innerHTML = "";
        vi.restoreAllMocks();
    });

    it("seeds a board from a pattern: reset with the spec/rule, then set the sparse cells", async () => {
        const fake = fakeBackend();
        const gridView = fakeGridView();
        const { pane } = mountPane(fake, gridView);
        const pattern: PatternPayload = {
            format: "cellular-automaton-lab-pattern",
            version: 5,
            topology_spec: snapshot().topology_spec,
            rule: "conway",
            cells_by_id: { a: 1, c: 1 },
        };

        await pane.seedFromPattern(pattern, 7);

        expect(fake.postControl).toHaveBeenCalledWith("/api/control/reset", {
            topology_spec: pattern.topology_spec,
            speed: 7,
            rule: "conway",
            randomize: false,
        });
        expect(fake.setCells).toHaveBeenCalledWith([
            { id: "a", state: 1 },
            { id: "c", state: 1 },
        ]);
        expect(gridView.render).toHaveBeenCalled();
    });

    it("skips the cell write when the forked frame is empty", async () => {
        const fake = fakeBackend();
        const { pane } = mountPane(fake);
        await pane.seedFromPattern(
            {
                format: "cellular-automaton-lab-pattern",
                version: 5,
                topology_spec: snapshot().topology_spec,
                rule: "conway",
                cells_by_id: {},
            },
            7,
        );

        expect(fake.postControl).toHaveBeenCalledWith("/api/control/reset", expect.anything());
        expect(fake.setCells).not.toHaveBeenCalled();
    });

    it("steps and toggles run/pause through the session control endpoints", async () => {
        const paused = snapshot({ running: false, generation: 0 });
        const fake = fakeBackend(paused);
        const { pane } = mountPane(fake);
        pane.applySnapshot(paused);

        await pane.step();
        expect(fake.postControl).toHaveBeenLastCalledWith("/api/control/step");

        // Paused at gen 0 -> start.
        await pane.runToggle();
        expect(fake.postControl).toHaveBeenLastCalledWith("/api/control/start");

        // Paused at gen > 0 -> resume.
        pane.applySnapshot(snapshot({ running: false, generation: 4 }));
        await pane.runToggle();
        expect(fake.postControl).toHaveBeenLastCalledWith("/api/control/resume");

        // Running -> pause.
        pane.applySnapshot(snapshot({ running: true, generation: 4 }));
        await pane.runToggle();
        expect(fake.postControl).toHaveBeenLastCalledWith("/api/control/pause");
    });

    it("commits a painted cell to the session on a canvas click", async () => {
        const fake = fakeBackend();
        const { pane, canvas } = mountPane(fake, fakeGridView({ id: "b" }));
        pane.applySnapshot(snapshot());

        canvas.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        await vi.waitFor(() => expect(fake.setCells).toHaveBeenCalledWith([{ id: "b", state: 1 }]));
    });

    it("applies a programmatic cell edit without a pointer gesture", async () => {
        const fake = fakeBackend();
        const { pane } = mountPane(fake);
        pane.applySnapshot(snapshot());

        await pane.applyCellEdit("b", 1);

        expect(fake.setCells).toHaveBeenCalledWith([{ id: "b", state: 1 }]);
    });

    it("no-ops a programmatic cell edit that matches the current state", async () => {
        const fake = fakeBackend();
        const { pane } = mountPane(fake);
        pane.applySnapshot(snapshot({ cell_states: [0, 1, 0, 0] }));

        await pane.applyCellEdit("b", 1);

        expect(fake.setCells).not.toHaveBeenCalled();
    });

    it("undoes and redoes a committed paint as inverse cell writes", async () => {
        const fake = fakeBackend();
        const { pane } = mountPane(fake);
        pane.applySnapshot(snapshot());

        expect(pane.canUndo()).toBe(false);
        await pane.applyCellEdit("b", 1);
        expect(fake.setCells).toHaveBeenLastCalledWith([{ id: "b", state: 1 }]);
        expect(pane.canUndo()).toBe(true);
        expect(pane.canRedo()).toBe(false);

        // Undo restores b's pre-paint state (0), not a board-wide rewind.
        await pane.undo();
        expect(fake.setCells).toHaveBeenLastCalledWith([{ id: "b", state: 0 }]);
        expect(pane.canUndo()).toBe(false);
        expect(pane.canRedo()).toBe(true);

        // Redo re-applies the paint.
        await pane.redo();
        expect(fake.setCells).toHaveBeenLastCalledWith([{ id: "b", state: 1 }]);
        expect(pane.canUndo()).toBe(true);
        expect(pane.canRedo()).toBe(false);
    });

    it("clears the redo stack when a new paint is committed", async () => {
        const fake = fakeBackend();
        const { pane } = mountPane(fake);
        pane.applySnapshot(snapshot());

        await pane.applyCellEdit("b", 1);
        await pane.undo();
        expect(pane.canRedo()).toBe(true);

        // A fresh paint invalidates the redo branch.
        await pane.applyCellEdit("c", 1);
        expect(pane.canRedo()).toBe(false);
        expect(pane.canUndo()).toBe(true);
    });

    it("clears both history stacks on reseed", async () => {
        const fake = fakeBackend();
        const { pane } = mountPane(fake);
        pane.applySnapshot(snapshot());
        await pane.applyCellEdit("b", 1);
        await pane.undo();
        expect(pane.canRedo()).toBe(true);

        await pane.seedFromPattern(
            {
                format: "cellular-automaton-lab-pattern",
                version: 5,
                topology_spec: snapshot().topology_spec,
                rule: "conway",
                cells_by_id: { a: 1 },
            },
            7,
        );

        expect(pane.canUndo()).toBe(false);
        expect(pane.canRedo()).toBe(false);
    });

    it("stops responding to canvas clicks after dispose", async () => {
        const fake = fakeBackend();
        const { pane, canvas } = mountPane(fake, fakeGridView({ id: "b" }));
        pane.applySnapshot(snapshot());
        pane.dispose();

        canvas.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        await new Promise((resolve) => setTimeout(resolve, 10));
        expect(fake.setCells).not.toHaveBeenCalled();
    });
});
