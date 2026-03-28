import type {
    MutationRunner,
    MutationRunnerOptions,
    PostControlFunction,
    SetCellRequestFunction,
    SetCellsRequestFunction,
    SetCellsRequestFunction as SetCellsFn,
    ToggleCellRequestFunction,
} from "./controller.js";
import type { CellIdentifier, CellStateUpdate, SimulationSnapshot, TopologyCell } from "./domain.js";
import type { AppState } from "./state.js";

export interface CoordinateCell {
    x: number;
    y: number;
}

export interface PaintableCell extends CellIdentifier {
    x?: number;
    y?: number;
    kind?: string;
    state?: number;
}

export interface IndexedTopologyPaintableCell extends TopologyCell {
    index: number;
    neighbors?: string[];
    kind?: string;
    x?: number;
    y?: number;
}

export interface PreviewPaintCell extends PaintableCell {
    state: number;
}

export interface DragPaintResult {
    changed: boolean;
    previewCells: PreviewPaintCell[];
}

export interface DragPaintCommit {
    moved: boolean;
    pointerId: number | null;
    paintedCells: PreviewPaintCell[];
}

export interface DragPaintSession {
    start(cell: PaintableCell, paintState?: number, pointerId?: number | null): void;
    update(cell: PaintableCell): DragPaintResult;
    end(): DragPaintCommit | null;
    getPreviewCells(): PreviewPaintCell[];
}

export interface EditorHistoryEntry {
    forwardCells: CellStateUpdate[];
    inverseCells: CellStateUpdate[];
}

export interface EditorHistoryCommands {
    undo(): Promise<SimulationSnapshot | null>;
    redo(): Promise<SimulationSnapshot | null>;
}

export interface EditorSessionPointerContext {
    pointerId: number | null;
}

export interface EditorSessionController {
    supportsEditorTools(): boolean;
    currentTool(): string;
    beginPointerSession(cell: PaintableCell, pointerId?: number | null): Promise<boolean>;
    handlePointerMove(cell: PaintableCell): void;
    handlePointerUp(): Promise<SimulationSnapshot | null>;
    handleClick(cell: PaintableCell): Promise<{ handled: boolean }>;
    cancelActivePreview(): Promise<void>;
    enableClickSuppression(): void;
    isClickSuppressed(): boolean;
    isPointerActive(): boolean;
}

export interface LegacyDragController {
    begin(cell: PaintableCell, pointerId?: number | null): void;
    update(cell: PaintableCell): void;
    end(): Promise<SimulationSnapshot | null>;
    isActive(): boolean;
    currentPointerId(): number | null;
}

export interface GridInteractionBindings {
    surfaceElement: HTMLElement | null;
    resolveCellFromEvent: (event: PointerEvent | MouseEvent) => PaintableCell | null;
    onPointerDown(event: PointerEvent, cell: PaintableCell): void;
    onPointerMove(event: PointerEvent, cell: PaintableCell): void;
    onPointerUp(event: PointerEvent): void;
    onPointerCancel(event: PointerEvent): void;
    onClick(event: MouseEvent, cell: PaintableCell): void;
}

export interface EditorSessionOptions {
    state: AppState | null;
    getPaintState: () => number;
    getEditorTool?: () => string;
    getBrushSize?: () => number;
    previewPaintCells: (cells: PreviewPaintCell[]) => void;
    clearPreview: () => void;
    setCellsRequest: SetCellsRequestFunction;
    postControl: PostControlFunction;
    renderControlPanel?: () => void;
    setPointerCapture: (pointerId: number | null) => void;
    releasePointerCapture: (pointerId: number | null) => void;
    runStateMutation: (
        task: () => Promise<SimulationSnapshot>,
        options?: MutationRunnerOptions & { recoverWithRefresh?: boolean; source?: string },
    ) => Promise<SimulationSnapshot>;
}

export interface HistoryCommandsOptions {
    state: AppState;
    setCellsRequest: SetCellsFn;
    renderControlPanel?: () => void;
    supportsEditorTools?: () => boolean;
    runStateMutation: (
        task: () => Promise<SimulationSnapshot>,
        options?: MutationRunnerOptions & { recoverWithRefresh?: boolean; source?: string },
    ) => Promise<SimulationSnapshot>;
}

export interface LegacyDragOptions {
    getPaintState: () => number;
    previewPaintCells: (cells: PreviewPaintCell[]) => void;
    clearPreview: () => void;
    setCellsRequest: SetCellsRequestFunction;
    runStateMutation: (
        task: () => Promise<SimulationSnapshot>,
        options?: MutationRunnerOptions & { recoverWithRefresh?: boolean; source?: string },
    ) => Promise<SimulationSnapshot>;
    setPointerCapture: (pointerId: number | null) => void;
    releasePointerCapture: (pointerId: number | null) => void;
    enableClickSuppression: () => void;
}

export interface InteractionControllerOptions {
    surfaceElement: HTMLElement | null;
    state?: AppState | null;
    resolveCellFromEvent: (event: PointerEvent | MouseEvent) => PaintableCell | null;
    previewPaintCells: (cells: PreviewPaintCell[]) => void;
    clearPreview: () => void;
    mutationRunner: MutationRunner;
    onError: (error: unknown) => void;
    applySimulationState: (simulationState: SimulationSnapshot, options?: { source?: string }) => void;
    refreshState: () => Promise<void>;
    toggleCellRequest: ToggleCellRequestFunction;
    setCellRequest: SetCellRequestFunction;
    setCellsRequest: SetCellsRequestFunction;
    postControl: PostControlFunction;
    getPaintState: () => number;
    simulationMutations?: {
        runStateMutation: (
            task: () => Promise<SimulationSnapshot>,
            options?: MutationRunnerOptions & { recoverWithRefresh?: boolean; source?: string },
        ) => Promise<SimulationSnapshot>;
        runSerialized<T>(task: () => Promise<T>, options?: MutationRunnerOptions): Promise<T>;
    } | null;
    dismissOverlays?: () => Promise<boolean> | boolean;
    armEditMode?: (() => boolean) | null;
    hideEditCue?: (() => boolean) | null;
    setPatternStatus?: ((message: string, tone?: string) => void) | null;
    getEditorTool?: () => string;
    getBrushSize?: () => number;
    renderControlPanel?: () => void;
    setTimeoutFn?: (callback: () => void, delay: number) => number;
}
