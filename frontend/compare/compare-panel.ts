import type {
    AppBootstrapData,
    CompareRequest,
    PatternPayload,
    RuleDefinition,
    SeedComparisonResult,
    TopologyComparisonResultPayload,
    TopologyPreview,
} from "../types/domain.js";
import type { SimulationBackend } from "../types/controller.js";
import { buildShareUrl } from "../share-link.js";
import { TRAVERSAL_OPTIONS } from "./compare-options.js";
import { buildClassificationGrid, buildPhasePortraitSvg, familyColor } from "./compare-charts.js";
import { buildBoardThumbnailSvg } from "./compare-thumbnail.js";
import { createSeedPad } from "./compare-seed-pad.js";
import { createSeedPreview } from "./compare-seed-preview.js";
import { COMPARE_PANEL_STYLES } from "./compare-styles.js";

// Matches _MAX_PREVIEW_CELLS in backend/simulation/topology_preview.py; larger
// patches are not offered a thumbnail (the backend would reject them anyway).
const MAX_PREVIEW_CELLS = 4000;

// Mirrors the pattern schema in pattern-io.ts / parsers/pattern.ts; reused so a
// begin/end state can be encoded as a shareable board link.
const PATTERN_FORMAT = "cellular-automaton-lab-pattern";
const PATTERN_VERSION = 5;

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

interface MountComparePanelOptions {
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    host?: HTMLElement;
    /** When provided, begin/end open into the current board instead of a new tab. */
    onOpenPattern?: (pattern: PatternPayload) => void;
}

interface TilingOption {
    geometry: string;
    label: string;
    family: string;
}

const DEFAULT_SEED = "01100 11000 01000";
const STYLE_ELEMENT_ID = "compare-panel-styles";

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

function ensureStyles(): void {
    if (document.getElementById(STYLE_ELEMENT_ID)) {
        return;
    }
    const style = el("style", { id: STYLE_ELEMENT_ID, textContent: COMPARE_PANEL_STYLES });
    document.head.append(style);
}

export interface ComparePanelHandle {
    dispose(): void;
}

export function mountComparePanel(options: MountComparePanelOptions): ComparePanelHandle {
    ensureStyles();
    const host = options.host ?? document.body;
    const allTilings = tilingOptions(options.bootstrapData);
    const selected = defaultSelection(allTilings);

    let rules: RuleDefinition[] = [];
    let rulesLoaded = false;
    let running = false;
    let lastFocus: HTMLElement | null = null;
    const previewCache = new Map<string, Promise<TopologyPreview>>();

    const toggleButton = el(
        "button",
        { class: "compare-toggle", type: "button", title: "Compare a seed across tilings" },
        ["⊞ Compare tilings"],
    );

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

    const tilingList = el("div", { class: "compare-tilings" });

    const seedPreview = createSeedPreview({
        backend: options.backend,
        getSeed: () => seedInput.value,
        getTraversal: () => traversalSelect.value,
        getGridSize: () => clampNumber(gridInput.value, 2, 64, 16),
        getTilings: () =>
            allTilings
                .filter((tiling) => selected.has(tiling.geometry))
                .map((tiling) => ({ geometry: tiling.geometry, label: tiling.label })),
    });

    const seedPad = createSeedPad({
        getSeed: () => seedInput.value,
        onSeedChange: (formatted) => {
            seedInput.value = formatted;
            seedPreview.redraw();
        },
    });
    seedInput.addEventListener("input", () => {
        seedPad.syncFromSeed();
        seedPreview.redraw();
    });
    traversalSelect.addEventListener("change", () => seedPreview.refresh());
    gridInput.addEventListener("change", () => seedPreview.refresh());

    const runButton = el("button", { class: "compare-run", type: "button" }, ["Run comparison"]);
    const statusLine = el("div", { class: "compare-status", role: "status" });
    const resultsArea = el("div", { class: "compare-results" });

    const closeButton = el(
        "button",
        { class: "compare-close", type: "button", "aria-label": "Close" },
        ["×"],
    );

    const dialog = el(
        "div",
        {
            class: "compare-dialog",
            role: "dialog",
            "aria-modal": "true",
            "aria-label": "Compare tilings",
            tabindex: "-1",
        },
        [
            el("div", { class: "compare-header" }, [
                el("h2", { class: "compare-title", textContent: "Compare seed across tilings" }),
                closeButton,
            ]),
            el("p", {
                class: "compare-intro",
                textContent:
                    "Map one seed onto each tiling through a canonical traversal, run the same rule, and compare how topology shapes the outcome.",
            }),
            el("div", { class: "compare-form" }, [
                labeledField("Rule", ruleSelect),
                labeledField("Seed (bits)", seedInput),
                labeledField("Traversal", traversalSelect),
                labeledField("Steps", stepsInput),
                labeledField("Grid size", gridInput),
            ]),
            el("div", { class: "compare-seedpad-block" }, [
                el("div", {
                    class: "compare-seedpad-title",
                    textContent: "Or draw the seed (read row-major into the bit string)",
                }),
                seedPad.element,
                el("div", {
                    class: "compare-seedpad-title",
                    textContent: "Seed lands like this on:",
                }),
                seedPreview.element,
            ]),
            el("div", { class: "compare-tilings-block" }, [tilingControlsBar(), tilingList]),
            el("div", { class: "compare-actions" }, [runButton, statusLine]),
            resultsArea,
        ],
    );

    const backdrop = el("div", { class: "compare-backdrop", hidden: true }, [dialog]);

    host.append(toggleButton, backdrop);
    renderTilingChecklist();

    function labeledField(label: string, field: HTMLElement): HTMLLabelElement {
        return el("label", { class: "compare-label" }, [el("span", { textContent: label }), field]);
    }

    function tilingControlsBar(): HTMLElement {
        const allButton = el("button", {
            class: "compare-mini",
            type: "button",
            textContent: "All",
        });
        const noneButton = el("button", {
            class: "compare-mini",
            type: "button",
            textContent: "None",
        });
        const resetButton = el("button", {
            class: "compare-mini",
            type: "button",
            textContent: "Representative",
        });
        allButton.addEventListener("click", () => {
            allTilings.forEach((option) => selected.add(option.geometry));
            renderTilingChecklist();
            seedPreview.refresh();
        });
        noneButton.addEventListener("click", () => {
            selected.clear();
            renderTilingChecklist();
            seedPreview.refresh();
        });
        resetButton.addEventListener("click", () => {
            selected.clear();
            defaultSelection(allTilings).forEach((geometry) => selected.add(geometry));
            renderTilingChecklist();
            seedPreview.refresh();
        });
        return el("div", { class: "compare-tilings-controls" }, [
            el("span", { class: "compare-tilings-summary", id: "compare-tilings-summary" }),
            allButton,
            noneButton,
            resetButton,
        ]);
    }

    function renderTilingChecklist(): void {
        tilingList.replaceChildren();
        const byFamily = new Map<string, TilingOption[]>();
        for (const option of allTilings) {
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
                ]),
            );
            for (const option of optionsForFamily) {
                const checkbox = el("input", {
                    type: "checkbox",
                    checked: selected.has(option.geometry),
                });
                checkbox.addEventListener("change", () => {
                    if (checkbox.checked) {
                        selected.add(option.geometry);
                    } else {
                        selected.delete(option.geometry);
                    }
                    updateSummary();
                    seedPreview.refresh();
                });
                group.append(
                    el("label", { class: "compare-tiling" }, [
                        checkbox,
                        el("span", { textContent: option.label }),
                    ]),
                );
            }
            tilingList.append(group);
        }
        updateSummary();
    }

    function updateSummary(): void {
        const summary = dialog.querySelector("#compare-tilings-summary");
        if (summary) {
            summary.textContent = `${selected.size} / ${allTilings.length} selected`;
        }
        runButton.disabled = running || selected.size === 0;
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
    }

    function setRunning(next: boolean): void {
        running = next;
        runButton.textContent = next ? "Running…" : "Run comparison";
        updateSummary();
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
            rule: ruleSelect.value || "conway",
            traversal: traversalSelect.value,
            steps: clampNumber(stepsInput.value, 1, 500, 50),
            grid_size: clampNumber(gridInput.value, 2, 64, 16),
            geometries: [...selected],
            include_states: true,
        };

        try {
            const comparison = await options.backend.compareSeed(request);
            renderResults(comparison);
            statusLine.textContent = `Done — ${comparison.results.length} tilings, ${comparison.seed_bits} bits.`;
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
            buildClassificationGrid(comparison, {
                onRowHover: highlightGeometry,
                renderRowActions: (result) => renderRowActions(comparison, result),
            }),
        );
    }

    function openPattern(pattern: PatternPayload): void {
        if (options.onOpenPattern) {
            options.onOpenPattern(pattern);
            close();
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
        const beginLabel = inPlace ? "begin" : "begin ↗";
        const beginTitle = inPlace
            ? "Load the seed on this tiling into the board"
            : "Open the seed on this tiling in a new tab";
        wrap.append(linkButton(beginLabel, beginTitle, () => openPattern(begin)));
        if (end) {
            const endLabel = inPlace ? "end" : "end ↗";
            const endTitle = inPlace
                ? "Load the final state on this tiling into the board"
                : "Open the final state on this tiling in a new tab";
            wrap.append(linkButton(endLabel, endTitle, () => openPattern(end)));
        }
        wrap.append(copyLinkButton(end ?? begin));
        if (
            result.topology_spec &&
            result.cell_count > 0 &&
            result.cell_count <= MAX_PREVIEW_CELLS
        ) {
            const previewButton = linkButton("▸ preview", "Show begin/end thumbnails", () =>
                togglePreview(comparison, result, previewButton),
            );
            wrap.append(previewButton);
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
    ): HTMLElement {
        return el("div", { class: "compare-thumb-block" }, [
            el("div", { class: "compare-thumb-label", textContent: label }),
            buildBoardThumbnailSvg(preview, cellsById, { liveColor, label: `${label} state` }),
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
                    thumbnailBlock("Begin", preview, result.initial_cells_by_id ?? {}, liveColor),
                    thumbnailBlock("End", preview, result.final_cells_by_id ?? {}, liveColor),
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

    function copyLinkButton(pattern: PatternPayload): HTMLButtonElement {
        const button = el(
            "button",
            { class: "compare-link", type: "button", title: "Copy a shareable link to this state" },
            ["⧉ link"],
        );
        button.addEventListener("click", () => {
            const url = buildShareUrl(pattern, window.location.href);
            const clipboard = navigator.clipboard;
            if (!clipboard) {
                window.prompt("Copy this share link:", url);
                return;
            }
            void clipboard.writeText(url).then(
                () => {
                    button.textContent = "copied";
                    window.setTimeout(() => (button.textContent = "⧉ link"), 1200);
                },
                () => window.prompt("Copy this share link:", url),
            );
        });
        return button;
    }

    function open(): void {
        lastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        backdrop.hidden = false;
        void ensureRules();
        seedPreview.refresh();
        dialog.focus();
    }

    function close(): void {
        backdrop.hidden = true;
        highlightGeometry(null);
        lastFocus?.focus();
    }

    function onKeydown(event: KeyboardEvent): void {
        if (event.key === "Escape" && !backdrop.hidden) {
            close();
        }
    }

    toggleButton.addEventListener("click", open);
    closeButton.addEventListener("click", close);
    runButton.addEventListener("click", () => void runComparison());
    backdrop.addEventListener("click", (event) => {
        if (event.target === backdrop) {
            close();
        }
    });
    document.addEventListener("keydown", onKeydown);

    return {
        dispose(): void {
            document.removeEventListener("keydown", onKeydown);
            seedPad.dispose();
            seedPreview.dispose();
            toggleButton.remove();
            backdrop.remove();
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
