/**
 * The compare panel's content and behaviour, decoupled from any surrounding
 * chrome. `createComparePanelContent` builds the form, seed workspace, tiling
 * picker, run/play actions, the live filmstrip view, and the results — wiring
 * all of it together — and returns an element plus a small lifecycle handle.
 *
 * It deliberately knows nothing about *how* it is presented: the modal in
 * `compare-panel.ts` wraps this in a dialog, and a future workspace route can
 * mount the same element full-page. The host owns showing/hiding, focus, and
 * the close affordance; it drives this content through `activate()` (call when
 * shown), `handleEscape()` (let an open menu swallow Escape first), and
 * `onRequestClose` (the content asks to be dismissed, e.g. after open-in-place).
 */

import type {
    AppBootstrapData,
    CompareRequest,
    FilmstripRequest,
    PatternPayload,
    RuleDefinition,
    SeedComparisonResult,
    TopologyComparisonResultPayload,
    TopologyPreview,
} from "../types/domain.js";
import type { SimulationBackend } from "../types/controller.js";
import { buildShareUrl } from "../share-link.js";
import { buildCompareRunUrl, type CompareRunConfig } from "./compare-run-link.js";
import { SEED_SHAPE_OPTIONS, TRAVERSAL_OPTIONS } from "./compare-options.js";
import { buildClassificationGrid, buildPhasePortraitSvg, familyColor } from "./compare-charts.js";
import { buildBoardThumbnailSvg } from "./compare-thumbnail.js";
import { createSeedPad } from "./compare-seed-pad.js";
import { createSeedPreview } from "./compare-seed-preview.js";
import { createFilmstripView, type FilmstripViewController } from "./compare-filmstrip-view.js";
import { COMPARE_PANEL_STYLES } from "./compare-styles.js";
import { ruleSupportsTilingFamily } from "../rule-compatibility.js";

// Matches _MAX_PREVIEW_CELLS in backend/simulation/topology_preview.py; larger
// patches are not offered a thumbnail (the backend would reject them anyway).
const MAX_PREVIEW_CELLS = 10000;

// Mirrors the pattern schema in pattern-io.ts / parsers/pattern.ts; reused so a
// begin/end state can be encoded as a shareable board link.
const PATTERN_FORMAT = "cellular-automaton-lab-pattern";
const PATTERN_VERSION = 5;

const DEFAULT_SEED = "01100 11000 01000";
const STYLE_ELEMENT_ID = "compare-panel-styles";

/** Build a shareable board pattern for a result's begin or end state, if states were returned. */
function buildStatePattern(
    comparison: SeedComparisonResult,
    result: TopologyComparisonResultPayload,
    phase: "begin" | "end",
): PatternPayload | null {
    const cells = phase === "begin" ? result.initial_cells_by_id : result.final_cells_by_id;
    if (!result.topology_spec || cells === undefined) {
        return null;
    }
    return {
        format: PATTERN_FORMAT,
        version: PATTERN_VERSION,
        topology_spec: result.topology_spec,
        rule: comparison.rule_name,
        cells_by_id: cells,
    };
}

function openPatternInTab(pattern: PatternPayload): void {
    window.open(buildShareUrl(pattern, window.location.href), "_blank", "noopener");
}

export interface ComparePanelContentOptions {
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    /** When provided, begin/end open into the current board instead of a new tab. */
    onOpenPattern?: (pattern: PatternPayload) => void;
    /** The content asks its host to dismiss it (e.g. after loading in place). */
    onRequestClose?: () => void;
}

export interface ComparePanelContentHandle {
    /** The content root; mount it inside a dialog, a route, or any container. */
    element: HTMLElement;
    /** Call when the content becomes visible: load rules and refresh previews. */
    activate(): void;
    /** Populate the workspace from a decoded run link without running it. */
    applyRunConfig(config: CompareRunConfig): Promise<void>;
    /** Let an open action menu consume Escape; returns true when it did. */
    handleEscape(): boolean;
    dispose(): void;
}

interface TilingOption {
    geometry: string;
    tilingFamily: string;
    label: string;
    family: string;
}

type TilingPreset = "representative" | "regular" | "mixed" | "aperiodic" | "all" | "none";

interface ActionMenuItem {
    label: string;
    title: string;
    onClick(): void;
}

type ElementAttrs = Record<string, string | number | boolean | null | undefined>;

function el<K extends keyof HTMLElementTagNameMap>(
    tag: K,
    attrs: ElementAttrs = {},
    children: Array<Node | string> = [],
): HTMLElementTagNameMap[K] {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
        if (value === undefined || value === null || value === false) {
            continue;
        }
        if (key === "textContent" || key === "text") {
            node.textContent = String(value);
            continue;
        }
        node.setAttribute(key, value === true ? "" : String(value));
    }
    for (const child of children) {
        node.append(typeof child === "string" ? document.createTextNode(child) : child);
    }
    return node;
}

function tilingOptions(bootstrapData: AppBootstrapData): TilingOption[] {
    return bootstrapData.topology_catalog
        .map((definition) => ({
            geometry: definition.geometry_keys[definition.default_adjacency_mode] ?? "",
            tilingFamily: definition.tiling_family,
            label: definition.label,
            family: definition.family,
        }))
        .filter((option): option is TilingOption => option.geometry.length > 0);
}

/** All regular grids plus one representative per other family: a fast default sweep. */
function defaultSelection(options: TilingOption[]): Set<string> {
    const selection = new Set<string>();
    const seenFamilies = new Set<string>();
    for (const option of options) {
        if (option.family === "regular") {
            selection.add(option.geometry);
        } else if (!seenFamilies.has(option.family)) {
            seenFamilies.add(option.family);
            selection.add(option.geometry);
        }
    }
    return selection;
}

export function ensureComparePanelStyles(): void {
    if (document.getElementById(STYLE_ELEMENT_ID)) {
        return;
    }
    const style = el("style", { id: STYLE_ELEMENT_ID, textContent: COMPARE_PANEL_STYLES });
    document.head.append(style);
}

export function createComparePanelContent(
    options: ComparePanelContentOptions,
): ComparePanelContentHandle {
    ensureComparePanelStyles();
    const allTilings = tilingOptions(options.bootstrapData);
    const selected = defaultSelection(allTilings);

    let rules: RuleDefinition[] = [];
    let rulesLoaded = false;
    let running = false;
    let tilingSearchQuery = "";
    const previewCache = new Map<string, Promise<TopologyPreview>>();
    const presetButtons = new Map<TilingPreset, HTMLButtonElement>();

    const ruleSelect = el("select", { class: "compare-field" });
    const seedInput = el("input", {
        class: "compare-field",
        type: "text",
        value: DEFAULT_SEED,
        spellcheck: "false",
    });
    const traversalSelect = el(
        "select",
        { class: "compare-field" },
        TRAVERSAL_OPTIONS.map((option) =>
            el("option", { value: option.value, textContent: option.label }),
        ),
    );
    const stepsInput = el("input", {
        class: "compare-field",
        type: "number",
        value: "50",
        min: "1",
        max: "500",
    });
    const gridInput = el("input", {
        class: "compare-field",
        type: "number",
        value: "16",
        min: "2",
        max: "64",
    });
    const shapeSelect = el(
        "select",
        { class: "compare-field" },
        SEED_SHAPE_OPTIONS.map((option) =>
            el("option", { value: option.value, textContent: option.label }),
        ),
    );

    const tilingList = el("div", { class: "compare-tilings" });
    const tilingSearchInput = el("input", {
        class: "compare-field compare-tilings-search",
        type: "search",
        placeholder: "Search tilings",
        "aria-label": "Search tilings",
    });

    // "" = bit-string seed (pad/preview); otherwise a named shape (Policy A).
    const isShapeMode = (): boolean => shapeSelect.value !== "";

    const seedPreview = createSeedPreview({
        backend: options.backend,
        getSeed: () => seedInput.value,
        getTraversal: () => traversalSelect.value,
        getGridSize: () => clampNumber(gridInput.value, 2, 64, 16),
        getPattern: () => shapeSelect.value,
        getPreviewHref: ({ cellsById, preview }) =>
            patternShareUrl({
                format: PATTERN_FORMAT,
                version: PATTERN_VERSION,
                topology_spec: preview.topology_spec,
                rule: selectedRuleName(),
                cells_by_id: cellsById,
            }),
        getTilings: () =>
            allTilings
                .filter((tiling) => selected.has(tiling.geometry))
                .map((tiling) => ({ geometry: tiling.geometry, label: tiling.label })),
    });

    const seedPad = createSeedPad({
        getSeed: () => seedInput.value,
        onSeedChange: (formatted) => {
            seedInput.value = formatted;
            redrawPreview();
        },
    });
    // The live preview applies to both seed sources: a bit string placed by
    // traversal, or a named shape placed geometrically (Policy A).
    const refreshPreview = (): void => {
        seedPreview.refresh();
    };
    const redrawPreview = (): void => {
        seedPreview.redraw();
    };
    seedInput.addEventListener("input", () => {
        seedPad.syncFromSeed();
        redrawPreview();
    });
    traversalSelect.addEventListener("change", refreshPreview);
    gridInput.addEventListener("change", refreshPreview);

    const runButton = el("button", { class: "compare-run", type: "button" }, ["Run comparison"]);
    const playButton = el(
        "button",
        {
            class: "compare-run compare-run-secondary",
            type: "button",
            title: "Run every selected tiling on a shared clock and play them side by side",
        },
        ["▶ Play side by side"],
    );
    const copyRunButton = el(
        "button",
        {
            class: "compare-run compare-run-secondary",
            type: "button",
            title: "Copy a link that restores this compare run setup",
        },
        ["Copy run link"],
    );
    const statusLine = el("div", { class: "compare-status", role: "status" });
    const filmstripArea = el("div", { class: "compare-filmstrip-area", hidden: true });
    const resultsArea = el("div", { class: "compare-results" });
    let filmstripView: FilmstripViewController | null = null;

    const seedPadBlock = el("div", { class: "compare-seedpad-block" }, [
        el("div", {
            class: "compare-seedpad-title",
            textContent: "Draw the seed",
        }),
        seedPad.element,
        el("details", { class: "compare-seedbits" }, [
            el("summary", { class: "compare-seedbits-summary", textContent: "Bit string" }),
            labeledField("Seed bits", seedInput),
        ]),
    ]);

    // The placement preview applies to both seed sources, so it lives outside the
    // bit-pad block (which is hidden in shape mode).
    const seedPreviewBlock = el("div", { class: "compare-seedpreview-block" }, [
        el("div", {
            class: "compare-seedpad-title",
            textContent: "Seed lands like this on:",
        }),
        seedPreview.element,
    ]);
    const seedWorkspace = el("div", { class: "compare-seed-workspace" }, [
        seedPadBlock,
        seedPreviewBlock,
    ]);

    // Switching seed source toggles the bit pad/preview and refreshes accordingly.
    shapeSelect.addEventListener("change", () => {
        syncShapeMode();
        seedPreview.refresh();
    });

    const root = el("div", { class: "compare-content" }, [
        el("p", {
            class: "compare-intro",
            textContent:
                "Map one seed onto each tiling through a canonical traversal, run the same rule, and compare how topology shapes the outcome.",
        }),
        el("div", { class: "compare-form" }, [
            labeledField("Rule", ruleSelect),
            labeledField("Seed source", shapeSelect),
            labeledField("Traversal", traversalSelect),
            labeledField("Steps", stepsInput),
            labeledField("Grid size", gridInput),
        ]),
        seedWorkspace,
        el("div", { class: "compare-tilings-block" }, [tilingControlsBar(), tilingList]),
        el("div", { class: "compare-actions" }, [runButton, playButton, copyRunButton, statusLine]),
        filmstripArea,
        resultsArea,
    ]);

    renderTilingChecklist();

    function labeledField(label: string, field: HTMLElement): HTMLLabelElement {
        return el("label", { class: "compare-label" }, [el("span", { textContent: label }), field]);
    }

    function tilingControlsBar(): HTMLElement {
        tilingSearchInput.addEventListener("input", () => {
            tilingSearchQuery = tilingSearchInput.value;
            renderTilingChecklist();
        });
        const presetButton = (label: string, preset: TilingPreset): HTMLButtonElement => {
            const button = el("button", {
                class: "compare-mini",
                type: "button",
                textContent: label,
                "aria-pressed": "false",
            });
            button.addEventListener("click", () => applyTilingPreset(preset));
            presetButtons.set(preset, button);
            return button;
        };
        return el("div", { class: "compare-tilings-controls" }, [
            el("span", { class: "compare-tilings-summary", id: "compare-tilings-summary" }),
            el("div", { class: "compare-tilings-tools" }, [
                tilingSearchInput,
                el("div", { class: "compare-tilings-presets" }, [
                    presetButton("Representative", "representative"),
                    presetButton("Regular", "regular"),
                    presetButton("Mixed", "mixed"),
                    presetButton("Aperiodic", "aperiodic"),
                    presetButton("All", "all"),
                    presetButton("None", "none"),
                ]),
            ]),
        ]);
    }

    function renderTilingChecklist(): void {
        pruneSelectionForSelectedRule();
        tilingList.replaceChildren();
        const visibleTilings = allTilings.filter((option) => matchesTilingSearch(option));
        if (visibleTilings.length === 0) {
            tilingList.append(
                el("div", {
                    class: "compare-tilings-empty",
                    textContent: "No tilings match this search.",
                }),
            );
            updateSummary();
            return;
        }
        const byFamily = new Map<string, TilingOption[]>();
        for (const option of visibleTilings) {
            const bucket = byFamily.get(option.family) ?? [];
            bucket.push(option);
            byFamily.set(option.family, bucket);
        }
        for (const [family, optionsForFamily] of byFamily) {
            const group = el("div", { class: "compare-tilings-group" });
            group.append(
                el("div", { class: "compare-tilings-family" }, [
                    el("span", {
                        class: "compare-dot",
                        style: `background:${familyColor(family)}`,
                    }),
                    el("span", { textContent: family }),
                    el("span", {
                        class: "compare-family-count",
                        "data-family": family,
                        textContent: familySelectionCountText(family),
                    }),
                ]),
            );
            for (const option of optionsForFamily) {
                const compatible = tilingCompatibleWithSelectedRule(option);
                const checkbox = el("input", {
                    type: "checkbox",
                    checked: compatible && selected.has(option.geometry),
                    disabled: !compatible,
                    title: compatible ? "" : "Unsupported for the selected rule",
                });
                checkbox.addEventListener("change", () => {
                    if (!tilingCompatibleWithSelectedRule(option)) {
                        checkbox.checked = false;
                        selected.delete(option.geometry);
                        updateSummary();
                        return;
                    }
                    if (checkbox.checked) {
                        selected.add(option.geometry);
                    } else {
                        selected.delete(option.geometry);
                    }
                    updateSummary();
                    refreshPreview();
                });
                group.append(
                    el(
                        "label",
                        {
                            class: compatible ? "compare-tiling" : "compare-tiling is-disabled",
                            title: compatible ? "" : "Unsupported for the selected rule",
                        },
                        [checkbox, el("span", { textContent: option.label })],
                    ),
                );
            }
            tilingList.append(group);
        }
        updateSummary();
    }

    function matchesTilingSearch(option: TilingOption): boolean {
        const query = tilingSearchQuery.trim().toLowerCase();
        if (query.length === 0) {
            return true;
        }
        return [option.label, option.geometry, option.family].some((value) =>
            value.toLowerCase().includes(query),
        );
    }

    function isMixedFamily(family: string): boolean {
        return family === "mixed" || family === "periodic";
    }

    function applyTilingPreset(preset: TilingPreset): void {
        replaceSelection(selectionForPreset(preset));
        renderTilingChecklist();
        refreshPreview();
    }

    function selectionForPreset(preset: TilingPreset): Set<string> {
        if (preset === "representative") {
            return defaultSelection(allTilings);
        }
        if (preset === "regular") {
            return new Set(
                allTilings
                    .filter((option) => option.family === "regular")
                    .map((option) => option.geometry),
            );
        }
        if (preset === "mixed") {
            return new Set(
                allTilings
                    .filter((option) => isMixedFamily(option.family))
                    .map((option) => option.geometry),
            );
        }
        if (preset === "aperiodic") {
            return new Set(
                allTilings
                    .filter((option) => option.family === "aperiodic")
                    .map((option) => option.geometry),
            );
        }
        if (preset === "all") {
            return new Set(allTilings.map((option) => option.geometry));
        }
        return new Set();
    }

    function replaceSelection(nextSelection: Set<string>): void {
        selected.clear();
        nextSelection.forEach((geometry) => selected.add(geometry));
    }

    function sameSelection(left: Set<string>, right: Set<string>): boolean {
        return left.size === right.size && [...left].every((geometry) => right.has(geometry));
    }

    function activePreset(): TilingPreset | null {
        const presets: TilingPreset[] = [
            "representative",
            "regular",
            "mixed",
            "aperiodic",
            "all",
            "none",
        ];
        return (
            presets.find((preset) => sameSelection(selected, selectionForPreset(preset))) ?? null
        );
    }

    function updatePresetButtons(): void {
        const active = activePreset();
        for (const [preset, button] of presetButtons) {
            const isActive = preset === active;
            button.classList.toggle("is-active", isActive);
            button.setAttribute("aria-pressed", isActive ? "true" : "false");
        }
    }

    function updateSummary(): void {
        const summary = root.querySelector("#compare-tilings-summary");
        if (summary) {
            summary.textContent = summaryText();
        }
        updateFamilyCountLabels();
        updatePresetButtons();
        const disabled = running || selected.size === 0;
        runButton.disabled = disabled;
        playButton.disabled = disabled;
        copyRunButton.disabled = disabled;
    }

    function familySelectionCounts(family: string): { selectedCount: number; totalCount: number } {
        let selectedCount = 0;
        let totalCount = 0;
        for (const option of allTilings) {
            if (option.family !== family) {
                continue;
            }
            if (!tilingCompatibleWithSelectedRule(option)) {
                continue;
            }
            totalCount += 1;
            if (selected.has(option.geometry)) {
                selectedCount += 1;
            }
        }
        return { selectedCount, totalCount };
    }

    function familySelectionCountText(family: string): string {
        const { selectedCount, totalCount } = familySelectionCounts(family);
        return `${selectedCount}/${totalCount}`;
    }

    function updateFamilyCountLabels(): void {
        root.querySelectorAll<HTMLElement>(".compare-family-count").forEach((node) => {
            const family = node.dataset.family;
            if (family) {
                node.textContent = familySelectionCountText(family);
            }
        });
    }

    function summaryText(): string {
        const counts = { regular: 0, mixed: 0, aperiodic: 0 };
        for (const option of allTilings) {
            if (!selected.has(option.geometry)) {
                continue;
            }
            if (option.family === "regular") {
                counts.regular += 1;
            } else if (isMixedFamily(option.family)) {
                counts.mixed += 1;
            } else if (option.family === "aperiodic") {
                counts.aperiodic += 1;
            }
        }
        const parts = [
            `${selected.size} / ${compatibleTilingsForSelectedRule().length} selected`,
            ...(counts.regular > 0 ? [`Regular ${counts.regular}`] : []),
            ...(counts.mixed > 0 ? [`Mixed ${counts.mixed}`] : []),
            ...(counts.aperiodic > 0 ? [`Aperiodic ${counts.aperiodic}`] : []),
        ];
        return parts.join(" · ");
    }

    function selectedRuleName(): string {
        return ruleSelect.value || rules[0]?.name || "conway";
    }

    function selectedRule(): RuleDefinition | null {
        return rules.find((rule) => rule.name === selectedRuleName()) ?? null;
    }

    function tilingCompatibleWithSelectedRule(option: TilingOption): boolean {
        return ruleSupportsTilingFamily(selectedRule(), option.tilingFamily);
    }

    function compatibleTilingsForSelectedRule(): TilingOption[] {
        return allTilings.filter((option) => tilingCompatibleWithSelectedRule(option));
    }

    function pruneSelectionForSelectedRule({ selectAllIfEmpty = false } = {}): void {
        const compatibleTilings = compatibleTilingsForSelectedRule();
        const compatibleGeometries = new Set(compatibleTilings.map((option) => option.geometry));
        let changed = false;
        for (const geometry of [...selected]) {
            if (!compatibleGeometries.has(geometry)) {
                selected.delete(geometry);
                changed = true;
            }
        }
        if (selectAllIfEmpty && selected.size === 0 && compatibleTilings.length > 0) {
            compatibleTilings.forEach((option) => selected.add(option.geometry));
            changed = true;
        }
        if (changed) {
            refreshPreview();
        }
    }

    function patternShareUrl(pattern: PatternPayload): string {
        return buildShareUrl(pattern, window.location.href);
    }

    function currentRunConfig(): CompareRunConfig {
        const config: CompareRunConfig = {
            seed: seedInput.value,
            rule: selectedRuleName(),
            traversal: traversalSelect.value,
            frames: clampNumber(stepsInput.value, 1, 500, 50),
            grid_size: clampNumber(gridInput.value, 2, 64, 16),
            geometries: [...selected],
        };
        if (isShapeMode()) {
            config.pattern = shapeSelect.value;
        }
        return config;
    }

    function compareRunUrl(): string {
        return buildCompareRunUrl(currentRunConfig(), window.location.href);
    }

    async function ensureRules(): Promise<void> {
        if (rulesLoaded) {
            return;
        }
        try {
            const response = await options.backend.getRules();
            rules = response.rules;
        } catch {
            rules = [];
        }
        rulesLoaded = true;
        ruleSelect.replaceChildren(
            ...rules.map((rule) =>
                el("option", { value: rule.name, textContent: rule.display_name ?? rule.name }),
            ),
        );
        const conway = rules.find((rule) => rule.name === "conway");
        if (conway) {
            ruleSelect.value = "conway";
        }
        ruleSelect.addEventListener("change", () => {
            pruneSelectionForSelectedRule({ selectAllIfEmpty: true });
            renderTilingChecklist();
            refreshPreview();
        });
        pruneSelectionForSelectedRule();
        renderTilingChecklist();
    }

    function setRunning(next: boolean): void {
        running = next;
        runButton.textContent = next ? "Running…" : "Run comparison";
        updateSummary();
    }

    function selectHasValue(select: HTMLSelectElement, value: string): boolean {
        return [...select.options].some((option) => option.value === value);
    }

    function syncShapeMode(): void {
        const shapeMode = isShapeMode();
        seedWorkspace.classList.toggle("is-shape-mode", shapeMode);
        seedPadBlock.style.display = shapeMode ? "none" : "";
        seedInput.disabled = shapeMode;
    }

    async function applyRunConfig(config: CompareRunConfig): Promise<void> {
        await ensureRules();

        seedInput.value = config.seed;
        seedPad.syncFromSeed();
        if (selectHasValue(ruleSelect, config.rule)) {
            ruleSelect.value = config.rule;
        }
        if (selectHasValue(traversalSelect, config.traversal)) {
            traversalSelect.value = config.traversal;
        }
        stepsInput.value = String(config.frames);
        gridInput.value = String(config.grid_size);
        shapeSelect.value =
            config.pattern && selectHasValue(shapeSelect, config.pattern) ? config.pattern : "";
        syncShapeMode();

        const knownGeometries = new Set(allTilings.map((tiling) => tiling.geometry));
        replaceSelection(
            new Set(config.geometries.filter((geometry) => knownGeometries.has(geometry))),
        );
        renderTilingChecklist();
        refreshPreview();
        resultsArea.replaceChildren();
        filmstripArea.hidden = true;
        statusLine.textContent = `Loaded run link — ${selected.size} tilings ready.`;
    }

    function highlightGeometry(geometry: string | null): void {
        resultsArea.querySelectorAll<SVGElement>("[data-geometry]").forEach((node) => {
            node.classList.toggle(
                "is-dimmed",
                geometry !== null && node.getAttribute("data-geometry") !== geometry,
            );
        });
    }

    async function runComparison(): Promise<void> {
        if (running || selected.size === 0) {
            return;
        }
        setRunning(true);
        statusLine.textContent = `Running ${selected.size} tilings…`;
        resultsArea.replaceChildren();

        const request: CompareRequest = {
            seed: seedInput.value,
            rule: selectedRuleName(),
            traversal: traversalSelect.value,
            steps: clampNumber(stepsInput.value, 1, 500, 50),
            grid_size: clampNumber(gridInput.value, 2, 64, 16),
            geometries: [...selected],
            include_states: true,
            ...(isShapeMode() ? { pattern: shapeSelect.value } : {}),
        };

        try {
            const comparison = await options.backend.compareSeed(request);
            renderResults(comparison);
            const sourceDesc = isShapeMode()
                ? `shape "${shapeSelect.value}"`
                : `${comparison.seed_bits} bits`;
            statusLine.textContent = `Done — ${comparison.results.length} tilings, ${sourceDesc}.`;
        } catch (error) {
            statusLine.textContent = `Error: ${error instanceof Error ? error.message : String(error)}`;
        } finally {
            setRunning(false);
        }
    }

    async function runFilmstrip(): Promise<void> {
        if (running || selected.size === 0) {
            return;
        }
        setRunning(true);
        statusLine.textContent = `Building filmstrip for ${selected.size} tilings…`;

        const request: FilmstripRequest = {
            seed: seedInput.value,
            rule: selectedRuleName(),
            traversal: traversalSelect.value,
            // The backend further clamps frames to its filmstrip ceiling.
            frames: clampNumber(stepsInput.value, 1, 500, 50),
            grid_size: clampNumber(gridInput.value, 2, 64, 16),
            geometries: [...selected],
            ...(isShapeMode() ? { pattern: shapeSelect.value } : {}),
        };

        try {
            const filmstrip = await options.backend.requestFilmstrip(request);
            if (!filmstripView) {
                filmstripView = createFilmstripView({
                    backend: options.backend,
                    getLiveColor: () => liveColorForRule(selectedRuleName()),
                    loop: true,
                });
                filmstripArea.append(filmstripView.element);
            }
            filmstripArea.hidden = false;
            await filmstripView.load(filmstrip);
            statusLine.textContent = `Filmstrip ready — ${filmstrip.tilings.length} tilings × ${filmstrip.frame_count} generations. Press play.`;
        } catch (error) {
            statusLine.textContent = `Error: ${error instanceof Error ? error.message : String(error)}`;
        } finally {
            setRunning(false);
        }
    }

    function renderResults(comparison: Parameters<typeof buildPhasePortraitSvg>[0]): void {
        resultsArea.replaceChildren();
        if (comparison.degenerate) {
            resultsArea.append(
                el("div", {
                    class: "compare-warning",
                    textContent:
                        "This seed extincts quickly on most selected tilings — not a meaningful comparison. Try a larger seed, different rule, or more steps.",
                }),
            );
        }
        resultsArea.append(
            el("div", {
                class: "compare-section-title",
                textContent: "Phase portrait — live(t) / live(0)",
            }),
            buildPhasePortraitSvg(comparison),
            el("div", { class: "compare-section-title", textContent: "End-state classification" }),
            el("div", { class: "compare-grid-scroll" }, [
                buildClassificationGrid(comparison, {
                    onRowHover: highlightGeometry,
                    renderRowActions: (result) => renderRowActions(comparison, result),
                }),
            ]),
        );
    }

    function openPattern(pattern: PatternPayload): void {
        if (options.onOpenPattern) {
            options.onOpenPattern(pattern);
            options.onRequestClose?.();
            return;
        }
        openPatternInTab(pattern);
    }

    function renderRowActions(
        comparison: SeedComparisonResult,
        result: TopologyComparisonResultPayload,
    ): Node | null {
        const begin = buildStatePattern(comparison, result, "begin");
        if (!begin) {
            return null;
        }
        const end = buildStatePattern(comparison, result, "end");
        const wrap = el("div", { class: "compare-row-actions" });
        const inPlace = options.onOpenPattern;
        const beginTitle = inPlace
            ? "Load the seed on this tiling into the board"
            : "Open the seed on this tiling in a new tab";
        const openItems: ActionMenuItem[] = [
            {
                label: "Begin",
                title: beginTitle,
                onClick: () => openPattern(begin),
            },
        ];
        if (end) {
            const endTitle = inPlace
                ? "Load the final state on this tiling into the board"
                : "Open the final state on this tiling in a new tab";
            openItems.push({
                label: "End",
                title: endTitle,
                onClick: () => openPattern(end),
            });
        }
        wrap.append(actionMenu("Open", "Open state", openItems));
        if (end) {
            // Symmetric with the open buttons: a shareable link for either state.
            wrap.append(
                actionMenu("Copy", "Copy share link", [
                    copyLinkMenuItem(begin, "Begin", "Copy a shareable link to the seed state"),
                    copyLinkMenuItem(end, "End", "Copy a shareable link to the final state"),
                ]),
            );
        } else {
            wrap.append(
                actionMenu("Copy", "Copy share link", [
                    copyLinkMenuItem(begin, "Link", "Copy a shareable link to this state"),
                ]),
            );
        }
        if (result.topology_spec && result.cell_count > 0) {
            if (result.cell_count <= MAX_PREVIEW_CELLS) {
                const previewButton = linkButton("▸ preview", "Show begin/end thumbnails", () =>
                    togglePreview(comparison, result, previewButton),
                );
                wrap.append(previewButton);
            } else {
                // Too dense for a useful 132 px thumbnail; say so rather than
                // silently dropping the preview affordance.
                wrap.append(
                    el("span", {
                        class: "compare-row-note",
                        textContent: "preview too large",
                        title: `${result.cell_count.toLocaleString()} cells exceeds the ${MAX_PREVIEW_CELLS.toLocaleString()}-cell preview limit`,
                    }),
                );
            }
        }
        return wrap;
    }

    function previewKey(result: TopologyComparisonResultPayload): string {
        const spec = result.topology_spec;
        return `${result.geometry}:${spec?.width}x${spec?.height}:${spec?.patch_depth}`;
    }

    function fetchPreview(result: TopologyComparisonResultPayload): Promise<TopologyPreview> {
        const key = previewKey(result);
        let pending = previewCache.get(key);
        if (!pending) {
            const spec = result.topology_spec;
            pending = options.backend.previewTopology({
                geometry: result.geometry,
                width: spec?.width ?? 16,
                height: spec?.height ?? 16,
                ...(spec?.patch_depth === undefined ? {} : { patch_depth: spec.patch_depth }),
            });
            previewCache.set(key, pending);
        }
        return pending;
    }

    function liveColorForRule(ruleName: string): (state: number) => string {
        const rule = rules.find((candidate) => candidate.name === ruleName);
        const colorByValue = new Map<number, string>();
        for (const definition of rule?.states ?? []) {
            colorByValue.set(definition.value, definition.color);
        }
        return (state) => colorByValue.get(state) ?? "var(--live, #1f2430)";
    }

    function thumbnailBlock(
        label: string,
        preview: TopologyPreview,
        cellsById: Record<string, number>,
        liveColor: (state: number) => string,
        pattern: PatternPayload | null = null,
    ): HTMLElement {
        const thumbnail = buildBoardThumbnailSvg(preview, cellsById, {
            liveColor,
            label: `${label} state`,
        });
        const media = pattern
            ? el(
                  "a",
                  {
                      class: "compare-thumb-link",
                      href: patternShareUrl(pattern),
                      target: "_blank",
                      rel: "noopener",
                      title: `Open ${label.toLowerCase()} state in a new tab`,
                      "aria-label": `Open ${label.toLowerCase()} state in a new tab`,
                  },
                  [thumbnail],
              )
            : thumbnail;
        return el("div", { class: "compare-thumb-block" }, [
            el("div", { class: "compare-thumb-label", textContent: label }),
            media,
        ]);
    }

    function togglePreview(
        comparison: SeedComparisonResult,
        result: TopologyComparisonResultPayload,
        button: HTMLButtonElement,
    ): void {
        const row = button.closest("tr");
        if (!row) {
            return;
        }
        const sibling = row.nextElementSibling;
        if (sibling instanceof HTMLElement && sibling.classList.contains("compare-detail")) {
            sibling.remove();
            button.textContent = "▸ preview";
            return;
        }
        button.textContent = "▾ preview";
        const cell = el("td", { class: "compare-detail-cell" });
        cell.colSpan = row.children.length;
        cell.append(el("div", { class: "compare-detail-status", textContent: "Loading preview…" }));
        const detail = el("tr", { class: "compare-detail" }, [cell]);
        row.after(detail);
        void renderPreviewInto(comparison, result, cell);
    }

    async function renderPreviewInto(
        comparison: SeedComparisonResult,
        result: TopologyComparisonResultPayload,
        cell: HTMLTableCellElement,
    ): Promise<void> {
        try {
            const preview = await fetchPreview(result);
            const liveColor = liveColorForRule(comparison.rule_name);
            cell.replaceChildren(
                el("div", { class: "compare-detail-grid" }, [
                    thumbnailBlock(
                        "Begin",
                        preview,
                        result.initial_cells_by_id ?? {},
                        liveColor,
                        buildStatePattern(comparison, result, "begin"),
                    ),
                    thumbnailBlock(
                        "End",
                        preview,
                        result.final_cells_by_id ?? {},
                        liveColor,
                        buildStatePattern(comparison, result, "end"),
                    ),
                ]),
            );
        } catch (error) {
            cell.replaceChildren(
                el("div", {
                    class: "compare-detail-status",
                    textContent: `Preview failed: ${error instanceof Error ? error.message : String(error)}`,
                }),
            );
        }
    }

    function linkButton(label: string, title: string, onClick: () => void): HTMLButtonElement {
        const button = el("button", { class: "compare-link", type: "button", title }, [label]);
        button.addEventListener("click", onClick);
        return button;
    }

    function actionMenu(label: string, title: string, items: ActionMenuItem[]): HTMLElement {
        const details = el("details", { class: "compare-action-menu" });
        const summary = el("summary", { class: "compare-link", title, textContent: label });
        const panel = el(
            "div",
            { class: "compare-action-menu-panel" },
            items.map((item) => {
                const button = el("button", {
                    class: "compare-action-menu-item",
                    type: "button",
                    title: item.title,
                    textContent: item.label,
                });
                button.addEventListener("click", () => {
                    details.removeAttribute("open");
                    item.onClick();
                });
                return button;
            }),
        );
        details.append(summary, panel);
        return details;
    }

    function copyLinkMenuItem(
        pattern: PatternPayload,
        label: string,
        title: string,
    ): ActionMenuItem {
        return {
            label,
            title,
            onClick: () => copyPatternLink(pattern, label),
        };
    }

    function copyPatternLink(pattern: PatternPayload, copiedLabel: string): void {
        const url = patternShareUrl(pattern);
        const clipboard = navigator.clipboard;
        if (!clipboard) {
            window.prompt("Copy this share link:", url);
            return;
        }
        void clipboard.writeText(url).then(
            () => {
                statusLine.textContent = `Copied ${copiedLabel.toLowerCase()} share link.`;
            },
            () => window.prompt("Copy this share link:", url),
        );
    }

    function copyRunLink(): void {
        const url = compareRunUrl();
        const clipboard = navigator.clipboard;
        if (!clipboard) {
            window.prompt("Copy this run link:", url);
            return;
        }
        void clipboard.writeText(url).then(
            () => {
                statusLine.textContent = "Copied run link.";
            },
            () => window.prompt("Copy this run link:", url),
        );
    }

    // Native <details> menus stay open until re-clicked; close any open one when
    // the click lands outside it so only one menu is ever open at a time.
    function onDocumentPointerDown(event: Event): void {
        const target = event.target;
        for (const menu of root.querySelectorAll(".compare-action-menu[open]")) {
            if (!(target instanceof Node) || !menu.contains(target)) {
                menu.removeAttribute("open");
            }
        }
    }

    runButton.addEventListener("click", () => void runComparison());
    playButton.addEventListener("click", () => void runFilmstrip());
    copyRunButton.addEventListener("click", copyRunLink);
    document.addEventListener("pointerdown", onDocumentPointerDown);

    return {
        element: root,
        activate(): void {
            void ensureRules();
            refreshPreview();
            highlightGeometry(null);
        },
        applyRunConfig,
        handleEscape(): boolean {
            const openMenu = root.querySelector(".compare-action-menu[open]");
            if (openMenu) {
                openMenu.removeAttribute("open");
                return true;
            }
            return false;
        },
        dispose(): void {
            document.removeEventListener("pointerdown", onDocumentPointerDown);
            seedPad.dispose();
            seedPreview.dispose();
            filmstripView?.dispose();
        },
    };
}

function clampNumber(raw: string, low: number, high: number, fallback: number): number {
    const parsed = Number.parseInt(raw, 10);
    if (!Number.isFinite(parsed)) {
        return fallback;
    }
    return Math.min(high, Math.max(low, parsed));
}
