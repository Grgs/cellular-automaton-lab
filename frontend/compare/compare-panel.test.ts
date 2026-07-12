import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type {
    AppBootstrapData,
    FilmstripRequest,
    SeedComparisonResult,
    SeedFilmstripResult,
    SimulationSnapshot,
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

        // Saved runs/sets are demoted below the live output, not above it.
        const saved = document.querySelector(".compare-saved");
        expect(saved).not.toBeNull();
        expect(
            filmstrip!.compareDocumentPosition(saved!) & Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();
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
        ruleSelect.value = "kagome-life";
        ruleSelect.dispatchEvent(new Event("change"));

        const analysisRun = [...document.querySelectorAll<HTMLButtonElement>(".compare-run")].find(
            (button) => button.textContent === "Run analysis",
        );
        analysisRun?.click();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        expect(compareSeed.mock.calls.at(0)?.[0]).toMatchObject({
            pattern: "glider",
            rule: "kagome-life",
            geometries: ["kagome"],
        });
        handle.dispose();
    });

    it("runs the filmstrip from the setup strip primary action", async () => {
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
        expect(document.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        const setupRun = document.querySelector<HTMLButtonElement>(".compare-setup-run");
        await vi.waitFor(() => expect(setupRun?.textContent).toBe("Up to date"));
        expect(setupRun?.disabled).toBe(true);
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

        expect(setupRun?.textContent).toBe("Run changes");
        expect(setupRun?.classList.contains("is-stale")).toBe(true);
        expect(setupRun?.disabled).toBe(false);
        setupRun?.click();
        await vi.waitFor(() => expect(requestFilmstrip).toHaveBeenCalledTimes(2));
        await vi.waitFor(() => expect(setupRun?.textContent).toBe("Up to date"));
        handle.dispose();
    });

    it("renders four board tiles cleanly without an add-tiling tile", async () => {
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
        expect(document.querySelector(".compare-filmstrip-add")).toBeNull();
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
        expect(run?.textContent).toBe("Run changes");
        run?.click();
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

    it("uses config tabs and keeps Run comparison out of the sheet", async () => {
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

        document
            .querySelector<HTMLButtonElement>('.compare-dock-icon[aria-label="Configure the run"]')
            ?.click();

        const sheet = document.querySelector<HTMLElement>(".compare-config-sheet");
        expect(sheet?.classList.contains("is-open")).toBe(true);
        expect(document.querySelector<HTMLElement>("#compare-config-panel-setup")?.hidden).toBe(
            false,
        );
        expect(sheet?.textContent).not.toContain("Run comparison");

        document.querySelector<HTMLButtonElement>("#compare-config-tab-analysis")?.click();
        expect(document.querySelector<HTMLElement>("#compare-config-panel-analysis")?.hidden).toBe(
            false,
        );
        document.querySelector<HTMLButtonElement>("#compare-config-tab-help")?.click();
        const helpPanel = document.querySelector<HTMLElement>("#compare-config-panel-help");
        expect(helpPanel?.hidden).toBe(false);
        expect(helpPanel?.textContent).toContain("Same seed");
        expect(helpPanel?.textContent).toContain("Different tilings");
        document.querySelector<HTMLButtonElement>(".compare-run-secondary")?.click();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        handle.dispose();
    });

    it("limits compare tilings to the selected rule's compatible families", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        await vi.waitFor(() => {
            expect(
                [...document.querySelectorAll<HTMLSelectElement>("select.compare-field")].some(
                    (select) =>
                        [...select.options].some((option) => option.value === "kagome-life"),
                ),
            ).toBe(true);
        });
        const ruleSelect = [
            ...document.querySelectorAll<HTMLSelectElement>("select.compare-field"),
        ].find((select) => [...select.options].some((option) => option.value === "kagome-life"));
        if (!ruleSelect) {
            throw new Error("missing rule select");
        }
        ruleSelect.value = "kagome-life";
        ruleSelect.dispatchEvent(new Event("change", { bubbles: true }));

        expect(checkedTilingLabels()).toEqual(["Kagome"]);
        expect(disabledTilingLabels()).toEqual([
            "Square",
            "Hex",
            "Periodic Face",
            "Spectre",
            "Penrose",
        ]);
        expect(summaryText()).toBe("1 / 1 selected · Mixed 1");

        clickRunAnalysis();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        expect(compareSeed.mock.calls.at(0)?.[0]?.rule).toBe("kagome-life");
        expect(compareSeed.mock.calls.at(0)?.[0]?.geometries).toEqual(["kagome"]);
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
        expect(document.querySelector<HTMLElement>(".wall-page")?.hidden).toBe(true);
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
        ].find((button) => button.textContent === "Run comparison");
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
            backend,
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
            rule: "kagome-life",
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
            "kagome-life",
            "glider",
            "row-major",
            "12",
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
        seedField: HTMLInputElement;
        editToggle: HTMLButtonElement;
    }> {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const filmstripRequest = vi.fn(async () => twoBoardFilmstrip());
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
        return { handle, filmstripRequest, seedField, editToggle };
    }

    function paintCell(cellId: string): void {
        const polygon = document.querySelector(
            `.compare-filmstrip-board [data-cell-id="${cellId}"]`,
        );
        expect(polygon).not.toBeNull();
        polygon?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    }

    it("edit mode paints the shared seed at gen 0 and re-runs the wall", async () => {
        const { handle, filmstripRequest, seedField, editToggle } =
            await mountWithLoadedFilmstrip();

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

    it("opens and closes the configuration sheet from the dock gear", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        const handle = mountComparePanel({
            openOnMount: true,
            backend,
            bootstrapData: bootstrapData(),
        });
        const sheet = () => document.querySelector<HTMLElement>(".compare-config-sheet");
        // Closed by default: inert and not open.
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

    it("Escape closes the config sheet before it exits speaker view", async () => {
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

    it("removes a board from the wall via its ✕ chrome and re-runs without it", async () => {
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

        // Arrow keys step the shared clock; Space toggles play/pause.
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
        expect(counter()).toBe("gen 1 / 1");
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true }));
        expect(counter()).toBe("gen 0 / 1");
        document.dispatchEvent(new KeyboardEvent("keydown", { key: " ", bubbles: true }));
        expect(
            document.querySelector<HTMLButtonElement>(
                '.compare-filmstrip-btn[title="Play / pause"]',
            )?.textContent,
        ).toBe("⏸ Pause");

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
