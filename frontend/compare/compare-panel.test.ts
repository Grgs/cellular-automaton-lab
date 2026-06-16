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

function openCompareDialog(): void {
    document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
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
        // Default representative selection: both regular grids + one per other family.
        expect(document.querySelectorAll(".compare-tiling input:checked")).toHaveLength(5);
        expect(activePresetLabels()).toEqual(["Representative"]);
        handle.dispose();
        expect(document.querySelector(".compare-toggle")).toBeNull();
    });

    it("filters tilings by search without changing the selected set", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        expect(summaryText()).toBe("5 / 6 selected · Regular 2 · Mixed 2 · Aperiodic 1");
        expect(familyHeaderTexts()).toEqual([
            "regular 2/2",
            "mixed 1/1",
            "periodic 1/1",
            "aperiodic 1/2",
        ]);

        setTilingSearch("Penrose");
        expect(tilingLabels()).toEqual(["Penrose"]);
        expect(checkedTilingLabels()).toEqual([]);
        expect(summaryText()).toBe("5 / 6 selected · Regular 2 · Mixed 2 · Aperiodic 1");
        expect(familyHeaderTexts()).toEqual(["aperiodic 1/2"]);

        setTilingSearch("aperiodic");
        expect(tilingLabels()).toEqual(["Spectre", "Penrose"]);
    });

    it("shows an empty state when no tilings match the search", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        setTilingSearch("not-a-tiling");

        expect(document.querySelector(".compare-tilings-empty")?.textContent).toBe(
            "No tilings match this search.",
        );
        expect(tilingLabels()).toEqual([]);
        expect(summaryText()).toBe("5 / 6 selected · Regular 2 · Mixed 2 · Aperiodic 1");
    });

    it("applies tiling presets and updates the family summary", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

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
    });

    it("clears the active preset when the selection becomes custom", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

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
    });

    it("runs with selected tilings hidden by the current search", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        openCompareDialog();
        clickPreset("Regular");
        setTilingSearch("Penrose");
        expect(tilingLabels()).toEqual(["Penrose"]);

        document.querySelector<HTMLButtonElement>(".compare-run")?.click();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        expect(compareSeed.mock.calls.at(0)?.[0]?.geometries).toEqual(["square", "hex"]);
    });

    it("limits compare tilings to the selected rule's compatible families", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        openCompareDialog();
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

        document.querySelector<HTMLButtonElement>(".compare-run")?.click();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        expect(compareSeed.mock.calls.at(0)?.[0]?.rule).toBe("kagome-life");
        expect(compareSeed.mock.calls.at(0)?.[0]?.geometries).toEqual(["kagome"]);
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

    it("renders grouped row actions and opens a share URL from the open menu", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        document.querySelector<HTMLButtonElement>(".compare-run")?.click();

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
    });

    it("closes an open action menu when clicking outside it", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        document.querySelector<HTMLButtonElement>(".compare-run")?.click();
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
    });

    it("copies distinct share links for the begin and end states", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const writeText = vi.fn(async (_text: string) => {});
        vi.stubGlobal("navigator", { clipboard: { writeText } });
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });

        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        document.querySelector<HTMLButtonElement>(".compare-run")?.click();

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
    });

    it("loads begin/end into the board and closes when onOpenPattern is provided", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
        const onOpenPattern = vi.fn();
        const { backend } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData(), onOpenPattern });

        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        document.querySelector<HTMLButtonElement>(".compare-run")?.click();

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
        // dialog closes after loading in place
        expect(document.querySelector<HTMLElement>(".compare-backdrop")?.hidden).toBe(true);
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

    it("shape mode sends a pattern and hides the bit pad", async () => {
        const { mountComparePanel } = await import("./compare-panel.js");
        const { backend, compareSeed } = fakeBackend();
        mountComparePanel({ backend, bootstrapData: bootstrapData() });
        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();

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

        document.querySelector<HTMLButtonElement>(".compare-run")?.click();
        await vi.waitFor(() => expect(compareSeed).toHaveBeenCalledTimes(1));
        expect(compareSeed.mock.calls.at(0)?.[0]?.pattern).toBe("glider");
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
        mountComparePanel({ backend: wideBackend, bootstrapData: bootstrapData() });

        document.querySelector<HTMLButtonElement>(".compare-toggle")?.click();
        document.querySelector<HTMLButtonElement>(".compare-run")?.click();

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
    });
});
