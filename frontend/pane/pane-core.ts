/**
 * A reusable single editable board pane: one canvas backed by one independent
 * simulation session, with pointer painting, run/step controls, and snapshot
 * polling. It is the shared machinery behind the Split View panes and the
 * wall's live focus pane, so both drive their boards through the same code.
 *
 * The pane owns rendering, gestures, and polling; the consumer owns the tool
 * state (via getters), the DOM chrome around the canvas, and the backend's
 * lifecycle. `seedFromPattern` reconstructs a board from a `PatternPayload`
 * (topology spec + rule + sparse cells) using only existing session endpoints —
 * no backend changes.
 */

import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_FILL,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
    type EditorTool,
} from "../editor-tools.js";
import type { SimulationBackend } from "../types/controller-api.js";
import type { GridView, ViewportDimensions } from "../types/controller-view.js";
import type {
    AppBootstrapData,
    BootstrappedTopologyDefinition,
    IndexedTopologyCell,
    PatternPayload,
    SimulationSnapshot,
    TopologyIndex,
    TopologySpec,
} from "../types/domain.js";
import type { PaintableCell, PreviewPaintCell } from "../types/editor.js";
import type { AppState } from "../types/state.js";

const POLL_INTERVAL_MS = 250;

export interface PaneViewportDimensionsOptions {
    viewportWidth: number;
    viewportHeight: number;
    geometry: string;
    cellSize: number;
    fallbackDimensions: ViewportDimensions;
    maxCellCount?: number;
}

export interface PaneCellSizeOptions {
    viewportWidth: number;
    viewportHeight: number;
    width: number;
    height: number;
    topology: SimulationSnapshot["topology"];
    geometry: string;
    fallbackCellSize: number;
}

export type PaneEditorCellsBuilder = (
    state: AppState,
    tool: string,
    startCell: PaintableCell,
    endCell: PaintableCell | null | undefined,
    paintState: number,
    brushSize: number,
) => PreviewPaintCell[];

export interface PaneEditGesture {
    tool: EditorTool;
    pointerId: number | null;
    startCell: PaintableCell;
    currentCell: PaintableCell;
    previewCells: Map<string, PreviewPaintCell>;
    moved: boolean;
}

export function element<K extends keyof HTMLElementTagNameMap>(
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

/** A stable, session-id-safe suffix so a base session can spawn named children. */
export function paneSessionId(baseSessionId: string, paneId: string): string {
    return `${validSessionIdPart(baseSessionId)}-${validSessionIdPart(paneId)}`;
}

export function geometryForSpec(
    definitions: readonly BootstrappedTopologyDefinition[],
    spec: TopologySpec,
): string {
    const definition = definitions.find(
        (candidate) => candidate.tiling_family === spec.tiling_family,
    );
    return definition?.geometry_keys[spec.adjacency_mode] ?? spec.tiling_family;
}

function cssPixelValue(value: string): number {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : 0;
}

export function fitCanvasElementToViewport(canvas: HTMLCanvasElement, viewport: HTMLElement): void {
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

export function indexPaneTopology(snapshot: SimulationSnapshot): TopologyIndex {
    const byId = new Map<string, IndexedTopologyCell>();
    snapshot.topology.cells.forEach((cell, index) => {
        byId.set(cell.id, { ...cell, index });
    });
    return { byId };
}

export function findPaneCellById(
    topologyIndex: TopologyIndex,
    cellId: string,
): IndexedTopologyCell | null {
    return topologyIndex.byId.get(cellId) ?? null;
}

export function resolvePanePaintState(
    snapshot: SimulationSnapshot,
    selectedPaintState: number,
): number {
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

export function paneEditorState(
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

/**
 * The app-runtime-owned seams the wall needs to spin up a live focus pane: an
 * independent backend session, a canvas grid view, and the editor geometry
 * helpers. `baseSessionId` is null when no host session exists at all, which
 * the wall reads as "fork into the Lab instead". Both hosts that do provide
 * one differ in cost: a server fork is just another lightweight backend
 * session, but a standalone fork boots its own persist-free Pyodide runtime
 * from scratch, so `forkCapacity` caps how many can run at once there.
 */
export interface FocusPaneServices {
    baseSessionId: string | null;
    backendFactory: (sessionId: string) => SimulationBackend;
    createGridView: (canvas: HTMLCanvasElement) => GridView;
    buildEditorToolCells: PaneEditorCellsBuilder;
    resolveCellSize?: (options: PaneCellSizeOptions) => number;
    resolveViewportDimensions?: (options: PaneViewportDimensionsOptions) => ViewportDimensions;
    /** Maximum concurrent live forks; undefined means unlimited. */
    forkCapacity?: number;
}

export interface EditablePaneOptions {
    canvas: HTMLCanvasElement;
    viewport: HTMLElement;
    backend: SimulationBackend;
    gridView: GridView;
    bootstrapData: AppBootstrapData;
    definitions: readonly BootstrappedTopologyDefinition[];
    getTool?: () => EditorTool;
    getBrushSize?: () => number;
    getPaintState: () => number;
    setPaintState?: (state: number) => void;
    resolveCellSize?: (options: PaneCellSizeOptions) => number;
    buildEditorToolCells?: PaneEditorCellsBuilder;
    /** Fired after every applied snapshot so the consumer can update its chrome. */
    onSnapshot?: (snapshot: SimulationSnapshot) => void;
    onError?: (error: unknown) => void;
}

export interface EditablePaneHandle {
    getSnapshot(): SimulationSnapshot | null;
    applySnapshot(snapshot: SimulationSnapshot): void;
    refresh(): Promise<void>;
    render(): void;
    /** Reconstruct the board from a pattern (topology spec + rule + sparse cells). */
    seedFromPattern(pattern: PatternPayload, speed: number): Promise<void>;
    /**
     * Apply one cell edit directly (no pointer, no preview gesture) — for
     * carrying a paint stroke over into a board that was just programmatically
     * seeded, e.g. an auto-fork triggered by that same stroke.
     */
    applyCellEdit(cellId: string, state: number): Promise<void>;
    step(): Promise<void>;
    runToggle(): Promise<void>;
    dispose(): void;
}

export function createEditablePane(options: EditablePaneOptions): EditablePaneHandle {
    const {
        canvas,
        viewport,
        backend,
        gridView,
        bootstrapData,
        definitions,
        getPaintState,
        resolveCellSize,
        onSnapshot,
        onError = (error) => console.error(error),
    } = options;
    const getTool = options.getTool ?? (() => DEFAULT_EDITOR_TOOL);
    const getBrushSize = options.getBrushSize ?? (() => DEFAULT_BRUSH_SIZE);
    const buildEditorToolCells =
        options.buildEditorToolCells ??
        ((_state, _tool, startCell, _endCell, paintState) => [{ ...startCell, state: paintState }]);
    const fallbackCellSize = bootstrapData.app_defaults.ui.cell_size;
    const controller = new AbortController();
    const { signal } = controller;

    let snapshot: SimulationSnapshot | null = null;
    let pollTimer: number | null = null;
    let activeGesture: PaneEditGesture | null = null;
    let suppressFollowupClick = false;
    let disposed = false;

    function clearPoll(): void {
        if (pollTimer !== null) {
            window.clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function syncPoll(): void {
        if (disposed || !snapshot?.running) {
            clearPoll();
            return;
        }
        if (pollTimer !== null) {
            return;
        }
        pollTimer = window.setInterval(() => {
            void refresh();
        }, POLL_INTERVAL_MS);
    }

    function render(): void {
        if (!snapshot) {
            return;
        }
        const geometry = geometryForSpec(definitions, snapshot.topology_spec);
        const viewportWidth = viewport.clientWidth;
        const viewportHeight = viewport.clientHeight;
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
        gridView.render?.(
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
        fitCanvasElementToViewport(canvas, viewport);
    }

    function applySnapshot(next: SimulationSnapshot): void {
        snapshot = next;
        render();
        onSnapshot?.(next);
        syncPoll();
    }

    async function refresh(): Promise<void> {
        try {
            applySnapshot(await backend.getState());
        } catch (error) {
            onError(error);
            clearPoll();
        }
    }

    function buildToolCells(
        tool: EditorTool,
        startCell: PaintableCell,
        endCell: PaintableCell | null,
    ): PreviewPaintCell[] {
        if (!snapshot) {
            return [];
        }
        const geometry = geometryForSpec(definitions, snapshot.topology_spec);
        const paintState = resolvePanePaintState(snapshot, getPaintState());
        const state = paneEditorState(snapshot, fallbackCellSize, tool, getBrushSize(), paintState);
        state.renderCellSize =
            resolveCellSize?.({
                viewportWidth: viewport.clientWidth,
                viewportHeight: viewport.clientHeight,
                width: snapshot.topology.width ?? snapshot.topology_spec.width,
                height: snapshot.topology.height ?? snapshot.topology_spec.height,
                topology: snapshot.topology,
                geometry,
                fallbackCellSize,
            }) ?? fallbackCellSize;
        state.cellSize = state.renderCellSize;
        const cells = buildEditorToolCells(
            state,
            tool,
            startCell,
            endCell,
            paintState,
            getBrushSize(),
        );
        if (cells.length > 0 || (tool !== EDITOR_TOOL_BRUSH && tool !== EDITOR_TOOL_FILL)) {
            return cells;
        }
        return [{ ...startCell, state: paintState }];
    }

    function previewCells(cells: PreviewPaintCell[]): void {
        gridView.setPreviewCells(cells);
        gridView.setGestureOutline(
            cells,
            resolvePanePaintState(snapshot!, getPaintState()) === 0 ? "erase" : "paint",
        );
    }

    function clearPreview(): void {
        gridView.clearPreview();
        gridView.clearGestureOutline();
    }

    async function commitCells(cells: PreviewPaintCell[]): Promise<void> {
        const current = snapshot ?? (await backend.getState());
        const topologyIndex = indexPaneTopology(current);
        const updates = cells.flatMap((cell) => {
            const resolved = findPaneCellById(topologyIndex, cell.id);
            if (!resolved) {
                return [];
            }
            const state = Number(cell.state);
            if (Number(current.cell_states[resolved.index] ?? 0) === state) {
                return [];
            }
            return [{ id: resolved.id, state }];
        });
        if (updates.length === 0) {
            return;
        }
        const wasRunning = Boolean(snapshot?.running);
        if (wasRunning) {
            applySnapshot(await backend.postControl("/api/control/pause"));
        }
        applySnapshot(await backend.setCells(updates));
        if (wasRunning) {
            applySnapshot(await backend.postControl("/api/control/resume"));
        }
    }

    function suppressNextClick(): void {
        suppressFollowupClick = true;
        window.setTimeout(() => {
            suppressFollowupClick = false;
        }, 0);
    }

    canvas.addEventListener(
        "pointerdown",
        (event) => {
            const cell = gridView.getCellFromPointerEvent?.(event) ?? null;
            if (!cell) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            const paintableCell = cell as PaintableCell;
            const selectedTool = getTool();
            if (selectedTool === EDITOR_TOOL_FILL) {
                const cells = buildToolCells(EDITOR_TOOL_FILL, paintableCell, paintableCell);
                previewCells(cells);
                suppressNextClick();
                void commitCells(cells)
                    .then(() => clearPreview())
                    .catch(onError);
                return;
            }
            const tool =
                selectedTool === EDITOR_TOOL_LINE || selectedTool === EDITOR_TOOL_RECTANGLE
                    ? selectedTool
                    : EDITOR_TOOL_BRUSH;
            const cells = buildToolCells(tool, paintableCell, paintableCell);
            activeGesture = {
                tool,
                pointerId: event.pointerId ?? null,
                startCell: paintableCell,
                currentCell: paintableCell,
                previewCells: new Map(cells.map((previewCell) => [previewCell.id, previewCell])),
                moved: false,
            };
            previewCells(cells);
            canvas.setPointerCapture?.(event.pointerId);
        },
        { signal },
    );
    canvas.addEventListener(
        "pointermove",
        (event) => {
            if (!activeGesture) {
                return;
            }
            const cell = gridView.getCellFromPointerEvent?.(event) ?? null;
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
                    ? buildToolCells(EDITOR_TOOL_LINE, activeGesture.currentCell, paintableCell)
                    : buildToolCells(activeGesture.tool, activeGesture.startCell, paintableCell);
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
            previewCells(Array.from(activeGesture.previewCells.values()));
        },
        { signal },
    );
    canvas.addEventListener(
        "pointerup",
        (event) => {
            if (!activeGesture) {
                return;
            }
            event.preventDefault();
            canvas.releasePointerCapture?.(event.pointerId);
            const cells = Array.from(activeGesture.previewCells.values());
            activeGesture = null;
            suppressNextClick();
            void commitCells(cells)
                .then(() => clearPreview())
                .catch(onError);
        },
        { signal },
    );
    canvas.addEventListener(
        "click",
        (event) => {
            if (suppressFollowupClick || activeGesture) {
                return;
            }
            const cell = gridView.getCellFromPointerEvent?.(event) ?? null;
            if (!cell) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            const paintableCell = cell as PaintableCell;
            const tool = getTool() === EDITOR_TOOL_FILL ? EDITOR_TOOL_FILL : EDITOR_TOOL_BRUSH;
            const cells = buildToolCells(tool, paintableCell, paintableCell);
            previewCells(cells);
            void commitCells(cells)
                .then(() => clearPreview())
                .catch(onError);
        },
        { signal },
    );
    canvas.addEventListener(
        "pointercancel",
        () => {
            if (!activeGesture) {
                return;
            }
            activeGesture = null;
            clearPreview();
        },
        { signal },
    );

    return {
        getSnapshot: () => snapshot,
        applySnapshot,
        refresh,
        render,
        async seedFromPattern(pattern: PatternPayload, speed: number): Promise<void> {
            const reset = await backend.postControl("/api/control/reset", {
                topology_spec: pattern.topology_spec,
                speed,
                rule: pattern.rule,
                randomize: false,
            });
            const updates = Object.entries(pattern.cells_by_id).map(([id, state]) => ({
                id,
                state: Number(state),
            }));
            applySnapshot(updates.length > 0 ? await backend.setCells(updates) : reset);
        },
        applyCellEdit(cellId: string, state: number): Promise<void> {
            return commitCells([{ id: cellId, state }]);
        },
        async step(): Promise<void> {
            applySnapshot(await backend.postControl("/api/control/step"));
        },
        async runToggle(): Promise<void> {
            const current = snapshot ?? (await backend.getState());
            if (current.running) {
                applySnapshot(await backend.postControl("/api/control/pause"));
                return;
            }
            const path = current.generation > 0 ? "/api/control/resume" : "/api/control/start";
            applySnapshot(await backend.postControl(path));
        },
        dispose(): void {
            disposed = true;
            clearPoll();
            controller.abort();
            clearPreview();
        },
    };
}
