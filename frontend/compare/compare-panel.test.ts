import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type {
    AppBootstrapData,
    CompareRequest,
    FilmstripRequest,
    SeedComparisonResult,
    SeedFilmstripResult,
    SimulationSnapshot,
    TopologyPreviewRequest,
} from "../types/domain.js";
import type { SimulationBackend } from "../types/controller.js";
import type { GridView } from "../types/controller-view.js";
import type { FocusPaneServices } from "../pane/pane-core.js";
import type { ComparePanelHandle } from "./compare-panel.js";

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
        app_defaults: {
            simulation: {
                topology_spec: {
                    tiling_family: "square",
                    adjacency_mode: "edge",
                    sizing_mode: "grid",
                    width: 16,
                    height: 16,
                    patch_depth: 0,
                },
                speed: 5,
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
            topology("Square", "square", "regular"),
            topology("Hex", "hex", "regular"),
            topology("Kagome", "kagome", "mixed"),
            topology("Periodic Face", "periodic-face", "periodic"),
            topology("Spectre", "spectre", "aperiodic"),
            topology("Penrose", "penrose", "aperiodic"),
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

function fakeBackend() {
    const snapshot = {} as SimulationSnapshot;
    const compareSeed = vi.fn(async (_request: CompareRequest) => comparisonResult());
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
                    compatible_tiling_families: null,
                },
                {
                    name: "wireworld",
                    display_name: "WireWorld",
                    description: "",
                    default_paint_state: 1,
                    supports_randomize: true,
                    states: [],
                    rule_protocol: "universal-v1",
                    supports_all_topologies: true,
                    compatible_tiling_families: null,
                },
                {
                    name: "kagome-life",
                    display_name: "Kagome Life",
                    description: "",
                    default_paint_state: 1,
                    supports_randomize: true,
                    states: [],
                    rule_protocol: "mixed-v1",
                    supports_all_topologies: false,
                    compatible_tiling_families: ["Kagome"],
                },
            ],
        }),
        dispose: () => {},
        postControl: async () => snapshot,
        toggleCell: async () => snapshot,
        setCell: async () => snapshot,
        setCells: async () => snapshot,
        compareSeed,
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

function twoBoardFilmstrip(): SeedFilmstripResult {
    const board = (geometry: string) => ({
        geometry,
        tiling_family: geometry,
        family: "regular",
        cell_count: 100,
        topology: {} as never,
        topology_spec: {
            tiling_family: geometry,
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 16,
            height: 16,
            patch_depth: 0,
        },
        frames: [{ "c:1:1": 1 }, { "c:2:1": 1 }],
        extinction_step: null,
        period: null,
        note: null,
        // Pull-back map for edit mode: bit i of the seed lands on seed_order[i].
        seed_order: ["c:1:1", "c:2:1"],
    });
    return {
        rule_name: "conway",
        seed: "111",
        traversal: "bfs",
        frame_count: 2,
        grid_size: 16,
        tilings: [board("square"), board("hex")],
    };
}

/** Three boards: above the two-board minimum, so per-board removal is offered. */
function threeBoardFilmstrip(): SeedFilmstripResult {
    const base = twoBoardFilmstrip();
    const third = { ...base.tilings[0]!, geometry: "tri", tiling_family: "tri" };
    return { ...base, tilings: [...base.tilings, third] };
}

function fourBoardFilmstrip(): SeedFilmstripResult {
    const base = twoBoardFilmstrip();
    const extra = ["kagome", "periodic-face"].map((geometry) => ({
        ...base.tilings[0]!,
        geometry,
        tiling_family: geometry,
    }));
    return { ...base, tilings: [...base.tilings, ...extra] };
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

function forkSnapshot(): SimulationSnapshot {
    return {
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 16,
            height: 16,
            patch_depth: 0,
        },
        speed: 5,
        running: false,
        generation: 9,
        state_revision: 0,
        state_epoch: 1,
        rule: {
            name: "conway",
            display_name: "Conway",
            description: "",
            default_paint_state: 1,
            supports_randomize: true,
            states: [{ value: 1, label: "Live", color: "#000", paintable: true }],
            rule_protocol: "universal-v1",
            supports_all_topologies: true,
            compatible_tiling_families: null,
        },
        topology_revision: "rev",
        topology: {
            topology_revision: "rev",
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 16,
                height: 16,
                patch_depth: 0,
            },
            width: 16,
            height: 16,
            cells: [{ id: "c:1:1", kind: "square", neighbors: [] }],
        },
        cell_states: [0],
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

function deferred<T>(): {
    promise: Promise<T>;
    resolve: (value: T) => void;
    reject: (reason: unknown) => void;
} {
    let resolve!: (value: T) => void;
    let reject!: (reason: unknown) => void;
    const promise = new Promise<T>((nextResolve, nextReject) => {
        resolve = nextResolve;
        reject = nextReject;
    });
    return { promise, resolve, reject };
}

function clickRunAnalysis(): void {
    const button = [...document.querySelectorAll<HTMLButtonElement>(".compare-run")].find(
        (candidate) => candidate.textContent === "Run analysis",
    );
    if (!button) {
        throw new Error("missing Run analysis button");
    }
    button.click();
}

function setTilingSearch(query: string): void {
    const search = document.querySelector<HTMLInputElement>(".compare-tilings-search");
    if (!search) {
        throw new Error("missing tiling search");
    }
    search.value = query;
    search.dispatchEvent(new Event("input", { bubbles: true }));
}

function clickPreset(label: string): void {
    const button = [...document.querySelectorAll<HTMLButtonElement>(".compare-mini")].find(
        (candidate) => candidate.textContent === label,
    );
    if (!button) {
        throw new Error(`missing preset ${label}`);
    }
    button.click();
}

function clickButton(label: string): void {
    const button = [...document.querySelectorAll<HTMLButtonElement>("button")].find(
        (candidate) => candidate.textContent === label,
    );
    if (!button) {
        throw new Error(`missing button ${label}`);
    }
    button.click();
}

function activePresetLabels(): string[] {
    return [...document.querySelectorAll<HTMLButtonElement>(".compare-tilings-presets button")]
        .filter((button) => button.getAttribute("aria-pressed") === "true")
        .map((button) => button.textContent ?? "");
}

function tilingLabels(): string[] {
    return [...document.querySelectorAll<HTMLElement>(".compare-tiling span")].map(
        (node) => node.textContent ?? "",
    );
}

function checkedTilingLabels(): string[] {
    return [...document.querySelectorAll<HTMLLabelElement>(".compare-tiling")]
        .filter((label) => label.querySelector<HTMLInputElement>("input")?.checked)
        .map((label) => label.querySelector("span")?.textContent ?? "");
}

function disabledTilingLabels(): string[] {
    return [...document.querySelectorAll<HTMLLabelElement>(".compare-tiling")]
        .filter((label) => label.querySelector<HTMLInputElement>("input")?.disabled)
        .map((label) => label.querySelector("span")?.textContent ?? "");
}

function selectedChipLabels(): string[] {
    return [...document.querySelectorAll<HTMLElement>(".compare-selected-chip-label")].map(
        (node) => node.textContent ?? "",
    );
}

function removeSelectedChip(label: string): void {
    const chip = [...document.querySelectorAll<HTMLButtonElement>(".compare-selected-chip")].find(
        (candidate) => candidate.textContent?.includes(label),
    );
    if (!chip) {
        throw new Error(`missing selected chip ${label}`);
    }
    chip.click();
}

function summaryText(): string {
    return document.querySelector<HTMLElement>(".compare-tilings-summary")?.textContent ?? "";
}

function familyHeaderTexts(): string[] {
    return [...document.querySelectorAll<HTMLElement>(".compare-tilings-family")].map((header) => {
        const family = header.querySelector<HTMLElement>("span:nth-child(2)")?.textContent ?? "";
        const count = header.querySelector<HTMLElement>(".compare-family-count")?.textContent ?? "";
        return `${family} ${count}`;
    });
}

function menuByLabel(label: string): HTMLDetailsElement {
    const menu = [...document.querySelectorAll<HTMLDetailsElement>(".compare-action-menu")].find(
        (candidate) => candidate.querySelector("summary")?.textContent === label,
    );
    if (!menu) {
        throw new Error(`missing action menu ${label}`);
    }
    return menu;
}

function clickMenuItem(menuLabel: string, itemLabel: string): void {
    const menu = menuByLabel(menuLabel);
    menu.open = true;
    const item = [...menu.querySelectorAll<HTMLButtonElement>(".compare-action-menu-item")].find(
        (candidate) => candidate.textContent === itemLabel,
    );
    if (!item) {
        throw new Error(`missing ${itemLabel} in ${menuLabel} menu`);
    }
    item.click();
}

describe("mountComparePanel", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
        Object.defineProperty(window, "localStorage", {
            configurable: true,
            value: memoryStorage(),
        });
    });

    afterEach(() => {
        document.body.innerHTML = "";
        document.getElementById("compare-panel-styles")?.remove();
        window.history.replaceState(null, "", "/");
        window.localStorage?.clear();
        vi.restoreAllMocks();
        Object.defineProperty(window, "innerWidth", { configurable: true, value: 1024 });
    });

    it("mounts hidden, opens via the handle, and renders no trigger of its own", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({ backend, bootstrapData: bootstrapData() });
        const page = document.querySelector<HTMLElement>(".wall-page");
        // The workspace router owns opening; the panel renders no toggle button.
        expect(document.querySelector(".compare-toggle")).toBeNull();
        expect(page?.hidden).toBe(true);
        // Default representative selection: both regular grids + one per other family.
        expect(document.querySelectorAll(".compare-tiling input:checked")).toHaveLength(5);
        expect(activePresetLabels()).toEqual(["Representative"]);

        handle.open();
        expect(page?.hidden).toBe(false);
        handle.dispose();
        expect(document.querySelector(".wall-page")).toBeNull();
    });

    it("shows empty saved-state hints and disables unavailable saved actions", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        const hints = [...document.querySelectorAll<HTMLElement>(".compare-saved-empty")].map(
            (hint) => hint.textContent,
        );
        expect(hints).toEqual([
            "No saved runs yet. Name the current setup and choose Save run.",
            "No saved tiling sets yet. Select tilings, name the set, and choose Save set.",
        ]);
        expect(
            document.querySelector<HTMLSelectElement>('select[aria-label="Saved compare runs"]')
                ?.disabled,
        ).toBe(true);
        const loadRun = [...document.querySelectorAll<HTMLButtonElement>("button")].find(
            (button) => button.textContent === "Load run",
        );
        const deleteSet = [...document.querySelectorAll<HTMLButtonElement>("button")].find(
            (button) => button.textContent === "Delete set",
        );
        expect(loadRun?.disabled).toBe(true);
        expect(deleteSet?.disabled).toBe(true);
        handle.dispose();
    });

    it("filters tilings by search without changing the selected set", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        expect(summaryText()).toBe("5 / 6 selected · Regular 2 · Mixed 2 · Aperiodic 1");
        expect(selectedChipLabels()).toEqual([
            "Square",
            "Hex",
            "Kagome",
            "Periodic Face",
            "Spectre",
        ]);
        expect(familyHeaderTexts()).toEqual([
            "regular 2/2",
            "mixed 1/1",
            "periodic 1/1",
            "aperiodic 1/2",
        ]);

        setTilingSearch("Penrose");
        expect(tilingLabels()).toEqual(["Penrose"]);
        expect(checkedTilingLabels()).toEqual([]);
        expect(selectedChipLabels()).toContain("Square");
        expect(selectedChipLabels()).toContain("Spectre");
        expect(summaryText()).toBe("5 / 6 selected · Regular 2 · Mixed 2 · Aperiodic 1");
        expect(familyHeaderTexts()).toEqual(["aperiodic 1/2"]);

        setTilingSearch("aperiodic");
        expect(tilingLabels()).toEqual(["Spectre", "Penrose"]);
        handle.dispose();
    });

    it("removes selected tilings from the persistent chip row", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        setTilingSearch("Penrose");
        expect(tilingLabels()).toEqual(["Penrose"]);
        removeSelectedChip("Square");

        expect(selectedChipLabels()).not.toContain("Square");
        expect(summaryText()).toBe("4 / 6 selected · Regular 1 · Mixed 2 · Aperiodic 1");
        setTilingSearch("");
        expect(checkedTilingLabels()).toEqual(["Hex", "Kagome", "Periodic Face", "Spectre"]);
        expect(activePresetLabels()).toEqual([]);
        handle.dispose();
    });

    it("shows an empty state when no tilings match the search", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        setTilingSearch("not-a-tiling");

        expect(document.querySelector(".compare-tilings-empty")?.textContent).toBe(
            "No tilings match this search.",
        );
        expect(tilingLabels()).toEqual([]);
        expect(summaryText()).toBe("5 / 6 selected · Regular 2 · Mixed 2 · Aperiodic 1");
        handle.dispose();
    });

    it("applies tiling presets and updates the family summary", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        clickPreset("Regular");
        expect(checkedTilingLabels()).toEqual(["Square", "Hex"]);
        expect(summaryText()).toBe("2 / 6 selected · Regular 2");
        expect(activePresetLabels()).toEqual(["Regular"]);
        expect(familyHeaderTexts()).toEqual([
            "regular 2/2",
            "mixed 0/1",
            "periodic 0/1",
            "aperiodic 0/2",
        ]);

        clickPreset("Mixed");
        expect(checkedTilingLabels()).toEqual(["Kagome", "Periodic Face"]);
        expect(summaryText()).toBe("2 / 6 selected · Mixed 2");
        expect(activePresetLabels()).toEqual(["Mixed"]);

        clickPreset("Aperiodic");
        expect(checkedTilingLabels()).toEqual(["Spectre", "Penrose"]);
        expect(summaryText()).toBe("2 / 6 selected · Aperiodic 2");
        expect(activePresetLabels()).toEqual(["Aperiodic"]);

        clickPreset("All");
        expect(checkedTilingLabels()).toEqual([
            "Square",
            "Hex",
            "Kagome",
            "Periodic Face",
            "Spectre",
            "Penrose",
        ]);
        expect(summaryText()).toBe("6 / 6 selected · Regular 2 · Mixed 2 · Aperiodic 2");
        expect(activePresetLabels()).toEqual(["All"]);

        clickPreset("None");
        expect(checkedTilingLabels()).toEqual([]);
        expect(summaryText()).toBe("0 / 6 selected");
        expect(activePresetLabels()).toEqual(["None"]);

        clickPreset("Representative");
        expect(checkedTilingLabels()).toEqual([
            "Square",
            "Hex",
            "Kagome",
            "Periodic Face",
            "Spectre",
        ]);
        expect(summaryText()).toBe("5 / 6 selected · Regular 2 · Mixed 2 · Aperiodic 1");
        expect(activePresetLabels()).toEqual(["Representative"]);
        handle.dispose();
    });

    it("caps new wall selections on narrow screens and explains the limit", async () => {
        const originalWidth = window.innerWidth;
        Object.defineProperty(window, "innerWidth", { configurable: true, value: 480 });
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        try {
            clickPreset("All");
            expect(checkedTilingLabels()).toHaveLength(4);
            expect(disabledTilingLabels()).toEqual(["Spectre", "Penrose"]);
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "supports up to 4 tilings",
            );
            expect(
                document.querySelector<HTMLInputElement>(".compare-tiling input:disabled")?.title,
            ).toContain("supports up to 4 tilings");
        } finally {
            handle.dispose();
            Object.defineProperty(window, "innerWidth", {
                configurable: true,
                value: originalWidth,
            });
        }
    });

    it("prevents a seventh tiling before sending a filmstrip request", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const sourceData = bootstrapData();
        const square = sourceData.topology_catalog[0]!;
        const triangle = {
            ...square,
            tiling_family: "Triangle",
            label: "Triangle",
            picker_order: 99,
            geometry_keys: { edge: "triangle" },
        };
        const data: AppBootstrapData = {
            ...sourceData,
            topology_catalog: [...sourceData.topology_catalog, triangle],
        };
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: data,
        });

        clickPreset("All");
        expect(checkedTilingLabels()).toHaveLength(6);
        expect(disabledTilingLabels()).toEqual(["Triangle"]);
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
            "supports up to 6 tilings",
        );

        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        expect(requestFilmstrip.mock.calls[0]?.[0]?.geometries).toHaveLength(6);
        await vi.waitFor(() => {
            expect(
                document.querySelector<HTMLButtonElement>(".compare-filmstrip-add")?.disabled,
            ).toBe(true);
        });
        document.querySelector<HTMLButtonElement>(".compare-filmstrip-add")?.click();
        expect(requestFilmstrip).toHaveBeenCalledTimes(1);
        handle.dispose();
    });

    it("clears the active preset when the selection becomes custom", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        clickPreset("Regular");
        expect(activePresetLabels()).toEqual(["Regular"]);

        document.querySelector<HTMLInputElement>(".compare-tiling input:checked")?.click();

        expect(summaryText()).toBe("1 / 6 selected · Regular 1");
        expect(activePresetLabels()).toEqual([]);
        expect(familyHeaderTexts()).toEqual([
            "regular 1/2",
            "mixed 0/1",
            "periodic 0/1",
            "aperiodic 0/2",
        ]);
        handle.dispose();
    });

    it("runs with selected tilings hidden by the current search", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        clickPreset("Regular");
        setTilingSearch("Penrose");
        expect(tilingLabels()).toEqual(["Penrose"]);

        clickRunAnalysis();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        expect(compareSeed.mock.calls.at(0)?.[0]?.geometries).toEqual(["square", "hex"]);
        handle.dispose();
    });

    it("leads with the side-by-side and demotes the analysis below it", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        await vi.waitFor(() => {
            expect(
                document.querySelector<HTMLElement>(".compare-setup-strip")?.textContent,
            ).toContain("Conway");
        });
        const setupStrip = document.querySelector<HTMLElement>(".compare-setup-strip");
        expect(setupStrip?.textContent).toContain("Seed");
        expect(setupStrip?.textContent).toContain("Rule");
        expect(setupStrip?.textContent).toContain("Tilings");
        expect(setupStrip?.textContent).toContain("Run comparison");
        expect(setupStrip?.querySelectorAll(".compare-setup-status")).toHaveLength(2);
        expect(
            setupStrip?.querySelector<HTMLButtonElement>(".compare-setup-action")?.textContent,
        ).toContain("Edit");
        const explainer = document.querySelector<HTMLElement>(".compare-explainer");
        expect(explainer?.textContent).toContain("Same seed");
        expect(explainer?.textContent).toContain("Same rule");
        expect(explainer?.textContent).toContain("Different tilings");

        const runButtons = [...document.querySelectorAll<HTMLButtonElement>(".compare-run")];
        const play = runButtons.find((b) => b.textContent === "Run comparison");
        const run = runButtons.find((b) => b.textContent === "Run analysis");

        // Run comparison is the primary wall action; Run analysis is secondary.
        expect(play?.classList.contains("compare-run-secondary")).toBe(false);
        expect(run?.classList.contains("compare-run-secondary")).toBe(true);

        // The live filmstrip appears above the analysis section in document order,
        // and the Run button + results live inside that (scroll-down) section.
        const filmstrip = document.querySelector(".compare-filmstrip-area");
        const analysis = document.querySelector(".compare-analysis");
        expect(filmstrip).not.toBeNull();
        expect(analysis).not.toBeNull();
        expect(
            filmstrip!.compareDocumentPosition(analysis!) & Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();
        expect(analysis!.contains(run ?? null)).toBe(true);
        expect(analysis!.querySelector(".compare-results")).not.toBeNull();

        // Each capability is owned by the workspace region that renders it.
        const saved = document.querySelector(".compare-saved");
        expect(saved).not.toBeNull();
        expect(filmstrip?.closest(".compare-board-wall")).not.toBeNull();
        expect(analysis?.closest(".compare-inspector")).not.toBeNull();
        expect(saved?.closest(".compare-setup-sidebar")).not.toBeNull();
        handle.dispose();
    });

    it("edits the comparison seed and rule from the setup strip", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-setup-select")).toHaveLength(2);
        });
        const [seedSelect, ruleSelect] = [
            ...document.querySelectorAll<HTMLSelectElement>(".compare-setup-select"),
        ];
        if (!seedSelect || !ruleSelect) {
            throw new Error("missing setup strip selects");
        }

        seedSelect.value = "glider";
        seedSelect.dispatchEvent(new Event("change"));
        ruleSelect.value = "wireworld";
        ruleSelect.dispatchEvent(new Event("change"));

        const analysisRun = [...document.querySelectorAll<HTMLButtonElement>(".compare-run")].find(
            (button) => button.textContent === "Run analysis",
        );
        analysisRun?.click();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        expect(compareSeed.mock.calls.at(0)?.[0]).toMatchObject({
            pattern: "glider",
            rule: "wireworld",
            geometries: ["square", "hex", "kagome", "periodic-face", "spectre"],
        });
        handle.dispose();
    });

    it("runs the filmstrip from the setup strip primary action", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });

        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();

        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        const setupRun = document.querySelector<HTMLButtonElement>(".compare-setup-run");
        await vi.waitFor(() => expect(setupRun?.textContent).toBe("Up to date"));
        expect(setupRun?.disabled).toBe(true);
        handle.dispose();
    });

    it("auto-runs only the latest configuration after 400 ms", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        const seedField = document.querySelector<HTMLInputElement>(
            'input.compare-field[type="text"]',
        );
        if (!seedField) throw new Error("missing seed field");

        for (const seed of ["1", "10", "10101"]) {
            seedField.value = seed;
            seedField.dispatchEvent(new Event("input", { bubbles: true }));
        }
        expect(requestFilmstrip).not.toHaveBeenCalled();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1), {
            timeout: 1_000,
        });
        expect(requestFilmstrip.mock.calls[0]?.[0]?.seed).toBe("10101");
        handle.dispose();
    });

    it("shows invalid auto-run configuration inline without issuing a request", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async () => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        const wallGenerations = document.querySelector<HTMLInputElement>(
            ".compare-form input[type=number]",
        );
        if (!wallGenerations) throw new Error("missing wall generations field");
        wallGenerations.value = "0";
        wallGenerations.dispatchEvent(new Event("input", { bubbles: true }));

        await new Promise((resolve) => window.setTimeout(resolve, 500));
        expect(requestFilmstrip).not.toHaveBeenCalled();
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
            "Wall generations must be an integer",
        );
        handle.dispose();
    });

    it("runs analysis only while its tab is visible and reuses the normalized cache", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        const requestFilmstrip = vi.fn(async () => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, compareSeed, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));

        const tab = (label: string) =>
            [...document.querySelectorAll<HTMLButtonElement>(".compare-config-tab")].find(
                (button) => button.textContent === label,
            );
        tab("Analysis")?.click();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1), { timeout: 1_000 });
        tab("Setup")?.click();
        tab("Analysis")?.click();
        await new Promise((resolve) => window.setTimeout(resolve, 500));

        expect(compareSeed).toHaveBeenCalledTimes(1);
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
            "cached",
        );
        handle.dispose();
    });

    it("only highlights the setup run action when the wall is stale", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async () => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        const setupRun = document.querySelector<HTMLButtonElement>(".compare-setup-run");
        setupRun?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        await vi.waitFor(() => expect(setupRun?.textContent).toBe("Up to date"));
        expect(setupRun?.classList.contains("is-current")).toBe(true);
        expect(setupRun?.disabled).toBe(true);

        const seedField = document.querySelector<HTMLInputElement>(
            'input.compare-field[type="text"]',
        );
        seedField!.value = "10101";
        seedField!.dispatchEvent(new Event("input", { bubbles: true }));

        expect(setupRun?.textContent).toBe("Run now");
        expect(setupRun?.classList.contains("is-stale")).toBe(true);
        expect(setupRun?.disabled).toBe(false);
        setupRun?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        await vi.waitFor(() => expect(setupRun?.textContent).toBe("Up to date"));
        handle.dispose();
    });

    it("applies a WireWorld rule change to the next filmstrip request", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async (request: FilmstripRequest) => ({
            ...twoBoardFilmstrip(),
            rule_name: request.rule ?? "conway",
        }));
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        const applyButton = document.querySelector<HTMLButtonElement>(".compare-setup-run");
        applyButton?.click();
        await vi.waitFor(() => expect(applyButton?.textContent).toBe("Up to date"));

        const ruleSelect = document.querySelector<HTMLSelectElement>(
            'select[aria-label="Comparison rule"]',
        );
        if (!ruleSelect) {
            throw new Error("missing comparison rule select");
        }
        ruleSelect.value = "wireworld";
        ruleSelect.dispatchEvent(new Event("change", { bubbles: true }));

        expect(applyButton?.textContent).toBe("Run now");
        applyButton?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        expect(requestFilmstrip.mock.calls[1]?.[0]?.rule).toBe("wireworld");
        await vi.waitFor(() => expect(applyButton?.textContent).toBe("Up to date"));
        handle.dispose();
    });

    it("restores a valid bit seed when the setup strip leaves an empty named shape", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        await handle.applyRunConfig({
            seed: "",
            rule: "conway",
            traversal: "bfs",
            frames: 12,
            grid_size: 16,
            geometries: ["square", "hex"],
            pattern: "r-pentomino",
        });

        const seedSelect = document.querySelector<HTMLSelectElement>(
            'select[aria-label="Comparison seed"]',
        );
        if (!seedSelect) {
            throw new Error("missing comparison seed select");
        }
        seedSelect.value = "";
        seedSelect.dispatchEvent(new Event("change", { bubbles: true }));

        expect(
            document.querySelector<HTMLInputElement>('input.compare-field[type="text"]')?.value,
        ).toBe("01100 11000 01000");
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        expect(requestFilmstrip.mock.calls[0]?.[0]).toMatchObject({
            seed: "01100 11000 01000",
        });
        expect(requestFilmstrip.mock.calls[0]?.[0]?.pattern).toBeUndefined();
        handle.dispose();
    });

    it("renders a compact add control without counting it as a board tile", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async () => fourBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });

        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();

        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(4);
        });
        expect(document.querySelector(".compare-filmstrip-add")).not.toBeNull();
        expect(document.querySelectorAll(".compare-filmstrip-label")).toHaveLength(4);
        expect(document.querySelectorAll(".compare-filmstrip-count")).toHaveLength(4);
        handle.dispose();
    });

    it("shows building and updating states while filmstrip requests are in flight", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const resolvers: Array<(filmstrip: SeedFilmstripResult) => void> = [];
        const requestFilmstrip = vi.fn(
            () =>
                new Promise<SeedFilmstripResult>((resolve) => {
                    resolvers.push(resolve);
                }),
        );
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        const run = document.querySelector<HTMLButtonElement>(".compare-setup-run");
        run?.click();
        expect(run?.textContent).toBe("Running...");

        await vi.waitFor(() => {
            expect(document.querySelector<HTMLElement>(".compare-wall-loading")?.hidden).toBe(
                false,
            );
        });
        expect(document.querySelector(".compare-wall-loading")?.textContent).toContain(
            "Building comparison...",
        );

        resolvers.shift()?.(twoBoardFilmstrip());
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
            expect(document.querySelector<HTMLElement>(".compare-wall-loading")?.hidden).toBe(true);
        });

        const seedField = document.querySelector<HTMLInputElement>(
            'input.compare-field[type="text"]',
        );
        seedField!.value = "1110";
        seedField!.dispatchEvent(new Event("input", { bubbles: true }));
        expect(run?.textContent).toBe("Run now");
        run?.click();
        expect(run?.textContent).toBe("Applying...");
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-wall-loading")?.textContent).toContain(
                "Updating comparison...",
            );
        });
        expect(document.querySelector<HTMLElement>(".compare-wall-loading")?.hidden).toBe(false);
        resolvers.shift()?.(twoBoardFilmstrip());
        await vi.waitFor(() => {
            expect(document.querySelector<HTMLElement>(".compare-wall-loading")?.hidden).toBe(true);
        });
        handle.dispose();
    });

    it("uses setup tabs while analysis renders in the inspector", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        await vi.waitFor(() => {
            expect(
                document.querySelector<HTMLElement>(".compare-setup-strip")?.textContent,
            ).toContain("Conway");
        });

        const sheet = document.querySelector<HTMLElement>(".compare-config-sheet");
        expect(sheet?.classList.contains("is-open")).toBe(true);
        expect(document.querySelector<HTMLElement>("#compare-config-panel-setup")?.hidden).toBe(
            false,
        );
        expect(sheet?.textContent).toContain("Run comparison");

        document.querySelector<HTMLButtonElement>("#compare-config-tab-analysis")?.click();
        expect(document.querySelector<HTMLElement>("#compare-config-panel-analysis")?.hidden).toBe(
            false,
        );
        expect(
            document
                .querySelector<HTMLElement>("#compare-config-panel-analysis")
                ?.closest(".compare-inspector"),
        ).not.toBeNull();
        document.querySelector<HTMLButtonElement>("#compare-config-tab-help")?.click();
        const helpPanel = document.querySelector<HTMLElement>("#compare-config-panel-help");
        expect(helpPanel?.hidden).toBe(false);
        expect(helpPanel?.textContent).toContain("Same seed");
        expect(helpPanel?.textContent).toContain("Different tilings");
        document.querySelector<HTMLButtonElement>(".compare-run-secondary")?.click();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        handle.dispose();
    });

    it("keeps tiling-specific rules out of the comparison wall", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        await vi.waitFor(() => {
            expect(
                document.querySelectorAll(".compare-setup-select option").length,
            ).toBeGreaterThan(0);
        });
        const ruleValues = [...document.querySelectorAll<HTMLOptionElement>("select option")].map(
            (option) => option.value,
        );
        expect(ruleValues).toContain("wireworld");
        expect(ruleValues).not.toContain("kagome-life");
        expect(disabledTilingLabels()).toEqual([]);
        handle.dispose();
    });

    it("keeps default filmstrip tilings when the active Lab rule is too narrow", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripRequests: FilmstripRequest[] = [];
        const requestFilmstrip: SimulationBackend["requestFilmstrip"] = async (request) => {
            filmstripRequests.push(request);
            return twoBoardFilmstrip();
        };
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
            getInitialRuleName: () => "kagome-life",
        });

        await handle.runDefaultFilmstrip({
            seed: "",
            rule: "conway",
            traversal: "bfs",
            frames: 12,
            grid_size: 8,
            geometries: ["square", "hex"],
            pattern: "r-pentomino",
        });

        expect(filmstripRequests).toHaveLength(1);
        expect(filmstripRequests[0]?.rule).toBe("conway");
        expect(filmstripRequests[0]?.geometries).toEqual(["square", "hex"]);
        expect(checkedTilingLabels()).toEqual(["Square", "Hex"]);
        expect(summaryText()).toBe("2 / 6 selected · Regular 2");
        expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        expect(document.querySelector(".compare-explainer-body")?.textContent).toContain(
            "Generation0",
        );
        handle.dispose();
    });

    it("runs a comparison and renders the portrait and grid", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        clickRunAnalysis();

        await vi.waitFor(() => {
            expect(compareSeed).toHaveBeenCalledTimes(1);
            expect(document.querySelector(".compare-grid tbody tr")).not.toBeNull();
        });
        expect(document.querySelectorAll(".compare-portrait__line").length).toBeGreaterThan(0);
        const request = compareSeed.mock.calls.at(0)?.[0];
        expect(request?.geometries).toContain("square");
        expect(request?.traversal).toBe("bfs");
        expect(request?.include_states).toBe(true);
        handle.dispose();
    });

    it("keeps wall-generation and analysis-step limits truthful", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        const field = (label: string): HTMLInputElement => {
            const labelNode = [
                ...document.querySelectorAll<HTMLLabelElement>(".compare-form label"),
            ].find((candidate) => candidate.querySelector("span")?.textContent === label);
            const input = labelNode?.querySelector<HTMLInputElement>("input");
            if (!input) throw new Error(`missing ${label} field`);
            return input;
        };
        const wallGenerations = field("Wall generations");
        const analysisSteps = field("Analysis steps");
        const gridSize = field("Grid size");
        const bitSeed = document.querySelector<HTMLInputElement>(
            ".compare-seedbits input.compare-field",
        );
        const wallRun = document.querySelector<HTMLButtonElement>(".compare-setup-run");
        const analysisRun = [...document.querySelectorAll<HTMLButtonElement>(".compare-run")].find(
            (button) => button.textContent === "Run analysis",
        );
        if (!bitSeed || !wallRun || !analysisRun) throw new Error("missing compare controls");

        expect(wallGenerations.max).toBe("240");
        expect(analysisSteps.max).toBe("500");
        expect(gridSize.max).toBe("64");
        expect(bitSeed.maxLength).toBe(4096);

        wallGenerations.value = "241";
        wallGenerations.dispatchEvent(new Event("input", { bubbles: true }));
        expect(wallRun.disabled).toBe(true);
        expect(wallRun.title).toContain("1 to 240");
        expect(analysisRun.disabled).toBe(false);

        wallGenerations.value = "240";
        wallGenerations.dispatchEvent(new Event("input", { bubbles: true }));
        analysisSteps.value = "501";
        analysisSteps.dispatchEvent(new Event("input", { bubbles: true }));
        expect(wallRun.disabled).toBe(false);
        expect(analysisRun.disabled).toBe(true);
        expect(analysisRun.title).toContain("1 to 500");

        analysisSteps.value = "500";
        analysisSteps.dispatchEvent(new Event("input", { bubbles: true }));
        gridSize.value = "65";
        gridSize.dispatchEvent(new Event("input", { bubbles: true }));
        expect(wallRun.disabled).toBe(true);
        expect(analysisRun.disabled).toBe(true);
        expect(wallRun.title).toContain("2 to 64");

        gridSize.value = "64";
        gridSize.dispatchEvent(new Event("input", { bubbles: true }));
        wallRun.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        await vi.waitFor(() =>
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "Filmstrip ready",
            ),
        );
        expect(requestFilmstrip.mock.calls[0]?.[0]).toMatchObject({ frames: 240, grid_size: 64 });

        analysisRun.click();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        expect(compareSeed.mock.calls[0]?.[0]).toMatchObject({ steps: 500, grid_size: 64 });
        handle.dispose();
    });

    it("renders grouped row actions and opens a share URL from the open menu", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        clickRunAnalysis();

        await vi.waitFor(() => {
            expect(document.querySelector(".compare-row-actions")).not.toBeNull();
        });
        const actions = [
            ...document.querySelectorAll<HTMLElement>(".compare-row-actions .compare-link"),
        ].map((action) => action.textContent);
        expect(actions).toEqual(["Open", "Copy", "▸ preview"]);

        clickMenuItem("Open", "Begin");
        expect(openSpy).toHaveBeenCalledTimes(1);
        const openedUrl = String(openSpy.mock.calls.at(0)?.[0] ?? "");
        expect(openedUrl).toContain("#share=v1.");
        handle.dispose();
    });

    it("closes an open action menu when clicking outside it", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        clickRunAnalysis();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-row-actions")).not.toBeNull();
        });

        const openMenu = menuByLabel("Open");
        openMenu.open = true;
        // A pointerdown elsewhere in the dialog closes the open menu.
        const elsewhere = document.querySelector<HTMLElement>(".compare-run") ?? document.body;
        elsewhere.dispatchEvent(new Event("pointerdown", { bubbles: true }));
        expect(openMenu.open).toBe(false);

        // Opening a second menu closes the first so only one is ever open.
        const copyMenu = menuByLabel("Copy");
        openMenu.open = true;
        copyMenu
            .querySelector("summary")
            ?.dispatchEvent(new Event("pointerdown", { bubbles: true }));
        expect(openMenu.open).toBe(false);
        handle.dispose();
    });

    it("copies distinct share links for the begin and end states", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const writeText = vi.fn(async (_text: string) => {});
        vi.stubGlobal("navigator", { clipboard: { writeText } });
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        clickRunAnalysis();

        await vi.waitFor(() => {
            expect(document.querySelector(".compare-row-actions")).not.toBeNull();
        });
        const copyMenu = menuByLabel("Copy");
        const copyItems = [...copyMenu.querySelectorAll(".compare-action-menu-item")].map(
            (item) => item.textContent,
        );
        expect(copyItems).toEqual(["Begin", "End"]);

        clickMenuItem("Copy", "Begin");
        clickMenuItem("Copy", "End");
        await vi.waitFor(() => expect(writeText).toHaveBeenCalledTimes(2));
        const [beginUrl, endUrl] = writeText.mock.calls.map((call) => String(call[0]));
        expect(beginUrl).toContain("#share=v1.");
        expect(endUrl).toContain("#share=v1.");
        // begin (3 seed cells) and end (2 cells) encode different boards.
        expect(beginUrl).not.toEqual(endUrl);

        vi.unstubAllGlobals();
        handle.dispose();
    });

    it("loads begin/end into the board and closes when onOpenPattern is provided", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
        const onOpenPattern = vi.fn();
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
            onOpenPattern,
        });
        clickRunAnalysis();

        await vi.waitFor(() => {
            expect(document.querySelector(".compare-row-actions")).not.toBeNull();
        });
        const actions = [
            ...document.querySelectorAll<HTMLElement>(".compare-row-actions .compare-link"),
        ].map((action) => action.textContent);
        expect(actions).toEqual(["Open", "Copy", "▸ preview"]);

        clickMenuItem("Open", "Begin");
        expect(onOpenPattern).toHaveBeenCalledTimes(1);
        expect(openSpy).not.toHaveBeenCalled();
        const loaded = onOpenPattern.mock.calls.at(0)?.[0] as { cells_by_id?: unknown };
        expect(loaded?.cells_by_id).toBeDefined();
        // the wall closes after loading in place
        await vi.waitFor(() =>
            expect(document.querySelector<HTMLElement>(".wall-page")?.hidden).toBe(true),
        );
        handle.dispose();
    });

    it("forks the focused board's current generation into the Lab", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
        const onOpenPattern = vi.fn();
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => ({
                rule_name: "conway",
                seed: "111",
                traversal: "bfs",
                frame_count: 2,
                grid_size: 16,
                tilings: [
                    {
                        geometry: "square",
                        tiling_family: "square",
                        family: "regular",
                        cell_count: 100,
                        topology: {} as never,
                        topology_spec: {
                            tiling_family: "square",
                            adjacency_mode: "edge",
                            sizing_mode: "grid",
                            width: 16,
                            height: 16,
                            patch_depth: 0,
                        },
                        frames: [{ "c:1:1": 1 }, { "c:2:1": 1 }],
                        extinction_step: null,
                        period: null,
                        note: null,
                    },
                ],
            }),
        };
        const handle = mountComparePanel({
            openOnMount: true,
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
            onOpenPattern,
        });
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        // Focus the board (speaker view), step to gen 1, then open it in the Lab.
        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        document
            .querySelector<HTMLButtonElement>(
                '.compare-filmstrip-btn[title="Step forward one generation"]',
            )
            ?.click();
        document.querySelector<HTMLButtonElement>(".compare-hero-open-lab")?.click();

        expect(onOpenPattern).toHaveBeenCalledTimes(1);
        expect(openSpy).not.toHaveBeenCalled();
        const loaded = onOpenPattern.mock.calls.at(0)?.[0] as { cells_by_id?: unknown };
        expect(loaded?.cells_by_id).toEqual({ "c:2:1": 1 });
        handle.dispose();
    });

    it("explains why live side-by-side playback is unavailable with one tiling", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        clickPreset("None");
        document.querySelector<HTMLInputElement>(".compare-tiling input")?.click();

        const playSideBySide = [
            ...document.querySelectorAll<HTMLButtonElement>(".compare-run"),
        ].find((button) => button.textContent === "Run now");
        expect(playSideBySide?.disabled).toBe(true);
        expect(playSideBySide?.title).toBe("Select at least two tilings to run a comparison");
        // The dock's idle play button shares the same gate.
        const dockPlay = document.querySelector<HTMLButtonElement>(
            '.compare-dock .compare-filmstrip-btn[title="Run every selected tiling on a shared clock"]',
        );
        expect(dockPlay?.textContent).toBe("Run comparison");
        expect(dockPlay?.disabled).toBe(true);
        handle.dispose();
    });

    it("reports live filmstrip build failures in the status line", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const failingBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => {
                throw new Error("filmstrip boom");
            },
        };
        const handle = mountComparePanel({
            openOnMount: true,
            backend: failingBackend,
            bootstrapData: bootstrapData(),
        });
        clickPreset("Regular");
        const playSideBySide = [
            ...document.querySelectorAll<HTMLButtonElement>(".compare-run"),
        ].find((button) => button.textContent === "Run comparison");
        playSideBySide?.click();

        await vi.waitFor(() => {
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toBe(
                "Error: filmstrip boom",
            );
        });
        // A failed build falls back to the empty-state hero on the stage.
        expect(document.querySelector<HTMLElement>(".compare-stage-hero")?.hidden).toBe(false);
        handle.dispose();
    });

    it("renders a seed pad wired to the seed field", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

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
        handle.dispose();
    });

    it("shape mode sends a pattern and hides the bit pad", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        const shapeSelect = [
            ...document.querySelectorAll<HTMLSelectElement>("select.compare-field"),
        ].find((select) => [...select.options].some((option) => option.value === "glider"));
        if (!shapeSelect) {
            throw new Error("missing shape select");
        }
        shapeSelect.value = "glider";
        shapeSelect.dispatchEvent(new Event("change", { bubbles: true }));

        const padBlock = document.querySelector<HTMLElement>(".compare-seedpad-block");
        expect(padBlock?.style.display).toBe("none");

        clickRunAnalysis();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        expect(compareSeed.mock.calls.at(0)?.[0]?.pattern).toBe("glider");
        handle.dispose();
    });

    it("copies a shareable run link for the current workspace setup", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const writeText = vi.fn(async (_text: string) => {});
        vi.stubGlobal("navigator", { clipboard: { writeText } });
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        const copyRunButton = document.querySelector<HTMLButtonElement>(
            '.compare-dock-icon[aria-label="Copy run link"]',
        );
        copyRunButton?.click();

        await vi.waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
        const copiedUrl = String(writeText.mock.calls.at(0)?.[0] ?? "");
        expect(copiedUrl).toContain("#/compare&run=v1.");
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toBe(
            "Copied run link.",
        );

        vi.unstubAllGlobals();
        handle.dispose();
    });

    it("persists saved runs and tiling sets across remounts", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async () => twoBoardFilmstrip());
        const first = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        clickPreset("Regular");

        const runNameInput = document.querySelector<HTMLInputElement>(
            'input[aria-label="Saved run name"]',
        );
        const tilingSetNameInput = document.querySelector<HTMLInputElement>(
            'input[aria-label="Saved tiling set name"]',
        );
        if (!runNameInput || !tilingSetNameInput) {
            throw new Error("missing saved compare controls");
        }
        runNameInput.value = "Regular run";
        tilingSetNameInput.value = "Regular pair";
        clickButton("Save run");
        clickButton("Save set");
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toBe(
            'Saved tiling set "Regular pair".',
        );

        first.dispose();
        document.body.innerHTML = "";
        const second = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        clickPreset("None");
        expect(checkedTilingLabels()).toEqual([]);

        clickButton("Load set");
        expect(checkedTilingLabels()).toEqual(["Square", "Hex"]);
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toBe(
            'Loaded tiling set "Regular pair".',
        );

        clickPreset("None");
        clickButton("Load run");
        await vi.waitFor(() => {
            expect(checkedTilingLabels()).toEqual(["Square", "Hex"]);
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toBe(
                "Loaded run link — 2 tilings ready.",
            );
        });
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1), {
            timeout: 1_000,
        });
        second.dispose();
    });

    it("applies a decoded run config without running it", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        await handle.applyRunConfig({
            seed: "101",
            rule: "wireworld",
            traversal: "row-major",
            frames: 12,
            grid_size: 8,
            geometries: ["kagome"],
            pattern: "glider",
        });

        const fields = [
            ...document.querySelectorAll<HTMLInputElement | HTMLSelectElement>(
                ".compare-form .compare-field, .compare-seedbits .compare-field",
            ),
        ];
        expect(fields.map((field) => field.value)).toEqual([
            "wireworld",
            "glider",
            "row-major",
            "12",
            "50",
            "8",
            "101",
        ]);
        expect(checkedTilingLabels()).toEqual(["Kagome"]);
        expect(compareSeed).not.toHaveBeenCalled();
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toBe(
            "Loaded run link — 1 tilings ready.",
        );
        handle.dispose();
    });

    it("explains when a run link requests a tiling-specific rule", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });

        await handle.applyRunConfig({
            seed: "101",
            rule: "kagome-life",
            traversal: "bfs",
            frames: 12,
            grid_size: 8,
            geometries: ["kagome"],
        });

        expect(
            document.querySelector<HTMLSelectElement>('select[aria-label="Comparison rule"]')
                ?.value,
        ).toBe("conway");
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
            'Rule "kagome-life" is tiling-specific or unavailable on the wall; using Conway.',
        );
        handle.dispose();
    });

    it("returns the transport to idle when a run config replaces an active wall", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async () => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        await vi.waitFor(() =>
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "Filmstrip ready",
            ),
        );
        const playButton = document.querySelector<HTMLButtonElement>(
            '.compare-filmstrip-btn[aria-label="Play / pause"]',
        );
        expect(playButton?.textContent).toBe("▶ Play");

        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        expect(document.querySelector(".compare-filmstrip--speaker")).not.toBeNull();
        expect(window.location.hash).toContain("focus=square");

        // Loading a run config hides the wall; the shared clock must unbind
        // with it, or Play silently animates the hidden stale boards. Its
        // focused-board route must also go, or the replacement wall silently
        // reopens the old speaker when its boards attach.
        await handle.applyRunConfig({
            seed: "101",
            rule: "conway",
            traversal: "bfs",
            frames: 12,
            grid_size: 8,
            geometries: ["square", "hex"],
        });
        expect(playButton?.getAttribute("aria-label")).toBe("Run comparison");
        expect(playButton?.disabled).toBe(false);
        expect(window.location.hash).not.toContain("focus=");

        // The idle action runs the loaded comparison instead of resuming the old wall.
        playButton?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        await vi.waitFor(() =>
            expect(document.querySelector(".compare-filmstrip--speaker")).toBeNull(),
        );
        handle.dispose();
    });

    it("prevents an obsolete filmstrip success and finally handler from replacing a newer run", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const oldRequest = deferred<SeedFilmstripResult>();
        const currentRequest = deferred<SeedFilmstripResult>();
        const requestFilmstrip = vi
            .fn<SimulationBackend["requestFilmstrip"]>()
            .mockImplementationOnce(() => oldRequest.promise)
            .mockImplementationOnce(() => currentRequest.promise);
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });

        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        await handle.applyRunConfig({
            seed: "101",
            rule: "conway",
            traversal: "bfs",
            frames: 12,
            grid_size: 8,
            geometries: ["hex", "square"],
        });
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        expect(requestFilmstrip).toHaveBeenCalledTimes(1);

        oldRequest.resolve({ ...twoBoardFilmstrip(), seed: "obsolete" });
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        expect(document.querySelector(".compare-filmstrip-board")).toBeNull();
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
            "Building comparison",
        );
        const seedField = document.querySelector<HTMLInputElement>(
            'input.compare-field[type="text"]',
        );
        expect(seedField?.disabled).toBe(false);

        const current = twoBoardFilmstrip();
        currentRequest.resolve({
            ...current,
            seed: "101",
            tilings: [current.tilings[1]!, current.tilings[0]!],
        });
        await vi.waitFor(() =>
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "Filmstrip ready",
            ),
        );
        expect(
            [...document.querySelectorAll<HTMLElement>(".compare-filmstrip-label")].map(
                (label) => label.textContent,
            ),
        ).toEqual(["hex", "square"]);
        expect(seedField?.disabled).toBe(false);
        handle.dispose();
    });

    it("ignores an obsolete filmstrip rejection while a replacement request remains busy", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const oldRequest = deferred<SeedFilmstripResult>();
        const currentRequest = deferred<SeedFilmstripResult>();
        const requestFilmstrip = vi
            .fn<SimulationBackend["requestFilmstrip"]>()
            .mockImplementationOnce(() => oldRequest.promise)
            .mockImplementationOnce(() => currentRequest.promise);
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        await handle.applyRunConfig({
            seed: "101",
            rule: "conway",
            traversal: "bfs",
            frames: 12,
            grid_size: 8,
            geometries: ["square", "hex"],
        });
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        expect(requestFilmstrip).toHaveBeenCalledTimes(1);

        oldRequest.reject(new Error("obsolete failure"));
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        expect(document.querySelector<HTMLElement>(".compare-stale-notice")?.hidden).toBe(true);
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).not.toContain(
            "obsolete failure",
        );
        expect(document.querySelector<HTMLButtonElement>(".compare-setup-run")?.disabled).toBe(
            true,
        );

        currentRequest.resolve(twoBoardFilmstrip());
        await vi.waitFor(() =>
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "Filmstrip ready",
            ),
        );
        handle.dispose();
    });

    it("keeps the previous wall playable, blocks management, and retries a failed update with the latest setup", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi
            .fn<SimulationBackend["requestFilmstrip"]>()
            .mockResolvedValueOnce(twoBoardFilmstrip())
            .mockRejectedValueOnce(new Error("temporary outage"))
            .mockImplementationOnce(async (request) => ({
                ...twoBoardFilmstrip(),
                seed: request.seed,
            }));
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        await vi.waitFor(() =>
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "Filmstrip ready",
            ),
        );
        document
            .querySelector<HTMLButtonElement>('.compare-filmstrip-btn[aria-label="Play / pause"]')
            ?.click();

        const rule = document.querySelector<HTMLSelectElement>(
            'select[aria-label="Comparison rule"]',
        );
        if (!rule) throw new Error("missing setup rule");
        rule.value = "wireworld";
        rule.dispatchEvent(new Event("change", { bubbles: true }));
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        await vi.waitFor(() =>
            expect(document.querySelector<HTMLElement>(".compare-stale-notice")?.hidden).toBe(
                false,
            ),
        );

        const notice = document.querySelector<HTMLElement>(".compare-stale-notice");
        expect(notice?.getAttribute("role")).toBe("alert");
        expect(notice?.textContent).toContain("still showing the previous result");
        expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        expect(
            document.querySelector<HTMLButtonElement>(
                '.compare-filmstrip-btn[aria-label="Play / pause"]',
            )?.disabled,
        ).toBe(false);
        for (const control of document.querySelectorAll<HTMLButtonElement>(
            ".compare-filmstrip-add, .compare-filmstrip-label, .compare-filmstrip-remove",
        )) {
            expect(control.disabled).toBe(true);
            expect(control.title).toBe("Retry the failed update before editing this wall");
        }

        const setupSeed = document.querySelector<HTMLSelectElement>(
            'select[aria-label="Comparison seed"]',
        );
        if (!setupSeed) throw new Error("missing setup seed");
        setupSeed.value = "glider";
        setupSeed.dispatchEvent(new Event("change", { bubbles: true }));
        document.querySelector<HTMLButtonElement>(".compare-stale-retry")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(3));
        expect(requestFilmstrip.mock.calls.at(2)?.[0]).toMatchObject({
            pattern: "glider",
            rule: "wireworld",
        });
        await vi.waitFor(() => expect(notice?.hidden).toBe(true));
        expect(document.querySelector<HTMLButtonElement>(".compare-filmstrip-add")?.disabled).toBe(
            false,
        );
        handle.dispose();
    });

    it("lets an unchanged hidden wall request finish but invalidates work on disposal", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const hiddenRequest = deferred<SeedFilmstripResult>();
        const disposedRequest = deferred<SeedFilmstripResult>();
        const requestFilmstrip = vi
            .fn<SimulationBackend["requestFilmstrip"]>()
            .mockImplementationOnce(() => hiddenRequest.promise)
            .mockImplementationOnce(() => disposedRequest.promise);
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        handle.close();
        hiddenRequest.resolve(twoBoardFilmstrip());
        await vi.waitFor(() =>
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "Filmstrip ready",
            ),
        );
        handle.open();
        expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);

        const rule = document.querySelector<HTMLSelectElement>(
            'select[aria-label="Comparison rule"]',
        );
        if (!rule) throw new Error("missing setup rule");
        rule.value = "wireworld";
        rule.dispatchEvent(new Event("change", { bubbles: true }));
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        handle.dispose();
        disposedRequest.resolve(twoBoardFilmstrip());
        await Promise.resolve();
        expect(document.querySelector(".compare-content")).toBeNull();
    });

    it("keeps obsolete analysis resolve and finally handlers from replacing a newer analysis", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const oldAnalysis = deferred<SeedComparisonResult>();
        const currentAnalysis = deferred<SeedComparisonResult>();
        const compareSeed = vi
            .fn<SimulationBackend["compareSeed"]>()
            .mockImplementationOnce(() => oldAnalysis.promise)
            .mockImplementationOnce(() => currentAnalysis.promise);
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, compareSeed },
            bootstrapData: bootstrapData(),
        });
        clickRunAnalysis();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        await handle.applyRunConfig({
            seed: "101",
            rule: "wireworld",
            traversal: "bfs",
            frames: 12,
            grid_size: 8,
            geometries: ["square", "hex"],
        });
        clickRunAnalysis();
        expect(compareSeed).toHaveBeenCalledTimes(1);

        oldAnalysis.resolve(comparisonResult());
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(2));
        expect(document.querySelector(".compare-row-actions")).toBeNull();
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
            "Updating analysis for 2 tilings",
        );
        expect(
            document.querySelector<HTMLSelectElement>('select[aria-label="Comparison rule"]')
                ?.disabled,
        ).toBe(false);

        currentAnalysis.resolve({ ...comparisonResult(), rule_name: "wireworld" });
        await vi.waitFor(() =>
            expect(document.querySelector(".compare-row-actions")).not.toBeNull(),
        );
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
            "Done",
        );
        expect(
            document.querySelector<HTMLSelectElement>('select[aria-label="Comparison rule"]')
                ?.disabled,
        ).toBe(false);
        handle.dispose();
    });

    it("expands a row preview into begin/end thumbnails", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        clickRunAnalysis();

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
        expect(document.querySelectorAll(".compare-detail .compare-thumb-link")).toHaveLength(2);
        const hrefs = [...document.querySelectorAll<HTMLAnchorElement>(".compare-detail a")].map(
            (anchor) => anchor.getAttribute("href") ?? "",
        );
        expect(hrefs).toHaveLength(2);
        expect(hrefs.every((href) => href.includes("#share=v1."))).toBe(true);
        expect(hrefs[0]).not.toEqual(hrefs[1]);
        const labels = [...document.querySelectorAll(".compare-thumb-label")].map(
            (n) => n.textContent,
        );
        expect(labels).toEqual(["Begin", "End"]);

        // toggling again collapses the detail row
        previewButton?.click();
        expect(document.querySelector(".compare-detail")).toBeNull();
        handle.dispose();
    });

    it("renders as a full-page wall, not a dialog", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            backend,
            bootstrapData: bootstrapData(),
            openOnMount: true,
        });

        const page = document.querySelector<HTMLElement>(".wall-page");
        // The wall is the page: a landmark region, not a modal dialog.
        expect(page).not.toBeNull();
        expect(page?.getAttribute("role")).toBe("region");
        expect(page?.getAttribute("aria-modal")).toBeNull();
        expect(document.querySelector(".compare-backdrop")).toBeNull();
        expect(document.querySelector(".compare-dialog")).toBeNull();
        // The shell owns the header (brand + route buttons); the panel renders
        // no header or exit affordance of its own.
        expect(page?.querySelector(".wall-header")).toBeNull();
        expect(page?.querySelector(".compare-back")).toBeNull();
        expect(page?.hidden).toBe(false);

        // The wall has no "outside": clicking its own surface must not close it.
        page?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        expect(page?.hidden).toBe(false);

        // The router (via the shell header) is the only exit.
        handle.close();
        expect(page?.hidden).toBe(true);
        handle.dispose();
    });

    async function mountWithLoadedFilmstrip(overrides?: {
        onOpenPattern?: (pattern: unknown) => void;
        focusPaneServices?: FocusPaneServices;
    }): Promise<{
        handle: ComparePanelHandle;
        filmstripRequest: ReturnType<typeof vi.fn>;
        sourceFilmstrip: SeedFilmstripResult;
        seedField: HTMLInputElement;
        editToggle: HTMLButtonElement;
    }> {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const sourceFilmstrip = twoBoardFilmstrip();
        const filmstripRequest = vi.fn(async () => sourceFilmstrip);
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip: filmstripRequest },
            bootstrapData: bootstrapData(),
            ...(overrides?.onOpenPattern ? { onOpenPattern: overrides.onOpenPattern } : {}),
            ...(overrides?.focusPaneServices
                ? { focusPaneServices: overrides.focusPaneServices }
                : {}),
        });
        const seedField = [
            ...document.querySelectorAll<HTMLInputElement>('input.compare-field[type="text"]'),
        ].find((input) => /^[01\s,]*$/.test(input.value));
        if (!seedField) {
            throw new Error("seed field not found");
        }
        seedField.value = "101";
        seedField.dispatchEvent(new Event("input", { bubbles: true }));
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        });
        const editToggle = document.querySelector<HTMLButtonElement>(".compare-edit-toggle");
        if (!editToggle) {
            throw new Error("edit toggle not found");
        }
        return { handle, filmstripRequest, sourceFilmstrip, seedField, editToggle };
    }

    function paintCell(cellId: string): void {
        const polygon = document.querySelector(
            `.compare-filmstrip-board [data-cell-id="${cellId}"]`,
        );
        expect(polygon).not.toBeNull();
        polygon?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    }

    it("edit mode paints the shared seed at gen 0 and re-runs the wall", async () => {
        const { handle, filmstripRequest, sourceFilmstrip, seedField, editToggle } =
            await mountWithLoadedFilmstrip();
        const originalFrameZero = sourceFilmstrip.tilings.map((tiling) => ({
            ...(tiling.frames[0] ?? {}),
        }));

        // The toggle waits for a loaded run, then arms edit mode.
        expect(editToggle.disabled).toBe(false);
        expect(editToggle.getAttribute("aria-pressed")).toBe("false");
        editToggle.click();
        expect(editToggle.getAttribute("aria-pressed")).toBe("true");
        expect(document.querySelector(".compare-filmstrip.is-editing")).not.toBeNull();
        const boardsBefore = [
            ...document.querySelectorAll<HTMLElement>(".compare-filmstrip-board"),
        ];

        // Painting c:1:1 (bit 0 of "101") clears that bit; the board is not
        // zoomed by the click.
        paintCell("c:1:1");
        expect(seedField.value).toBe("001");
        expect(document.querySelector(".compare-filmstrip-board.is-hero")).toBeNull();

        // Generation 0 re-projects immediately on every board (the painted cell
        // goes dead), and the authoritative re-run is debounced behind it.
        await vi.waitFor(() => {
            const polygons = document.querySelectorAll('[data-cell-id="c:1:1"]');
            expect(polygons.length).toBeGreaterThan(0);
            for (const polygon of polygons) {
                expect(polygon.classList.contains("is-live")).toBe(false);
            }
        });
        expect(sourceFilmstrip.tilings.map((tiling) => tiling.frames[0])).toEqual(
            originalFrameZero,
        );
        await vi.waitFor(
            () => {
                expect(filmstripRequest).toHaveBeenCalledTimes(2);
            },
            { timeout: 3000 },
        );
        const boardsAfter = [...document.querySelectorAll<HTMLElement>(".compare-filmstrip-board")];
        expect(boardsAfter).toHaveLength(2);
        expect(boardsAfter[0]).toBe(boardsBefore[0]);
        expect(boardsAfter[1]).toBe(boardsBefore[1]);
        expect(document.querySelector<HTMLElement>(".compare-wall-loading")?.hidden).toBe(true);
        handle.dispose();
    });

    it("keeps edit-triggered reruns quiet while the existing wall stays mounted", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const resolvers: Array<(filmstrip: SeedFilmstripResult) => void> = [];
        const requestFilmstrip = vi.fn(
            () =>
                new Promise<SeedFilmstripResult>((resolve) => {
                    resolvers.push(resolve);
                }),
        );
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        resolvers.shift()?.(twoBoardFilmstrip());
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        });
        const firstBoard = document.querySelector<HTMLElement>(".compare-filmstrip-board");
        expect(firstBoard).not.toBeNull();

        document.querySelector<HTMLButtonElement>(".compare-edit-toggle")?.click();
        paintCell("c:1:1");
        await vi.waitFor(
            () => {
                expect(requestFilmstrip).toHaveBeenCalledTimes(2);
            },
            { timeout: 3000 },
        );

        expect(document.querySelector<HTMLElement>(".compare-wall-loading")?.hidden).toBe(true);
        expect(
            document
                .querySelector<HTMLElement>(".compare-filmstrip-area")
                ?.classList.contains("is-loading"),
        ).toBe(false);
        expect(document.querySelector<HTMLElement>(".compare-filmstrip-board")).toBe(firstBoard);

        resolvers.shift()?.(twoBoardFilmstrip());
        await vi.waitFor(() => {
            expect(document.querySelector<HTMLElement>(".compare-filmstrip-board")).toBe(
                firstBoard,
            );
        });
        handle.dispose();
    });

    it("edit mode leaves zooming to the expand glyph", async () => {
        const { handle, editToggle } = await mountWithLoadedFilmstrip();
        editToggle.click();

        const expand = document.querySelector<HTMLElement>(
            ".compare-filmstrip-board .compare-filmstrip-expand",
        );
        expand?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        expect(document.querySelector(".compare-filmstrip-board.is-hero")).not.toBeNull();

        expand?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        expect(document.querySelector(".compare-filmstrip-board.is-hero")).toBeNull();
        handle.dispose();
    });

    it("rewinds to the seed frame when edit mode paints away from gen 0", async () => {
        const onOpenPattern = vi.fn();
        const { handle, filmstripRequest, seedField, editToggle } = await mountWithLoadedFilmstrip({
            onOpenPattern,
        });
        editToggle.click();

        document
            .querySelector<HTMLButtonElement>(
                '.compare-filmstrip-btn[title="Step forward one generation"]',
            )
            ?.click();
        paintCell("c:1:1");

        // Edit seed always edits the shared generation-0 seed. It should not
        // open the board in the Lab or detach it from the shared wall clock.
        expect(seedField.value).toBe("001");
        expect(onOpenPattern).not.toHaveBeenCalled();
        expect(document.querySelector(".compare-filmstrip-counter")?.textContent).toBe("gen 0 / 1");
        expect(document.querySelector(".compare-focus-pane")).toBeNull();
        await vi.waitFor(
            () => {
                expect(filmstripRequest).toHaveBeenCalledTimes(2);
            },
            { timeout: 3000 },
        );
        handle.dispose();
    });

    it("keeps edit-mode paints on the shared seed even when live fork support exists", async () => {
        const { backend } = fakeBackend();
        const setCells = vi.fn(async () => forkSnapshot());
        const focusBackend: SimulationBackend = {
            ...backend,
            getState: async () => forkSnapshot(),
            postControl: (async () =>
                forkSnapshot()) as unknown as SimulationBackend["postControl"],
            setCells: setCells as unknown as SimulationBackend["setCells"],
            dispose: vi.fn(),
        };
        const backendFactory = vi.fn(() => focusBackend);
        const focusPaneServices: FocusPaneServices = {
            baseSessionId: "sess",
            backendFactory,
            createGridView: () => fakeGridView(),
            buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
                { ...startCell, state: paintState },
            ],
        };
        const { handle, filmstripRequest, seedField, editToggle } = await mountWithLoadedFilmstrip({
            focusPaneServices,
        });
        editToggle.click();

        document
            .querySelector<HTMLButtonElement>(
                '.compare-filmstrip-btn[title="Step forward one generation"]',
            )
            ?.click();
        paintCell("c:1:1");

        expect(seedField.value).toBe("001");
        expect(backendFactory).not.toHaveBeenCalled();
        expect(setCells).not.toHaveBeenCalled();
        expect(document.querySelector(".compare-focus-pane")).toBeNull();
        expect(document.querySelector(".compare-filmstrip-board.is-hero")).toBeNull();
        await vi.waitFor(
            () => {
                expect(filmstripRequest).toHaveBeenCalledTimes(2);
            },
            { timeout: 3000 },
        );
        handle.dispose();
    });

    it("converts a shape seed to an editable bit-string on first paint", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripRequest = vi.fn(async () => twoBoardFilmstrip());
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip: filmstripRequest },
            bootstrapData: bootstrapData(),
        });
        const shapeSelect = [
            ...document.querySelectorAll<HTMLSelectElement>("select.compare-field"),
        ].find((select) => [...select.options].some((option) => option.value === "r-pentomino"));
        if (!shapeSelect) {
            throw new Error("shape select not found");
        }
        shapeSelect.value = "r-pentomino";
        shapeSelect.dispatchEvent(new Event("change", { bubbles: true }));
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        });

        document.querySelector<HTMLButtonElement>(".compare-edit-toggle")?.click();
        const polygon = document.querySelector('.compare-filmstrip-board [data-cell-id="c:1:1"]');
        polygon?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

        // frames[0] = {c:1:1} pulls back to "1"; painting that cell toggles it
        // off, leaving the converted, editable seed "0" and no shape selection.
        expect(shapeSelect.value).toBe("");
        const seedField = [
            ...document.querySelectorAll<HTMLInputElement>('input.compare-field[type="text"]'),
        ].find((input) => /^[01\s,]*$/.test(input.value) && !input.disabled);
        expect(seedField?.value).toBe("0");
        expect(document.querySelector(".compare-status")?.textContent).toContain("converted");
        handle.dispose();
    });

    it("keeps the seed-placement previews live after a paint converts shape to bits", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const basePreview = await backend.previewTopology({ geometry: "square", grid_size: 16 });
        // Mirror the server: pattern requests answer with shape placements and
        // no traversal order; traversal requests answer with the order.
        const previewTopology = vi.fn(async (request: TopologyPreviewRequest) =>
            request.pattern
                ? { ...basePreview, shape_cells: { "c:1:1": 1 } }
                : { ...basePreview, order: ["c:1:1"] },
        );
        const handle = mountComparePanel({
            openOnMount: true,
            backend: {
                ...backend,
                requestFilmstrip: async () => twoBoardFilmstrip(),
                previewTopology,
            },
            bootstrapData: bootstrapData(),
        });
        const shapeSelect = [
            ...document.querySelectorAll<HTMLSelectElement>("select.compare-field"),
        ].find((select) => [...select.options].some((option) => option.value === "r-pentomino"));
        if (!shapeSelect) {
            throw new Error("shape select not found");
        }
        shapeSelect.value = "r-pentomino";
        shapeSelect.dispatchEvent(new Event("change", { bubbles: true }));
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        });

        // Painting converts the shape to bits ("1" -> toggled to "0").
        document.querySelector<HTMLButtonElement>(".compare-edit-toggle")?.click();
        document
            .querySelector('.compare-filmstrip-board [data-cell-id="c:1:1"]')
            ?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        const seedField = [
            ...document.querySelectorAll<HTMLInputElement>('input.compare-field[type="text"]'),
        ].find((input) => /^[01\s,]*$/.test(input.value) && !input.disabled);
        expect(seedField?.value).toBe("0");

        // Typing bits must render on the placement thumbnails. Before the
        // conversion refetched them, they were still the shape-mode responses
        // (no traversal order), which map every bit string to an empty board.
        seedField!.value = "1";
        seedField!.dispatchEvent(new Event("input", { bubbles: true }));
        // Let the redraw debounce flush first: until it fires, the stale
        // shape-placement thumbnails (also accent-filled) still sit in the DOM
        // and would satisfy the assertion vacuously.
        await new Promise((resolve) => setTimeout(resolve, 150));
        await vi.waitFor(() => {
            const live = [
                ...document.querySelectorAll<SVGElement>(".compare-seedpreview svg [fill]"),
            ].filter((node) => (node.getAttribute("fill") ?? "").includes("accent"));
            expect(live.length).toBeGreaterThan(0);
        });
        handle.dispose();
    });

    it("opens and closes the configuration sheet from the dock gear", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        const sheet = () => document.querySelector<HTMLElement>(".compare-config-sheet");
        // Desktop setup starts visible, then the gear and close button collapse it.
        expect(sheet()?.classList.contains("is-open")).toBe(true);
        expect(sheet()?.hasAttribute("inert")).toBe(false);

        document
            .querySelector<HTMLButtonElement>('.compare-dock-icon[aria-label="Configure the run"]')
            ?.click();
        expect(sheet()?.classList.contains("is-open")).toBe(false);
        expect(sheet()?.hasAttribute("inert")).toBe(true);

        document
            .querySelector<HTMLButtonElement>('.compare-dock-icon[aria-label="Configure the run"]')
            ?.click();
        expect(sheet()?.classList.contains("is-open")).toBe(true);
        expect(sheet()?.hasAttribute("inert")).toBe(false);

        document.querySelector<HTMLButtonElement>(".compare-config-sheet-close")?.click();
        expect(sheet()?.classList.contains("is-open")).toBe(false);
        expect(sheet()?.hasAttribute("inert")).toBe(true);
        handle.dispose();
    });

    it("uses exclusive keyboard-accessible setup and inspector drawers below 960 px", async () => {
        Object.defineProperty(window, "innerWidth", { configurable: true, value: 800 });
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip: async () => twoBoardFilmstrip() },
            bootstrapData: bootstrapData(),
        });
        const setup = document.querySelector<HTMLElement>(".compare-setup-sidebar");
        const inspector = document.querySelector<HTMLElement>(".compare-inspector");
        const setupToggle = document.querySelector<HTMLButtonElement>(
            '.compare-dock-icon[aria-label="Configure the run"]',
        );
        const inspectorToggle = document.querySelector<HTMLButtonElement>(
            '.compare-dock-icon[aria-label="Inspect selected board"]',
        );
        expect(setup?.classList.contains("is-open")).toBe(false);
        expect(inspector?.classList.contains("is-open")).toBe(false);

        setupToggle?.focus();
        setupToggle?.click();
        expect(setup?.classList.contains("is-open")).toBe(true);
        expect(setupToggle?.getAttribute("aria-expanded")).toBe("true");
        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(inspectorToggle?.disabled).toBe(false));

        inspectorToggle?.focus();
        inspectorToggle?.click();
        expect(setup?.classList.contains("is-open")).toBe(false);
        expect(inspector?.classList.contains("is-open")).toBe(true);
        document.querySelector<HTMLButtonElement>(".compare-inspector-close")?.click();
        expect(document.activeElement).toBe(inspectorToggle);
        handle.dispose();
    });

    it("preserves inspector selection across compatible reruns and falls back to the first board", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const first = twoBoardFilmstrip();
        const second = { ...first, tilings: [first.tilings[1]!, first.tilings[0]!] };
        const third = {
            ...first,
            tilings: [
                first.tilings[1]!,
                { ...first.tilings[0]!, geometry: "kagome", tiling_family: "kagome" },
            ],
        };
        const requestFilmstrip = vi
            .fn<SimulationBackend["requestFilmstrip"]>()
            .mockResolvedValueOnce(first)
            .mockResolvedValueOnce(second)
            .mockResolvedValueOnce(third);
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        const rerun = async (seed: string, expectedCalls: number) => {
            const seedField = document.querySelector<HTMLInputElement>(
                'input.compare-field[type="text"]',
            );
            if (!seedField) throw new Error("missing seed field");
            seedField.value = seed;
            seedField.dispatchEvent(new Event("input", { bubbles: true }));
            document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
            await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(expectedCalls));
            await vi.waitFor(() =>
                expect(
                    document.querySelector<HTMLElement>(".compare-explainer-body")?.textContent,
                ).toContain("Generation0"),
            );
        };

        document.querySelector<HTMLButtonElement>(".compare-setup-run")?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));
        await vi.waitFor(() =>
            expect(
                document.querySelector<HTMLElement>(".compare-explainer-body")?.textContent,
            ).toContain("Boardsquare"),
        );
        await rerun("101", 2);
        expect(
            document.querySelector<HTMLElement>(".compare-explainer-body")?.textContent,
        ).toContain("Boardsquare");
        await rerun("111", 3);
        expect(
            document.querySelector<HTMLElement>(".compare-explainer-body")?.textContent,
        ).toContain("Boardhex");
        handle.dispose();
    });

    it("Escape closes the config sheet before it exits speaker view", async () => {
        Object.defineProperty(window, "innerWidth", { configurable: true, value: 800 });
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const handle = mountComparePanel({
            openOnMount: true,
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
        });
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        const filmstrip = () => document.querySelector<HTMLElement>(".compare-filmstrip");
        const sheet = () => document.querySelector<HTMLElement>(".compare-config-sheet");

        // Enter speaker view, then open the config sheet over it.
        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        expect(filmstrip()?.classList.contains("compare-filmstrip--speaker")).toBe(true);
        document
            .querySelector<HTMLButtonElement>('.compare-dock-icon[aria-label="Configure the run"]')
            ?.click();
        expect(sheet()?.classList.contains("is-open")).toBe(true);

        // First Escape closes the sheet but stays in speaker view.
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        expect(sheet()?.classList.contains("is-open")).toBe(false);
        expect(filmstrip()?.classList.contains("compare-filmstrip--speaker")).toBe(true);

        // Second Escape returns to the gallery.
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        expect(filmstrip()?.classList.contains("compare-filmstrip--speaker")).toBe(false);
        handle.dispose();
    });

    it("re-renders the explainer on a frame tick without disturbing the summary", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip: async () => twoBoardFilmstrip() },
            bootstrapData: bootstrapData(),
        });
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        // Focus a board so the explainer shows the per-generation view.
        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        const generationCopy = (): string | undefined => {
            const items = [...document.querySelectorAll(".compare-explainer-item")];
            const row = items.find(
                (item) =>
                    item.querySelector(".compare-explainer-key")?.textContent === "Generation",
            );
            return row?.querySelector(".compare-explainer-copy")?.textContent ?? undefined;
        };
        expect(generationCopy()).toBe("0 of 1");

        // The summary's run button reflects the settled wall; capture it so we
        // can confirm a frame tick leaves the summary untouched.
        const setupRun = () =>
            document.querySelector<HTMLButtonElement>(".compare-setup-run")?.textContent;
        const summaryBefore = setupRun();
        const selectedChipBefore = document.querySelector(".compare-selected-chip");
        expect(selectedChipBefore).not.toBeNull();

        // Advance one generation via the transport's step control. This drives
        // onFrameChange, whose only render path is the explainer subscription.
        document
            .querySelector<HTMLButtonElement>(
                '.compare-filmstrip-btn[aria-label="Step forward one generation"]',
            )
            ?.click();

        expect(generationCopy()).toBe("1 of 1");
        expect(setupRun()).toBe(summaryBefore);
        expect(document.querySelector(".compare-selected-chip")).toBe(selectedChipBefore);
        handle.dispose();
    });

    it("returns to the gallery from the hero's back button", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const handle = mountComparePanel({
            openOnMount: true,
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
        });
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });
        const filmstrip = () => document.querySelector<HTMLElement>(".compare-filmstrip");

        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        expect(filmstrip()?.classList.contains("compare-filmstrip--speaker")).toBe(true);
        // The hero toolbelt's back button exits speaker view.
        const back = document.querySelector<HTMLButtonElement>(".compare-hero-back");
        expect(back).toBeTruthy();
        back?.click();
        expect(filmstrip()?.classList.contains("compare-filmstrip--speaker")).toBe(false);
        expect(
            document.querySelector<HTMLButtonElement>(".compare-inspector-replace")?.disabled,
        ).toBe(false);
        handle.dispose();
    });

    it("focuses a board into speaker view and lets Escape peel back to the gallery", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const twoBoard = (geometry: string) => ({
            geometry,
            tiling_family: geometry,
            family: "regular",
            cell_count: 100,
            topology: {} as never,
            topology_spec: {
                tiling_family: geometry,
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 16,
                height: 16,
                patch_depth: 0,
            },
            frames: [{ "c:1:1": 1 }, { "c:2:1": 1 }],
            extinction_step: null,
            period: null,
            note: null,
        });
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => ({
                rule_name: "conway",
                seed: "111",
                traversal: "bfs",
                frame_count: 2,
                grid_size: 16,
                tilings: [twoBoard("square"), twoBoard("hex")],
            }),
        };
        const handle = mountComparePanel({
            openOnMount: true,
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
        });
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        const filmstrip = () => document.querySelector<HTMLElement>(".compare-filmstrip");
        const page = () => document.querySelector<HTMLElement>(".wall-page");

        // Focus the first board -> speaker view, mirrored into the hash.
        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        expect(filmstrip()?.classList.contains("compare-filmstrip--speaker")).toBe(true);
        expect(window.location.hash).toContain("focus=square");

        // Escape returns to the gallery (and clears the focus slot) without closing.
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        expect(filmstrip()?.classList.contains("compare-filmstrip--speaker")).toBe(false);
        expect(window.location.hash).not.toContain("focus=");
        expect(page()?.hidden).toBe(false);

        // The wall is the page: a further Escape does not leave it.
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        expect(page()?.hidden).toBe(false);
        handle.dispose();
    });

    it("returns to the gallery when a re-run drops the focused board", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const board = (geometry: string) => ({
            geometry,
            tiling_family: geometry,
            family: "regular",
            cell_count: 100,
            topology: {} as never,
            topology_spec: {
                tiling_family: geometry,
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 16,
                height: 16,
                patch_depth: 0,
            },
            frames: [{ "c:1:1": 1 }, { "c:2:1": 1 }],
            extinction_step: null,
            period: null,
            note: null,
        });
        let wallGeometries = ["square", "hex"];
        const requestFilmstrip = vi.fn(async () => ({
            rule_name: "conway",
            seed: "111",
            traversal: "bfs",
            frame_count: 2,
            grid_size: 16,
            tilings: wallGeometries.map(board),
        }));
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        // Focus square: speaker view, back button armed.
        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        expect(document.querySelector(".compare-filmstrip--speaker")).not.toBeNull();
        const backButton = document.querySelector<HTMLButtonElement>(".compare-hero-back");
        expect(backButton?.disabled).toBe(false);

        // The next authoritative wall no longer contains the focused board.
        wallGeometries = ["hex", "kagome"];
        await handle.applyRunConfig({
            seed: "111",
            rule: "conway",
            traversal: "bfs",
            frames: 12,
            grid_size: 16,
            geometries: wallGeometries,
        });
        const playButton = document.querySelector<HTMLButtonElement>(
            '.compare-filmstrip-btn[aria-label="Run comparison"]',
        );
        expect(playButton).not.toBeNull();
        playButton?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        await vi.waitFor(() =>
            expect(document.querySelector(".compare-filmstrip--speaker")).toBeNull(),
        );

        // Gallery restored: no focus slot in the URL, back button disarmed.
        expect(window.location.hash).not.toContain("focus=");
        expect(document.querySelector<HTMLButtonElement>(".compare-hero-back")?.disabled).toBe(
            true,
        );
        handle.dispose();
    });

    it("scrubs a focus slot that names no board instead of leaving it in the URL", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend: { ...backend, requestFilmstrip: async () => twoBoardFilmstrip() },
            bootstrapData: bootstrapData(),
        });
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });
        const filmstrip = () => document.querySelector<HTMLElement>(".compare-filmstrip");

        // A stale or mistyped deep link while the wall is unfocused: the view
        // stays on the gallery, and the dead slot must not linger in the URL
        // claiming a focus that isn't there.
        window.location.hash = "#focus=not-a-board";
        window.dispatchEvent(new Event("hashchange"));
        await vi.waitFor(() => {
            expect(window.location.hash).not.toContain("focus=");
        });
        expect(filmstrip()?.classList.contains("compare-filmstrip--speaker")).toBe(false);

        // A valid slot still deep-links into speaker view afterwards.
        window.location.hash = "#focus=square";
        window.dispatchEvent(new Event("hashchange"));
        await vi.waitFor(() => {
            expect(filmstrip()?.classList.contains("compare-filmstrip--speaker")).toBe(true);
        });
        handle.dispose();
        window.history.replaceState(null, "", window.location.pathname);
    });

    it("keeps the seed workspace in Configure during speaker view (no seed rail)", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const handle = mountComparePanel({
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        // Focusing a board changes the stage layout only. Seed editing is edit
        // mode's job in either layout (paint gen 0 for the shared seed), so
        // the old reparenting rail is gone and the seed pad stays in the
        // config sheet for bit-level control.
        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        expect(
            document.querySelector(".compare-stage-main")?.classList.contains("is-speaker"),
        ).toBe(true);
        expect(document.querySelector(".compare-seed-rail")).toBeNull();
        expect(
            document.querySelector(".compare-config-panel-setup .compare-seed-workspace"),
        ).not.toBeNull();
        handle.dispose();
    });

    it("replaces the wall explainer with focused-board context in speaker view", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            backend: { ...backend, requestFilmstrip: async () => twoBoardFilmstrip() },
            bootstrapData: bootstrapData(),
        });
        handle.open();

        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();

        const explainer = document.querySelector<HTMLElement>(".compare-explainer");
        expect(explainer?.textContent).toContain("Focused board");
        expect(explainer?.textContent).toContain("Board");
        expect(explainer?.textContent).toContain("Generation");
        expect(explainer?.textContent).toContain("Live count");
        expect(explainer?.textContent).toContain("Current tiling");
        expect(explainer?.textContent).toContain("Open in Lab");
        expect(explainer?.textContent).not.toContain("Same seed");
        handle.dispose();
    });

    it("removes a board from the wall via its × chrome and re-runs without it", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => threeBoardFilmstrip());
        const handle = mountComparePanel({
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(3);
        });
        const firstRequest = requestFilmstrip.mock.calls.at(0)?.[0];
        expect(firstRequest?.geometries).toContain("square");

        document
            .querySelector<HTMLButtonElement>(".compare-filmstrip-remove")
            ?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

        expect(document.querySelector(".compare-status")?.textContent).toContain("Removed");
        // Removals coalesce into one debounced re-run that drops the geometry.
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2), {
            timeout: 3000,
        });
        expect(requestFilmstrip.mock.calls.at(1)?.[0]?.geometries).not.toContain("square");
        handle.dispose();
    });

    it("holds the two-board floor against a rapid removal burst", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => threeBoardFilmstrip());
        const handle = mountComparePanel({
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        handle.open();
        // Pin the selection to exactly the three displayed boards so the
        // two-board floor is genuinely one removal away.
        await handle.applyRunConfig({
            seed: "111",
            rule: "conway",
            traversal: "bfs",
            frames: 12,
            grid_size: 16,
            geometries: ["square", "hex", "kagome"],
        });
        document
            .querySelector<HTMLButtonElement>('.compare-filmstrip-btn[aria-label="Run comparison"]')
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(3);
        });

        // Two removals inside one debounce window. The second must be judged
        // against the pending two-board selection, not the still-displayed
        // three-board strip, or the wall would collapse below its floor.
        const removeButtons = [
            ...document.querySelectorAll<HTMLButtonElement>(".compare-filmstrip-remove"),
        ];
        removeButtons[0]?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        removeButtons[1]?.dispatchEvent(new MouseEvent("click", { bubbles: true }));

        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2), {
            timeout: 3000,
        });
        const rerunGeometries = requestFilmstrip.mock.calls.at(1)?.[0]?.geometries ?? [];
        expect(rerunGeometries).toHaveLength(2);
        expect(requestFilmstrip).toHaveBeenCalledTimes(2);
        handle.dispose();
    });

    it("keeps a replacement in the selected board's wall position", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => threeBoardFilmstrip());
        const handle = mountComparePanel({
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(3);
        });

        document.querySelectorAll<HTMLButtonElement>(".compare-filmstrip-label")[1]?.click();
        const penroseChoice = [
            ...document.querySelectorAll<HTMLButtonElement>(".compare-board-tiling-choice"),
        ].find((choice) => choice.textContent?.includes("Penrose"));
        expect(penroseChoice?.disabled).toBe(false);
        penroseChoice?.click();

        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        expect(requestFilmstrip.mock.calls.at(1)?.[0]?.geometries).toEqual([
            "square",
            "penrose",
            "kagome",
            "periodic-face",
            "spectre",
        ]);
        handle.dispose();
    });

    it("adds a tiling directly from the wall's searchable picker", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => threeBoardFilmstrip());
        const handle = mountComparePanel({
            backend: { ...backend, requestFilmstrip },
            bootstrapData: bootstrapData(),
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(3);
        });

        document.querySelector<HTMLButtonElement>(".compare-filmstrip-add")?.click();
        expect(document.activeElement?.className).toContain("compare-board-tiling-picker-search");
        const penroseChoice = [
            ...document.querySelectorAll<HTMLButtonElement>(".compare-board-tiling-choice"),
        ].find((choice) => choice.textContent?.includes("Penrose"));
        expect(penroseChoice?.disabled).toBe(false);
        penroseChoice?.click();

        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        expect(requestFilmstrip.mock.calls.at(1)?.[0]?.geometries.at(-1)).toBe("penrose");
        handle.dispose();
    });

    it("opens the tiling checklist with search focused from the dock's ⊞ button", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            backend,
            bootstrapData: bootstrapData(),
        });
        handle.open();

        document.querySelector<HTMLButtonElement>(".compare-tilings-open")?.click();

        expect(document.querySelector(".compare-config-sheet")?.classList.contains("is-open")).toBe(
            true,
        );
        expect(document.querySelector<HTMLElement>("#compare-config-panel-tilings")?.hidden).toBe(
            false,
        );
        expect(
            document
                .querySelector<HTMLButtonElement>("#compare-config-tab-tilings")
                ?.classList.contains("is-active"),
        ).toBe(true);
        expect(document.activeElement?.className).toContain("compare-tilings-search");
        handle.dispose();
    });

    it("opens the tiling tab from the setup strip Tilings item", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            backend,
            bootstrapData: bootstrapData(),
        });
        handle.open();

        document
            .querySelector<HTMLButtonElement>(
                '.compare-setup-action[aria-label="Choose tilings on the wall"]',
            )
            ?.click();

        expect(document.querySelector(".compare-config-sheet")?.classList.contains("is-open")).toBe(
            true,
        );
        expect(document.querySelector<HTMLElement>("#compare-config-panel-tilings")?.hidden).toBe(
            false,
        );
        expect(document.activeElement?.className).toContain("compare-tilings-search");
        handle.dispose();
    });

    it("forks the focused board into a live pane on the wall when a session is available", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const focusBackend: SimulationBackend = {
            ...backend,
            getState: async () => forkSnapshot(),
            postControl: (async () =>
                forkSnapshot()) as unknown as SimulationBackend["postControl"],
            setCells: (async () => forkSnapshot()) as unknown as SimulationBackend["setCells"],
            dispose: vi.fn(),
        };
        const backendFactory = vi.fn(() => focusBackend);
        const focusPaneServices: FocusPaneServices = {
            baseSessionId: "sess",
            backendFactory,
            createGridView: () => fakeGridView(),
            buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
                { ...startCell, state: paintState },
            ],
        };
        const handle = mountComparePanel({
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
            focusPaneServices,
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        const forkLive = document.querySelector<HTMLButtonElement>(".compare-hero-fork");
        expect(forkLive, "fork-live button present in speaker view").toBeTruthy();
        expect(forkLive?.textContent).toBe("Edit live");
        forkLive?.click();

        await vi.waitFor(() => {
            expect(
                document.querySelector<HTMLElement>(".compare-status")?.textContent ?? "",
            ).not.toContain("Fork failed");
            expect(document.querySelector(".compare-focus-pane")).not.toBeNull();
        });
        // The fork runs on a session derived from this board's geometry, and
        // the hero SVG is replaced.
        expect(backendFactory).toHaveBeenCalledWith("sess-focus-square");
        expect(
            document.querySelector(".compare-filmstrip-board.is-hero .compare-focus-pane"),
        ).not.toBeNull();
        // Already forked: the toolbelt's fork button hides (Discard, in the
        // pane's own chip, is the way to undo it).
        expect(document.querySelector<HTMLButtonElement>(".compare-hero-fork")?.hidden).toBe(true);
        handle.dispose();
    });

    it("re-runs the whole wall from a fork's current state as the new shared seed", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const requestFilmstrip = vi.fn(async (_request: FilmstripRequest) => twoBoardFilmstrip());
        const filmstripBackend: SimulationBackend = { ...backend, requestFilmstrip };
        // The fork's live state: c:1:1 (bit 0 of the shared seed) is alive.
        const liveForkSnapshot = () => ({ ...forkSnapshot(), cell_states: [1] });
        const focusBackend: SimulationBackend = {
            ...backend,
            getState: async () => liveForkSnapshot(),
            postControl: (async () =>
                liveForkSnapshot()) as unknown as SimulationBackend["postControl"],
            setCells: (async () => liveForkSnapshot()) as unknown as SimulationBackend["setCells"],
            dispose: vi.fn(),
        };
        const focusPaneServices: FocusPaneServices = {
            baseSessionId: "sess",
            backendFactory: () => focusBackend,
            createGridView: () => fakeGridView(),
            buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
                { ...startCell, state: paintState },
            ],
        };
        const handle = mountComparePanel({
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
            focusPaneServices,
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(1));

        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        document.querySelector<HTMLButtonElement>(".compare-hero-fork")?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-focus-pane")).not.toBeNull();
        });

        document.querySelector<HTMLButtonElement>(".compare-focus-pane-rejoin")?.click();

        // The fork's live cells pull back through the board's seed_order
        // (c:1:1 alive -> bit 0 -> "1"), become the shared seed, and the wall
        // re-runs from it -- which also disposes the fork.
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        await vi.waitFor(() =>
            expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
                "Filmstrip ready",
            ),
        );
        const seedField = [
            ...document.querySelectorAll<HTMLInputElement>('input.compare-field[type="text"]'),
        ].find((input) => /^[01\s,]*$/.test(input.value) && !input.disabled);
        expect(seedField?.value).toBe("1");
        expect(requestFilmstrip.mock.calls.at(1)?.[0]).toMatchObject({ seed: "1" });
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-focus-pane")).toBeNull();
        });
        expect(focusBackend.dispose).toHaveBeenCalled();
        handle.dispose();
    });

    it("keeps a live fork running after leaving its board (persists across views)", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const focusBackend: SimulationBackend = {
            ...backend,
            getState: async () => forkSnapshot(),
            postControl: (async () =>
                forkSnapshot()) as unknown as SimulationBackend["postControl"],
            setCells: (async () => forkSnapshot()) as unknown as SimulationBackend["setCells"],
            dispose: vi.fn(),
        };
        const focusPaneServices: FocusPaneServices = {
            baseSessionId: "sess",
            backendFactory: () => focusBackend,
            createGridView: () => fakeGridView(),
            buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
                { ...startCell, state: paintState },
            ],
        };
        const handle = mountComparePanel({
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
            focusPaneServices,
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        });

        const boards = () => document.querySelectorAll<HTMLElement>(".compare-filmstrip-board");
        boards()[0]?.click();
        document.querySelector<HTMLButtonElement>(".compare-hero-fork")?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-focus-pane")).not.toBeNull();
        });

        // Leave the board (back to the gallery): the fork is not disposed, and
        // its pane keeps rendering in that board's own (now non-hero) tile.
        document.querySelector<HTMLButtonElement>(".compare-hero-back")?.click();
        expect(focusBackend.dispose).not.toHaveBeenCalled();
        expect(document.querySelector(".compare-focus-pane")).not.toBeNull();
        expect(
            document.querySelector(".compare-filmstrip-board.is-hero .compare-focus-pane"),
        ).toBeNull();

        // Re-entering the same board shows the same live pane as the hero again
        // rather than re-forking it.
        boards()[0]?.click();
        expect(
            document.querySelector(".compare-filmstrip-board.is-hero .compare-focus-pane"),
        ).not.toBeNull();

        // Closing the wall (not just changing focus) does tear it down.
        handle.close();
        expect(focusBackend.dispose).toHaveBeenCalledTimes(1);
        handle.dispose();
    });

    it("forks two different boards at once, each keeping its own live pane", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const focusBackendFor = (): SimulationBackend => ({
            ...backend,
            getState: async () => forkSnapshot(),
            postControl: (async () =>
                forkSnapshot()) as unknown as SimulationBackend["postControl"],
            setCells: (async () => forkSnapshot()) as unknown as SimulationBackend["setCells"],
            dispose: vi.fn(),
        });
        const backendFactory = vi.fn(focusBackendFor);
        const focusPaneServices: FocusPaneServices = {
            baseSessionId: "sess",
            backendFactory,
            createGridView: () => fakeGridView(),
            buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
                { ...startCell, state: paintState },
            ],
        };
        const handle = mountComparePanel({
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
            focusPaneServices,
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        });

        const boards = () => document.querySelectorAll<HTMLElement>(".compare-filmstrip-board");
        boards()[0]?.click();
        document.querySelector<HTMLButtonElement>(".compare-hero-fork")?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-focus-pane")).toHaveLength(1);
        });

        boards()[1]?.click();
        document.querySelector<HTMLButtonElement>(".compare-hero-fork")?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-focus-pane")).toHaveLength(2);
        });
        expect(backendFactory).toHaveBeenCalledWith("sess-focus-square");
        expect(backendFactory).toHaveBeenCalledWith("sess-focus-hex");

        // Discarding one (the current hero, hex) leaves the other running.
        document
            .querySelector<HTMLButtonElement>(
                ".compare-filmstrip-board.is-hero .compare-focus-pane-discard",
            )
            ?.click();
        expect(document.querySelectorAll(".compare-focus-pane")).toHaveLength(1);
        expect(
            document.querySelector(".compare-filmstrip-board.is-hero .compare-focus-pane"),
        ).toBeNull();

        handle.dispose();
    });

    it("caps concurrent live forks when the host reports a capacity", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const focusBackend: SimulationBackend = {
            ...backend,
            getState: async () => forkSnapshot(),
            postControl: (async () =>
                forkSnapshot()) as unknown as SimulationBackend["postControl"],
            setCells: (async () => forkSnapshot()) as unknown as SimulationBackend["setCells"],
            dispose: vi.fn(),
        };
        const focusPaneServices: FocusPaneServices = {
            baseSessionId: "standalone",
            backendFactory: () => focusBackend,
            createGridView: () => fakeGridView(),
            buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
                { ...startCell, state: paintState },
            ],
            forkCapacity: 1,
        };
        const handle = mountComparePanel({
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
            focusPaneServices,
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        });

        const boards = () => document.querySelectorAll<HTMLElement>(".compare-filmstrip-board");
        boards()[0]?.click();
        document.querySelector<HTMLButtonElement>(".compare-hero-fork")?.click();
        await vi.waitFor(() => {
            expect(document.querySelectorAll(".compare-focus-pane")).toHaveLength(1);
        });

        boards()[1]?.click();
        document.querySelector<HTMLButtonElement>(".compare-hero-fork")?.click();

        expect(document.querySelectorAll(".compare-focus-pane")).toHaveLength(1);
        expect(document.querySelector<HTMLElement>(".compare-status")?.textContent).toContain(
            "Only 1 live fork",
        );
        handle.dispose();
    });

    it("pauses playback and disposes the live focus pane when the wall closes", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const focusDispose = vi.fn();
        const focusBackend: SimulationBackend = {
            ...backend,
            getState: async () => forkSnapshot(),
            postControl: (async () =>
                forkSnapshot()) as unknown as SimulationBackend["postControl"],
            setCells: (async () => forkSnapshot()) as unknown as SimulationBackend["setCells"],
            dispose: focusDispose,
        };
        const focusPaneServices: FocusPaneServices = {
            baseSessionId: "sess",
            backendFactory: () => focusBackend,
            createGridView: () => fakeGridView(),
            buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
                { ...startCell, state: paintState },
            ],
        };
        const handle = mountComparePanel({
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
            focusPaneServices,
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        document.querySelector<HTMLButtonElement>(".compare-hero-fork")?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-focus-pane")).not.toBeNull();
        });

        const playPause = document.querySelector<HTMLButtonElement>(
            '.compare-filmstrip-btn[title="Play / pause"]',
        );
        playPause?.click();
        expect(playPause?.textContent).toBe("⏸ Pause");

        handle.close();

        expect(document.querySelector<HTMLElement>(".wall-page")?.hidden).toBe(true);
        expect(playPause?.textContent).toBe("▶ Play");
        expect(document.querySelector(".compare-focus-pane")).toBeNull();
        expect(focusDispose).toHaveBeenCalledTimes(1);
        handle.dispose();
    });

    it("still attaches a fork to its own board if focus changes before it lands", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const focusDispose = vi.fn();
        const focusBackend: SimulationBackend = {
            ...backend,
            getState: async () => forkSnapshot(),
            postControl: (async () =>
                forkSnapshot()) as unknown as SimulationBackend["postControl"],
            setCells: (async () => forkSnapshot()) as unknown as SimulationBackend["setCells"],
            dispose: focusDispose,
        };
        const focusPaneServices: FocusPaneServices = {
            baseSessionId: "sess",
            backendFactory: () => focusBackend,
            createGridView: () => fakeGridView(),
            buildEditorToolCells: (_state, _tool, startCell, _endCell, paintState) => [
                { ...startCell, state: paintState },
            ],
        };
        const handle = mountComparePanel({
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
            focusPaneServices,
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        document.querySelector<HTMLButtonElement>(".compare-hero-fork")?.click();
        // Unfocus before the async fork (dynamic import + backend factory)
        // resolves. The fork targets its own board by geometry, not whichever
        // board happens to be the hero, so it still attaches successfully.
        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();

        await vi.waitFor(() => {
            expect(document.querySelector(".compare-focus-pane")).not.toBeNull();
        });
        expect(focusDispose).not.toHaveBeenCalled();
        expect(
            document.querySelector(".compare-filmstrip-board.is-hero .compare-focus-pane"),
        ).toBeNull();
        expect(
            document.querySelector<HTMLElement>(".compare-status")?.textContent ?? "",
        ).not.toContain("Fork failed");
        handle.dispose();
    });

    it("forks the focused board into the Lab when no live session is available", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => twoBoardFilmstrip(),
        };
        const onOpenPattern = vi.fn();
        const handle = mountComparePanel({
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
            onOpenPattern,
        });
        handle.open();
        [...document.querySelectorAll<HTMLButtonElement>(".compare-run")]
            .find((button) => button.textContent === "Run comparison")
            ?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        document.querySelector<HTMLElement>(".compare-filmstrip-board")?.click();
        expect(document.querySelector(".compare-hero-fork")).toBeNull();
        const openInLab = document.querySelector<HTMLButtonElement>(".compare-hero-open-lab");
        expect(openInLab).toBeTruthy();
        expect(openInLab?.textContent).toBe("Open in Lab");
        openInLab?.click();

        // No live session: the explicit Lab action opens the frame in the Lab.
        expect(onOpenPattern).toHaveBeenCalledTimes(1);
        expect(document.querySelector(".compare-focus-pane")).toBeNull();
        handle.dispose();
    });

    it("drives the docked transport with space and arrow keys once a filmstrip is live", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripBackend: SimulationBackend = {
            ...backend,
            requestFilmstrip: async () => ({
                rule_name: "conway",
                seed: "111",
                traversal: "bfs",
                frame_count: 2,
                grid_size: 16,
                tilings: [
                    {
                        geometry: "square",
                        tiling_family: "square",
                        family: "regular",
                        cell_count: 100,
                        topology: {} as never,
                        topology_spec: {
                            tiling_family: "square",
                            adjacency_mode: "edge",
                            sizing_mode: "grid",
                            width: 16,
                            height: 16,
                            patch_depth: 0,
                        },
                        frames: [{ "c:1:1": 1 }, { "c:2:1": 1 }],
                        extinction_step: null,
                        period: null,
                        note: null,
                    },
                ],
            }),
        };
        const handle = mountComparePanel({
            openOnMount: true,
            backend: filmstripBackend,
            bootstrapData: bootstrapData(),
        });
        const playSideBySide = [
            ...document.querySelectorAll<HTMLButtonElement>(".compare-run"),
        ].find((button) => button.textContent === "Run comparison");
        playSideBySide?.click();
        await vi.waitFor(() => {
            expect(document.querySelector(".compare-filmstrip-board")).not.toBeNull();
        });

        const counter = () =>
            document.querySelector<HTMLElement>(".compare-filmstrip-counter")?.textContent;
        expect(counter()).toBe("gen 0 / 1");

        const playPauseButton = () =>
            document.querySelector<HTMLButtonElement>(
                '.compare-filmstrip-btn[title="Play / pause"]',
            );

        // Arrow keys step the shared clock; Space on the wall toggles play/pause.
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
        expect(counter()).toBe("gen 1 / 1");
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true }));
        expect(counter()).toBe("gen 0 / 1");
        document.dispatchEvent(new KeyboardEvent("keydown", { key: " ", bubbles: true }));
        expect(playPauseButton()?.textContent).toBe("⏸ Pause");
        document.dispatchEvent(new KeyboardEvent("keydown", { key: " ", bubbles: true }));
        expect(playPauseButton()?.textContent).toBe("▶ Play");

        // Focused controls keep their native Space behavior instead of starting
        // the wall clock. Custom keyboard widgets that prevent the event also win.
        const routeButton = document.createElement("button");
        document.body.append(routeButton);
        routeButton.dispatchEvent(new KeyboardEvent("keydown", { key: " ", bubbles: true }));
        expect(playPauseButton()?.textContent).toBe("▶ Play");

        const board = document.querySelector<HTMLElement>(".compare-filmstrip-board");
        board?.dispatchEvent(new KeyboardEvent("keydown", { key: " ", bubbles: true }));
        expect(document.querySelector(".compare-filmstrip--speaker")).not.toBeNull();
        expect(playPauseButton()?.textContent).toBe("▶ Play");

        handle.dispose();
    });

    it("shows a 'preview too large' note instead of a preview for oversized tilings", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const oversized = comparisonResult();
        const oversizedRow = oversized.results[0];
        if (!oversizedRow) {
            throw new Error("missing result row");
        }
        oversizedRow.cell_count = 50000;
        const { backend } = fakeBackend();
        const wideBackend: SimulationBackend = { ...backend, compareSeed: async () => oversized };
        const handle = mountComparePanel({
            openOnMount: true,
            backend: wideBackend,
            bootstrapData: bootstrapData(),
        });
        clickRunAnalysis();

        await vi.waitFor(() => {
            expect(document.querySelector(".compare-row-actions")).not.toBeNull();
        });
        const note = document.querySelector<HTMLElement>(".compare-row-note");
        expect(note?.textContent).toBe("preview too large");
        expect(note?.getAttribute("title")).toContain("50,000");
        const previewButton = [
            ...document.querySelectorAll<HTMLButtonElement>(".compare-link"),
        ].find((button) => button.textContent?.includes("preview"));
        expect(previewButton).toBeUndefined();
        handle.dispose();
    });
});
