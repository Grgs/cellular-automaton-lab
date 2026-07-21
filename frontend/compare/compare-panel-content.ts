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
import { element as el } from "./compare-dom.js";
import {
    buildComparisonStatePattern,
    buildFilmstripFramePattern,
    PATTERN_FORMAT,
    PATTERN_VERSION,
} from "./compare-patterns.js";
import { buildCompareRunUrl, type CompareRunConfig } from "./compare-run-link.js";
import {
    comparisonTilingOptions,
    type CompareTilingOption as TilingOption,
    defaultComparisonSelection,
    wallTilingPickerOptions,
} from "./compare-tiling-options.js";
import { hashWithFocus, hashWithoutFocus, readFocusFromHash } from "./compare-route.js";
import {
    FEATURED_COMPARE_DEMO_LOOP_START,
    FEATURED_COMPARE_DEMO_SPEED,
    FEATURED_COMPARE_DEMO_STILL_FRAME,
    SEED_SHAPE_OPTIONS,
    TRAVERSAL_OPTIONS,
} from "./compare-options.js";
import {
    buildClassificationGrid,
    buildPhasePortraitSvg,
    buildPortraitLegend,
    familyColor,
} from "./compare-charts.js";
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
// `?inline` keeps the stylesheet inside this chunk (not an emitted .css asset)
// while letting Vite's CSS minifier strip the comments and whitespace.
import COMPARE_PANEL_STYLES from "./compare-panel.css?inline";
import { ruleSupportsTilingFamily } from "../rule-compatibility.js";
import {
    MIN_WALL_TILINGS,
    WALL_HARD_TILING_LIMIT,
    wallCapacityMessage,
    wallTilingCapacity,
} from "./compare-capacity.js";
import {
    MAX_ANALYSIS_STEPS,
    MAX_COMPARE_GRID_SIZE,
    MAX_COMPARE_SEED_LENGTH,
    MAX_WALL_GENERATIONS,
    MIN_COMPARE_GRID_SIZE,
    MIN_COMPARE_STEPS,
} from "./compare-limits.js";
import { createCompareWorkspaceStore, inspectedBoard } from "./compare-workspace-store.js";
import { subscribeSelector } from "./compare-workspace-subscriptions.js";
import { createLatestConfigScheduler } from "./latest-config-scheduler.js";
import { createCompareWorkspaceLayout } from "./compare-workspace-layout.js";

// Matches _MAX_PREVIEW_CELLS in backend/simulation/topology_preview.py; larger
// patches are not offered a thumbnail (the backend would reject them anyway).
const MAX_PREVIEW_CELLS = 10000;

const DEFAULT_SEED = "01100 11000 01000";
const STYLE_ELEMENT_ID = "compare-panel-styles";
const WAIT_FOR_WALL_UPDATE = "Wait for the wall update to finish";
const FAILED_UPDATE_MANAGEMENT_REASON = "Retry the failed update before editing this wall";

interface RunFilmstripOptions {
    /** Suppress the full-wall loading veil for debounced edits that can refresh in place. */
    quietUpdate?: boolean;
}

interface ScheduledFilmstripRun {
    kind: "filmstrip";
    config: CompareRunConfig;
    playback?: FilmstripLoadOptions;
    runOptions: RunFilmstripOptions;
}

interface ScheduledAnalysisRun {
    kind: "analysis";
    request: CompareRequest;
    key: string;
}

type ScheduledCompareRun = ScheduledFilmstripRun | ScheduledAnalysisRun;

interface OperationTicket {
    id: number;
    revision: number;
    kind: "analysis" | "filmstrip";
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

function isInteractiveShortcutTarget(target: EventTarget | null): boolean {
    if (!(target instanceof HTMLElement)) {
        return false;
    }
    if (target.isContentEditable) {
        return true;
    }
    return Boolean(
        target.closest(
            "button, a[href], input, select, textarea, summary, " +
                '[tabindex]:not([tabindex="-1"])',
        ),
    );
}

export interface ComparePanelContentOptions {
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    /** When provided, begin/end open into the current board instead of a new tab. */
    onOpenPattern?: (pattern: PatternPayload) => void | Promise<void>;
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
    /** Close the configuration sheet if it is open; returns true when it did. */
    closeConfigIfOpen(): boolean;
    /** Return from speaker view to the gallery if a board is focused; true when it did. */
    exitFocusIfAny(): boolean;
    /** Handle a playback shortcut (space/arrows) once a filmstrip is live; true if consumed. */
    handlePlaybackKey(event: KeyboardEvent): boolean;
    dispose(): void;
}

type TilingPreset = "representative" | "regular" | "mixed" | "aperiodic" | "all" | "none";
type ConfigTab = "setup" | "tilings" | "help" | "saved";

interface ActionMenuItem {
    label: string;
    title: string;
    onClick(): void;
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
    const allTilings = comparisonTilingOptions(options.bootstrapData);
    const currentWallCapacity = (): number => wallTilingCapacity();
    const selected = new Set(
        [...defaultComparisonSelection(allTilings)].slice(0, currentWallCapacity()),
    );

    let rules: RuleDefinition[] = [];
    let rulesLoaded = false;
    let disposed = false;
    let operationSequence = 0;
    let lifecycleRevision = 0;
    let activeOperation: OperationTicket | null = null;
    let tilingSearchQuery = "";
    let activeConfigTab: ConfigTab = "setup";
    const previewCache = new Map<string, Promise<TopologyPreview>>();
    const analysisCache = new Map<string, SeedComparisonResult>();
    const presetButtons = new Map<TilingPreset, HTMLButtonElement>();
    let editingSavedRunId = "";
    let editingSavedTilingSetId = "";
    // True while the stage-wide analysis overlay is open; gates the analysis
    // scheduling that used to be tied to the (now removed) analysis config tab.
    let analysisOverlayOpen = false;

    // Rule and seed live in the always-visible quick strip (one authoritative
    // control each), so they carry the strip styling and the accessible names
    // the strip advertises rather than being duplicated in the Setup tab.
    const ruleSelect = el("select", {
        class: "compare-field compare-setup-value compare-setup-select",
        "aria-label": "Comparison rule",
        title: "Choose the comparison rule",
    });
    const seedInput = el("input", {
        class: "compare-field",
        type: "text",
        value: DEFAULT_SEED,
        maxlength: String(MAX_COMPARE_SEED_LENGTH),
        spellcheck: "false",
    });
    const traversalSelect = el(
        "select",
        { class: "compare-field" },
        TRAVERSAL_OPTIONS.map((option) =>
            el("option", { value: option.value, textContent: option.label }),
        ),
    );
    const wallGenerationsInput = el("input", {
        class: "compare-field",
        type: "number",
        value: "50",
        min: String(MIN_COMPARE_STEPS),
        max: String(MAX_WALL_GENERATIONS),
    });
    const analysisStepsInput = el("input", {
        class: "compare-field",
        type: "number",
        value: "50",
        min: String(MIN_COMPARE_STEPS),
        max: String(MAX_ANALYSIS_STEPS),
    });
    const gridInput = el("input", {
        class: "compare-field",
        type: "number",
        value: "16",
        min: String(MIN_COMPARE_GRID_SIZE),
        max: String(MAX_COMPARE_GRID_SIZE),
    });
    const shapeSelect = el(
        "select",
        {
            class: "compare-field compare-setup-value compare-setup-select",
            "aria-label": "Comparison seed",
            title: "Choose the shared seed",
        },
        SEED_SHAPE_OPTIONS.map((option) =>
            el("option", { value: option.value, textContent: option.label }),
        ),
    );

    const tilingList = el("div", { class: "compare-tilings" });
    const selectedTilingsList = el("div", {
        class: "compare-selected-tilings",
        "aria-label": "Selected tilings",
    });
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
        getGridSize: () =>
            clampNumber(gridInput.value, MIN_COMPARE_GRID_SIZE, MAX_COMPARE_GRID_SIZE, 16),
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
            updateSummary();
            scheduleWallRerun();
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
        updateSummary();
        scheduleWallRerun();
    });
    traversalSelect.addEventListener("change", () => {
        refreshPreview();
        updateSummary();
        scheduleWallRerun();
    });
    wallGenerationsInput.addEventListener("input", () => {
        updateSummary();
        scheduleWallRerun();
    });
    wallGenerationsInput.addEventListener("change", () => {
        updateSummary();
        scheduleWallRerun();
    });
    analysisStepsInput.addEventListener("input", () => {
        updateSummary();
        if (analysisOverlayOpen) {
            scheduleAnalysis();
        }
    });
    analysisStepsInput.addEventListener("change", () => {
        updateSummary();
        if (analysisOverlayOpen) {
            scheduleAnalysis();
        }
    });
    gridInput.addEventListener("input", () => {
        updateSummary();
        scheduleWallRerun();
    });
    gridInput.addEventListener("change", () => {
        refreshPreview();
        updateSummary();
        scheduleWallRerun();
    });

    // "Run comparison" builds (or rebuilds) the live wall from the setup strip
    // and idle dock transport. The analytical table is a deeper workflow and
    // is named separately as "Run analysis".
    const runButton = el("button", { class: "compare-run compare-run-secondary", type: "button" }, [
        "Run analysis",
    ]);
    // Copy-link and configure collapse into compact dock icons rather than
    // labelled buttons competing with the transport.
    const copyRunButton = el(
        "button",
        {
            class: "compare-dock-icon",
            type: "button",
            title: "Copy a link that restores this compare run setup",
            "aria-label": "Copy run link",
        },
        [dockGlyph("⧉"), dockLabel("Copy link")],
    );
    const configButton = el(
        "button",
        {
            class: "compare-dock-icon",
            type: "button",
            title: "Configure the run",
            "aria-label": "Configure the run",
        },
        [dockGlyph("⚙"), dockLabel("Setup")],
    );
    const inspectorButton = el(
        "button",
        {
            class: "compare-dock-icon",
            type: "button",
            title: "Inspect the selected board",
            "aria-label": "Inspect selected board",
        },
        [dockGlyph("ⓘ"), dockLabel("Inspector")],
    );
    // Analysis is its own stage-wide surface (a dimmed overlay), not a cramped
    // inspector tail, so it gets a dock button beside the other surfaces.
    const analysisButton = el(
        "button",
        {
            class: "compare-dock-icon compare-analysis-open",
            type: "button",
            title: "Run a statistical analysis across the selected tilings",
            "aria-label": "Analyze the tilings",
        },
        [dockGlyph("📊"), dockLabel("Analysis")],
    );
    // One click from the wall to the searchable tiling checklist: opens the
    // config sheet with the Tilings disclosure expanded and search focused.
    const tilingsButton = el(
        "button",
        {
            class: "compare-dock-icon compare-tilings-open",
            type: "button",
            title: "Choose the tilings on the wall",
            "aria-label": "Choose tilings",
        },
        [dockGlyph("⊞"), dockLabel("Tilings")],
    );
    const configSheetCloseButton = el(
        "button",
        {
            class: "compare-close compare-config-sheet-close",
            type: "button",
            title: "Close configuration",
            "aria-label": "Close configuration",
        },
        ["✕"],
    );
    const inspectorCloseButton = el(
        "button",
        {
            class: "compare-close compare-inspector-close",
            type: "button",
            "aria-label": "Close inspector",
        },
        ["✕"],
    );
    // Edit mode: board clicks paint the shared seed (at gen 0) instead of
    // zooming; the ⤢ glyph stays the one zoom affordance while it is on.
    const editModeButton = el(
        "button",
        {
            class: "compare-dock-icon compare-edit-toggle",
            type: "button",
            title: "Edit the seed by painting boards",
            "aria-label": "Toggle edit mode",
            "aria-pressed": "false",
            disabled: true,
        },
        [dockGlyph("✎"), dockLabel("Edit seed")],
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
    const statusLine = el("div", {
        class: "compare-status",
        role: "status",
        "aria-live": "polite",
    });
    const setupTilingsValue = el("strong", {
        class: "compare-setup-value",
        textContent: "Loading",
        title: "Loading",
    });
    const setupRunButton = el(
        "button",
        {
            class: "compare-run compare-setup-run",
            type: "button",
            title: "Run every selected tiling on a shared clock",
        },
        ["Run comparison"],
    );
    const setupTilingsItem = el(
        "button",
        {
            class: "compare-setup-item compare-setup-action",
            type: "button",
            title: "Choose the tilings on the wall",
            "aria-label": "Choose tilings on the wall",
        },
        [
            el("span", { class: "compare-setup-label", textContent: "Tilings" }),
            el("span", { class: "compare-setup-action-row" }, [
                setupTilingsValue,
                el("span", { class: "compare-setup-action-text", textContent: "Edit" }),
            ]),
        ],
    );
    const setupStrip = el(
        "section",
        { class: "compare-setup-strip", "aria-label": "Comparison setup" },
        [
            setupItem("Seed", shapeSelect),
            setupItem("Rule", ruleSelect),
            setupTilingsItem,
            setupRunButton,
        ],
    );
    const stageHero = el("div", { class: "compare-stage-hero" }, [
        el("div", { class: "compare-stage-hero-glyph", "aria-hidden": "true", textContent: "▦" }),
        el("div", {
            class: "compare-stage-hero-title",
            textContent: "Watch one seed evolve across every tiling",
        }),
        el("p", {
            class: "compare-stage-hero-blurb",
            textContent: "Pick a rule and tilings, then run every board on one shared clock.",
        }),
    ]);
    const wallLoadingOverlay = el(
        "div",
        {
            class: "compare-wall-loading",
            role: "status",
            "aria-live": "polite",
            hidden: true,
        },
        [
            el("span", {
                class: "compare-wall-loading-text",
                textContent: "Building comparison...",
            }),
            el("div", { class: "compare-wall-loading-grid", "aria-hidden": "true" }, [
                el("span", { class: "compare-wall-loading-card" }),
                el("span", { class: "compare-wall-loading-card" }),
                el("span", { class: "compare-wall-loading-card" }),
                el("span", { class: "compare-wall-loading-card" }),
            ]),
        ],
    );
    const retryWallUpdateButton = el("button", {
        class: "compare-mini compare-stale-retry",
        type: "button",
        textContent: "Retry update",
    });
    const staleResultNoticeMessage = el("span", { class: "compare-stale-notice-message" });
    const staleResultNotice = el(
        "div",
        {
            class: "compare-stale-notice",
            role: "alert",
            hidden: true,
        },
        [staleResultNoticeMessage, retryWallUpdateButton],
    );
    // Names the run that is playing (seed · rule · N tilings) so the wall isn't
    // an unlabelled animation; hidden on the empty-state hero.
    const stageCaption = el("div", {
        class: "compare-stage-caption",
        hidden: true,
    });
    const filmstripArea = el("div", { class: "compare-filmstrip-area" }, [
        stageCaption,
        stageHero,
        wallLoadingOverlay,
    ]);
    // The dock's play button doubles as "Run comparison" before any run is
    // attached, so the transport owns the primary action rather than a separate
    // button sitting beside it.
    const filmstripTransport = createFilmstripTransport({
        onRun: () => void runFilmstrip(),
        onPlayStateChange: (playing) => {
            workspaceStore.update((state) => ({
                ...state,
                playback: { ...state.playback, playing },
            }));
        },
    });
    const resultsArea = el("div", { class: "compare-results" });
    let filmstripView: FilmstripViewController | null = null;
    const workspaceStore = createCompareWorkspaceStore(currentRunConfig());
    // Store-derived renders driven by selector subscriptions. Handles are torn
    // down in dispose(). Views that also depend on local UI state (the tiling
    // selection Set, config fields) stay imperatively invoked; only the
    // purely store-derived renders live here.
    const storeRenderSubscriptions: Array<() => void> = [];

    function syncWorkspaceConfiguration(config = currentRunConfig()): CompareRunConfig {
        workspaceStore.update((state) => ({
            ...state,
            configuration: config,
            orderedBoards: config.geometries,
        }));
        return config;
    }

    function selectedBoardGeometry(): string | null {
        return inspectedBoard(workspaceStore.getState());
    }

    function selectedBoardElement(): HTMLElement | null {
        const geometry = selectedBoardGeometry();
        const filmstrip = workspaceStore.getState().results.filmstrip;
        if (!geometry || !filmstrip || !filmstripView) {
            return null;
        }
        const index = filmstrip.tilings.findIndex((tiling) => tiling.geometry === geometry);
        return index < 0
            ? null
            : (filmstripView.element.querySelectorAll<HTMLElement>(".compare-filmstrip-board")[
                  index
              ] ?? null);
    }

    const workspaceScheduler = createLatestConfigScheduler<ScheduledCompareRun>({
        delayMs: 400,
        validate: (scheduled) =>
            scheduled.kind === "filmstrip" ? wallConfigProblem() : analysisConfigProblem(),
        execute: (scheduled, signal) =>
            scheduled.kind === "filmstrip"
                ? performFilmstrip(scheduled, signal)
                : performAnalysis(scheduled, signal),
        onInvalid: (message) => {
            statusLine.textContent = message;
            updateSummary();
        },
        onStateChange: ({ status, config, error }) => {
            workspaceStore.update((state) => ({
                ...state,
                operation: {
                    ...state.operation,
                    kind: status === "idle" ? null : (config?.kind ?? null),
                    status,
                    error: error instanceof Error ? error.message : error ? String(error) : null,
                },
            }));
            // The operation slice drives the summary subscription; no manual
            // updateSummary is needed for the button/status refresh.
        },
    });
    // Live forks are per-board (keyed by geometry) and outlive a focus change:
    // a forked board keeps running as a live tile in the gallery, and speaker
    // view of it is just this same pane shown at hero size (see the
    // `:not(.is-hero)` compact styling in compare-panel.css).
    const forkedBoards = new Map<string, FocusPaneHandle>();
    function syncWorkspaceForks(): void {
        workspaceStore.update((state) => ({
            ...state,
            forkedBoards: [...forkedBoards.keys()],
        }));
    }
    // Live in-place forking needs an independent server session; standalone
    // (no baseSessionId) forks into the Lab instead. A host may also cap
    // concurrent forks (undefined means unlimited) -- see the check in
    // forkFocusedBoardLive below.
    const focusLiveEnabled = Boolean(options.focusPaneServices?.baseSessionId);

    // The focused board is mirrored into the hash (`&focus=<geometry>`) so speaker
    // view is shareable and the browser back button returns to the gallery.
    function mirrorFocusToHash(geometry: string | null): void {
        workspaceStore.update((state) => ({ ...state, focusedBoard: geometry }));
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
        const filmstrip = workspaceStore.getState().results.filmstrip;
        if (!filmstripView || !filmstrip) {
            return;
        }
        const requested = readFocusFromHash(window.location.hash);
        if (
            requested !== null &&
            !filmstrip.tilings.some((tiling) => tiling.geometry === requested)
        ) {
            // A stale or mistyped deep link. The view treats it as "no focus",
            // but when the wall is already unfocused it never notifies, so the
            // dead slot would sit in the URL claiming a focus that isn't there.
            // Scrub it here so the hash keeps matching what is on screen.
            mirrorFocusToHash(null);
            filmstripView.focus(null);
            return;
        }
        filmstripView.focus(requested);
    }

    // ------ Edit mode: paint the shared seed by clicking board cells (gen 0) ------
    //
    // A frame-0 cell pulls back to a bit through the board's `seed_order`
    // (bit i of the seed lands on seed_order[i]), so a paint toggles that bit,
    // re-projects generation 0 onto every board immediately (exact, not an
    // approximation), and debounces the authoritative re-run that recomputes
    // the evolution frames. Mid-timeline edits have no seed representation --
    // they will fork the board live in a later phase; for now they hint.
    let editMode = false;

    function normalizedSeedBits(): string {
        return seedInput.value.replace(/[^01]/g, "");
    }

    /** Pull a board's frame 0 back to the shortest seed that reproduces it. */
    function reconstructSeedBits(order: string[], frame0: Record<string, number>): string {
        const indexOf = new Map(order.map((cellId, index) => [cellId, index]));
        let maxIndex = -1;
        for (const cellId of Object.keys(frame0)) {
            const index = indexOf.get(cellId);
            if (index !== undefined && index > maxIndex) {
                maxIndex = index;
            }
        }
        if (maxIndex < 0) {
            return "0";
        }
        let bits = "";
        for (let index = 0; index <= maxIndex; index += 1) {
            bits += frame0[order[index]!] ? "1" : "0";
        }
        return bits;
    }

    /** Re-project the seed onto every board's generation 0 and re-render them. */
    function projectSeedOntoFrameZero(bits: string): void {
        const filmstrip = workspaceStore.getState().results.filmstrip;
        if (!filmstrip || !filmstripView) {
            return;
        }
        const changedTilings: TopologyFilmstrip[] = [];
        const tilings = filmstrip.tilings.map((tiling) => {
            const order = tiling.seed_order;
            if (!order || order.length === 0 || tiling.frames.length === 0) {
                return tiling;
            }
            const frame: Record<string, number> = {};
            for (let index = 0; index < bits.length && index < order.length; index += 1) {
                if (bits[index] === "1") {
                    frame[order[index]!] = 1;
                }
            }
            const frames = [...tiling.frames];
            frames[0] = frame;
            const changed = { ...tiling, frames };
            changedTilings.push(changed);
            return changed;
        });
        const nextFilmstrip = { ...filmstrip, tilings };
        const installed = workspaceStore.update((state) =>
            state.results.filmstrip === filmstrip
                ? {
                      ...state,
                      results: { ...state.results, filmstrip: nextFilmstrip },
                  }
                : state,
        );
        if (installed.results.filmstrip !== nextFilmstrip) {
            return;
        }
        for (const tiling of changedTilings) {
            filmstripView.updateBoardData(tiling);
        }
    }

    function scheduledFilmstripRun(
        playback?: FilmstripLoadOptions,
        runOptions: RunFilmstripOptions = {},
    ): ScheduledFilmstripRun {
        return {
            kind: "filmstrip",
            config: syncWorkspaceConfiguration(),
            runOptions,
            ...(playback === undefined ? {} : { playback }),
        };
    }

    // A single 400ms latest-config-wins queue covers painting and every setup
    // mutation. HTTP work is aborted; Pyodide may finish but cannot install a
    // stale result because the scheduler's signal is checked before rendering.
    function scheduleWallRerun(): void {
        workspaceScheduler.schedule(scheduledFilmstripRun(undefined, { quietUpdate: true }));
    }

    function setEditMode(next: boolean): void {
        if (editMode === next) {
            return;
        }
        editMode = next;
        editModeButton.setAttribute("aria-pressed", next ? "true" : "false");
        editModeButton.classList.toggle("is-active", next);
        const rewoundToSeed =
            next && filmstripView !== null && filmstripView.currentFrameIndex() !== 0;
        if (rewoundToSeed) {
            filmstripTransport.reset();
        }
        filmstripView?.setEditMode(next);
        if (next) {
            statusLine.textContent = rewoundToSeed
                ? "Edit mode — returned to generation 0 so paints update the shared seed."
                : "Edit mode — click cells to edit the shared seed.";
        } else {
            statusLine.textContent = "";
        }
    }

    function handlePaintCell(geometry: string, cellId: string): void {
        const filmstrip = workspaceStore.getState().results.filmstrip;
        if (!filmstrip || !filmstripView) {
            return;
        }
        const tiling = filmstrip.tilings.find((entry) => entry.geometry === geometry);
        if (!tiling) {
            statusLine.textContent = "This board cannot edit the seed.";
            return;
        }
        const frameIndex = filmstripView.currentFrameIndex();
        if (frameIndex !== 0) {
            filmstripTransport.reset();
        }
        const order = tiling.seed_order;
        if (!order || order.length === 0) {
            statusLine.textContent = "This board cannot edit the seed.";
            return;
        }
        const bitIndex = order.indexOf(cellId);
        if (bitIndex < 0) {
            return;
        }

        // A named-shape seed has no bit-string; convert it on first paint by
        // pulling this board's generation 0 back through its traversal. The
        // conversion is geometry-specific, so the other boards re-project from
        // the bits (a visible one-time reflow -- see the Gate 0 findings).
        let converted = false;
        if (isShapeMode()) {
            seedInput.value = reconstructSeedBits(order, tiling.frames[0] ?? {});
            shapeSelect.value = "";
            syncShapeMode();
            // Programmatic select writes fire no "change" event, so refetch the
            // placement previews here: the cached shape-mode responses carry
            // shape_cells but no traversal order, and redrawing bits against
            // them renders every thumbnail empty.
            refreshPreview();
            converted = true;
        }

        const bits = normalizedSeedBits().padEnd(bitIndex + 1, "0");
        const toggled =
            bits.slice(0, bitIndex) +
            (bits[bitIndex] === "1" ? "0" : "1") +
            bits.slice(bitIndex + 1);
        seedInput.value = toggled;
        seedPad.syncFromSeed();
        redrawPreview();
        updateSummary();

        projectSeedOntoFrameZero(toggled);
        statusLine.textContent = converted
            ? "Shape converted to an editable seed — every board now runs from it."
            : "Seed updated — re-running the wall…";
        scheduleWallRerun();
    }

    // Selection editing from the wall itself: a board's × chrome drops that
    // tiling from the run (the filmstrip view disables it at the two-board
    // minimum), with removals coalescing into one debounced re-run.
    function removeBoardFromWall(geometry: string): void {
        if (!selected.has(geometry)) {
            return;
        }
        // Removals coalesce into one debounced rebuild, so the displayed strip
        // still shows the pre-removal boards while more clicks arrive. The
        // filmstrip's own remove-button disable is keyed off that stale strip,
        // so guard the two-board minimum here against the pending selection --
        // otherwise a burst of clicks drops below it and the coalesced rerun
        // collapses the wall to the empty hero.
        if (selected.size <= MIN_WALL_TILINGS) {
            statusLine.textContent = "Keep at least two tilings on the wall.";
            filmstripView?.setBoardsRemovable(false);
            return;
        }
        selected.delete(geometry);
        // Reflect the new floor on the still-displayed boards immediately, so a
        // fast follow-up click sees a disabled control instead of overshooting.
        filmstripView?.setBoardsRemovable(selected.size > MIN_WALL_TILINGS);
        const tiling = workspaceStore
            .getState()
            .results.filmstrip?.tilings.find((entry) => entry.geometry === geometry);
        statusLine.textContent = `Removed ${tiling?.label || geometry} — updating the wall…`;
        renderTilingChecklist();
        refreshPreview();
        scheduleWallRerun();
    }

    function replaceBoardOnWall(previousGeometry: string, nextGeometry: string): void {
        if (previousGeometry === nextGeometry || !selected.has(previousGeometry)) {
            return;
        }
        const next = allTilings.find((tiling) => tiling.geometry === nextGeometry);
        if (!next || selected.has(nextGeometry) || !tilingCompatibleWithSelectedRule(next)) {
            return;
        }
        // A Set carries the wall's display order. Deleting and re-adding here
        // would append the replacement, even though the user edited a specific
        // tile. Rebuild the Set with the new geometry in that tile's slot.
        const orderedSelection = [...selected];
        const replacedIndex = orderedSelection.indexOf(previousGeometry);
        selected.clear();
        orderedSelection.forEach((geometry, index) => {
            selected.add(index === replacedIndex ? nextGeometry : geometry);
        });
        statusLine.textContent = `Replaced a board with ${next.label} — updating the wall…`;
        renderTilingChecklist();
        refreshPreview();
        void runFilmstrip();
    }

    function addBoardToWall(geometry: string): void {
        if (selected.has(geometry)) {
            return;
        }
        const tiling = allTilings.find((option) => option.geometry === geometry);
        if (!tiling || !tilingCompatibleWithSelectedRule(tiling)) {
            return;
        }
        if (selected.size >= currentWallCapacity()) {
            statusLine.textContent = wallCapacityMessage(currentWallCapacity());
            filmstripView?.refreshAddControl();
            return;
        }
        selected.add(geometry);
        statusLine.textContent = `Added ${tiling.label} — updating the wall…`;
        renderTilingChecklist();
        refreshPreview();
        void runFilmstrip();
    }

    editModeButton.addEventListener("click", () => setEditMode(!editMode));

    /**
     * Rejoin the shared clock: pull a fork's current live cells back to a
     * bit-string through the board's traversal (same pull-back as a gen-0
     * paint), make that the shared seed, and re-run the wall — every board
     * restarts from this state as its generation 0, and the re-run disposes
     * the fork it came from. Multi-state cells collapse to alive (the shared
     * seed is binary); generation numbering restarts by design.
     */
    function adoptForkStateAsSeed(geometry: string, cellsById: Record<string, number>): void {
        const filmstrip = workspaceStore.getState().results.filmstrip;
        if (!filmstrip) {
            return;
        }
        const order = filmstrip.tilings.find((entry) => entry.geometry === geometry)?.seed_order;
        if (!order || order.length === 0) {
            statusLine.textContent = "This board cannot rebuild the shared seed.";
            return;
        }
        if (isShapeMode()) {
            shapeSelect.value = "";
            syncShapeMode();
            // Same as the gen-0 paint conversion: a programmatic source switch
            // must refetch previews or they render the bits against stale
            // shape-mode responses that have no traversal order.
            refreshPreview();
        }
        seedInput.value = reconstructSeedBits(order, cellsById);
        seedPad.syncFromSeed();
        redrawPreview();
        updateSummary();
        statusLine.textContent = "Re-running every board from the forked state…";
        void runFilmstrip();
    }

    function handleFocusChanged(geometry: string | null): void {
        // Forks are per-board and outlive a focus change: leaving a forked
        // board keeps it running as a live tile in the gallery instead of
        // tearing it down.
        mirrorFocusToHash(geometry);
        if (geometry !== null) {
            workspaceStore.update((state) => ({ ...state, selectedBoard: geometry }));
            // On a wide layout the inspector is a side column, so focusing a
            // board opens it beside the hero (its stats and the toolbelt). On a
            // narrow layout the inspector is a full overlay with a backdrop that
            // would bury the very board just focused, so leave it to the ⓘ
            // button there.
            if (window.innerWidth >= 960) {
                workspaceLayout.openInspector();
            }
        }
        // Seed editing is edit mode's job in either layout (paint gen 0 for
        // the shared seed, any later gen to fork the board live), so speaker
        // view only changes the stage layout -- the seed pad stays in the
        // config sheet for bit-level control.
        stageMain.classList.toggle("is-speaker", geometry !== null);
        // Focus/selection changes publish to the store, which refreshes the
        // summary through its subscription.
    }

    function disposeForkedBoard(geometry: string): void {
        const pane = forkedBoards.get(geometry);
        if (!pane) {
            return;
        }
        forkedBoards.delete(geometry);
        syncWorkspaceForks();
        pane.dispose();
        filmstripView?.setBoardOverlay(geometry, null);
    }

    /**
     * A live fork runs on its own clock, so wall playback visibly skips that
     * board. The first time the shared clock moves while a fork is active,
     * say so — otherwise the forked board just looks stuck.
     */
    let forkClockNoteShown = false;
    function noteDetachedForksOnClockMove(): void {
        if (forkedBoards.size === 0) {
            forkClockNoteShown = false;
            return;
        }
        if (forkClockNoteShown) {
            return;
        }
        forkClockNoteShown = true;
        const names = [...forkedBoards.keys()]
            .map(
                (geometry) =>
                    allTilings.find((tiling) => tiling.geometry === geometry)?.label ?? geometry,
            )
            .join(", ");
        statusLine.textContent =
            `${names} is live-forked and runs on its own clock, so wall playback skips it — ` +
            "use the Run on its chip, or ▶ Run wall from here / Discard to rejoin.";
    }

    function disposeAllForkedBoards(): void {
        for (const geometry of [...forkedBoards.keys()]) {
            disposeForkedBoard(geometry);
        }
    }

    function reportFocusPaneError(error: unknown): void {
        statusLine.textContent = `Fork failed: ${error instanceof Error ? error.message : String(error)}`;
    }

    function disposeDetachedBackend(backend: SimulationBackend): void {
        void Promise.resolve(backend.dispose()).catch(reportFocusPaneError);
    }

    /**
     * Fork a board live at a given frame, or -- if it's already forked --
     * apply `initialPaint` straight to that live pane instead of a second
     * fork attempt (the pane's own chip, Discard, is the way to undo a fork).
     * `initialPaint` carries over the paint stroke that triggered an
     * auto-fork from a mid-timeline edit; the explicit hero fork button calls
     * this with no paint.
     */
    async function forkBoardLive(
        geometry: string,
        frameIndex: number,
        initialPaint?: { cellId: string; state: number },
    ): Promise<void> {
        const filmstrip = workspaceStore.getState().results.filmstrip;
        if (!filmstripView || !filmstrip) {
            return;
        }
        const existing = forkedBoards.get(geometry);
        if (existing) {
            if (initialPaint) {
                await existing.applyCellEdit(initialPaint.cellId, initialPaint.state);
            }
            return;
        }
        const tiling = filmstrip.tilings.find((candidate) => candidate.geometry === geometry);
        if (!tiling) {
            return;
        }
        const pattern = buildFilmstripFramePattern(filmstrip, tiling, frameIndex);
        if (!pattern) {
            statusLine.textContent = "This generation cannot be forked.";
            return;
        }
        const services = options.focusPaneServices;
        // Standalone (no server session): fork into the Lab instead of in
        // place, folding the paint into the pattern so it isn't dropped.
        if (!services?.baseSessionId) {
            openPattern(
                initialPaint
                    ? {
                          ...pattern,
                          cells_by_id: {
                              ...pattern.cells_by_id,
                              [initialPaint.cellId]: initialPaint.state,
                          },
                      }
                    : pattern,
            );
            return;
        }
        if (services.forkCapacity !== undefined && forkedBoards.size >= services.forkCapacity) {
            statusLine.textContent = `Only ${services.forkCapacity} live forks at a time here — discard one first.`;
            return;
        }
        let backend: SimulationBackend | null = null;
        try {
            backend = services.backendFactory(
                paneSessionId(services.baseSessionId, `focus-${geometry}`),
            );
            const { mountFocusPane } = await import("./compare-focus-pane.js");

            // Re-read the wall: an update may have replaced it while the pane
            // modules loaded, and a fork must not attach to a vanished board.
            const latestWall = workspaceStore.getState().results.filmstrip;
            if (
                !filmstripView ||
                forkedBoards.has(geometry) ||
                !latestWall?.tilings.some((candidate) => candidate.geometry === geometry)
            ) {
                disposeDetachedBackend(backend);
                backend = null;
                return;
            }

            let nextPane: FocusPaneHandle | null = null;
            nextPane = mountFocusPane({
                // Display-only: the chip and canvas aria name the board.
                geometry: tiling.label || tiling.geometry,
                frameIndex,
                pattern,
                backend,
                bootstrapData: options.bootstrapData,
                createGridView: services.createGridView,
                buildEditorToolCells: services.buildEditorToolCells,
                ...(services.resolveCellSize ? { resolveCellSize: services.resolveCellSize } : {}),
                ...(initialPaint ? { initialPaint } : {}),
                onRunWallFromHere: (cellsById) => adoptForkStateAsSeed(geometry, cellsById),
                onDiscard: () => {
                    if (forkedBoards.get(geometry) === nextPane) {
                        forkedBoards.delete(geometry);
                        // The store's forkedBoards change refreshes the summary
                        // through its subscription.
                        syncWorkspaceForks();
                    }
                    filmstripView?.setBoardOverlay(geometry, null);
                },
                onError: reportFocusPaneError,
            });
            backend = null;

            if (!filmstripView.setBoardOverlay(geometry, nextPane.element)) {
                nextPane.dispose();
                return;
            }
            forkedBoards.set(geometry, nextPane);
            syncWorkspaceForks();
        } catch (error) {
            if (backend) {
                disposeDetachedBackend(backend);
            }
            reportFocusPaneError(error);
        }
    }

    async function forkFocusedBoardLive(): Promise<void> {
        const geometry = selectedBoardGeometry();
        if (!filmstripView || !geometry) {
            return;
        }
        await forkBoardLive(geometry, filmstripView.currentFrameIndex());
    }

    function openFocusedBoardInLab(): void {
        const geometry = selectedBoardGeometry();
        const filmstrip = workspaceStore.getState().results.filmstrip;
        if (!filmstripView || !filmstrip || !geometry) {
            return;
        }
        const tiling = filmstrip.tilings.find((candidate) => candidate.geometry === geometry);
        if (!tiling) {
            return;
        }
        const pattern = buildFilmstripFramePattern(
            filmstrip,
            tiling,
            filmstripView.currentFrameIndex(),
        );
        if (!pattern) {
            statusLine.textContent = "This generation cannot be opened in the Lab.";
            return;
        }
        openPattern(pattern);
    }

    function showStageHero(): void {
        stageHero.hidden = false;
        stageCaption.hidden = true;
        if (filmstripView) {
            filmstripView.element.hidden = true;
        }
    }

    function showStageBoards(): void {
        stageHero.hidden = true;
        stageCaption.hidden = stageCaption.textContent === "";
        if (filmstripView) {
            filmstripView.element.hidden = false;
        }
    }

    function optionLabel(select: HTMLSelectElement, value: string): string {
        return [...select.options].find((option) => option.value === value)?.textContent ?? "";
    }

    /** Drop a "Category: " prefix so the caption reads "R-pentomino", not "Shape: R-pentomino". */
    function conciseLabel(label: string): string {
        const separator = label.indexOf(": ");
        return separator >= 0 ? label.slice(separator + 2) : label;
    }

    function updateStageCaption(runConfig: CompareRunConfig): void {
        const seedLabel = runConfig.pattern
            ? conciseLabel(optionLabel(shapeSelect, runConfig.pattern)) || runConfig.pattern
            : "Custom seed";
        const ruleLabel = conciseLabel(optionLabel(ruleSelect, runConfig.rule)) || runConfig.rule;
        const count = runConfig.geometries.length;
        stageCaption.textContent = `${seedLabel} · ${ruleLabel} · ${count} tiling${
            count === 1 ? "" : "s"
        }`;
        stageCaption.hidden = stageHero.hidden === false;
    }

    /**
     * The bottom status reflects whether the shared clock is running, so it does
     * not sit on "Press play" while the demo autoplays. It anchors on "Filmstrip
     * ready" while paused and names the board count, but the transport owns the
     * generation counter, so the status no longer restates a (differently
     * framed) generation count.
     */
    function filmstripReadyStatus(playing: boolean): string {
        const count = workspaceStore.getState().results.filmstrip?.tilings.length ?? 0;
        const boards = `${count} tiling${count === 1 ? "" : "s"}`;
        return playing
            ? `Playing ${boards} in lockstep.`
            : `Filmstrip ready — ${boards}. Press play.`;
    }

    function setWallLoading(message: string | null): void {
        if (message) {
            wallLoadingOverlay.querySelector(".compare-wall-loading-text")!.textContent = message;
            wallLoadingOverlay.hidden = false;
            filmstripArea.classList.add("is-loading");
            return;
        }
        wallLoadingOverlay.hidden = true;
        filmstripArea.classList.remove("is-loading");
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

    // The inspector toolbelt acts on the selected board: return from focus,
    // open the current frame in the Lab, or edit it live when the host supports it.
    const heroBackButton = el(
        "button",
        {
            class: "compare-hero-tool compare-hero-back",
            type: "button",
            title: "Back to the wall",
            "aria-label": "Back to the wall",
        },
        ["Back to wall"],
    );
    const heroOpenLabButton = el(
        "button",
        {
            class: "compare-hero-tool compare-hero-open-lab",
            type: "button",
            title: "Open this generation in the Lab",
            "aria-label": "Open this generation in the Lab",
        },
        ["Open in Lab"],
    );
    const heroForkButton = el(
        "button",
        {
            class: "compare-hero-tool compare-hero-fork",
            type: "button",
            title: "Fork this generation into a live, editable board on the wall",
        },
        ["Edit live"],
    );
    const inspectorReplaceButton = el(
        "button",
        {
            class: "compare-hero-tool compare-inspector-replace",
            type: "button",
            title: "Replace the selected board",
        },
        ["Replace"],
    );
    const inspectorRemoveButton = el(
        "button",
        {
            class: "compare-hero-tool compare-inspector-remove",
            type: "button",
            title: "Remove the selected board",
        },
        ["Remove"],
    );
    copyRunButton.classList.add("compare-hero-tool");
    const heroToolbelt = el("div", { class: "compare-hero-toolbelt" }, [
        heroBackButton,
        heroOpenLabButton,
        ...(focusLiveEnabled ? [heroForkButton] : []),
        inspectorReplaceButton,
        inspectorRemoveButton,
        copyRunButton,
    ]);

    const stageMain = el("div", { class: "compare-stage-main" }, [
        staleResultNotice,
        filmstripArea,
    ]);
    const explainerTitle = el("summary", {
        class: "compare-explainer-title",
        textContent: "What you are seeing",
    });
    const explainerBody = el("div", { class: "compare-explainer-body" });
    // The accessible name tracks the visible summary (set in updateExplainer),
    // so a screen reader hears "Focused board" in speaker view rather than a
    // fixed, now-wrong "How the comparison works".
    const explainerPanel = el(
        "details",
        { class: "compare-explainer", "aria-label": explainerTitle.textContent ?? "", open: true },
        [explainerTitle, explainerBody],
    );
    const stageFrame = el("div", { class: "compare-stage-frame" }, [
        el("div", { class: "compare-stage-body" }, [stageMain]),
    ]);

    // Switching seed source toggles the bit pad/preview and refreshes accordingly.
    shapeSelect.addEventListener("change", () => {
        // Named-shape run configs legitimately carry an empty bit seed. When
        // the user returns to Bits, restore an editable seed before the next
        // request drops the pattern field; otherwise both seed sources are
        // absent and server/standalone validation rejects the rebuild.
        if (!isShapeMode() && normalizedSeedBits().length === 0) {
            seedInput.value = DEFAULT_SEED;
            seedPad.syncFromSeed();
        }
        syncShapeMode();
        seedPreview.refresh();
        updateSummary();
        scheduleWallRerun();
    });

    // Setup tabs coordinate the persistent desktop sidebars and the exclusive
    // narrow-screen drawers without recreating their interactive content.
    const configTabButtons = new Map<ConfigTab, HTMLButtonElement>();
    const configTabPanels = new Map<ConfigTab, HTMLElement>();
    const configTabs = el(
        "div",
        { class: "compare-config-tabs", role: "tablist", "aria-label": "Configuration sections" },
        [
            configTabButton("setup", "Setup"),
            configTabButton("tilings", "Tilings"),
            configTabButton("help", "Help"),
            configTabButton("saved", "Saved"),
        ],
    );
    // Rule and seed source now live only in the always-visible quick strip; the
    // Setup tab keeps the deeper knobs and the seed pad.
    const setupConfigPanel = configPanel("setup", [
        el("div", { class: "compare-form" }, [
            labeledField("Traversal", traversalSelect),
            labeledField("Wall generations", wallGenerationsInput),
            labeledField("Analysis steps", analysisStepsInput),
            labeledField("Grid size", gridInput),
        ]),
        seedWorkspace,
    ]);
    const tilingsConfigPanel = configPanel("tilings", [
        el("div", { class: "compare-tilings-block" }, [
            tilingControlsBar(),
            selectedTilingsList,
            tilingList,
        ]),
    ]);
    // Analysis lives on its own stage-wide overlay (dimmed wall behind), so the
    // phase portrait and the wide result table get real room instead of the
    // 280px inspector tail with a nested horizontal scroll. The Run button sits
    // with the results it produces.
    const analysisCloseButton = el(
        "button",
        {
            class: "compare-close compare-analysis-close",
            type: "button",
            title: "Close analysis",
            "aria-label": "Close analysis",
        },
        ["✕"],
    );
    // A decorative click-to-dismiss layer; Escape and the ✕ button are the
    // accessible closers, so keep it out of the a11y tree (and off the tab order).
    const analysisBackdrop = el("button", {
        class: "compare-analysis-backdrop",
        type: "button",
        tabindex: "-1",
        "aria-hidden": "true",
    });
    const analysisOverlay = el(
        "div",
        {
            class: "compare-analysis-overlay",
            hidden: true,
            inert: true,
        },
        [
            analysisBackdrop,
            el(
                "div",
                {
                    class: "compare-analysis-panel",
                    role: "dialog",
                    "aria-modal": "true",
                    "aria-label": "Statistical analysis",
                },
                [
                    el("div", { class: "compare-analysis-header" }, [
                        el("strong", {
                            class: "compare-analysis-title",
                            textContent: "Statistical analysis",
                        }),
                        analysisCloseButton,
                    ]),
                    el("div", { class: "compare-analysis compare-analysis-body" }, [
                        el("p", {
                            class: "compare-intro",
                            textContent:
                                "Run the same seed to a fixed horizon and chart how each topology diverges — a phase portrait plus a per-tiling result table.",
                        }),
                        runButton,
                        resultsArea,
                    ]),
                ],
            ),
        ],
    );
    const helpConfigPanel = configPanel("help", [
        el("div", { class: "compare-help" }, comparisonHelpContent()),
    ]);
    const savedConfigPanel = configPanel("saved", [savedCompareControls()]);
    const configSheet = el(
        "aside",
        {
            class: "compare-config-sheet compare-setup-sidebar",
            inert: true,
            "aria-label": "Comparison setup",
        },
        [
            el("div", { class: "compare-config-sheet-header" }, [
                el("div", { class: "compare-config-sheet-title", textContent: "Setup" }),
                configSheetCloseButton,
            ]),
            configTabs,
            el("div", { class: "compare-config-sheet-body" }, [
                setupStrip,
                setupConfigPanel,
                tilingsConfigPanel,
                helpConfigPanel,
                savedConfigPanel,
            ]),
        ],
    );
    const inspector = el(
        "aside",
        {
            class: "compare-inspector",
            inert: true,
            "aria-label": "Selected board inspector",
        },
        [
            el("div", { class: "compare-inspector-header" }, [
                el("strong", { textContent: "Inspector" }),
                inspectorCloseButton,
            ]),
            el("div", { class: "compare-inspector-body" }, [heroToolbelt, explainerPanel]),
        ],
    );
    activateConfigTab("setup");

    const boardWall = el("main", { class: "compare-stage compare-board-wall" }, [stageFrame]);
    const dock = el("div", { class: "compare-dock" }, [
        filmstripTransport.element,
        editModeButton,
        tilingsButton,
        configButton,
        analysisButton,
        inspectorButton,
        statusLine,
    ]);
    const workspaceLayout = createCompareWorkspaceLayout({
        setup: configSheet,
        boardWall,
        inspector,
        dock,
        setupToggle: configButton,
        inspectorToggle: inspectorButton,
    });
    const root = el("div", { class: "compare-content" }, [
        workspaceLayout.element,
        analysisOverlay,
    ]);

    renderTilingChecklist();
    refreshSavedControls();

    // The explainer is purely store-derived: inspected board, the wall result,
    // and the current frame index. Subscribing to exactly that slice means a
    // frame tick refreshes the explainer without touching the summary, and no
    // mutation site has to remember to call updateExplainer.
    const selectExplainerState = (state: ReturnType<typeof workspaceStore.getState>) =>
        [inspectedBoard(state), state.results.filmstrip, state.playback.frameIndex] as const;
    storeRenderSubscriptions.push(
        subscribeSelector(workspaceStore, selectExplainerState, (explainerState) =>
            updateExplainer(explainerState),
        ),
    );
    updateExplainer(selectExplainerState(workspaceStore.getState()));

    // The summary's store-derived inputs: the operation lifecycle, the wall
    // result and its key, focus/selection, and fork membership. Folding
    // forkedBoards to a joined string keeps every selector element a primitive
    // or stable reference (the frozen array is a fresh object each update), so
    // the slice only changes on a genuine change. It deliberately omits
    // playback, so the clock ticking never re-runs the summary. The summary
    // also depends on local UI state (the selection Set, config fields), which
    // still triggers updateSummary imperatively from those event handlers.
    storeRenderSubscriptions.push(
        subscribeSelector(
            workspaceStore,
            (state) =>
                [
                    state.operation.status,
                    state.operation.executing,
                    state.operation.kind,
                    state.operation.wallUpdateFailed,
                    state.results.filmstrip,
                    state.results.filmstripKey,
                    state.focusedBoard,
                    state.selectedBoard,
                    state.forkedBoards.join(","),
                ] as const,
            () => updateSummary(),
        ),
    );

    // Keep the bottom status honest about the clock: when playback toggles
    // (autoplay, or the user), refresh it -- but only while it is already the
    // filmstrip-ready line, so transient messages (errors, "Updating…", "Saved
    // run") are never clobbered.
    storeRenderSubscriptions.push(
        subscribeSelector(
            workspaceStore,
            (state) => state.playback.playing,
            (playing) => {
                const showingReadyLine =
                    statusLine.textContent === filmstripReadyStatus(true) ||
                    statusLine.textContent === filmstripReadyStatus(false);
                if (showingReadyLine) {
                    statusLine.textContent = filmstripReadyStatus(playing);
                }
            },
        ),
    );

    function labeledField(label: string, field: HTMLElement): HTMLLabelElement {
        return el("label", { class: "compare-label" }, [el("span", { textContent: label }), field]);
    }

    function setupItem(label: string, value: HTMLElement): HTMLElement {
        return el("div", { class: "compare-setup-item compare-setup-status" }, [
            el("span", { class: "compare-setup-label", textContent: label }),
            value,
        ]);
    }

    function dockGlyph(text: string): HTMLElement {
        return el("span", {
            class: "compare-dock-glyph",
            "aria-hidden": "true",
            textContent: text,
        });
    }

    function dockLabel(text: string): HTMLElement {
        return el("span", { class: "compare-dock-label", textContent: text });
    }

    function explainerItem(title: string, body: string): HTMLElement {
        return el("div", { class: "compare-explainer-item" }, [
            el("span", { class: "compare-explainer-key", textContent: title }),
            el("span", { class: "compare-explainer-copy", textContent: body }),
        ]);
    }

    function comparisonHelpContent(): HTMLElement[] {
        return [
            el("div", { class: "compare-help-title", textContent: "How the comparison works" }),
            explainerItem(
                "Same seed",
                "One starting pattern is projected onto every selected board.",
            ),
            explainerItem(
                "Same rule",
                "Each board runs the selected rule on the same generation clock.",
            ),
            explainerItem(
                "Different tilings",
                "Topology changes the neighbors, so outcomes can diverge.",
            ),
            el("div", {
                class: "compare-explainer-hint",
                textContent: "Click a board to focus it. Use Open in Lab to continue from a frame.",
            }),
        ];
    }

    function configTabButton(tab: ConfigTab, label: string): HTMLButtonElement {
        const button = el("button", {
            class: "compare-config-tab",
            type: "button",
            role: "tab",
            id: `compare-config-tab-${tab}`,
            "aria-controls": `compare-config-panel-${tab}`,
            "aria-selected": "false",
            tabindex: "-1",
            textContent: label,
        });
        button.addEventListener("click", () => activateConfigTab(tab, { focus: true }));
        button.addEventListener("keydown", handleConfigTabKeydown);
        configTabButtons.set(tab, button);
        return button;
    }

    function configPanel(tab: ConfigTab, children: Array<Node | string>): HTMLElement {
        const panel = el(
            "section",
            {
                class: `compare-config-panel compare-config-panel-${tab}`,
                role: "tabpanel",
                id: `compare-config-panel-${tab}`,
                "aria-labelledby": `compare-config-tab-${tab}`,
                hidden: true,
            },
            children,
        );
        configTabPanels.set(tab, panel);
        return panel;
    }

    function activateConfigTab(tab: ConfigTab, options: { focus?: boolean } = {}): void {
        activeConfigTab = tab;
        for (const [candidate, button] of configTabButtons) {
            const active = candidate === tab;
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-selected", active ? "true" : "false");
            button.tabIndex = active ? 0 : -1;
            configTabPanels.get(candidate)!.hidden = !active;
        }
        if (options.focus) {
            configTabButtons.get(tab)?.focus();
        }
    }

    function handleConfigTabKeydown(event: KeyboardEvent): void {
        const tabs: ConfigTab[] = ["setup", "tilings", "help", "saved"];
        const activeIndex = tabs.findIndex(
            (tab) => configTabButtons.get(tab) === document.activeElement,
        );
        if (activeIndex < 0) {
            return;
        }
        let nextIndex: number;
        if (event.key === "ArrowLeft") {
            nextIndex = (activeIndex + tabs.length - 1) % tabs.length;
        } else if (event.key === "ArrowRight") {
            nextIndex = (activeIndex + 1) % tabs.length;
        } else if (event.key === "Home") {
            nextIndex = 0;
        } else if (event.key === "End") {
            nextIndex = tabs.length - 1;
        } else {
            return;
        }
        event.preventDefault();
        activateConfigTab(tabs[nextIndex]!, { focus: true });
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
                const capacityReached =
                    selected.size >= currentWallCapacity() && !selected.has(option.geometry);
                const disabledReason = !compatible
                    ? "Unsupported for the selected rule"
                    : capacityReached
                      ? wallCapacityMessage(currentWallCapacity())
                      : "";
                const checkbox = el("input", {
                    type: "checkbox",
                    checked: compatible && selected.has(option.geometry),
                    disabled: !compatible || capacityReached,
                    title: disabledReason,
                });
                checkbox.addEventListener("change", () => {
                    if (!tilingCompatibleWithSelectedRule(option)) {
                        checkbox.checked = false;
                        selected.delete(option.geometry);
                        updateSummary();
                        return;
                    }
                    if (checkbox.checked) {
                        if (selected.size >= currentWallCapacity()) {
                            checkbox.checked = false;
                            statusLine.textContent = wallCapacityMessage(currentWallCapacity());
                            updateSummary();
                            return;
                        }
                        selected.add(option.geometry);
                    } else {
                        selected.delete(option.geometry);
                    }
                    updateSummary();
                    refreshPreview();
                    scheduleWallRerun();
                });
                group.append(
                    el(
                        "label",
                        {
                            class: [
                                "compare-tiling",
                                compatible ? "" : "is-disabled",
                                compatible && selected.has(option.geometry) ? "is-selected" : "",
                            ]
                                .filter(Boolean)
                                .join(" "),
                            title: disabledReason,
                        },
                        [checkbox, el("span", { textContent: option.label })],
                    ),
                );
            }
            tilingList.append(group);
        }
        updateSummary();
    }

    function selectedTilingOptions(): TilingOption[] {
        return allTilings.filter((option) => selected.has(option.geometry));
    }

    function renderSelectedTilings(): void {
        selectedTilingsList.replaceChildren();
        const selectedOptions = selectedTilingOptions();
        selectedTilingsList.classList.toggle("is-empty", selectedOptions.length === 0);
        if (selectedOptions.length === 0) {
            selectedTilingsList.append(
                el("span", {
                    class: "compare-selected-empty",
                    textContent: "No tilings selected.",
                }),
            );
            return;
        }
        selectedTilingsList.append(
            el("span", { class: "compare-selected-label", textContent: "Selected" }),
        );
        for (const option of selectedOptions) {
            const chip = el(
                "button",
                {
                    class: "compare-selected-chip",
                    type: "button",
                    title: `Remove ${option.label} from the comparison`,
                    "aria-label": `Remove ${option.label} from the comparison`,
                },
                [
                    el("span", { class: "compare-selected-chip-label", textContent: option.label }),
                    el("span", {
                        class: "compare-selected-chip-remove",
                        "aria-hidden": "true",
                        textContent: "×",
                    }),
                ],
            );
            chip.addEventListener("click", () => {
                selected.delete(option.geometry);
                renderTilingChecklist();
                refreshPreview();
                scheduleWallRerun();
            });
            selectedTilingsList.append(chip);
        }
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
        const omitted = replaceSelection(selectionForPreset(preset));
        renderTilingChecklist();
        refreshPreview();
        scheduleWallRerun();
        if (omitted > 0) {
            statusLine.textContent = `${wallCapacityMessage(currentWallCapacity())} ${omitted} tiling${omitted === 1 ? " was" : "s were"} not added.`;
        }
    }

    function selectionForPreset(preset: TilingPreset): Set<string> {
        if (preset === "representative") {
            return defaultComparisonSelection(allTilings);
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

    function replaceSelection(nextSelection: Set<string>): number {
        selected.clear();
        const limit = currentWallCapacity();
        for (const geometry of nextSelection) {
            if (selected.size >= limit) {
                break;
            }
            selected.add(geometry);
        }
        return Math.max(0, nextSelection.size - selected.size);
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
            button.disabled = false;
            button.title = `Select ${button.textContent} tilings`;
        }
    }

    function updateSummary(): void {
        const summary = root.querySelector("#compare-tilings-summary");
        if (summary) {
            summary.textContent = summaryText();
        }
        renderSelectedTilings();
        updateFamilyCountLabels();
        updatePresetButtons();
        const wallProblem = wallConfigProblem();
        const analysisProblem = analysisConfigProblem();
        const { results, operation } = workspaceStore.getState();
        const running = operation.executing;
        const canAnalyze = !running && selected.size > 0 && analysisProblem === null;
        const canPlay = !running && selected.size >= MIN_WALL_TILINGS && wallProblem === null;
        const current = wallProblem === null && isFilmstripCurrent();
        const wallFilmstrip = results.filmstrip;
        const stale = wallFilmstrip !== null && !current && selected.size >= MIN_WALL_TILINGS;
        const failedFilmstrip = operation.status === "failed" && operation.kind === "filmstrip";
        const failedAnalysis = operation.status === "failed" && operation.kind === "analysis";
        // Queued but not yet executing: debouncing, or launched without an
        // open request bracket (cache hits never open one).
        const queued =
            operation.status === "pending" || (operation.status === "updating" && !running);
        const pendingFilmstrip = queued && operation.kind === "filmstrip";
        const pendingAnalysis = queued && operation.kind === "analysis";
        runButton.disabled = !canAnalyze;
        runButton.textContent = failedAnalysis
            ? "Retry analysis"
            : pendingAnalysis
              ? "Run now"
              : running
                ? "Running…"
                : "Run analysis";
        runButton.title = running
            ? WAIT_FOR_WALL_UPDATE
            : (analysisProblem ?? "Run the selected tilings as a longer statistical analysis");
        setupRunButton.disabled = !canPlay || current;
        setupRunButton.classList.toggle("is-current", current && !running);
        setupRunButton.classList.toggle("is-stale", stale && !running);
        setupRunButton.textContent = failedFilmstrip
            ? "Retry"
            : pendingFilmstrip
              ? "Run now"
              : running
                ? wallFilmstrip
                    ? "Applying..."
                    : "Running..."
                : wallProblem
                  ? "Check setup"
                  : current
                    ? "Up to date"
                    : stale
                      ? "Apply changes"
                      : "Run comparison";
        const playTitle = (() => {
            if (running) {
                return WAIT_FOR_WALL_UPDATE;
            }
            if (wallProblem) {
                return wallProblem;
            }
            if (selected.size < MIN_WALL_TILINGS) {
                return "Select at least two tilings to run a comparison";
            }
            if (current) {
                return "The wall already matches this setup";
            }
            if (stale) {
                return "Update the wall with the changed setup";
            }
            return "Run every selected tiling on a shared clock";
        })();
        setupRunButton.title = playTitle;
        // The dock's idle play button shares the same gate as the Configure one.
        filmstripTransport.setIdleRunEnabled(canPlay);
        copyRunButton.disabled = running || selected.size === 0 || wallProblem !== null;
        // Already-forked hero: Discard (in the pane's own chip) is the way to
        // undo it, so the toolbelt's fork button hides rather than offering a
        // confusing second fork.
        const inspectedGeometry = selectedBoardGeometry();
        heroForkButton.hidden = inspectedGeometry !== null && forkedBoards.has(inspectedGeometry);
        heroForkButton.disabled = running;
        heroOpenLabButton.disabled = running || inspectedGeometry === null;
        heroBackButton.disabled = workspaceStore.getState().focusedBoard === null;
        inspectorButton.disabled = wallFilmstrip === null;
        const inspectedBoard = selectedBoardElement();
        inspectorReplaceButton.disabled = running || inspectedBoard === null;
        inspectorRemoveButton.disabled =
            running ||
            inspectedBoard?.querySelector<HTMLButtonElement>(".compare-filmstrip-remove")
                ?.disabled !== false;
        // Painting needs boards on the stage; the toggle waits for a run.
        editModeButton.disabled = running || !wallFilmstrip;
        editModeButton.title = running ? WAIT_FOR_WALL_UPDATE : "Edit the seed by painting boards";
        updateSetupSummary();
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

    function updateSetupSummary(): void {
        const ruleLabel = selectedRule()?.display_name ?? selectedRuleName();
        const tilingLabel = `${selected.size} selected`;
        setupTilingsValue.textContent = tilingLabel;
        ruleSelect.title = ruleLabel;
        setupTilingsValue.title = summaryText();
    }

    function updateExplainer([inspectedGeometry, filmstrip, frameIndex]: ReturnType<
        typeof selectExplainerState
    >): void {
        if (inspectedGeometry && filmstrip) {
            const tiling = filmstrip.tilings.find(
                (candidate) => candidate.geometry === inspectedGeometry,
            );
            if (tiling) {
                const frame = tiling.frames[frameIndex] ?? {};
                const liveCells = Object.values(frame).filter((state) => state !== 0).length;
                const catalog = allTilings.find(
                    (candidate) => candidate.geometry === tiling.geometry,
                );
                const family = catalog?.family ? catalog.family.replace(/-/g, " ") : "tiling";
                explainerTitle.textContent = "Focused board";
                explainerPanel.setAttribute("aria-label", "Focused board");
                explainerBody.replaceChildren(
                    explainerItem("Board", tiling.label || tiling.geometry),
                    explainerItem(
                        "Generation",
                        `${frameIndex} of ${Math.max(filmstrip.frame_count - 1, 0)}`,
                    ),
                    explainerItem("Live count", `${liveCells} live cells`),
                    explainerItem("Current tiling", `${family} · ${tiling.geometry}`),
                    explainerItem(
                        "Open in Lab",
                        "Loads this exact generation into the single-board editor.",
                    ),
                    ...(focusLiveEnabled
                        ? [
                              explainerItem(
                                  "Edit live",
                                  "Forks this generation into an editable board that stays on the wall.",
                              ),
                          ]
                        : []),
                );
                return;
            }
        }
        explainerTitle.textContent = "What you are seeing";
        explainerPanel.setAttribute("aria-label", "What you are seeing");
        explainerBody.replaceChildren(
            explainerItem(
                "Same seed",
                "One starting pattern is projected onto every selected board.",
            ),
            explainerItem(
                "Same rule",
                "Each board runs the selected rule on the same generation clock.",
            ),
            explainerItem(
                "Different tilings",
                "Topology changes the neighbors, so outcomes can diverge.",
            ),
            el("div", {
                class: "compare-explainer-hint",
                textContent: "Click a board to focus it. Use Open in Lab to continue from a frame.",
            }),
        );
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
            compatibleTilings
                .slice(0, currentWallCapacity())
                .forEach((option) => selected.add(option.geometry));
            changed = true;
        }
        if (changed) {
            refreshPreview();
        }
    }

    function patternShareUrl(pattern: PatternPayload): string {
        return buildShareUrl(pattern, window.location.href);
    }

    function integerRangeProblem(
        field: HTMLInputElement,
        label: string,
        minimum: number,
        maximum: number,
    ): string | null {
        const value = Number(field.value);
        if (!Number.isInteger(value) || value < minimum || value > maximum) {
            return `${label} must be an integer from ${minimum} to ${maximum}.`;
        }
        return null;
    }

    function sharedConfigProblem(): string | null {
        if (!isShapeMode()) {
            if (seedInput.value.trim().length === 0) {
                return "Enter a bit seed or choose a named seed shape.";
            }
            if (seedInput.value.length > MAX_COMPARE_SEED_LENGTH) {
                return `Bit seeds can contain at most ${MAX_COMPARE_SEED_LENGTH} characters.`;
            }
        }
        return integerRangeProblem(
            gridInput,
            "Grid size",
            MIN_COMPARE_GRID_SIZE,
            MAX_COMPARE_GRID_SIZE,
        );
    }

    function wallConfigProblem(): string | null {
        return (
            sharedConfigProblem() ??
            integerRangeProblem(
                wallGenerationsInput,
                "Wall generations",
                MIN_COMPARE_STEPS,
                MAX_WALL_GENERATIONS,
            )
        );
    }

    function analysisConfigProblem(): string | null {
        return (
            sharedConfigProblem() ??
            integerRangeProblem(
                analysisStepsInput,
                "Analysis steps",
                MIN_COMPARE_STEPS,
                MAX_ANALYSIS_STEPS,
            )
        );
    }

    function currentRunConfig(): CompareRunConfig {
        const config: CompareRunConfig = {
            seed: seedInput.value,
            rule: selectedRuleName(),
            traversal: traversalSelect.value,
            frames: clampNumber(
                wallGenerationsInput.value,
                MIN_COMPARE_STEPS,
                MAX_WALL_GENERATIONS,
                50,
            ),
            grid_size: clampNumber(
                gridInput.value,
                MIN_COMPARE_GRID_SIZE,
                MAX_COMPARE_GRID_SIZE,
                16,
            ),
            geometries: [...selected],
        };
        if (isShapeMode()) {
            config.pattern = shapeSelect.value;
        }
        return config;
    }

    function runConfigKey(config: CompareRunConfig): string {
        return JSON.stringify(config);
    }

    function isFilmstripCurrent(): boolean {
        return (
            workspaceStore.getState().results.filmstrip !== null &&
            workspaceStore.getState().results.filmstripKey === runConfigKey(currentRunConfig())
        );
    }

    function compareRunUrl(): string {
        return buildCompareRunUrl(currentRunConfig(), window.location.href);
    }

    function refreshSavedControls(preferredRunId = "", preferredTilingSetId = ""): void {
        const runs = listSavedCompareRuns();
        const tilingSets = listSavedTilingSets();
        workspaceStore.update((state) => ({
            ...state,
            saved: { runs, tilingSets },
        }));
        populateSavedSelect(savedRunSelect, runs, "No saved runs", preferredRunId);
        populateSavedSelect(
            savedTilingSetSelect,
            tilingSets,
            "No saved tiling sets",
            preferredTilingSetId,
        );
        const hasRuns = runs.length > 0;
        const hasTilingSets = tilingSets.length > 0;
        loadRunButton.disabled = !hasRuns;
        deleteRunButton.disabled = !hasRuns;
        loadTilingSetButton.disabled = !hasTilingSets;
        deleteTilingSetButton.disabled = !hasTilingSets;
        savedRunHint.textContent = hasRuns
            ? `${runs.length} saved run${runs.length === 1 ? "" : "s"} available.`
            : "No saved runs yet. Name the current setup and choose Save run.";
        savedTilingSetHint.textContent = hasTilingSets
            ? `${tilingSets.length} saved tiling set${tilingSets.length === 1 ? "" : "s"} available.`
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
        const saved = workspaceStore
            .getState()
            .saved.runs.find((run) => run.id === savedRunSelect.value);
        if (!saved) {
            return;
        }
        await applyRunConfig(saved.config);
        editingSavedRunId = saved.id;
        savedRunNameInput.value = saved.name;
        refreshSavedControls(saved.id, savedTilingSetSelect.value);
    }

    function deleteSelectedRun(): void {
        const saved = workspaceStore
            .getState()
            .saved.runs.find((run) => run.id === savedRunSelect.value);
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
        const saved = workspaceStore
            .getState()
            .saved.tilingSets.find((set) => set.id === savedTilingSetSelect.value);
        if (!saved) {
            return;
        }
        const knownGeometries = new Set(allTilings.map((tiling) => tiling.geometry));
        const omitted = replaceSelection(
            new Set(saved.geometries.filter((geometry) => knownGeometries.has(geometry))),
        );
        pruneSelectionForSelectedRule({ selectAllIfEmpty: true });
        renderTilingChecklist();
        refreshPreview();
        editingSavedTilingSetId = saved.id;
        savedTilingSetNameInput.value = saved.name;
        refreshSavedControls(savedRunSelect.value, saved.id);
        statusLine.textContent =
            omitted > 0
                ? `Loaded tiling set "${saved.name}" with ${selected.size} tilings. ${wallCapacityMessage(currentWallCapacity())}`
                : `Loaded tiling set "${saved.name}".`;
        scheduleWallRerun();
    }

    function deleteSelectedTilingSet(): void {
        const saved = workspaceStore
            .getState()
            .saved.tilingSets.find((set) => set.id === savedTilingSetSelect.value);
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
            // A wall compares multiple topology families by definition. Keep
            // tiling-specific rules in the Lab, where their compatible tiling
            // can be selected explicitly, and expose only universal rules here.
            rules = response.rules.filter(
                (rule) => rule.supports_all_topologies && rule.compatible_tiling_families === null,
            );
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
            updateSummary();
            scheduleWallRerun();
        });
        pruneSelectionForSelectedRule({ selectAllIfEmpty: true });
        renderTilingChecklist();
    }

    function setRunning(next: boolean): void {
        workspaceStore.update((state) => ({
            ...state,
            operation: { ...state.operation, executing: next },
        }));
        runButton.textContent = next ? "Running…" : "Run analysis";
        // Quiet the transport too: a play press accepted mid-rebuild would be
        // wiped when the fresh filmstrip attaches paused at the seed.
        filmstripTransport.setBusy(next);
        filmstripView?.setManagementBusy(next);
        retryWallUpdateButton.disabled = next;
        retryWallUpdateButton.title = next
            ? WAIT_FOR_WALL_UPDATE
            : "Retry the update using the latest setup";
        // The executing flag published above refreshes the summary through its
        // subscription; the browser paints only the settled DOM either way.
        if (!next) {
            renderTilingChecklist();
            refreshSavedControls(savedRunSelect.value, savedTilingSetSelect.value);
            syncShapeMode();
            window.requestAnimationFrame(() => focusTilingSearchIfOpen());
        }
    }

    function ownsOperation(ticket: OperationTicket): boolean {
        return (
            !disposed && ticket.revision === lifecycleRevision && activeOperation?.id === ticket.id
        );
    }

    function beginOperation(kind: OperationTicket["kind"]): OperationTicket {
        const ticket = { id: ++operationSequence, revision: lifecycleRevision, kind };
        activeOperation = ticket;
        setRunning(true);
        return ticket;
    }

    function finishOperation(ticket: OperationTicket): void {
        if (!ownsOperation(ticket)) {
            return;
        }
        activeOperation = null;
        setWallLoading(null);
        setRunning(false);
    }

    function invalidateOperations(): void {
        lifecycleRevision += 1;
        activeOperation = null;
        if (workspaceStore.getState().operation.executing) {
            setWallLoading(null);
            setRunning(false);
        }
    }

    function clearFailedWallUpdate(): void {
        workspaceStore.update((state) => ({
            ...state,
            operation: { ...state.operation, wallUpdateFailed: false },
        }));
        staleResultNotice.hidden = true;
        staleResultNoticeMessage.textContent = "";
        filmstripView?.setManagementBlocked(null);
    }

    function reportFailedWallUpdate(message: string): void {
        workspaceStore.update((state) => ({
            ...state,
            operation: { ...state.operation, wallUpdateFailed: true },
        }));
        staleResultNoticeMessage.textContent = `Update failed: ${message}. The wall is still showing the previous result.`;
        staleResultNotice.hidden = false;
        filmstripView?.setManagementBlocked(FAILED_UPDATE_MANAGEMENT_REASON);
    }

    function selectHasValue(select: HTMLSelectElement, value: string): boolean {
        return [...select.options].some((option) => option.value === value);
    }

    function syncShapeMode(): void {
        const shapeMode = isShapeMode();
        seedWorkspace.classList.toggle("is-shape-mode", shapeMode);
        seedPadBlock.style.display = shapeMode ? "none" : "";
        seedInput.disabled = shapeMode;
        updateSetupSummary();
    }

    async function applyRunConfig(config: CompareRunConfig): Promise<void> {
        // A loaded run replaces the entire wall. Older backend work may still
        // settle, but it no longer owns any visible or busy state.
        invalidateOperations();
        clearFailedWallUpdate();
        await ensureRules();
        if (disposed) {
            return;
        }

        seedInput.value = config.seed;
        seedPad.syncFromSeed();
        const requestedRuleAvailable =
            rules.length === 0 || selectHasValue(ruleSelect, config.rule);
        if (selectHasValue(ruleSelect, config.rule)) {
            ruleSelect.value = config.rule;
        }
        if (selectHasValue(traversalSelect, config.traversal)) {
            traversalSelect.value = config.traversal;
        }
        wallGenerationsInput.value = String(config.frames);
        gridInput.value = String(config.grid_size);
        shapeSelect.value =
            config.pattern && selectHasValue(shapeSelect, config.pattern) ? config.pattern : "";
        syncShapeMode();

        const knownGeometries = new Set(allTilings.map((tiling) => tiling.geometry));
        const omitted = replaceSelection(
            new Set(config.geometries.filter((geometry) => knownGeometries.has(geometry))),
        );
        renderTilingChecklist();
        refreshPreview();
        resultsArea.replaceChildren();
        showStageHero();
        stageMain.classList.remove("is-speaker");
        workspaceStore.update((state) => ({
            ...state,
            results: { ...state.results, filmstrip: null, filmstripKey: null },
        }));
        mirrorFocusToHash(null);
        // The loaded config replaces the current wall wholesale: tear down any
        // live forks with it and unbind the shared clock, or the transport
        // keeps playing the old, now-hidden boards instead of offering to run
        // the loaded comparison.
        disposeAllForkedBoards();
        filmstripView?.detachPlayer();
        setWallLoading(null);
        updateSummary();
        const configProblem = wallConfigProblem();
        const notices = [
            ...(!requestedRuleAvailable
                ? [
                      `Rule "${config.rule}" is tiling-specific or unavailable on the wall; using ${selectedRule()?.display_name ?? selectedRuleName()}.`,
                  ]
                : []),
            ...(omitted > 0 ? [wallCapacityMessage(currentWallCapacity())] : []),
            ...(configProblem ? [configProblem] : []),
        ];
        statusLine.textContent = `Loaded run link — ${selected.size} tilings ready.${notices.length > 0 ? ` ${notices.join(" ")}` : ""}`;
        scheduleWallRerun();
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
        await runFilmstrip();
    }

    function highlightGeometry(geometry: string | null): void {
        resultsArea.querySelectorAll<SVGElement>("[data-geometry]").forEach((node) => {
            node.classList.toggle(
                "is-dimmed",
                geometry !== null && node.getAttribute("data-geometry") !== geometry,
            );
        });
    }

    function scheduledAnalysisRun(): ScheduledAnalysisRun {
        const request: CompareRequest = {
            seed: seedInput.value,
            rule: selectedRuleName(),
            traversal: traversalSelect.value,
            steps: clampNumber(analysisStepsInput.value, MIN_COMPARE_STEPS, MAX_ANALYSIS_STEPS, 50),
            grid_size: clampNumber(
                gridInput.value,
                MIN_COMPARE_GRID_SIZE,
                MAX_COMPARE_GRID_SIZE,
                16,
            ),
            geometries: [...selected],
            include_states: true,
            ...(isShapeMode() ? { pattern: shapeSelect.value } : {}),
        };
        return { kind: "analysis", request, key: JSON.stringify(request) };
    }

    function scheduleAnalysis(): void {
        if (selected.size === 0) {
            statusLine.textContent = "Select at least one tiling to run analysis.";
            return;
        }
        workspaceScheduler.schedule(scheduledAnalysisRun());
    }

    function runComparison(): Promise<void> {
        if (disposed || selected.size === 0) {
            return Promise.resolve();
        }
        return workspaceScheduler.runNow(scheduledAnalysisRun());
    }

    async function performAnalysis(
        scheduled: ScheduledAnalysisRun,
        signal: AbortSignal,
    ): Promise<void> {
        const cached = analysisCache.get(scheduled.key);
        if (cached) {
            renderResults(cached);
            workspaceStore.update((state) => ({
                ...state,
                results: { ...state.results, analysis: cached, analysisKey: scheduled.key },
            }));
            statusLine.textContent = `Analysis ready — ${cached.results.length} tilings (cached).`;
            return;
        }
        const { request } = scheduled;
        const ticket = beginOperation("analysis");
        statusLine.textContent = `Updating analysis for ${request.geometries?.length ?? selected.size} tilings…`;

        try {
            const comparison = await options.backend.compareSeed(request, { signal });
            if (signal.aborted || !ownsOperation(ticket)) {
                return;
            }
            analysisCache.set(scheduled.key, comparison);
            renderResults(comparison);
            workspaceStore.update((state) => ({
                ...state,
                results: { ...state.results, analysis: comparison, analysisKey: scheduled.key },
            }));
            const sourceDesc = request.pattern
                ? `shape "${request.pattern}"`
                : `${comparison.seed_bits} bits`;
            statusLine.textContent = `Done — ${comparison.results.length} tilings, ${sourceDesc}.`;
        } catch (error) {
            if (signal.aborted || !ownsOperation(ticket)) {
                return;
            }
            statusLine.textContent = `Error: ${error instanceof Error ? error.message : String(error)}`;
            throw error;
        } finally {
            finishOperation(ticket);
        }
    }

    async function performFilmstrip(
        scheduled: ScheduledFilmstripRun,
        signal: AbortSignal,
    ): Promise<void> {
        if (disposed) {
            return;
        }
        const { config: runConfig, playback, runOptions } = scheduled;
        // The authoritative result owns each board slot, so any live forks are torn down first.
        disposeAllForkedBoards();
        if (runConfig.geometries.length < MIN_WALL_TILINGS) {
            statusLine.textContent = "Select at least two tilings to run a comparison.";
            showStageHero();
            setWallLoading(null);
            return;
        }
        if (runConfig.geometries.length > WALL_HARD_TILING_LIMIT) {
            statusLine.textContent = wallCapacityMessage(WALL_HARD_TILING_LIMIT);
            return;
        }
        const hadFilmstrip = workspaceStore.getState().results.filmstrip !== null;
        const loadingMessage = hadFilmstrip ? "Updating comparison..." : "Building comparison...";
        const showLoadingOverlay = !runOptions.quietUpdate || !hadFilmstrip;
        const ticket = beginOperation("filmstrip");
        statusLine.textContent = `${loadingMessage} ${runConfig.geometries.length} tilings…`;
        if (showLoadingOverlay) {
            setWallLoading(loadingMessage);
        }

        const requestKey = runConfigKey(runConfig);
        const request: FilmstripRequest = {
            seed: runConfig.seed,
            rule: runConfig.rule,
            traversal: runConfig.traversal,
            // The setup field is validated against the backend's filmstrip ceiling.
            frames: runConfig.frames,
            grid_size: runConfig.grid_size,
            geometries: runConfig.geometries,
            ...(runConfig.pattern === undefined ? {} : { pattern: runConfig.pattern }),
        };

        try {
            const filmstrip = await options.backend.requestFilmstrip(request, { signal });
            if (signal.aborted || !ownsOperation(ticket)) {
                return;
            }
            workspaceStore.update((state) => ({
                ...state,
                orderedBoards: filmstrip.tilings.map((tiling) => tiling.geometry),
                // Keep a still-present selection so the inspector holds the
                // board the user last looked at across a rerun, but do not
                // preselect one: an untouched wall has no "focused board", so
                // the inspector stays on its general explainer until a board
                // is chosen.
                selectedBoard: filmstrip.tilings.some(
                    (tiling) => tiling.geometry === state.selectedBoard,
                )
                    ? state.selectedBoard
                    : null,
                results: { ...state.results, filmstrip, filmstripKey: requestKey },
                playback: { frameIndex: 0, playing: false },
            }));
            if (!filmstripView) {
                filmstripView = createFilmstripView({
                    backend: options.backend,
                    transport: filmstripTransport,
                    getLiveColor: () => liveColorForRule(selectedRuleName()),
                    loop: true,
                    onFocusChange: handleFocusChanged,
                    onFrameChange: () => {
                        // Publishing the frame index re-renders the explainer
                        // through its subscription; the summary selector omits
                        // the frame index, so it stays put as the clock ticks.
                        workspaceStore.update((state) => ({
                            ...state,
                            playback: {
                                ...state.playback,
                                frameIndex: filmstripView?.currentFrameIndex() ?? 0,
                            },
                        }));
                        noteDetachedForksOnClockMove();
                    },
                    onPaintCell: handlePaintCell,
                    onRemoveBoard: removeBoardFromWall,
                    tilingOptions: wallTilingPickerOptions(allTilings),
                    onReplaceBoard: replaceBoardOnWall,
                    onAddBoard: addBoardToWall,
                    canAddBoard: () => selected.size < currentWallCapacity(),
                    addBoardDisabledReason: () => wallCapacityMessage(currentWallCapacity()),
                    isTilingAvailable: (geometry) =>
                        Boolean(
                            allTilings.find(
                                (tiling) =>
                                    tiling.geometry === geometry &&
                                    tilingCompatibleWithSelectedRule(tiling),
                            ),
                        ),
                });
                const operation = workspaceStore.getState().operation;
                filmstripView.setManagementBusy(operation.executing);
                filmstripView.setManagementBlocked(
                    operation.wallUpdateFailed ? FAILED_UPDATE_MANAGEMENT_REASON : null,
                );
                filmstripView.setEditMode(editMode);
                filmstripArea.append(filmstripView.element);
            }
            showStageBoards();
            await filmstripView.load(filmstrip, {
                ...(playback ?? {}),
                ...(hadFilmstrip ? { preserveBoards: true } : {}),
            });
            if (signal.aborted || !ownsOperation(ticket)) {
                return;
            }
            // Honour a deep-linked focus (e.g. #/compare&focus=square) now that boards exist.
            applyFocusFromHash();
            clearFailedWallUpdate();
            updateStageCaption(runConfig);
            statusLine.textContent = filmstripReadyStatus(
                workspaceStore.getState().playback.playing,
            );
            if (analysisOverlayOpen) {
                scheduleAnalysis();
            }
        } catch (error) {
            if (signal.aborted || !ownsOperation(ticket)) {
                return;
            }
            const message = error instanceof Error ? error.message : String(error);
            statusLine.textContent = `Error: ${message}`;
            if (hadFilmstrip) {
                showStageBoards();
                reportFailedWallUpdate(message);
            } else {
                clearFailedWallUpdate();
                showStageHero();
            }
            throw error;
        } finally {
            finishOperation(ticket);
        }
    }

    function runFilmstrip(
        playback?: FilmstripLoadOptions,
        runOptions: RunFilmstripOptions = {},
    ): Promise<void> {
        return workspaceScheduler.runNow(scheduledFilmstripRun(playback, runOptions));
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
        const tilingLabels = new Map(allTilings.map((tiling) => [tiling.geometry, tiling.label]));
        const legend = buildPortraitLegend(comparison);
        resultsArea.append(
            el("div", {
                class: "compare-section-title",
                textContent: "Phase portrait — live(t) / live(0)",
            }),
            buildPhasePortraitSvg(comparison),
            ...(legend ? [legend] : []),
            el("div", { class: "compare-section-title", textContent: "End-state classification" }),
            el("div", { class: "compare-grid-scroll" }, [
                buildClassificationGrid(comparison, {
                    onRowHover: highlightGeometry,
                    renderRowActions: (result) => renderRowActions(comparison, result),
                    labelForGeometry: (geometry) => tilingLabels.get(geometry),
                }),
            ]),
        );
    }

    async function openPattern(pattern: PatternPayload): Promise<void> {
        if (options.onOpenPattern) {
            await options.onOpenPattern(pattern);
            options.onRequestClose?.();
            return;
        }
        openPatternInTab(pattern);
    }

    function renderRowActions(
        comparison: SeedComparisonResult,
        result: TopologyComparisonResultPayload,
    ): Node | null {
        const begin = buildComparisonStatePattern(comparison, result, "begin");
        if (!begin) {
            return null;
        }
        const end = buildComparisonStatePattern(comparison, result, "end");
        const wrap = el("div", { class: "compare-row-actions" });
        const inPlace = options.onOpenPattern;
        const beginTitle = inPlace
            ? "Load the seed on this tiling into the board"
            : "Open the seed on this tiling in a new tab";
        const openItems: ActionMenuItem[] = [
            {
                label: "Begin",
                title: beginTitle,
                onClick: () => void openPattern(begin),
            },
        ];
        if (end) {
            const endTitle = inPlace
                ? "Load the final state on this tiling into the board"
                : "Open the final state on this tiling in a new tab";
            openItems.push({
                label: "End",
                title: endTitle,
                onClick: () => void openPattern(end),
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
        return (state) => colorByValue.get(state) ?? "var(--compare-live, var(--live, #2dd4bf))";
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
                        buildComparisonStatePattern(comparison, result, "begin"),
                    ),
                    thumbnailBlock(
                        "End",
                        preview,
                        result.final_cells_by_id ?? {},
                        liveColor,
                        buildComparisonStatePattern(comparison, result, "end"),
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

    // The dock toggles the setup region. On narrow screens Escape closes the
    // active drawer; `inert` keeps every closed region out of the tab order.
    function openConfigSheet(tab: ConfigTab = "setup"): void {
        activateConfigTab(tab);
        workspaceLayout.openSetup();
    }
    function closeConfigIfOpen(): boolean {
        return window.innerWidth < 960 && workspaceLayout.closeDrawer();
    }

    function openAnalysisOverlay(): void {
        if (analysisOverlayOpen) {
            return;
        }
        analysisOverlayOpen = true;
        analysisOverlay.hidden = false;
        analysisOverlay.removeAttribute("inert");
        analysisButton.setAttribute("aria-expanded", "true");
        // Opening runs the analysis on the current wall (or rebuilds first),
        // matching the old analysis tab's behaviour.
        if (isFilmstripCurrent()) {
            scheduleAnalysis();
        } else {
            scheduleWallRerun();
        }
        analysisCloseButton.focus();
    }
    function closeAnalysisOverlayIfOpen(): boolean {
        if (!analysisOverlayOpen) {
            return false;
        }
        analysisOverlayOpen = false;
        analysisOverlay.setAttribute("inert", "");
        analysisOverlay.hidden = true;
        analysisButton.setAttribute("aria-expanded", "false");
        analysisButton.focus();
        return true;
    }

    // The tilings shortcut lands ready to type: sheet open, Tilings disclosure
    // expanded, search focused.
    function focusTilingSearchIfOpen(): void {
        if (
            configSheet.classList.contains("is-open") &&
            !configTabPanels.get("tilings")?.hidden &&
            !tilingSearchInput.disabled
        ) {
            tilingSearchInput.focus();
            tilingSearchInput.select();
        }
    }

    function openTilingsSheet(): void {
        openConfigSheet("tilings");
        focusTilingSearchIfOpen();
        // Reassert focus after the opening click and sheet layout settle. Some
        // browsers restore focus to the activating dock button at the end of
        // the click sequence, which leaves the visible search box inactive.
        window.requestAnimationFrame(focusTilingSearchIfOpen);
    }

    runButton.addEventListener("click", () => void runComparison());
    retryWallUpdateButton.addEventListener("click", () => void workspaceScheduler.retry());
    setupRunButton.addEventListener("click", () => {
        if (isFilmstripCurrent()) {
            statusLine.textContent = "The comparison is already up to date.";
            updateSummary();
            return;
        }
        void runFilmstrip();
    });
    heroOpenLabButton.addEventListener("click", openFocusedBoardInLab);
    heroForkButton.addEventListener("click", () => void forkFocusedBoardLive());
    heroBackButton.addEventListener("click", () => filmstripView?.focus(null));
    inspectorReplaceButton.addEventListener("click", () => {
        selectedBoardElement()
            ?.querySelector<HTMLButtonElement>(".compare-filmstrip-label")
            ?.click();
    });
    inspectorRemoveButton.addEventListener("click", () => {
        selectedBoardElement()
            ?.querySelector<HTMLButtonElement>(".compare-filmstrip-remove")
            ?.click();
    });
    copyRunButton.addEventListener("click", copyRunLink);
    configButton.addEventListener("click", () => {
        if (!workspaceLayout.closeSetup()) {
            openConfigSheet("setup");
        }
    });
    inspectorButton.addEventListener("click", () => {
        if (!workspaceLayout.closeInspector()) {
            workspaceLayout.openInspector();
        }
    });
    analysisButton.addEventListener("click", () => {
        if (!closeAnalysisOverlayIfOpen()) {
            openAnalysisOverlay();
        }
    });
    analysisCloseButton.addEventListener("click", closeAnalysisOverlayIfOpen);
    analysisBackdrop.addEventListener("click", closeAnalysisOverlayIfOpen);
    setupTilingsItem.addEventListener("click", openTilingsSheet);
    tilingsButton.addEventListener("click", openTilingsSheet);
    configSheetCloseButton.addEventListener("click", workspaceLayout.closeSetup);
    inspectorCloseButton.addEventListener("click", workspaceLayout.closeInspector);
    document.addEventListener("pointerdown", onDocumentPointerDown);
    window.addEventListener("hashchange", onHashChangeFocus);
    const onWallCapacityChange = (): void => {
        renderTilingChecklist();
        filmstripView?.refreshAddControl();
    };
    window.addEventListener("resize", onWallCapacityChange);

    return {
        element: root,
        activate(): void {
            void ensureRules();
            refreshPreview();
            highlightGeometry(null);
        },
        deactivate(): void {
            filmstripTransport.pause();
            disposeAllForkedBoards();
            closeAnalysisOverlayIfOpen();
            root.querySelector(".compare-action-menu[open]")?.removeAttribute("open");
        },
        applyRunConfig,
        runFeaturedDemo,
        runDefaultFilmstrip,
        reportRunLinkError(message: string): void {
            statusLine.textContent = message;
        },
        handleEscape(): boolean {
            if (filmstripView?.closeTilingPicker()) {
                return true;
            }
            const openMenu = root.querySelector(".compare-action-menu[open]");
            if (openMenu) {
                openMenu.removeAttribute("open");
                return true;
            }
            // Peel the analysis overlay before the config sheet / speaker view.
            if (closeAnalysisOverlayIfOpen()) {
                return true;
            }
            return false;
        },
        closeConfigIfOpen,
        exitFocusIfAny(): boolean {
            if (workspaceStore.getState().focusedBoard !== null && filmstripView) {
                filmstripView.focus(null);
                return true;
            }
            return false;
        },
        handlePlaybackKey(event: KeyboardEvent): boolean {
            // Only claim playback keys once a live filmstrip exists, so typing in
            // the config fields (and plain Space) behaves normally until then.
            // Controls and custom keyboard widgets own their focused keystrokes;
            // a component may also have claimed the key before it bubbles here.
            if (
                !workspaceStore.getState().results.filmstrip ||
                event.defaultPrevented ||
                isInteractiveShortcutTarget(event.target)
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
            disposed = true;
            storeRenderSubscriptions.forEach((unsubscribe) => unsubscribe());
            invalidateOperations();
            workspaceScheduler.dispose();
            workspaceLayout.dispose();
            document.removeEventListener("pointerdown", onDocumentPointerDown);
            window.removeEventListener("hashchange", onHashChangeFocus);
            window.removeEventListener("resize", onWallCapacityChange);
            disposeAllForkedBoards();
            seedPad.dispose();
            seedPreview.dispose();
            filmstripView?.dispose();
        },
    };
}

function clampNumber(raw: string, low: number, high: number, fallback: number): number {
    const parsed = Number(raw);
    if (!Number.isFinite(parsed)) {
        return fallback;
    }
    return Math.min(high, Math.max(low, parsed));
}
