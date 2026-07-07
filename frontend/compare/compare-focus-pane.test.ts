import { afterEach, describe, expect, it, vi } from "vitest";

import { mountFocusPane } from "./compare-focus-pane.js";
import type { SimulationBackend } from "../types/controller-api.js";
import type { GridView } from "../types/controller-view.js";
import type { AppBootstrapData, PatternPayload, SimulationSnapshot } from "../types/domain.js";

function topologySpec() {
    return {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 2,
        height: 2,
        patch_depth: 0,
    };
}

function bootstrapData(): AppBootstrapData {
    return {
        app_defaults: {
            simulation: {
                topology_spec: topologySpec(),
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
        topology_catalog: [
            {
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
            },
        ],
        periodic_face_tilings: [],
        aperiodic_families: [],
        server_meta: { app_name: "test" },
        snapshot_version: 5,
    };
}

function snapshot(overrides: Partial<SimulationSnapshot> = {}): SimulationSnapshot {
    return {
        topology_spec: topologySpec(),
        speed: 7,
        running: false,
        generation: 0,
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
            topology_spec: topologySpec(),
            width: 2,
            height: 2,
            cells: [
                { id: "a", kind: "square", neighbors: [] },
                { id: "b", kind: "square", neighbors: [] },
            ],
        },
        cell_states: [0, 0],
        ...overrides,
    };
}

function fakeBackend(initial: SimulationSnapshot = snapshot()) {
    const postControl = vi.fn(async (_path: string, _body?: unknown) => initial);
    const setCells = vi.fn(async (_cells: unknown) => initial);
    const dispose = vi.fn();
    const backend: SimulationBackend = {
        getState: async () => initial,
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
            topology_spec: topologySpec(),
            cells: [],
        }),
    };
    return { backend, postControl, setCells, dispose };
}

function fakeGridView(): GridView {
    return {
        render: vi.fn(),
        getCellFromPointerEvent: () => null,
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

const pattern: PatternPayload = {
    format: "cellular-automaton-lab-pattern",
    version: 5,
    topology_spec: topologySpec(),
    rule: "conway",
    cells_by_id: { a: 1 },
};

function mount(fake: ReturnType<typeof fakeBackend>, onDiscard = vi.fn()) {
    const handle = mountFocusPane({
        geometry: "square",
        frameIndex: 9,
        pattern,
        backend: fake.backend,
        bootstrapData: bootstrapData(),
        createGridView: () => fakeGridView(),
        buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
            { ...startCell, state: paintState },
        ],
        onDiscard,
    });
    document.body.append(handle.element);
    return handle;
}

function chipButton(label: string): HTMLButtonElement {
    const button = [
        ...document.querySelectorAll<HTMLButtonElement>(".compare-focus-pane-action"),
    ].find((candidate) => candidate.textContent === label);
    if (!button) {
        throw new Error(`missing chip button: ${label}`);
    }
    return button;
}

describe("mountFocusPane", () => {
    afterEach(() => {
        document.body.innerHTML = "";
        vi.restoreAllMocks();
    });

    it("seeds the fork from the frame pattern and labels the chip", async () => {
        const fake = fakeBackend();
        mount(fake);

        expect(document.querySelector(".compare-focus-pane-info")?.textContent).toContain(
            "Forked from square gen 9",
        );
        // Doubles as the compact gallery-tile label once this board is no
        // longer the hero, so it carries the generation, not a static string.
        expect(document.querySelector(".compare-focus-pane-badge")?.textContent).toBe(
            "live · gen 9",
        );
        await vi.waitFor(() =>
            expect(fake.postControl).toHaveBeenCalledWith("/api/control/reset", {
                topology_spec: pattern.topology_spec,
                speed: 7,
                rule: "conway",
                randomize: false,
            }),
        );
        await vi.waitFor(() => expect(fake.setCells).toHaveBeenCalledWith([{ id: "a", state: 1 }]));
        // The rule's paintable states render as a palette.
        expect(document.querySelectorAll(".compare-focus-pane-swatch")).toHaveLength(2);
    });

    it("steps and runs the fork through the chip controls", async () => {
        const fake = fakeBackend();
        mount(fake);
        await vi.waitFor(() => expect(fake.setCells).toHaveBeenCalled());

        chipButton("Step").click();
        await vi.waitFor(() =>
            expect(fake.postControl).toHaveBeenLastCalledWith("/api/control/step"),
        );

        chipButton("Run").click();
        await vi.waitFor(() =>
            expect(fake.postControl).toHaveBeenLastCalledWith("/api/control/start"),
        );
    });

    it("carries the fork's own generation in its badge as it steps", async () => {
        // The badge doubles as the compact gallery-tile label, so it must track
        // this pane's own (detached) generation, not the seed frame it forked from.
        const stepped = snapshot({ generation: 1 });
        const initial = snapshot();
        const postControl = vi.fn(async (path: string) =>
            path === "/api/control/step" ? stepped : initial,
        );
        const backend: SimulationBackend = {
            getState: async () => initial,
            getRules: async () => ({ rules: [] }),
            dispose: vi.fn(),
            postControl: postControl as unknown as SimulationBackend["postControl"],
            toggleCell: async () => initial,
            setCell: async () => initial,
            setCells: async () => initial,
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
                topology_spec: topologySpec(),
                cells: [],
            }),
        };
        const handle = mountFocusPane({
            geometry: "square",
            frameIndex: 9,
            pattern,
            backend,
            bootstrapData: bootstrapData(),
            createGridView: () => fakeGridView(),
            buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
                { ...startCell, state: paintState },
            ],
            onDiscard: vi.fn(),
        });
        document.body.append(handle.element);
        // The seed lands at generation 0 (the pane's own detached clock),
        // overwriting the pre-seed placeholder that named the forked-from frame.
        await vi.waitFor(() =>
            expect(document.querySelector(".compare-focus-pane-badge")?.textContent).toBe(
                "live · gen 0",
            ),
        );

        chipButton("Step").click();

        await vi.waitFor(() =>
            expect(document.querySelector(".compare-focus-pane-badge")?.textContent).toBe(
                "live · gen 1",
            ),
        );
    });

    it("disposes the session and notifies on discard", async () => {
        const fake = fakeBackend();
        const onDiscard = vi.fn();
        mount(fake, onDiscard);
        await vi.waitFor(() => expect(fake.setCells).toHaveBeenCalled());

        chipButton("Discard").click();
        expect(fake.dispose).toHaveBeenCalledTimes(1);
        expect(onDiscard).toHaveBeenCalledTimes(1);
    });
});
