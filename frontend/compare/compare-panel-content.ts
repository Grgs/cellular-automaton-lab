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
    SeedFilmstripResult,
    TopologyComparisonResultPayload,
    TopologyFilmstrip,
    TopologyPreview,
} from "../types/domain.js";
import type { SimulationBackend } from "../types/controller.js";
import { buildShareUrl } from "../share-link.js";
import { buildCompareRunUrl, type CompareRunConfig } from "./compare-run-link.js";
import { hashWithFocus, hashWithoutFocus, readFocusFromHash } from "./compare-route.js";
import {
    FEATURED_COMPARE_DEMO_LOOP_START,
    FEATURED_COMPARE_DEMO_SPEED,
    FEATURED_COMPARE_DEMO_STILL_FRAME,
    SEED_SHAPE_OPTIONS,
    TRAVERSAL_OPTIONS,
} from "./compare-options.js";
import { buildClassificationGrid, buildPhasePortraitSvg, familyColor } from "./compare-charts.js";
import { buildBoardThumbnailSvg } from "./compare-thumbnail.js";
import { createSeedPad } from "./compare-seed-pad.js";
import { createSeedPreview } from "./compare-seed-preview.js";
import {
    createFilmstripView,
    type FilmstripLoadOptions,
    type FilmstripViewController,
} from "./compare-filmstrip-view.js";
import { createFilmstripTransport } from "./compare-transport.js";
import { paneSessionId, type FocusPaneServices } from "../pane/pane-core.js";
import type { FocusPaneHandle } from "./compare-focus-pane.js";
import {
    deleteSavedCompareRun,
    deleteSavedTilingSet,
    listSavedCompareRuns,
    listSavedTilingSets,
    saveCompareRun,
    saveTilingSet,
    type SavedCompareRun,
    type SavedTilingSet,
} from "./compare-storage.js";
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

/** Build a shareable board pattern for the live filmstrip's current generation. */
function buildFilmstripFramePattern(
    filmstrip: SeedFilmstripResult,
    tiling: TopologyFilmstrip,
    frameIndex: number,
): PatternPayload | null {
    const cells = tiling.frames[frameIndex];
    if (!tiling.topology_spec || cells === undefined) {
        return null;
    }
    return {
        format: PATTERN_FORMAT,
        version: PATTERN_VERSION,
        topology_spec: tiling.topology_spec,
        rule: filmstrip.rule_name,
        cells_by_id: cells,
    };
}

function openPatternInTab(pattern: PatternPayload): void {
    window.open(buildShareUrl(pattern, window.location.href), "_blank", "noopener");
}

function prefersReducedMotion(): boolean {
    return (
        typeof window !== "undefined" &&
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
}

export interface ComparePanelContentOptions {
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    /** When provided, begin/end open into the current board instead of a new tab. */
    onOpenPattern?: (pattern: PatternPayload) => void;
    /** The content asks its host to dismiss it (e.g. after loading in place). */
    onRequestClose?: () => void;
    /** Server-only seams for the live focus pane; absent/null baseSessionId = fork to the Lab. */
    focusPaneServices?: FocusPaneServices;
    /** The Lab rule active when the wall is opened; used for the default wall setup. */
    getInitialRuleName?: () => string | null | undefined;
}

export interface ComparePanelContentHandle {
    /** The content root; mount it inside a dialog, a route, or any container. */
    element: HTMLElement;
    /** Call when the content becomes visible: load rules and refresh previews. */
    activate(): void;
    /** Call when the content is hidden so background work can be suspended. */
    deactivate(): void;
    /** Populate the workspace from a decoded run link without running it. */
    applyRunConfig(config: CompareRunConfig): Promise<void>;
    /** Apply a config, build the live filmstrip, and start looping playback. */
    runFeaturedDemo(config: CompareRunConfig): Promise<void>;
    /** Apply a default wall config and build the filmstrip without autoplaying. */
    runDefaultFilmstrip(config: CompareRunConfig): Promise<void>;
    /** Show a run-link load problem in the status line (e.g. an unreadable link). */
    reportRunLinkError(message: string): void;
    /** Let an open action menu consume Escape; returns true when it did. */
    handleEscape(): boolean;
    /** Return from speaker view to the gallery if a board is focused; true when it did. */
    exitFocusIfAny(): boolean;
    /** Handle a playback shortcut (space/arrows) once a filmstrip is live; true if consumed. */
    handlePlaybackKey(event: KeyboardEvent): boolean;
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
    let savedRuns: SavedCompareRun[] = [];
    let savedTilingSets: SavedTilingSet[] = [];
    let editingSavedRunId = "";
    let editingSavedTilingSetId = "";

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

    // "Play side by side" is the showcase action, so it is the primary button;
    // the analytical "Run comparison" is secondary and lives in the analysis
    // section below the live boards.
    const runButton = el("button", { class: "compare-run compare-run-secondary", type: "button" }, [
        "Run comparison",
    ]);
    const playButton = el(
        "button",
        {
            class: "compare-run",
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
    const savedRunNameInput = el("input", {
        class: "compare-field compare-saved-name",
        type: "text",
        placeholder: "Run name",
        "aria-label": "Saved run name",
    });
    const savedRunSelect = el("select", {
        class: "compare-field compare-saved-select",
        "aria-label": "Saved compare runs",
    });
    const saveRunButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Save run",
    });
    const loadRunButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Load run",
    });
    const deleteRunButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Delete run",
    });
    const savedRunHint = el("div", {
        class: "compare-saved-empty",
        id: "compare-saved-runs-hint",
    });
    const savedTilingSetNameInput = el("input", {
        class: "compare-field compare-saved-name",
        type: "text",
        placeholder: "Tiling set name",
        "aria-label": "Saved tiling set name",
    });
    const savedTilingSetSelect = el("select", {
        class: "compare-field compare-saved-select",
        "aria-label": "Saved tiling sets",
    });
    const saveTilingSetButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Save set",
    });
    const loadTilingSetButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Load set",
    });
    const deleteTilingSetButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Delete set",
    });
    const savedTilingSetHint = el("div", {
        class: "compare-saved-empty",
        id: "compare-saved-tilings-hint",
    });
    const statusLine = el("div", { class: "compare-status", role: "status" });
    const liveStateLine = el("div", {
        class: "compare-live-state",
        role: "status",
        "aria-live": "polite",
        textContent:
            "No live filmstrip yet. Select at least two tilings, then choose Play side by side.",
    });
    const stageHero = el("div", { class: "compare-stage-hero" }, [
        el("div", { class: "compare-stage-hero-glyph", "aria-hidden": "true", textContent: "▦" }),
        el("div", {
            class: "compare-stage-hero-title",
            textContent: "Watch one seed evolve across every tiling",
        }),
        el("p", {
            class: "compare-stage-hero-blurb",
            textContent:
                "Pick a rule and tilings below, then press Play side by side to run them on one shared clock.",
        }),
    ]);
    const filmstripArea = el("div", { class: "compare-filmstrip-area" }, [stageHero]);
    const filmstripTransport = createFilmstripTransport();
    const resultsArea = el("div", { class: "compare-results" });
    let filmstripView: FilmstripViewController | null = null;
    let activeFilmstrip: SeedFilmstripResult | null = null;
    let currentFocusGeometry: string | null = null;
    let focusPane: FocusPaneHandle | null = null;
    // Live in-place forking needs an independent server session; standalone
    // (no baseSessionId) forks into the Lab instead.
    const focusLiveEnabled = Boolean(options.focusPaneServices?.baseSessionId);

    // The focused board is mirrored into the hash (`&focus=<geometry>`) so speaker
    // view is shareable and the browser back button returns to the gallery.
    function mirrorFocusToHash(geometry: string | null): void {
        currentFocusGeometry = geometry;
        const current = window.location.hash;
        const next =
            geometry === null ? hashWithoutFocus(current) : hashWithFocus(current, geometry);
        if (next === current) {
            return;
        }
        if (next === "") {
            window.history.replaceState(
                null,
                "",
                `${window.location.pathname}${window.location.search}`,
            );
        } else {
            window.location.hash = next;
        }
    }

    function applyFocusFromHash(): void {
        if (!filmstripView || !activeFilmstrip) {
            return;
        }
        filmstripView.focus(readFocusFromHash(window.location.hash));
    }

    // Speaker view moves the seed workspace into the rail beside the hero; the
    // gallery returns it to the Configure disclosure.
    function updateSeedRail(geometry: string | null): void {
        const speaker = geometry !== null;
        stageMain.classList.toggle("is-speaker", speaker);
        if (speaker) {
            seedRailBody.append(seedWorkspace);
            seedRail.hidden = false;
        } else {
            seedHome?.append(seedWorkspace);
            seedRail.hidden = true;
        }
    }

    function handleFocusChanged(geometry: string | null): void {
        // A focus change (swap or exit) invalidates any live fork on the old hero.
        disposeFocusPane();
        mirrorFocusToHash(geometry);
        updateSeedRail(geometry);
    }

    function disposeFocusPane(): void {
        if (focusPane) {
            focusPane.dispose();
            focusPane = null;
        }
        filmstripView?.setHeroOverlay(null);
    }

    function reportFocusPaneError(error: unknown): void {
        statusLine.textContent = `Fork failed: ${error instanceof Error ? error.message : String(error)}`;
    }

    function disposeDetachedBackend(backend: SimulationBackend): void {
        void Promise.resolve(backend.dispose()).catch(reportFocusPaneError);
    }

    async function forkFocusedBoardLive(): Promise<void> {
        const geometry = currentFocusGeometry;
        if (!filmstripView || !activeFilmstrip || !geometry) {
            return;
        }
        const tiling = activeFilmstrip.tilings.find((candidate) => candidate.geometry === geometry);
        if (!tiling) {
            return;
        }
        const frameIndex = filmstripView.currentFrameIndex();
        const pattern = buildFilmstripFramePattern(activeFilmstrip, tiling, frameIndex);
        if (!pattern) {
            statusLine.textContent = "This generation cannot be forked.";
            return;
        }
        const services = options.focusPaneServices;
        // Standalone (no server session): fork into the Lab instead of in place.
        if (!services?.baseSessionId) {
            openPattern(pattern);
            return;
        }
        disposeFocusPane();
        let backend: SimulationBackend | null = null;
        try {
            backend = services.backendFactory(paneSessionId(services.baseSessionId, "focus"));
            const { mountFocusPane } = await import("./compare-focus-pane.js");

            if (!filmstripView || currentFocusGeometry !== geometry) {
                disposeDetachedBackend(backend);
                backend = null;
                return;
            }

            let nextFocusPane: FocusPaneHandle | null = null;
            nextFocusPane = mountFocusPane({
                geometry: tiling.geometry,
                frameIndex,
                pattern,
                backend,
                bootstrapData: options.bootstrapData,
                createGridView: services.createGridView,
                buildEditorToolCells: services.buildEditorToolCells,
                ...(services.resolveCellSize ? { resolveCellSize: services.resolveCellSize } : {}),
                onDiscard: () => {
                    if (focusPane === nextFocusPane) {
                        focusPane = null;
                    }
                    filmstripView?.setHeroOverlay(null);
                },
                onError: reportFocusPaneError,
            });
            backend = null;

            if (
                currentFocusGeometry !== geometry ||
                !filmstripView ||
                !filmstripView.setHeroOverlay(nextFocusPane.element)
            ) {
                nextFocusPane.dispose();
                return;
            }
            focusPane = nextFocusPane;
        } catch (error) {
            if (backend) {
                disposeDetachedBackend(backend);
            }
            reportFocusPaneError(error);
        }
    }

    function showStageHero(): void {
        stageHero.hidden = false;
        if (filmstripView) {
            filmstripView.element.hidden = true;
        }
    }

    function showStageBoards(): void {
        stageHero.hidden = true;
        if (filmstripView) {
            filmstripView.element.hidden = false;
        }
    }

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

    // In speaker view the seed workspace is reparented into this rail beside the
    // hero so the shared seed stays editable without leaving the wall. The seed is
    // tiling-agnostic, so editing it re-runs every board; a per-board edit is a
    // one-way fork into the Lab instead (the fork buttons on each board).
    const railRerunButton = el(
        "button",
        {
            class: "compare-run compare-run-secondary compare-seed-rail-rerun",
            type: "button",
            title: "Re-run every board from the edited seed",
        },
        ["Re-run wall from this seed"],
    );
    const seedRailBody = el("div", { class: "compare-seed-rail-body" });
    const railForkButton = el(
        "button",
        {
            class: "compare-run compare-run-secondary compare-seed-rail-fork",
            type: "button",
            title: focusLiveEnabled
                ? "Fork this generation into a live, editable board on the wall"
                : "Fork this generation into the single-board Lab",
        },
        [focusLiveEnabled ? "⑂ Fork this board live" : "⑂ Fork this board in the Lab"],
    );
    const seedRail = el("div", { class: "compare-seed-rail", hidden: true }, [
        el("div", { class: "compare-seed-rail-title", textContent: "Edit the shared seed" }),
        seedRailBody,
        railRerunButton,
        railForkButton,
        el("p", {
            class: "compare-seed-rail-hint",
            textContent: focusLiveEnabled
                ? "Seed edits re-run every board. Fork a board to edit it live while the others keep looping."
                : "Seed edits re-run every board. Board edits fork into the Lab.",
        }),
    ]);

    const stageMain = el("div", { class: "compare-stage-main" }, [seedRail, filmstripArea]);

    // Switching seed source toggles the bit pad/preview and refreshes accordingly.
    shapeSelect.addEventListener("change", () => {
        syncShapeMode();
        seedPreview.refresh();
    });

    const root = el("div", { class: "compare-content" }, [
        // The synchronized side-by-side is the point of the page, so the stage
        // leads and the video-style transport is docked directly beneath it. In
        // speaker view the seed rail sits beside the hero within the stage.
        el("div", { class: "compare-stage" }, [stageMain, liveStateLine]),
        el("div", { class: "compare-dock" }, [
            filmstripTransport.element,
            el("div", { class: "compare-actions" }, [playButton, copyRunButton, statusLine]),
        ]),
        // Configuration and data wait quietly below the experience, collapsed
        // into disclosures the reader opens only when they want to tune a run.
        configSection("Configure the run", "compare-config-run", true, [
            el("div", { class: "compare-form" }, [
                labeledField("Rule", ruleSelect),
                labeledField("Seed source", shapeSelect),
                labeledField("Traversal", traversalSelect),
                labeledField("Steps", stepsInput),
                labeledField("Grid size", gridInput),
            ]),
            seedWorkspace,
        ]),
        configSection("Tilings", "compare-config-tilings", true, [
            el("div", { class: "compare-tilings-block" }, [tilingControlsBar(), tilingList]),
        ]),
        configSection("Cross-tiling analysis", "compare-config-analysis", false, [
            el("div", { class: "compare-analysis" }, [
                el("p", {
                    class: "compare-intro",
                    textContent:
                        "Run the same seed to a fixed horizon and chart how each topology diverges — a phase portrait plus a per-tiling result table.",
                }),
                runButton,
                resultsArea,
            ]),
        ]),
        configSection("Saved runs and tiling sets", "compare-config-saved", false, [
            savedCompareControls(),
        ]),
    ]);

    // The seed workspace's gallery home is the Configure disclosure; it shuttles
    // between there and the speaker-view rail as focus changes.
    const seedHome = seedWorkspace.parentElement;

    renderTilingChecklist();
    refreshSavedControls();

    function labeledField(label: string, field: HTMLElement): HTMLLabelElement {
        return el("label", { class: "compare-label" }, [el("span", { textContent: label }), field]);
    }

    function configSection(
        title: string,
        className: string,
        open: boolean,
        children: Array<Node | string>,
    ): HTMLDetailsElement {
        return el(
            "details",
            { class: `compare-config ${className}`, ...(open ? { open: true } : {}) },
            [
                el("summary", { class: "compare-config-summary", textContent: title }),
                el("div", { class: "compare-config-body" }, children),
            ],
        );
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

    function savedCompareControls(): HTMLElement {
        saveRunButton.addEventListener("click", saveCurrentRun);
        loadRunButton.addEventListener("click", () => void loadSelectedRun());
        deleteRunButton.addEventListener("click", deleteSelectedRun);
        saveTilingSetButton.addEventListener("click", saveCurrentTilingSet);
        loadTilingSetButton.addEventListener("click", loadSelectedTilingSet);
        deleteTilingSetButton.addEventListener("click", deleteSelectedTilingSet);

        return el("div", { class: "compare-saved" }, [
            el(
                "section",
                { class: "compare-saved-section", "aria-labelledby": "compare-saved-runs-title" },
                [
                    el("h3", {
                        class: "compare-saved-title",
                        id: "compare-saved-runs-title",
                        textContent: "Saved runs",
                    }),
                    el("div", { class: "compare-saved-row" }, [
                        savedRunNameInput,
                        saveRunButton,
                        savedRunSelect,
                        loadRunButton,
                        deleteRunButton,
                    ]),
                    savedRunHint,
                ],
            ),
            el(
                "section",
                {
                    class: "compare-saved-section",
                    "aria-labelledby": "compare-saved-tilings-title",
                },
                [
                    el("h3", {
                        class: "compare-saved-title",
                        id: "compare-saved-tilings-title",
                        textContent: "Saved tiling sets",
                    }),
                    el("div", { class: "compare-saved-row" }, [
                        savedTilingSetNameInput,
                        saveTilingSetButton,
                        savedTilingSetSelect,
                        loadTilingSetButton,
                        deleteTilingSetButton,
                    ]),
                    savedTilingSetHint,
                ],
            ),
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
        playButton.disabled = running || selected.size < 2;
        playButton.title =
            selected.size < 2
                ? "Select at least two tilings to play them side by side"
                : "Run every selected tiling on a shared clock and play them side by side";
        copyRunButton.disabled = disabled;
        railRerunButton.disabled = running || selected.size < 2;
        railForkButton.disabled = running;
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

    function ruleByName(ruleName: string): RuleDefinition | null {
        return rules.find((rule) => rule.name === ruleName) ?? null;
    }

    function tilingCompatibleWithRule(
        rule: RuleDefinition | null | undefined,
        option: TilingOption,
    ): boolean {
        return ruleSupportsTilingFamily(rule, option.tilingFamily);
    }

    function tilingCompatibleWithSelectedRule(option: TilingOption): boolean {
        return tilingCompatibleWithRule(selectedRule(), option);
    }

    function compatibleTilingsForSelectedRule(): TilingOption[] {
        return allTilings.filter((option) => tilingCompatibleWithSelectedRule(option));
    }

    function preferredInitialRuleName(): string | null {
        const candidate = options.getInitialRuleName?.();
        return typeof candidate === "string" && candidate.length > 0 ? candidate : null;
    }

    function ruleSupportsEveryGeometry(ruleName: string, geometries: readonly string[]): boolean {
        const rule = ruleByName(ruleName);
        if (!rule) {
            return false;
        }
        return geometries.every((geometry) => {
            const option = allTilings.find((tiling) => tiling.geometry === geometry);
            return option ? tilingCompatibleWithRule(rule, option) : false;
        });
    }

    function defaultFilmstripConfig(config: CompareRunConfig): CompareRunConfig {
        const preferredRuleName = preferredInitialRuleName();
        if (
            preferredRuleName &&
            selectHasValue(ruleSelect, preferredRuleName) &&
            ruleSupportsEveryGeometry(preferredRuleName, config.geometries)
        ) {
            return { ...config, rule: preferredRuleName };
        }
        return config;
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

    function refreshSavedControls(preferredRunId = "", preferredTilingSetId = ""): void {
        savedRuns = listSavedCompareRuns();
        savedTilingSets = listSavedTilingSets();
        populateSavedSelect(savedRunSelect, savedRuns, "No saved runs", preferredRunId);
        populateSavedSelect(
            savedTilingSetSelect,
            savedTilingSets,
            "No saved tiling sets",
            preferredTilingSetId,
        );
        const hasRuns = savedRuns.length > 0;
        const hasTilingSets = savedTilingSets.length > 0;
        loadRunButton.disabled = !hasRuns;
        deleteRunButton.disabled = !hasRuns;
        loadTilingSetButton.disabled = !hasTilingSets;
        deleteTilingSetButton.disabled = !hasTilingSets;
        savedRunHint.textContent = hasRuns
            ? `${savedRuns.length} saved run${savedRuns.length === 1 ? "" : "s"} available.`
            : "No saved runs yet. Name the current setup and choose Save run.";
        savedTilingSetHint.textContent = hasTilingSets
            ? `${savedTilingSets.length} saved tiling set${savedTilingSets.length === 1 ? "" : "s"} available.`
            : "No saved tiling sets yet. Select tilings, name the set, and choose Save set.";
    }

    function populateSavedSelect(
        select: HTMLSelectElement,
        items: readonly { id: string; name: string }[],
        emptyLabel: string,
        preferredId: string,
    ): void {
        select.replaceChildren();
        if (items.length === 0) {
            select.append(el("option", { value: "", textContent: emptyLabel }));
            select.disabled = true;
            return;
        }
        select.disabled = false;
        for (const item of items) {
            select.append(el("option", { value: item.id, textContent: item.name }));
        }
        if (preferredId && [...select.options].some((option) => option.value === preferredId)) {
            select.value = preferredId;
        }
    }

    function saveCurrentRun(): void {
        try {
            const replaceId = editingSavedRunId;
            const saved = saveCompareRun(savedRunNameInput.value, currentRunConfig());
            if (replaceId && replaceId !== saved.id) {
                deleteSavedCompareRun(replaceId);
            }
            editingSavedRunId = saved.id;
            savedRunNameInput.value = saved.name;
            refreshSavedControls(saved.id, savedTilingSetSelect.value);
            statusLine.textContent = `Saved run "${saved.name}".`;
        } catch (error) {
            statusLine.textContent = `Could not save run: ${error instanceof Error ? error.message : String(error)}`;
        }
    }

    async function loadSelectedRun(): Promise<void> {
        const saved = savedRuns.find((run) => run.id === savedRunSelect.value);
        if (!saved) {
            return;
        }
        await applyRunConfig(saved.config);
        editingSavedRunId = saved.id;
        savedRunNameInput.value = saved.name;
        refreshSavedControls(saved.id, savedTilingSetSelect.value);
    }

    function deleteSelectedRun(): void {
        const saved = savedRuns.find((run) => run.id === savedRunSelect.value);
        if (!saved) {
            return;
        }
        deleteSavedCompareRun(saved.id);
        if (editingSavedRunId === saved.id) {
            editingSavedRunId = "";
        }
        refreshSavedControls("", savedTilingSetSelect.value);
        statusLine.textContent = `Deleted run "${saved.name}".`;
    }

    function saveCurrentTilingSet(): void {
        try {
            const replaceId = editingSavedTilingSetId;
            const saved = saveTilingSet(savedTilingSetNameInput.value, [...selected]);
            if (replaceId && replaceId !== saved.id) {
                deleteSavedTilingSet(replaceId);
            }
            editingSavedTilingSetId = saved.id;
            savedTilingSetNameInput.value = saved.name;
            refreshSavedControls(savedRunSelect.value, saved.id);
            statusLine.textContent = `Saved tiling set "${saved.name}".`;
        } catch (error) {
            statusLine.textContent = `Could not save tiling set: ${error instanceof Error ? error.message : String(error)}`;
        }
    }

    function loadSelectedTilingSet(): void {
        const saved = savedTilingSets.find((set) => set.id === savedTilingSetSelect.value);
        if (!saved) {
            return;
        }
        const knownGeometries = new Set(allTilings.map((tiling) => tiling.geometry));
        replaceSelection(
            new Set(saved.geometries.filter((geometry) => knownGeometries.has(geometry))),
        );
        pruneSelectionForSelectedRule({ selectAllIfEmpty: true });
        renderTilingChecklist();
        refreshPreview();
        editingSavedTilingSetId = saved.id;
        savedTilingSetNameInput.value = saved.name;
        refreshSavedControls(savedRunSelect.value, saved.id);
        statusLine.textContent = `Loaded tiling set "${saved.name}".`;
    }

    function deleteSelectedTilingSet(): void {
        const saved = savedTilingSets.find((set) => set.id === savedTilingSetSelect.value);
        if (!saved) {
            return;
        }
        deleteSavedTilingSet(saved.id);
        if (editingSavedTilingSetId === saved.id) {
            editingSavedTilingSetId = "";
        }
        refreshSavedControls(savedRunSelect.value);
        statusLine.textContent = `Deleted tiling set "${saved.name}".`;
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
        const preferredRuleName = preferredInitialRuleName();
        const conway = rules.find((rule) => rule.name === "conway");
        if (preferredRuleName && selectHasValue(ruleSelect, preferredRuleName)) {
            ruleSelect.value = preferredRuleName;
        } else if (conway) {
            ruleSelect.value = "conway";
        }
        ruleSelect.addEventListener("change", () => {
            pruneSelectionForSelectedRule({ selectAllIfEmpty: true });
            renderTilingChecklist();
            refreshPreview();
        });
        pruneSelectionForSelectedRule({ selectAllIfEmpty: true });
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
        showStageHero();
        activeFilmstrip = null;
        liveStateLine.textContent =
            "Run link loaded. Choose Play side by side when you are ready to build the live filmstrip.";
        statusLine.textContent = `Loaded run link — ${selected.size} tilings ready.`;
    }

    async function runFeaturedDemo(config: CompareRunConfig): Promise<void> {
        await ensureRules();
        await applyRunConfig(defaultFilmstripConfig(config));
        // Reduced motion: rest on a lively frame instead of animating. Otherwise
        // autoplay and loop only the lively sub-window at a calmer speed.
        const playback: FilmstripLoadOptions = prefersReducedMotion()
            ? { initialFrame: FEATURED_COMPARE_DEMO_STILL_FRAME }
            : {
                  autoplay: true,
                  initialFrame: FEATURED_COMPARE_DEMO_LOOP_START,
                  loopStart: FEATURED_COMPARE_DEMO_LOOP_START,
                  speedMultiplier: FEATURED_COMPARE_DEMO_SPEED,
              };
        await runFilmstrip(playback);
    }

    async function runDefaultFilmstrip(config: CompareRunConfig): Promise<void> {
        await ensureRules();
        await applyRunConfig(defaultFilmstripConfig(config));
        await runFilmstrip({ initialFrame: FEATURED_COMPARE_DEMO_STILL_FRAME });
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

    async function runFilmstrip(playback?: FilmstripLoadOptions): Promise<void> {
        if (running) {
            return;
        }
        // A fresh run rebuilds every board, so any live fork is torn down first.
        disposeFocusPane();
        if (selected.size < 2) {
            statusLine.textContent = "Select at least two tilings to play side by side.";
            liveStateLine.textContent =
                "The live filmstrip needs two or more selected tilings for comparison.";
            showStageHero();
            return;
        }
        setRunning(true);
        statusLine.textContent = `Building filmstrip for ${selected.size} tilings…`;
        liveStateLine.textContent = "Building live side-by-side filmstrip…";

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
            activeFilmstrip = filmstrip;
            if (!filmstripView) {
                filmstripView = createFilmstripView({
                    backend: options.backend,
                    transport: filmstripTransport,
                    getLiveColor: () => liveColorForRule(selectedRuleName()),
                    loop: true,
                    onOpenFrame: openFilmstripFrame,
                    onFocusChange: handleFocusChanged,
                });
                filmstripArea.append(filmstripView.element);
            }
            showStageBoards();
            await filmstripView.load(filmstrip, playback);
            // Honour a deep-linked focus (e.g. #/compare&focus=square) now that boards exist.
            applyFocusFromHash();
            // Land the user on the live boards rather than the configuration above
            // them -- especially for the one-click featured demo.
            if (typeof filmstripArea.scrollIntoView === "function") {
                filmstripArea.scrollIntoView({
                    block: "start",
                    behavior: prefersReducedMotion() ? "auto" : "smooth",
                });
            }
            liveStateLine.textContent = `Live filmstrip ready with ${filmstrip.tilings.length} tilings and ${filmstrip.frame_count} generations.`;
            statusLine.textContent = `Filmstrip ready — ${filmstrip.tilings.length} tilings × ${filmstrip.frame_count} generations. Press play.`;
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            liveStateLine.textContent = `Live filmstrip failed: ${message}`;
            statusLine.textContent = `Error: ${message}`;
            showStageHero();
        } finally {
            setRunning(false);
        }
    }

    function openFilmstripFrame(tiling: TopologyFilmstrip, frameIndex: number): void {
        if (!activeFilmstrip) {
            return;
        }
        const pattern = buildFilmstripFramePattern(activeFilmstrip, tiling, frameIndex);
        if (!pattern) {
            statusLine.textContent = "This generation cannot be opened in build mode.";
            return;
        }
        openPattern(pattern);
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

    // Back/forward (or an external hash edit) re-applies the focused board.
    function onHashChangeFocus(): void {
        applyFocusFromHash();
    }

    runButton.addEventListener("click", () => void runComparison());
    playButton.addEventListener("click", () => void runFilmstrip());
    railRerunButton.addEventListener("click", () => void runFilmstrip());
    railForkButton.addEventListener("click", () => void forkFocusedBoardLive());
    copyRunButton.addEventListener("click", copyRunLink);
    document.addEventListener("pointerdown", onDocumentPointerDown);
    window.addEventListener("hashchange", onHashChangeFocus);

    return {
        element: root,
        activate(): void {
            void ensureRules();
            refreshPreview();
            highlightGeometry(null);
        },
        deactivate(): void {
            filmstripTransport.pause();
            disposeFocusPane();
            root.querySelector(".compare-action-menu[open]")?.removeAttribute("open");
        },
        applyRunConfig,
        runFeaturedDemo,
        runDefaultFilmstrip,
        reportRunLinkError(message: string): void {
            statusLine.textContent = message;
        },
        handleEscape(): boolean {
            const openMenu = root.querySelector(".compare-action-menu[open]");
            if (openMenu) {
                openMenu.removeAttribute("open");
                return true;
            }
            return false;
        },
        exitFocusIfAny(): boolean {
            if (currentFocusGeometry !== null && filmstripView) {
                filmstripView.focus(null);
                return true;
            }
            return false;
        },
        handlePlaybackKey(event: KeyboardEvent): boolean {
            // Only claim playback keys once a live filmstrip exists, so typing in
            // the config fields (and plain Space) behaves normally until then.
            if (!activeFilmstrip) {
                return false;
            }
            const target = event.target;
            if (
                target instanceof HTMLElement &&
                (target.isContentEditable || /^(input|select|textarea)$/i.test(target.tagName))
            ) {
                return false;
            }
            if (event.key === " " || event.key === "Spacebar") {
                filmstripTransport.toggle();
                return true;
            }
            if (event.key === "ArrowLeft") {
                filmstripTransport.step(-1);
                return true;
            }
            if (event.key === "ArrowRight") {
                filmstripTransport.step(1);
                return true;
            }
            return false;
        },
        dispose(): void {
            document.removeEventListener("pointerdown", onDocumentPointerDown);
            window.removeEventListener("hashchange", onHashChangeFocus);
            disposeFocusPane();
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
