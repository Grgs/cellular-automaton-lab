import { createHttpSimulationBackend } from "../api.js";
import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_FILL,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
    EDITOR_TOOLS,
    clampBrushSize,
} from "../editor-tools.js";
import type { EditorTool } from "../editor-tools.js";
import type { SimulationBackend } from "../types/controller-api.js";
import type { GridView, ViewportDimensions } from "../types/controller-view.js";
import type {
    AppBootstrapData,
    BootstrappedTopologyDefinition,
    IndexedTopologyCell,
    SimulationSnapshot,
    TopologyIndex,
    TopologySpec,
} from "../types/domain.js";
import type { PaintableCell, PreviewPaintCell } from "../types/editor.js";
import type { AppState } from "../types/state.js";

const STORAGE_KEY = "cellular-automaton-lab.live-compare.v1";
const POLL_INTERVAL_MS = 250;

type PaneId = "left" | "right";

interface LiveCompareStorageState {
    initialized?: boolean;
}

export interface LiveCompareWorkspaceOptions {
    trigger: HTMLButtonElement | null;
    gridPanel: HTMLElement | null;
    bootstrapData: AppBootstrapData;
    baseSessionId?: string | null;
    mainBackend?: SimulationBackend;
    controls?: LiveCompareControlElements;
    onReturnToSingleView?: () => void | Promise<void>;
    backendFactory?: (sessionId: string) => SimulationBackend;
    createGridView?: (canvas: HTMLCanvasElement) => GridView;
    resolveViewportDimensions?: (
        options: LiveCompareViewportDimensionsOptions,
    ) => ViewportDimensions;
    resolveCellSize?: (options: LiveCompareCellSizeOptions) => number;
    buildEditorToolCells?: LiveCompareEditorCellsBuilder;
    storage?: Storage | null;
    onError?: (error: unknown) => void;
}

export interface LiveCompareViewportDimensionsOptions {
    viewportWidth: number;
    viewportHeight: number;
    geometry: string;
    cellSize: number;
    fallbackDimensions: ViewportDimensions;
}

export interface LiveCompareCellSizeOptions {
    viewportWidth: number;
    viewportHeight: number;
    width: number;
    height: number;
    topology: SimulationSnapshot["topology"];
    geometry: string;
    fallbackCellSize: number;
}

export type LiveCompareEditorCellsBuilder = (
    state: AppState,
    tool: string,
    startCell: PaintableCell,
    endCell: PaintableCell | null | undefined,
    paintState: number,
    brushSize: number,
) => PreviewPaintCell[];

export interface LiveCompareControlElements {
    statusText?: HTMLElement | null;
    generationText?: HTMLElement | null;
    runToggleBtn?: HTMLButtonElement | null;
    stepBtn?: HTMLButtonElement | null;
    resetBtn?: HTMLButtonElement | null;
    randomBtn?: HTMLButtonElement | null;
    tilingFamilySelect?: HTMLSelectElement | null;
    tilingPickerMenu?: HTMLElement | null;
    tilingPickerToggle?: HTMLButtonElement | null;
    tilingPickerCurrentLabel?: HTMLElement | null;
}

export interface LiveCompareWorkspaceHandle {
    dispose(): void;
    isOpen(): boolean;
}

interface PaneElements {
    root: HTMLElement;
    viewport: HTMLElement;
    canvas: HTMLCanvasElement;
    status: HTMLElement;
    generation: HTMLElement;
    tilingSelect: HTMLSelectElement;
    runButton: HTMLButtonElement;
    stepButton: HTMLButtonElement;
    resetButton: HTMLButtonElement;
}

interface PaneState {
    id: PaneId;
    title: string;
    sessionId: string;
    backend: SimulationBackend;
    gridView: GridView;
    elements: PaneElements;
    snapshot: SimulationSnapshot | null;
    pollTimer: number | null;
}

interface PaneEditGesture {
    pane: PaneState;
    tool: EditorTool;
    pointerId: number | null;
    startCell: PaintableCell;
    currentCell: PaintableCell;
    previewCells: Map<string, PreviewPaintCell>;
    moved: boolean;
}

function readStorage(storage: Storage | null | undefined): LiveCompareStorageState {
    if (!storage) {
        return {};
    }
    try {
        const raw = storage.getItem(STORAGE_KEY);
        return raw ? (JSON.parse(raw) as LiveCompareStorageState) : {};
    } catch {
        return {};
    }
}

function writeStorage(storage: Storage | null | undefined, state: LiveCompareStorageState): void {
    if (!storage) {
        return;
    }
    try {
        storage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
        // Persistence is best-effort; split view still works for the session.
    }
}

function element<K extends keyof HTMLElementTagNameMap>(
    tag: K,
    className = "",
    text = "",
): HTMLElementTagNameMap[K] {
    const node = document.createElement(tag);
    if (className) {
        node.className = className;
    }
    if (text) {
        node.textContent = text;
    }
    return node;
}

function validSessionIdPart(value: string): string {
    return value.replace(/[^A-Za-z0-9_-]/g, "-").slice(0, 68) || "split";
}

function paneSessionId(baseSessionId: string, paneId: PaneId): string {
    return `${validSessionIdPart(baseSessionId)}-${paneId}`;
}

function topologyGeometry(definition: BootstrappedTopologyDefinition): string {
    return definition.geometry_keys[definition.default_adjacency_mode] || definition.tiling_family;
}

function geometryForSpec(
    definitions: readonly BootstrappedTopologyDefinition[],
    spec: TopologySpec,
): string {
    const definition = definitions.find(
        (candidate) => candidate.tiling_family === spec.tiling_family,
    );
    return definition?.geometry_keys[spec.adjacency_mode] ?? spec.tiling_family;
}

function resetSpecForTopology(
    definition: BootstrappedTopologyDefinition,
    defaults: AppBootstrapData["app_defaults"]["simulation"],
    dimensions?: ViewportDimensions | null,
): TopologySpec {
    const defaultSpec = defaults.topology_spec;
    return {
        ...defaultSpec,
        tiling_family: definition.tiling_family,
        adjacency_mode: definition.default_adjacency_mode,
        sizing_mode: definition.sizing_mode,
        ...(dimensions ? { width: dimensions.width, height: dimensions.height } : {}),
        patch_depth:
            definition.sizing_policy.control === "patch_depth"
                ? definition.sizing_policy.default
                : defaultSpec.patch_depth,
    };
}

function defaultRuleForTopology(
    definition: BootstrappedTopologyDefinition,
    fallbackRule: string | null,
): string | null {
    return (
        definition.default_rules[definition.default_adjacency_mode] ??
        Object.values(definition.default_rules)[0] ??
        fallbackRule
    );
}

function preferredRightTopology(
    definitions: readonly BootstrappedTopologyDefinition[],
    left: BootstrappedTopologyDefinition,
): BootstrappedTopologyDefinition {
    return (
        definitions.find((definition) => definition.tiling_family === "hex") ??
        definitions.find((definition) => definition.tiling_family !== left.tiling_family) ??
        left
    );
}

function topologyLabel(
    definitions: readonly BootstrappedTopologyDefinition[],
    tilingFamily: string,
): string {
    return (
        definitions.find((definition) => definition.tiling_family === tilingFamily)?.label ??
        tilingFamily
    );
}

function createPaneElements(
    paneId: PaneId,
    title: string,
    definitions: readonly BootstrappedTopologyDefinition[],
): PaneElements {
    const root = element("section", "live-compare-pane");
    root.dataset.pane = paneId;
    root.setAttribute("aria-label", `${title} split view pane`);

    const header = element("header", "live-compare-pane-header");
    const titleNode = element("strong", "live-compare-pane-title", title);
    const status = element("span", "live-compare-pane-status", "Paused");
    const generation = element("span", "live-compare-pane-generation", "Gen 0");
    const meta = element("div", "live-compare-pane-meta");
    meta.append(status, generation);

    const tilingSelect = element("select", "live-compare-tiling-select");
    tilingSelect.setAttribute("aria-label", `${title} tiling`);
    for (const definition of definitions) {
        const option = document.createElement("option");
        option.value = definition.tiling_family;
        option.textContent = definition.label;
        tilingSelect.append(option);
    }

    const runButton = element("button", "live-compare-pane-action", "Run");
    runButton.type = "button";
    const stepButton = element("button", "live-compare-pane-action", "Step");
    stepButton.type = "button";
    const resetButton = element("button", "live-compare-pane-action", "Reset");
    resetButton.type = "button";
    const actions = element("div", "live-compare-pane-actions");
    actions.append(runButton, stepButton, resetButton);
    header.append(titleNode, meta, tilingSelect, actions);

    const viewport = element("div", "live-compare-pane-viewport");
    const canvas = element("canvas", "grid-canvas live-compare-canvas");
    canvas.setAttribute("aria-label", `${title} cellular automaton grid`);
    viewport.append(canvas);
    root.append(header, viewport);

    return {
        root,
        viewport,
        canvas,
        status,
        generation,
        tilingSelect,
        runButton,
        stepButton,
        resetButton,
    };
}

function paneEditorState(
    snapshot: SimulationSnapshot,
    renderCellSize: number,
    selectedEditorTool: EditorTool,
    brushSize: number,
    selectedPaintState: number,
): AppState {
    return {
        topology: snapshot.topology,
        topologyIndex: indexPaneTopology(snapshot),
        topologySpec: snapshot.topology_spec,
        width: snapshot.topology.width ?? snapshot.topology_spec.width,
        height: snapshot.topology.height ?? snapshot.topology_spec.height,
        cellStates: snapshot.cell_states,
        cellSize: renderCellSize,
        renderCellSize,
        activeRule: snapshot.rule,
        rules: [snapshot.rule],
        editorRuleName: snapshot.rule.name,
        ruleSelectionOrigin: "default",
        selectedEditorTool,
        brushSize,
        selectedPaintState,
        selectedPresetIdsByRule: {},
        undoStack: [],
        redoStack: [],
        pollTimer: null,
        isRunning: snapshot.running,
        generation: snapshot.generation,
        speed: snapshot.speed,
        measuredSpeed: null,
        measuredSpeedSample: null,
        patchDepth: snapshot.topology_spec.patch_depth,
        pendingPatchDepth: null,
        patchDepthByTilingFamily: {},
        unsafeSizingEnabled: false,
        tileColorsEnabled: true,
        topologyRevision: snapshot.topology_revision,
        previewTopology: null,
        previewTopologyRevision: null,
        previewCellStatesById: null,
        cellSizeByTilingFamily: {},
        drawerOpen: false,
        overlaysDismissed: false,
        inspectorTemporarilyHidden: false,
        overlayRunPending: false,
        runningOverlayRestoreActive: false,
        inspectorOccludesGrid: false,
        editArmed: true,
        editCueVisible: false,
        firstRunHintDismissed: true,
        blockingActivityKind: null,
        blockingActivityMessage: "",
        blockingActivityDetail: "",
        blockingActivityVisible: false,
        blockingActivityStartedAt: null,
        patternStatus: { message: "", tone: "" },
    };
}

function resolvePanePaintState(snapshot: SimulationSnapshot, selectedPaintState: number): number {
    const paintableStates = snapshot.rule.states.filter((state) => state.paintable !== false);
    if (paintableStates.some((state) => state.value === selectedPaintState)) {
        return selectedPaintState;
    }
    return (
        paintableStates.find((state) => state.value === snapshot.rule.default_paint_state)?.value ??
        paintableStates.find((state) => state.value !== 0)?.value ??
        paintableStates[0]?.value ??
        1
    );
}

function cssPixelValue(value: string): number {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : 0;
}

function fitCanvasElementToViewport(canvas: HTMLCanvasElement, viewport: HTMLElement): void {
    const canvasWidth = Number.parseFloat(canvas.style.width) || canvas.width;
    const canvasHeight = Number.parseFloat(canvas.style.height) || canvas.height;
    if (canvasWidth <= 0 || canvasHeight <= 0) {
        return;
    }
    const viewportStyle = window.getComputedStyle(viewport);
    const availableWidth = Math.max(
        1,
        viewport.clientWidth -
            cssPixelValue(viewportStyle.paddingLeft) -
            cssPixelValue(viewportStyle.paddingRight),
    );
    const availableHeight = Math.max(
        1,
        viewport.clientHeight -
            cssPixelValue(viewportStyle.paddingTop) -
            cssPixelValue(viewportStyle.paddingBottom),
    );
    const scale = Math.min(1, availableWidth / canvasWidth, availableHeight / canvasHeight);
    canvas.style.width = `${canvasWidth * scale}px`;
    canvas.style.height = `${canvasHeight * scale}px`;
}

function indexPaneTopology(snapshot: SimulationSnapshot): TopologyIndex {
    const byId = new Map<string, IndexedTopologyCell>();
    snapshot.topology.cells.forEach((cell, index) => {
        byId.set(cell.id, { ...cell, index });
    });
    return { byId };
}

function findPaneCellById(
    topologyIndex: TopologyIndex,
    cellId: string,
): IndexedTopologyCell | null {
    return topologyIndex.byId.get(cellId) ?? null;
}

function renderPane(
    pane: PaneState,
    bootstrapData: AppBootstrapData,
    definitions: readonly BootstrappedTopologyDefinition[],
    resolveCellSize: LiveCompareWorkspaceOptions["resolveCellSize"],
): void {
    const snapshot = pane.snapshot;
    if (!snapshot) {
        pane.elements.status.textContent = "Loading";
        pane.elements.generation.textContent = "Gen -";
        return;
    }
    const geometry = geometryForSpec(definitions, snapshot.topology_spec);
    const fallbackCellSize = bootstrapData.app_defaults.ui.cell_size;
    const viewportWidth = pane.elements.viewport.clientWidth;
    const viewportHeight = pane.elements.viewport.clientHeight;
    const cellSize =
        viewportWidth > 0 && viewportHeight > 0
            ? (resolveCellSize?.({
                  viewportWidth,
                  viewportHeight,
                  width: snapshot.topology.width ?? snapshot.topology_spec.width,
                  height: snapshot.topology.height ?? snapshot.topology_spec.height,
                  topology: snapshot.topology,
                  geometry,
                  fallbackCellSize,
              }) ?? fallbackCellSize)
            : fallbackCellSize;
    pane.gridView.render?.(
        {
            topology: snapshot.topology,
            cellStates: snapshot.cell_states,
            previewCellStatesById: null,
            tileColorsEnabled: true,
        },
        cellSize,
        snapshot.rule.states,
        geometry,
    );
    fitCanvasElementToViewport(pane.elements.canvas, pane.elements.viewport);
    pane.elements.status.textContent = snapshot.running ? "Running" : "Paused";
    pane.elements.generation.textContent = `Gen ${snapshot.generation}`;
    pane.elements.runButton.textContent = snapshot.running ? "Pause" : "Run";
    pane.elements.tilingSelect.value = snapshot.topology_spec.tiling_family;
    pane.elements.root.dataset.running = snapshot.running ? "true" : "false";
    pane.elements.root.dataset.tilingLabel = topologyLabel(
        definitions,
        snapshot.topology_spec.tiling_family,
    );
}

export function mountLiveCompareWorkspace({
    trigger,
    gridPanel,
    bootstrapData,
    baseSessionId,
    mainBackend,
    controls = {},
    onReturnToSingleView = () => {},
    backendFactory = (sessionId) => createHttpSimulationBackend({ sessionId }),
    createGridView = () => {
        throw new Error("Live compare requires a grid view factory.");
    },
    resolveViewportDimensions,
    storage = typeof window !== "undefined" ? window.localStorage : null,
    onError = (error) => console.error(error),
    resolveCellSize,
    buildEditorToolCells = (_state, _tool, startCell, _endCell, paintState) => [
        { ...startCell, state: paintState },
    ],
}: LiveCompareWorkspaceOptions): LiveCompareWorkspaceHandle {
    if (!trigger || !gridPanel) {
        return { dispose() {}, isOpen: () => false };
    }
    const triggerButton = trigger;
    const hostGridPanel = gridPanel;

    const definitions = [...bootstrapData.topology_catalog].sort(
        (left, right) => left.picker_order - right.picker_order,
    );
    const defaultTopology = definitions[0];
    if (!baseSessionId || !defaultTopology) {
        triggerButton.disabled = true;
        triggerButton.title = "Live split view requires independent server sessions.";
        return { dispose() {}, isOpen: () => false };
    }

    const root = element("section", "live-compare-workspace");
    root.hidden = true;
    root.setAttribute("aria-label", "Live split tiling comparison");
    const mainStage = hostGridPanel.closest(".main-stage");

    const toolbar = element("div", "live-compare-toolbar");
    const summary = element("span", "live-compare-summary", "Split View");
    const transportActions = element("div", "live-compare-toolbar-group");
    const runBoth = element("button", "live-compare-action", "Run Both");
    runBoth.type = "button";
    const pauseBoth = element("button", "live-compare-action", "Pause Both");
    pauseBoth.type = "button";
    const stepBoth = element("button", "live-compare-action", "Step Both");
    stepBoth.type = "button";
    transportActions.append(runBoth, pauseBoth, stepBoth);

    const editorTools = element("div", "live-compare-toolbar-group");
    const toolButtons = new Map<EditorTool, HTMLButtonElement>();
    for (const tool of EDITOR_TOOLS) {
        const button = element(
            "button",
            "live-compare-editor-tool",
            tool === EDITOR_TOOL_RECTANGLE ? "Rect" : tool.charAt(0).toUpperCase() + tool.slice(1),
        );
        button.type = "button";
        button.dataset.tool = tool;
        toolButtons.set(tool, button);
        editorTools.append(button);
    }
    const brushTools = element("div", "live-compare-toolbar-group");
    const brushButtons = new Map<number, HTMLButtonElement>();
    for (const size of [1, 2, 3]) {
        const button = element("button", "live-compare-editor-tool", `${size}`);
        button.type = "button";
        button.dataset.brushSize = String(size);
        button.setAttribute("aria-label", `Brush size ${size}`);
        brushButtons.set(size, button);
        brushTools.append(button);
    }
    const paintPalette = element("div", "live-compare-paint-palette");
    toolbar.append(summary, transportActions, editorTools, brushTools, paintPalette);

    const paneGrid = element("div", "live-compare-panes");
    root.append(toolbar, paneGrid);
    hostGridPanel.append(root);

    const paneDefinitions: Record<PaneId, BootstrappedTopologyDefinition> = {
        left: defaultTopology,
        right: preferredRightTopology(definitions, defaultTopology),
    };

    const panes: PaneState[] = (["left", "right"] as PaneId[]).map((paneId) => {
        const elements = createPaneElements(
            paneId,
            paneId === "left" ? "Left" : "Right",
            definitions,
        );
        paneGrid.append(elements.root);
        return {
            id: paneId,
            title: paneId === "left" ? "Left" : "Right",
            sessionId: paneSessionId(baseSessionId, paneId),
            backend: backendFactory(paneSessionId(baseSessionId, paneId)),
            gridView: createGridView(elements.canvas),
            elements,
            snapshot: null,
            pollTimer: null,
        };
    });

    let open = false;
    let disposed = false;
    let activePane: PaneState | null = null;
    let selectedEditorTool: EditorTool = DEFAULT_EDITOR_TOOL;
    let brushSize = DEFAULT_BRUSH_SIZE;
    let selectedPaintState = 1;
    let activeGesture: PaneEditGesture | null = null;
    let suppressFollowupClick = false;
    const cleanupCallbacks: Array<() => void> = [];
    const disabledControlState = new Map<
        HTMLButtonElement | HTMLSelectElement,
        { disabled: boolean; title: string }
    >();

    function setSplitDisabledControls(disabled: boolean): void {
        const targets = [
            controls.resetBtn,
            controls.randomBtn,
            controls.tilingPickerToggle,
            controls.tilingFamilySelect,
        ].filter((node): node is HTMLButtonElement | HTMLSelectElement => Boolean(node));
        for (const target of targets) {
            if (disabled) {
                if (!disabledControlState.has(target)) {
                    disabledControlState.set(target, {
                        disabled: target.disabled,
                        title: target.title,
                    });
                }
                target.disabled = true;
                target.title = "Use the split pane controls while Split View is open.";
            } else {
                const previous = disabledControlState.get(target);
                if (previous) {
                    target.disabled = previous.disabled;
                    target.title = previous.title;
                }
            }
        }
        if (!disabled) {
            disabledControlState.clear();
        }
        if (disabled && controls.tilingPickerMenu) {
            controls.tilingPickerMenu.hidden = true;
        }
        if (disabled) {
            controls.tilingPickerToggle?.setAttribute("aria-expanded", "false");
        }
    }

    function paneRunSummary(): string {
        const runningCount = panes.filter((pane) => pane.snapshot?.running).length;
        if (runningCount === panes.length) {
            return "Running";
        }
        if (runningCount === 0) {
            return "Paused";
        }
        return "Mixed";
    }

    function generationSummary(): string {
        const generations = panes.map((pane) => pane.snapshot?.generation ?? 0);
        if (generations.every((generation) => generation === generations[0])) {
            return String(generations[0] ?? 0);
        }
        return generations.join(" / ");
    }

    function renderEditorToolbar(): void {
        toolButtons.forEach((button, tool) => {
            button.classList.toggle("is-selected", tool === selectedEditorTool);
            button.setAttribute("aria-pressed", tool === selectedEditorTool ? "true" : "false");
        });
        brushButtons.forEach((button, size) => {
            button.classList.toggle("is-selected", size === brushSize);
            button.setAttribute("aria-pressed", size === brushSize ? "true" : "false");
        });
        const snapshot = activePane?.snapshot;
        paintPalette.replaceChildren();
        if (!snapshot) {
            return;
        }
        selectedPaintState = resolvePanePaintState(snapshot, selectedPaintState);
        for (const state of snapshot.rule.states.filter(
            (candidate) => candidate.paintable !== false,
        )) {
            const button = element("button", "live-compare-paint-state", state.label);
            button.type = "button";
            button.dataset.state = String(state.value);
            button.classList.toggle("is-selected", state.value === selectedPaintState);
            button.setAttribute(
                "aria-pressed",
                state.value === selectedPaintState ? "true" : "false",
            );
            const swatch = element("span", "live-compare-paint-swatch");
            swatch.style.background = state.color;
            button.prepend(swatch);
            button.addEventListener("click", () => {
                selectedPaintState = state.value;
                renderEditorToolbar();
            });
            paintPalette.append(button);
        }
    }

    function updateTopControls(): void {
        if (!open) {
            return;
        }
        if (controls.statusText) {
            controls.statusText.textContent = `Split: ${paneRunSummary()}`;
        }
        if (controls.generationText) {
            controls.generationText.textContent = generationSummary();
        }
        if (controls.runToggleBtn) {
            const anyRunning = panes.some((pane) => pane.snapshot?.running);
            controls.runToggleBtn.textContent = anyRunning ? "Pause" : "Run";
            controls.runToggleBtn.classList.toggle("is-running", anyRunning);
            controls.runToggleBtn.dataset.controlAction = anyRunning ? "pause" : "run";
            controls.runToggleBtn.setAttribute(
                "aria-label",
                `${anyRunning ? "Pause" : "Run"} both split panes`,
            );
        }
        summary.textContent = `Split View - ${paneRunSummary()}`;
        renderEditorToolbar();
    }

    function setActivePane(pane: PaneState): void {
        activePane = pane;
        panes.forEach((candidate) =>
            candidate.elements.root.classList.toggle("is-active", candidate === pane),
        );
        updateTopControls();
    }

    function clearPoll(pane: PaneState): void {
        if (pane.pollTimer !== null) {
            window.clearInterval(pane.pollTimer);
            pane.pollTimer = null;
        }
    }

    function syncPoll(pane: PaneState): void {
        if (disposed || !open || !pane.snapshot?.running) {
            clearPoll(pane);
            return;
        }
        if (pane.pollTimer !== null) {
            return;
        }
        pane.pollTimer = window.setInterval(() => {
            void refreshPane(pane);
        }, POLL_INTERVAL_MS);
    }

    async function applyPaneSnapshot(pane: PaneState, snapshot: SimulationSnapshot): Promise<void> {
        pane.snapshot = snapshot;
        renderPane(pane, bootstrapData, definitions, resolveCellSize);
        updateTopControls();
        syncPoll(pane);
    }

    async function refreshPane(pane: PaneState): Promise<void> {
        try {
            await applyPaneSnapshot(pane, await pane.backend.getState());
        } catch (error) {
            onError(error);
            clearPoll(pane);
        }
    }

    async function resetPaneToTopology(
        pane: PaneState,
        definition: BootstrappedTopologyDefinition,
        randomize = false,
    ): Promise<void> {
        const fallbackRule = pane.snapshot?.rule.name ?? bootstrapData.app_defaults.simulation.rule;
        const fallbackDimensions = {
            width: bootstrapData.app_defaults.simulation.topology_spec.width,
            height: bootstrapData.app_defaults.simulation.topology_spec.height,
        };
        const viewportWidth = pane.elements.viewport.clientWidth;
        const viewportHeight = pane.elements.viewport.clientHeight;
        const geometry = topologyGeometry(definition);
        const dimensions =
            definition.sizing_policy.control === "cell_size" &&
            viewportWidth > 0 &&
            viewportHeight > 0
                ? (resolveViewportDimensions?.({
                      viewportWidth,
                      viewportHeight,
                      geometry,
                      cellSize: definition.sizing_policy.default,
                      fallbackDimensions,
                  }) ?? fallbackDimensions)
                : fallbackDimensions;
        const snapshot = await pane.backend.postControl("/api/control/reset", {
            topology_spec: resetSpecForTopology(
                definition,
                bootstrapData.app_defaults.simulation,
                dimensions,
            ),
            speed: pane.snapshot?.speed ?? bootstrapData.app_defaults.simulation.speed,
            rule: defaultRuleForTopology(definition, fallbackRule),
            randomize,
        });
        await applyPaneSnapshot(pane, snapshot);
    }

    async function initializePaneSessions(): Promise<void> {
        const stored = readStorage(storage);
        if (!stored.initialized) {
            await Promise.all(
                panes.map((pane) => resetPaneToTopology(pane, paneDefinitions[pane.id])),
            );
            writeStorage(storage, { initialized: true });
            return;
        }
        await Promise.all(panes.map((pane) => refreshPane(pane)));
    }

    async function sendPaneRunToggle(pane: PaneState): Promise<void> {
        const snapshot = pane.snapshot ?? (await pane.backend.getState());
        if (snapshot.running) {
            await applyPaneSnapshot(pane, await pane.backend.postControl("/api/control/pause"));
            return;
        }
        const path = snapshot.generation > 0 ? "/api/control/resume" : "/api/control/start";
        await applyPaneSnapshot(pane, await pane.backend.postControl(path));
    }

    async function runAllPanes(): Promise<void> {
        await Promise.all(
            panes.map(async (pane) => {
                const snapshot = pane.snapshot ?? (await pane.backend.getState());
                if (!snapshot.running) {
                    await sendPaneRunToggle(pane);
                }
            }),
        );
    }

    async function pauseAllPanes(): Promise<void> {
        await Promise.all(
            panes.map(async (pane) => {
                const snapshot = pane.snapshot ?? (await pane.backend.getState());
                if (snapshot.running) {
                    await applyPaneSnapshot(
                        pane,
                        await pane.backend.postControl("/api/control/pause"),
                    );
                }
            }),
        );
    }

    async function runToggleAllPanes(): Promise<void> {
        if (panes.some((pane) => pane.snapshot?.running)) {
            await pauseAllPanes();
            return;
        }
        await runAllPanes();
    }

    async function stepAllPanes(): Promise<void> {
        await Promise.all(
            panes.map((pane) =>
                pane.backend
                    .postControl("/api/control/step")
                    .then((snapshot) => applyPaneSnapshot(pane, snapshot)),
            ),
        );
    }

    function buildPaneToolCells(
        pane: PaneState,
        tool: EditorTool,
        startCell: PaintableCell,
        endCell: PaintableCell | null,
    ): PreviewPaintCell[] {
        const snapshot = pane.snapshot;
        if (!snapshot) {
            return [];
        }
        const geometry = geometryForSpec(definitions, snapshot.topology_spec);
        const state = paneEditorState(
            snapshot,
            bootstrapData.app_defaults.ui.cell_size,
            selectedEditorTool,
            brushSize,
            resolvePanePaintState(snapshot, selectedPaintState),
        );
        state.renderCellSize =
            resolveCellSize?.({
                viewportWidth: pane.elements.viewport.clientWidth,
                viewportHeight: pane.elements.viewport.clientHeight,
                width: snapshot.topology.width ?? snapshot.topology_spec.width,
                height: snapshot.topology.height ?? snapshot.topology_spec.height,
                topology: snapshot.topology,
                geometry,
                fallbackCellSize: bootstrapData.app_defaults.ui.cell_size,
            }) ?? bootstrapData.app_defaults.ui.cell_size;
        state.cellSize = state.renderCellSize;
        const paintState = resolvePanePaintState(snapshot, selectedPaintState);
        const cells = buildEditorToolCells(state, tool, startCell, endCell, paintState, brushSize);
        if (cells.length > 0 || (tool !== EDITOR_TOOL_BRUSH && tool !== EDITOR_TOOL_FILL)) {
            return cells;
        }
        return [{ ...startCell, state: paintState }];
    }

    async function commitPaneCells(pane: PaneState, cells: PreviewPaintCell[]): Promise<void> {
        setActivePane(pane);
        const snapshot = pane.snapshot ?? (await pane.backend.getState());
        const topologyIndex = indexPaneTopology(snapshot);
        const updates = cells.flatMap((cell) => {
            const resolved = findPaneCellById(topologyIndex, cell.id);
            if (!resolved) {
                return [];
            }
            const state = Number(cell.state);
            if (Number(snapshot.cell_states[resolved.index] ?? 0) === state) {
                return [];
            }
            return [{ id: resolved.id, state }];
        });
        if (updates.length === 0) {
            return;
        }
        const wasRunning = Boolean(pane.snapshot?.running);
        if (wasRunning) {
            await applyPaneSnapshot(pane, await pane.backend.postControl("/api/control/pause"));
        }
        await applyPaneSnapshot(pane, await pane.backend.setCells(updates));
        if (wasRunning) {
            await applyPaneSnapshot(pane, await pane.backend.postControl("/api/control/resume"));
        }
    }

    function previewPaneCells(pane: PaneState, cells: PreviewPaintCell[]): void {
        pane.gridView.setPreviewCells(cells);
        pane.gridView.setGestureOutline(cells, selectedPaintState === 0 ? "erase" : "paint");
    }

    function clearPanePreview(pane: PaneState): void {
        pane.gridView.clearPreview();
        pane.gridView.clearGestureOutline();
    }

    function suppressNextClick(): void {
        suppressFollowupClick = true;
        window.setTimeout(() => {
            suppressFollowupClick = false;
        }, 0);
    }

    function setOpen(nextOpen: boolean): void {
        if (open === nextOpen || disposed) {
            return;
        }
        open = nextOpen;
        root.hidden = !open;
        hostGridPanel.classList.toggle("is-live-compare", open);
        mainStage?.classList.toggle("is-live-compare", open);
        triggerButton.setAttribute("aria-pressed", open ? "true" : "false");
        triggerButton.textContent = open ? "Single View" : "Split View";
        if (open) {
            void mainBackend?.postControl("/api/control/pause").catch(onError);
            setSplitDisabledControls(true);
            setActivePane(activePane ?? panes[0]!);
            void initializePaneSessions()
                .then(() => updateTopControls())
                .catch(onError);
        } else {
            panes.forEach(clearPoll);
            setSplitDisabledControls(false);
            void Promise.resolve(onReturnToSingleView()).catch(onError);
        }
    }

    function handleTriggerClick(): void {
        setOpen(!open);
    }

    triggerButton.setAttribute("aria-pressed", "false");
    triggerButton.textContent = "Split View";
    triggerButton.addEventListener("click", handleTriggerClick);

    for (const pane of panes) {
        pane.elements.root.addEventListener("pointerdown", (event) => {
            setActivePane(pane);
            pane.elements.root.focus();
            event.stopPropagation();
        });
        pane.elements.canvas.addEventListener("pointerdown", (event) => {
            const cell = pane.gridView.getCellFromPointerEvent?.(event) ?? null;
            if (!cell) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            setActivePane(pane);
            const paintableCell = cell as PaintableCell;
            if (selectedEditorTool === EDITOR_TOOL_FILL) {
                const cells = buildPaneToolCells(
                    pane,
                    EDITOR_TOOL_FILL,
                    paintableCell,
                    paintableCell,
                );
                previewPaneCells(pane, cells);
                suppressNextClick();
                void commitPaneCells(pane, cells)
                    .then(() => clearPanePreview(pane))
                    .catch(onError);
                return;
            }
            const tool =
                selectedEditorTool === EDITOR_TOOL_LINE ||
                selectedEditorTool === EDITOR_TOOL_RECTANGLE
                    ? selectedEditorTool
                    : EDITOR_TOOL_BRUSH;
            const cells = buildPaneToolCells(pane, tool, paintableCell, paintableCell);
            activeGesture = {
                pane,
                tool,
                pointerId: event.pointerId ?? null,
                startCell: paintableCell,
                currentCell: paintableCell,
                previewCells: new Map(cells.map((previewCell) => [previewCell.id, previewCell])),
                moved: false,
            };
            previewPaneCells(pane, cells);
            pane.elements.canvas.setPointerCapture?.(event.pointerId);
        });
        pane.elements.canvas.addEventListener("pointermove", (event) => {
            if (!activeGesture || activeGesture.pane !== pane) {
                return;
            }
            const cell = pane.gridView.getCellFromPointerEvent?.(event) ?? null;
            if (!cell) {
                return;
            }
            event.preventDefault();
            const paintableCell = cell as PaintableCell;
            if (activeGesture.currentCell.id === paintableCell.id) {
                return;
            }
            activeGesture.moved = true;
            const cells =
                activeGesture.tool === EDITOR_TOOL_BRUSH
                    ? buildPaneToolCells(
                          pane,
                          EDITOR_TOOL_LINE,
                          activeGesture.currentCell,
                          paintableCell,
                      )
                    : buildPaneToolCells(
                          pane,
                          activeGesture.tool,
                          activeGesture.startCell,
                          paintableCell,
                      );
            if (activeGesture.tool === EDITOR_TOOL_BRUSH) {
                cells.forEach((previewCell) =>
                    activeGesture?.previewCells.set(previewCell.id, previewCell),
                );
            } else {
                activeGesture.previewCells = new Map(
                    cells.map((previewCell) => [previewCell.id, previewCell]),
                );
            }
            activeGesture.currentCell = paintableCell;
            previewPaneCells(pane, Array.from(activeGesture.previewCells.values()));
        });
        pane.elements.canvas.addEventListener("pointerup", (event) => {
            if (!activeGesture || activeGesture.pane !== pane) {
                return;
            }
            event.preventDefault();
            pane.elements.canvas.releasePointerCapture?.(event.pointerId);
            const cells = Array.from(activeGesture.previewCells.values());
            activeGesture = null;
            suppressNextClick();
            void commitPaneCells(pane, cells)
                .then(() => clearPanePreview(pane))
                .catch(onError);
        });
        pane.elements.canvas.addEventListener("click", (event) => {
            if (suppressFollowupClick || activeGesture) {
                return;
            }
            const cell = pane.gridView.getCellFromPointerEvent?.(event) ?? null;
            if (!cell) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            setActivePane(pane);
            const paintableCell = cell as PaintableCell;
            const tool =
                selectedEditorTool === EDITOR_TOOL_FILL ? EDITOR_TOOL_FILL : EDITOR_TOOL_BRUSH;
            const cells = buildPaneToolCells(pane, tool, paintableCell, paintableCell);
            previewPaneCells(pane, cells);
            void commitPaneCells(pane, cells)
                .then(() => clearPanePreview(pane))
                .catch(onError);
        });
        pane.elements.canvas.addEventListener("pointercancel", () => {
            if (!activeGesture || activeGesture.pane !== pane) {
                return;
            }
            activeGesture = null;
            clearPanePreview(pane);
        });
        pane.elements.tilingSelect.addEventListener("change", () => {
            setActivePane(pane);
            const definition = definitions.find(
                (candidate) => candidate.tiling_family === pane.elements.tilingSelect.value,
            );
            if (definition) {
                void resetPaneToTopology(pane, definition).catch(onError);
            }
        });
        pane.elements.runButton.addEventListener("click", () => {
            setActivePane(pane);
            void sendPaneRunToggle(pane).catch(onError);
        });
        pane.elements.stepButton.addEventListener("click", () => {
            setActivePane(pane);
            void pane.backend
                .postControl("/api/control/step")
                .then((snapshot) => applyPaneSnapshot(pane, snapshot))
                .catch(onError);
        });
        pane.elements.resetButton.addEventListener("click", () => {
            setActivePane(pane);
            const definition =
                definitions.find(
                    (candidate) => candidate.tiling_family === pane.elements.tilingSelect.value,
                ) ?? paneDefinitions[pane.id];
            void resetPaneToTopology(pane, definition).catch(onError);
        });
    }

    function interceptClick(
        button: HTMLButtonElement | null | undefined,
        action: () => Promise<void>,
    ): void {
        if (!button) {
            return;
        }
        const listener = (event: MouseEvent) => {
            if (!open) {
                return;
            }
            event.preventDefault();
            event.stopImmediatePropagation();
            void action().catch(onError);
        };
        button.addEventListener("click", listener, { capture: true });
        cleanupCallbacks.push(() =>
            button.removeEventListener("click", listener, { capture: true }),
        );
    }

    interceptClick(controls.runToggleBtn, runToggleAllPanes);
    interceptClick(controls.stepBtn, stepAllPanes);

    runBoth.addEventListener("click", () => {
        void runAllPanes().catch(onError);
    });
    pauseBoth.addEventListener("click", () => {
        void pauseAllPanes().catch(onError);
    });
    stepBoth.addEventListener("click", () => {
        void stepAllPanes().catch(onError);
    });

    toolButtons.forEach((button, tool) => {
        button.addEventListener("click", () => {
            selectedEditorTool = tool;
            renderEditorToolbar();
        });
    });
    brushButtons.forEach((button, size) => {
        button.addEventListener("click", () => {
            brushSize = clampBrushSize(size);
            renderEditorToolbar();
        });
    });

    function handleResize(): void {
        if (open) {
            panes.forEach((pane) => renderPane(pane, bootstrapData, definitions, resolveCellSize));
        }
    }

    window.addEventListener("resize", handleResize);

    return {
        dispose(): void {
            disposed = true;
            panes.forEach((pane) => {
                clearPoll(pane);
                void Promise.resolve(pane.backend.dispose()).catch(onError);
            });
            root.remove();
            hostGridPanel.classList.remove("is-live-compare");
            mainStage?.classList.remove("is-live-compare");
            setSplitDisabledControls(false);
            window.removeEventListener("resize", handleResize);
            triggerButton.removeEventListener("click", handleTriggerClick);
            cleanupCallbacks.forEach((cleanup) => cleanup());
            triggerButton.setAttribute("aria-pressed", "false");
            triggerButton.textContent = "Split View";
        },
        isOpen: () => open,
    };
}

export const liveCompareInternals = {
    paneSessionId,
    resetSpecForTopology,
    topologyGeometry,
    geometryForSpec,
};
