import { getGeometryAdapter } from "../geometry/registry.js";
import { asPolygonGeometryCache } from "../geometry/cache-guards.js";
import type { TopologyCell, TopologyPayload } from "../types/domain.js";
import type { PaintableCell, PreviewPaintCell } from "../types/editor.js";
import type {
    CanvasColors,
    CanvasRenderStyle,
    GeometryCache,
    RenderableTopologyCell,
} from "../types/rendering.js";
import type { CanvasSurfaceMetrics } from "./surface.js";

interface SharedRenderInputs {
    geometry: string;
    topology: TopologyPayload | null;
    metrics: CanvasSurfaceMetrics;
    geometryCache: GeometryCache | null;
    canvasColors: CanvasColors;
    renderStyle: CanvasRenderStyle;
    colorLookup: Map<number, string>;
    resolveRenderedCellColor: (
        stateValue: number,
        colorLookup: Map<number, string>,
        colors: CanvasColors,
        options?: {
            geometry?: string;
            x?: number | null;
            y?: number | null;
            cell?: TopologyCell | PaintableCell | null;
        },
    ) => string;
}

function resolvePreviewTopologyCell(
    cell: PaintableCell,
    topology: TopologyPayload | null,
    geometryCache: GeometryCache | null,
): RenderableTopologyCell | null {
    const polygonCache = asPolygonGeometryCache(geometryCache);
    return polygonCache?.cellsById.get(cell.id)?.cell
        || topology?.cells?.find((candidate) => candidate.id === cell.id)
        || null;
}

function resolveHoverStateValue(
    cell: PaintableCell,
    topology: TopologyPayload | null,
    cellStates: number[],
): number {
    if (typeof cell.state === "number") {
        return cell.state;
    }
    if (!Array.isArray(topology?.cells)) {
        return 0;
    }

    const topologyCellIndex = typeof cell.id === "string" && cell.id.length > 0
        ? topology.cells.findIndex((candidate) => candidate.id === cell.id)
        : -1;

    if (topologyCellIndex < 0) {
        return 0;
    }
    return cellStates[topologyCellIndex] ?? 0;
}

export function drawCommittedLayer({
    targetContext,
    cellStates,
    cellSize,
    ...shared
}: SharedRenderInputs & {
    targetContext: CanvasRenderingContext2D;
    cellStates: number[];
    cellSize: number;
}): void {
    const adapter = getGeometryAdapter(shared.geometry);
    targetContext.setTransform(shared.metrics.dpr ?? 1, 0, 0, shared.metrics.dpr ?? 1, 0, 0);
    targetContext.clearRect(0, 0, Math.max(shared.metrics.cssWidth, 1), Math.max(shared.metrics.cssHeight, 1));
    targetContext.fillStyle = shared.renderStyle.lineColor;
    targetContext.fillRect(0, 0, shared.metrics.cssWidth, shared.metrics.cssHeight);

    if (shared.topology?.cells) {
        shared.topology.cells.forEach((cell, index) => {
            adapter.drawCell({
                context: targetContext,
                cell,
                stateValue: cellStates[index] ?? 0,
                metrics: shared.metrics,
                cache: shared.geometryCache,
                colors: shared.canvasColors,
                colorLookup: shared.colorLookup,
                resolveRenderedCellColor: shared.resolveRenderedCellColor,
                renderStyle: shared.renderStyle,
                renderLayer: "committed",
            });
        });
    }

    if (typeof adapter.drawOverlay === "function") {
        adapter.drawOverlay({
            context: targetContext,
            width: shared.metrics.width,
            height: shared.metrics.height,
            metrics: shared.metrics,
            cache: shared.geometryCache,
            renderStyle: shared.renderStyle,
            cellSize,
        });
    }
}

export function drawPreviewLayer({
    context,
    previewCells,
    ...shared
}: SharedRenderInputs & {
    context: CanvasRenderingContext2D;
    previewCells: Map<string, PreviewPaintCell>;
}): void {
    if (previewCells.size === 0) {
        return;
    }

    const adapter = getGeometryAdapter(shared.geometry);
    previewCells.forEach((cell) => {
        if (adapter.family === "mixed") {
            const topologyCell = resolvePreviewTopologyCell(cell, shared.topology, shared.geometryCache);
            if (!topologyCell) {
                return;
            }
            adapter.drawCell({
                context,
                cell: topologyCell,
                stateValue: cell.state,
                metrics: shared.metrics,
                cache: shared.geometryCache,
                colors: shared.canvasColors,
                colorLookup: shared.colorLookup,
                resolveRenderedCellColor: shared.resolveRenderedCellColor,
                renderStyle: shared.renderStyle,
                renderLayer: "preview",
            });
            return;
        }

        if (cell.id.length === 0) {
            return;
        }
        adapter.drawCell({
            context,
            cell,
            stateValue: cell.state,
            metrics: shared.metrics,
            cache: shared.geometryCache,
            colors: shared.canvasColors,
            colorLookup: shared.colorLookup,
            resolveRenderedCellColor: shared.resolveRenderedCellColor,
            renderStyle: shared.renderStyle,
            renderLayer: "preview",
        });
    });
}

export function drawHoverLayer({
    context,
    hoveredCell,
    cellStates,
    ...shared
}: SharedRenderInputs & {
    context: CanvasRenderingContext2D;
    hoveredCell: PaintableCell | null;
    cellStates: number[];
}): void {
    if (!hoveredCell) {
        return;
    }

    const adapter = getGeometryAdapter(shared.geometry);
    const topologyCell = adapter.family === "mixed"
        ? resolvePreviewTopologyCell(hoveredCell, shared.topology, shared.geometryCache)
        : null;
    const renderCell = topologyCell || hoveredCell;
    adapter.drawCell({
        context,
        cell: renderCell,
        stateValue: resolveHoverStateValue(hoveredCell, shared.topology, cellStates),
        metrics: shared.metrics,
        cache: shared.geometryCache,
        colors: shared.canvasColors,
        colorLookup: shared.colorLookup,
        resolveRenderedCellColor: shared.resolveRenderedCellColor,
        renderStyle: shared.renderStyle,
        renderLayer: "hover",
    });
}
