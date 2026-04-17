import type { ViewportDimensions } from "./controller.js";
import type { CellStateDefinition, TopologyCell, TopologyPayload } from "./domain.js";
import type { GestureOutlineTone, PaintableCell, PreviewPaintCell, PreviewPaintCells } from "./editor.js";
import type { AppState } from "./state.js";

export interface Point2D {
    x: number;
    y: number;
}

export interface RenderableTopologyCell extends TopologyCell {
    kind?: string;
    x?: number;
    y?: number;
    center?: Point2D | null;
    vertices?: Point2D[];
}

export interface GridMetrics {
    geometry: string;
    width: number;
    height: number;
    cellSize: number;
    gap: number;
    cssWidth: number;
    cssHeight: number;
    xInset: number;
    yInset: number;
    pitch?: number;
    horizontalPitch?: number;
    verticalPitch?: number;
    radius?: number;
    hexWidth?: number;
    hexHeight?: number;
    oddRowOffset?: number;
    triangleSide?: number;
    triangleHeight?: number;
    scale?: number;
    coordinateScale?: number;
    baseMinX?: number;
    baseMinY?: number;
    unitWidth?: number;
    unitHeight?: number;
    rowOffsetX?: number;
}

export interface CanvasColors {
    line: string;
    dead: string;
    deadAlt: string;
    lineSoft: string;
    lineStrong: string;
    lineAperiodic: string;
    live: string;
    accent: string;
    accentStrong: string;
}

export interface RenderStyle {
    mode: "compact" | "standard" | "detailed";
    geometry: string;
    lineColorToken: string;
    triangleStrokeEnabled: boolean;
}

export interface CanvasRenderStyle extends RenderStyle {
    lineColor: string;
    aperiodicLineColor: string;
    hoverTintColor: string;
    hoverStrokeColor: string;
    selectionTintColor: string;
    selectionStrokeColor: string;
    gesturePaintStrokeColor: string;
    gestureEraseStrokeColor: string;
}

export interface HexGeometryCell {
    centerX: number;
    centerY: number;
    radius: number;
    hexWidth: number;
    minX?: number;
    maxX?: number;
    minY?: number;
    maxY?: number;
}

export interface TriangleGeometryCell {
    vertices: Point2D[];
    centerX?: number;
    centerY?: number;
    minX?: number;
    maxX?: number;
    minY?: number;
    maxY?: number;
}

export interface PolygonGeometryCell {
    cell: RenderableTopologyCell;
    vertices: Point2D[];
    centerX: number;
    centerY: number;
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
}

export type MixedGeometryCell = PolygonGeometryCell | null;

export interface PeriodicFaceTilingDescriptor {
    geometry: string;
    label: string;
    metric_model: string;
    base_edge: number;
    unit_width: number;
    unit_height: number;
    min_dimension: number;
    min_x: number;
    min_y: number;
    max_x: number;
    max_y: number;
    cell_count_per_unit: number;
    row_offset_x: number;
}

export interface HexGeometryCache {
    type: "hex";
    cells: HexGeometryCell[][];
}

export interface TriangleGeometryCache {
    type: "triangle";
    cells: TriangleGeometryCell[][];
    strokePath: Path2D | null;
}

export interface PolygonGeometryCache {
    type: string;
    cells: PolygonGeometryCell[];
    cellsById: Map<string, PolygonGeometryCell>;
    strokePath: Path2D | null;
}

export type GeometryCache = HexGeometryCache | TriangleGeometryCache | PolygonGeometryCache;

export interface RenderedCellArgs {
    context: CanvasRenderingContext2D;
    cell: TopologyCell | PaintableCell;
    stateValue: number;
    metrics: GridMetrics;
    cache: GeometryCache | null;
    colors: CanvasColors;
    colorLookup: Map<number, string>;
    renderStyle?: CanvasRenderStyle;
    renderLayer?: "committed" | "hover" | "selected" | "preview" | "gesture-paint" | "gesture-erase";
    resolveRenderedCellColor: (
        stateValue: number,
        colorLookup: Map<number, string>,
        fallbackColors: CanvasColors,
        options?: {
            geometry?: string;
            x?: number | null;
            y?: number | null;
            cell?: TopologyCell | PaintableCell | null;
        },
    ) => string;
}

export interface GeometryViewportPreviewArgs {
    state: AppState;
    dimensions: ViewportDimensions;
    currentTopology: TopologyPayload | null;
    currentCellStates: number[];
    buildPreviewCellStatesById: (
        currentTopology: TopologyPayload | null,
        currentCellStates: number[],
        nextTopology: TopologyPayload | null,
    ) => Record<string, number>;
    setViewportPreview: (
        state: AppState,
        nextTopology: TopologyPayload,
        previewCellStatesById: Record<string, number>,
        topologyRevision: string | null,
    ) => void;
    clearViewportPreview: (state: AppState) => void;
}

export interface GeometryBuildMetricsArgs {
    width: number;
    height: number;
    cellSize: number;
    topology?: TopologyPayload | null;
}

export interface GeometryFitViewportArgs {
    viewportWidth: number;
    viewportHeight: number;
    cellSize: number;
    fallbackDimensions?: ViewportDimensions;
}

export interface GeometryFitRenderCellSizeArgs {
    viewportWidth: number;
    viewportHeight: number;
    width: number;
    height: number;
    topology: TopologyPayload | null;
    fallbackCellSize: number;
}

export interface GeometryBuildCacheArgs {
    width: number;
    height: number;
    cellSize: number;
    metrics: GridMetrics;
    topology: TopologyPayload | null;
    maxCachedCells: number;
}

export interface GeometryResolveCellFromOffsetArgs {
    offsetX: number;
    offsetY: number;
    width: number;
    height: number;
    cellSize: number;
    metrics?: GridMetrics | null;
    cache?: GeometryCache | null;
}

export interface GeometryResolveCellCenterArgs {
    cell: TopologyCell | PaintableCell;
    width?: number;
    height?: number;
    cellSize: number;
    topology?: TopologyPayload | null;
    metrics?: GridMetrics | null;
    cache?: GeometryCache | null;
}

export interface GeometryResolveCoordinateCenterArgs {
    x: number;
    y: number;
    cellSize: number;
    metrics?: GridMetrics | null;
}

export interface GeometryDrawOverlayArgs {
    context: CanvasRenderingContext2D;
    width: number;
    height: number;
    metrics: GridMetrics;
    cache: GeometryCache | null;
    renderStyle: CanvasRenderStyle;
    cellSize: number;
}

export interface GeometryAdapter {
    geometry: string;
    family: "regular" | "mixed" | "aperiodic";
    buildMetrics(args: GeometryBuildMetricsArgs): GridMetrics;
    fitViewport?(args: GeometryFitViewportArgs): ViewportDimensions;
    fitRenderCellSize?(args: GeometryFitRenderCellSizeArgs): number;
    buildCache(args: GeometryBuildCacheArgs): GeometryCache | null;
    resolveCellFromOffset(args: GeometryResolveCellFromOffsetArgs): PaintableCell | null;
    resolveCellCenter(args: GeometryResolveCellCenterArgs): { x: number; y: number };
    resolveCoordinateCenter(args: GeometryResolveCoordinateCenterArgs): { x: number; y: number };
    drawCell(args: RenderedCellArgs): void;
    drawOverlay?(args: GeometryDrawOverlayArgs): void;
    buildCellGeometry?(args: {
        cell: TopologyCell | PaintableCell;
        metrics: GridMetrics;
        cache?: GeometryCache | null;
    }): MixedGeometryCell;
    applyViewportPreview(args: GeometryViewportPreviewArgs): {
        applied: boolean;
        renderGrid: boolean;
    };
}

export interface CanvasRenderPayload {
    topology: TopologyPayload | null;
    cellStates: number[];
    previewCellStatesById: Record<string, number> | null;
}

export interface CanvasGridView {
    render(
        payload: CanvasRenderPayload,
        cellSize: number,
        stateDefinitions: CellStateDefinition[],
        geometry: string,
    ): void;
    setPreviewCells(cells: PreviewPaintCells): void;
    clearPreview(): void;
    setHoveredCell(cell: PaintableCell | null): void;
    setSelectedCells(cells: PaintableCell[]): void;
    getSelectedCells(): PaintableCell[];
    setGestureOutline(cells: PaintableCell[], tone: GestureOutlineTone): void;
    flashGestureOutline(cells: PaintableCell[], tone: GestureOutlineTone, durationMs?: number): void;
    clearGestureOutline(): void;
    getCellFromPointerEvent(event: Event): PaintableCell | null;
}

export interface GeometryBounds {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
    width: number;
    height: number;
}

export interface RenderDiagnosticsSampleCell {
    role: "lexicographicFirst" | "centerNearest" | "boundaryFurthest";
    cellId: string;
    kind: string | null;
    rawCenter: Point2D;
    rawBounds: GeometryBounds;
    renderedCenter: Point2D;
    renderedBounds: GeometryBounds;
}

export interface RenderDiagnosticsOverlapPair {
    leftId: string;
    rightId: string;
    area: number;
    leftKind: string | null;
    rightKind: string | null;
}

export interface RenderDiagnosticsOverlapKindPair {
    kindPair: string;
    count: number;
}

export interface RenderDiagnosticsOverlapHotspots {
    representativeCellCount: number;
    sampledOverlapCount: number;
    maxSampledArea: number;
    topOverlapPairs: RenderDiagnosticsOverlapPair[];
    topKindPairs: RenderDiagnosticsOverlapKindPair[];
    transformSampleHits: string[];
}

export interface RenderDiagnosticsMetricInputs {
    renderedTopologyCenter: Point2D | null;
    renderedCellCount: number;
    orientationTokenCounts: Record<string, number> | null;
    angularSectorCounts: number[] | null;
}

export interface RenderDiagnosticsSnapshot {
    geometry: string;
    adapterGeometry: string;
    adapterFamily: "regular" | "mixed" | "aperiodic";
    topologyBounds: GeometryBounds | null;
    renderMetrics: {
        cellSize: number;
        renderCellSize: number;
        scale: number | null;
        coordinateScale: number;
        xInset: number;
        yInset: number;
        cssWidth: number;
        cssHeight: number;
        canvasWidth: number;
        canvasHeight: number;
    };
    sampleCells: {
        lexicographicFirst: RenderDiagnosticsSampleCell | null;
        centerNearest: RenderDiagnosticsSampleCell | null;
        boundaryFurthest: RenderDiagnosticsSampleCell | null;
    };
    metricInputs: RenderDiagnosticsMetricInputs;
    overlapHotspots: RenderDiagnosticsOverlapHotspots | null;
}
