import { DEFAULT_GEOMETRY, gridMetrics } from "./layout.js";
import {
    cellCenterOffset as resolveCellCenterOffset,
    resolveCellFromCanvasOffset as resolveGeometryCellFromOffset,
    topologyCellCenter as resolveTopologyCellCenter,
} from "./geometry-adapters.js";
import {
    buildStateColorLookup,
    resolveDeadCellColor,
    resolveRenderDetailLevel,
    resolveRenderStyle,
    resolveStateColor,
} from "./canvas/render-style.js";
import { drawTransientOverlaySnapshot } from "./canvas/overlay-renderer.js";
import {
    createCanvasCommittedRenderer,
    type CanvasCommittedRenderer,
} from "./canvas/committed-renderer.js";
import { createTransientOverlayController } from "./canvas/transient-overlays.js";
import type { GeometryCache, GridMetrics } from "./types/rendering.js";
import type { TopologyPayload } from "./types/domain.js";
import type { GestureOutlineTone, PaintableCell } from "./types/editor.js";
import type { CanvasGridView, CanvasRenderPayload } from "./types/rendering.js";

interface CreateCanvasGridViewOptions {
    canvas: HTMLCanvasElement;
    getDevicePixelRatio?: () => number;
    getComputedStyleFn?: (node: Element) => CSSStyleDeclaration;
    setTimeoutFn?: (callback: () => void, delay: number) => number;
    clearTimeoutFn?: (timerId: number) => void;
}

type RuntimeCanvasGridView = CanvasGridView & {
    supportsTopology: true;
} & Pick<CanvasCommittedRenderer, "getMetrics" | "getRenderDiagnostics" | "getRenderedCellCenter">;

export {
    buildStateColorLookup,
    resolveDeadCellColor,
    resolveRenderDetailLevel,
    resolveRenderStyle,
    resolveStateColor,
};

export function canvasPixelDimensions(
    width: number,
    height: number,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
    topology: TopologyPayload | null = null,
): GridMetrics & { width: number; height: number; pitch: number } {
    const metrics = gridMetrics(width, height, cellSize, geometry, topology);
    return {
        ...metrics,
        width: metrics.cssWidth,
        height: metrics.cssHeight,
        pitch: Number(metrics.pitch ?? metrics.horizontalPitch ?? 0),
    };
}

export function cellFromCanvasOffset(
    offsetX: number,
    offsetY: number,
    width: number,
    height: number,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
): PaintableCell | null {
    return resolveGeometryCellFromOffset(offsetX, offsetY, width, height, cellSize, geometry);
}

export function cellCenterOffset(
    x: number,
    y: number,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
): { x: number; y: number } {
    return resolveCellCenterOffset(x, y, cellSize, geometry);
}

export function topologyCellCenter(
    cell: PaintableCell,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
    width = 0,
    height = 0,
    metrics: GridMetrics | null = null,
    geometryCache: GeometryCache | null = null,
    topology: TopologyPayload | null = null,
): { x: number; y: number } {
    return resolveTopologyCellCenter(
        cell,
        cellSize,
        geometry,
        width,
        height,
        metrics,
        geometryCache,
        topology,
    );
}

export function createCanvasGridView({
    canvas,
    getDevicePixelRatio = () => window.devicePixelRatio || 1,
    getComputedStyleFn = (node) => window.getComputedStyle(node),
    setTimeoutFn = (callback: () => void, delay: number) => window.setTimeout(callback, delay),
    clearTimeoutFn = (timerId: number) => window.clearTimeout(timerId),
}: CreateCanvasGridViewOptions): RuntimeCanvasGridView {
    const committedRenderer = createCanvasCommittedRenderer({
        canvas,
        getDevicePixelRatio,
        getComputedStyleFn,
    });
    const transientOverlays = createTransientOverlayController({
        onChange: redrawTransientLayers,
        setTimeoutFn,
        clearTimeoutFn,
    });

    function redrawTransientLayers(): void {
        committedRenderer.restoreCommittedSurface();
        drawTransientOverlaySnapshot(committedRenderer.snapshot(), transientOverlays.snapshot());
    }

    function render(
        nextState: CanvasRenderPayload,
        nextCellSize?: number,
        nextStateDefinitions?: Parameters<CanvasCommittedRenderer["render"]>[2],
        nextGeometry?: string,
    ): void {
        transientOverlays.reconcileForRender(nextState.topology);
        committedRenderer.render(nextState, nextCellSize, nextStateDefinitions, nextGeometry);
        redrawTransientLayers();
    }

    function setPreviewCells(cells: Parameters<typeof transientOverlays.setPreviewCells>[0]): void {
        transientOverlays.setPreviewCells(cells);
    }

    function clearPreview(): void {
        transientOverlays.clearPreview();
    }

    function setHoveredCell(cell: PaintableCell | null): void {
        transientOverlays.setHoveredCell(cell);
    }

    function setSelectedCells(cells: PaintableCell[]): void {
        transientOverlays.setSelectedCells(cells);
    }

    function getSelectedCells(): PaintableCell[] {
        return transientOverlays.getSelectedCells();
    }

    function setGestureOutline(cells: PaintableCell[], tone: GestureOutlineTone): void {
        transientOverlays.setGestureOutline(cells, tone);
    }

    function flashGestureOutline(
        cells: PaintableCell[],
        tone: GestureOutlineTone,
        durationMs?: number,
    ): void {
        transientOverlays.flashGestureOutline(cells, tone, durationMs);
    }

    function clearGestureOutline(): void {
        transientOverlays.clearGestureOutline();
    }

    return {
        supportsTopology: true,
        render,
        setPreviewCells,
        clearPreview,
        setHoveredCell,
        setSelectedCells,
        getSelectedCells,
        setGestureOutline,
        flashGestureOutline,
        clearGestureOutline,
        getCellFromPointerEvent: committedRenderer.getCellFromPointerEvent,
        getMetrics: committedRenderer.getMetrics,
        getRenderDiagnostics: committedRenderer.getRenderDiagnostics,
        getRenderedCellCenter: committedRenderer.getRenderedCellCenter,
    };
}
