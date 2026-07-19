import { getGeometryAdapter } from "../geometry/registry.js";
import { asPolygonGeometryCache } from "../geometry/cache-guards.js";
import type { TopologyCell, TopologyIndex, TopologyPayload } from "../types/domain.js";
import type { GestureOutlineTone, PaintableCell, PreviewPaintCell } from "../types/editor.js";
import type {
    CanvasColors,
    CanvasRenderStyle,
    GeometryCache,
    PolygonIntersectionBounds,
    RenderableTopologyCell,
} from "../types/rendering.js";
import type { CanvasSurfaceMetrics } from "./surface.js";

interface SharedRenderInputs {
    geometry: string;
    topology: TopologyPayload | null;
    topologyIndex: TopologyIndex;
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
            tileColorsEnabled?: boolean;
        },
    ) => string;
}

function resolvePreviewTopologyCell(
    cell: PaintableCell,
    topologyIndex: TopologyIndex,
    geometryCache: GeometryCache | null,
): RenderableTopologyCell | null {
    const polygonCache = asPolygonGeometryCache(geometryCache);
    return polygonCache?.cellsById.get(cell.id)?.cell || topologyIndex.byId.get(cell.id) || null;
}

function resolveTransientRenderCell(
    cell: PaintableCell,
    geometry: string,
    topologyIndex: TopologyIndex,
    geometryCache: GeometryCache | null,
): TopologyCell | PaintableCell {
    const adapter = getGeometryAdapter(geometry);
    if (adapter.family !== "mixed") {
        return cell;
    }
    return resolvePreviewTopologyCell(cell, topologyIndex, geometryCache) || cell;
}

function resolveTransientStateValue(
    cell: PaintableCell,
    topologyIndex: TopologyIndex,
    cellStates: number[],
): number {
    if (typeof cell.state === "number") {
        return cell.state;
    }
    const indexedCell = topologyIndex.byId.get(cell.id);
    if (!indexedCell) {
        return 0;
    }
    return cellStates[indexedCell.index] ?? 0;
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
    targetContext.clearRect(
        0,
        0,
        Math.max(shared.metrics.cssWidth, 1),
        Math.max(shared.metrics.cssHeight, 1),
    );
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

export function drawCommittedCells({
    targetContext,
    cellStates,
    cellIndexes,
    dirtyBounds = null,
    cellSize,
    ...shared
}: SharedRenderInputs & {
    targetContext: CanvasRenderingContext2D;
    cellStates: number[];
    cellIndexes: number[];
    dirtyBounds?: PolygonIntersectionBounds | null;
    cellSize: number;
}): void {
    const adapter = getGeometryAdapter(shared.geometry);
    targetContext.setTransform(shared.metrics.dpr ?? 1, 0, 0, shared.metrics.dpr ?? 1, 0, 0);
    if (dirtyBounds) {
        targetContext.fillStyle = shared.renderStyle.lineColor;
        targetContext.fillRect(
            dirtyBounds.minX,
            dirtyBounds.minY,
            dirtyBounds.maxX - dirtyBounds.minX,
            dirtyBounds.maxY - dirtyBounds.minY,
        );
    }
    for (const index of cellIndexes) {
        const cell = shared.topology?.cells?.[index];
        if (!cell) {
            continue;
        }
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
            const topologyCell = resolvePreviewTopologyCell(
                cell,
                shared.topologyIndex,
                shared.geometryCache,
            );
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

    const renderCell = resolveTransientRenderCell(
        hoveredCell,
        shared.geometry,
        shared.topologyIndex,
        shared.geometryCache,
    );
    const adapter = getGeometryAdapter(shared.geometry);
    adapter.drawCell({
        context,
        cell: renderCell,
        stateValue: resolveTransientStateValue(hoveredCell, shared.topologyIndex, cellStates),
        metrics: shared.metrics,
        cache: shared.geometryCache,
        colors: shared.canvasColors,
        colorLookup: shared.colorLookup,
        resolveRenderedCellColor: shared.resolveRenderedCellColor,
        renderStyle: shared.renderStyle,
        renderLayer: "hover",
    });
}

export function drawSelectionLayer({
    context,
    selectedCells,
    cellStates,
    ...shared
}: SharedRenderInputs & {
    context: CanvasRenderingContext2D;
    selectedCells: PaintableCell[];
    cellStates: number[];
}): void {
    if (selectedCells.length === 0) {
        return;
    }

    const adapter = getGeometryAdapter(shared.geometry);
    selectedCells.forEach((selectedCell) => {
        const renderCell = resolveTransientRenderCell(
            selectedCell,
            shared.geometry,
            shared.topologyIndex,
            shared.geometryCache,
        );
        adapter.drawCell({
            context,
            cell: renderCell,
            stateValue: resolveTransientStateValue(selectedCell, shared.topologyIndex, cellStates),
            metrics: shared.metrics,
            cache: shared.geometryCache,
            colors: shared.canvasColors,
            colorLookup: shared.colorLookup,
            resolveRenderedCellColor: shared.resolveRenderedCellColor,
            renderStyle: shared.renderStyle,
            renderLayer: "selected",
        });
    });
}

export function drawGestureOutlineLayer({
    context,
    outlinedCells,
    tone,
    cellStates,
    ...shared
}: SharedRenderInputs & {
    context: CanvasRenderingContext2D;
    outlinedCells: PaintableCell[];
    tone: GestureOutlineTone | null;
    cellStates: number[];
}): void {
    if (!tone || outlinedCells.length === 0) {
        return;
    }

    const adapter = getGeometryAdapter(shared.geometry);
    outlinedCells.forEach((cell) => {
        const renderCell = resolveTransientRenderCell(
            cell,
            shared.geometry,
            shared.topologyIndex,
            shared.geometryCache,
        );
        adapter.drawCell({
            context,
            cell: renderCell,
            stateValue: resolveTransientStateValue(cell, shared.topologyIndex, cellStates),
            metrics: shared.metrics,
            cache: shared.geometryCache,
            colors: shared.canvasColors,
            colorLookup: shared.colorLookup,
            resolveRenderedCellColor: shared.resolveRenderedCellColor,
            renderStyle: shared.renderStyle,
            renderLayer: tone === "paint" ? "gesture-paint" : "gesture-erase",
        });
    });
}
