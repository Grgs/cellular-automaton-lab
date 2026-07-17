/**
 * Composition root for a reusable editable board pane. Session state,
 * rendering, pointer gestures, and edit history live in focused modules; this
 * file keeps the stable public API shared by Split View and Compare focus.
 */

import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_FILL,
    type EditorTool,
} from "../editor-tools.js";
import { indexTopology } from "../topology-index.js";
import type { SimulationBackend } from "../types/controller-api.js";
import type { GridView, ViewportDimensions } from "../types/controller-view.js";
import type {
    AppBootstrapData,
    BootstrappedTopologyDefinition,
    IndexedTopologyCell,
    PatternPayload,
    SimulationSnapshot,
    TopologyIndex,
} from "../types/domain.js";
import type { PaintableCell, PreviewPaintCell } from "../types/editor.js";
import type { AppState } from "../types/state.js";
import { createPaneEditHistory } from "./pane-edit-history.js";
import { createPaneGestureController } from "./pane-gestures.js";
import {
    createPaneRenderer,
    fitCanvasElementToViewport,
    geometryForSpec,
    type PaneCellSizeOptions,
    type PaneViewportDimensionsOptions,
} from "./pane-renderer.js";
import { createPaneSession } from "./pane-session.js";

export { fitCanvasElementToViewport, geometryForSpec } from "./pane-renderer.js";
export type { PaneCellSizeOptions, PaneViewportDimensionsOptions } from "./pane-renderer.js";
export type { PaneEditGesture } from "./pane-gestures.js";

export type PaneEditorCellsBuilder = (
    state: AppState,
    tool: string,
    startCell: PaintableCell,
    endCell: PaintableCell | null | undefined,
    paintState: number,
    brushSize: number,
) => PreviewPaintCell[];

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

export function indexPaneTopology(snapshot: SimulationSnapshot): TopologyIndex {
    return indexTopology(snapshot.topology);
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
        stateRevision: snapshot.state_revision,
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
    onSnapshot?: (snapshot: SimulationSnapshot) => void;
    onError?: (error: unknown) => void;
}

export interface EditablePaneHandle {
    getSnapshot(): SimulationSnapshot | null;
    applySnapshot(snapshot: SimulationSnapshot): void;
    refresh(): Promise<void>;
    render(): void;
    seedFromPattern(pattern: PatternPayload, speed: number): Promise<void>;
    applyCellEdit(cellId: string, state: number): Promise<void>;
    undo(): Promise<void>;
    redo(): Promise<void>;
    canUndo(): boolean;
    canRedo(): boolean;
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
    const renderer = createPaneRenderer({
        canvas,
        viewport,
        gridView,
        definitions,
        fallbackCellSize,
        resolveCellSize,
    });
    const session = createPaneSession({
        backend,
        onError,
        onSnapshot: (snapshot) => {
            renderer.render(snapshot);
            onSnapshot?.(snapshot);
        },
    });
    const history = createPaneEditHistory(session);

    function buildToolCells(
        tool: EditorTool,
        startCell: PaintableCell,
        endCell: PaintableCell | null,
    ): PreviewPaintCell[] {
        const snapshot = session.getSnapshot();
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
        const snapshot = session.getSnapshot();
        if (snapshot) {
            gridView.setGestureOutline(
                cells,
                resolvePanePaintState(snapshot, getPaintState()) === 0 ? "erase" : "paint",
            );
        }
    }

    function clearPreview(): void {
        gridView.clearPreview();
        gridView.clearGestureOutline();
    }

    const gestures = createPaneGestureController({
        canvas,
        gridView,
        getTool,
        buildToolCells,
        previewCells,
        clearPreview,
        commitCells: history.commit,
        onError,
    });
    session.registerCleanup(gestures.dispose);

    return {
        getSnapshot: session.getSnapshot,
        applySnapshot: session.applySnapshot,
        refresh: session.refresh,
        render: () => renderer.render(session.getSnapshot()),
        seedFromPattern: (pattern, speed) => session.seedFromPattern(pattern, speed, history.clear),
        applyCellEdit: (cellId, state) => history.commit([{ id: cellId, state }]),
        canUndo: history.canUndo,
        canRedo: history.canRedo,
        undo: history.undo,
        redo: history.redo,
        step: session.step,
        runToggle: session.runToggle,
        dispose: session.dispose,
    };
}
