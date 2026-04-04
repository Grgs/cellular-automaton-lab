import { resolveCellFromCanvasOffset, topologyCellCenter } from "./geometry-adapters.js";
import { resolveGeometryCache } from "./canvas/cache.js";
import { gridMetrics } from "./layout.js";
import { currentTopologyVariantKey } from "./state/simulation-state.js";
import { findTopologyCellById, isRegularGeometry, regularCellId } from "./topology.js";
import type { IndexedTopologyPaintableCell, PaintableCell, PreviewPaintCell } from "./types/editor.js";
import type { GeometryCache } from "./types/rendering.js";
import type { AppState } from "./types/state.js";

export function renderCellSize(state: AppState): number {
    return Number(state?.renderCellSize) || Number(state?.cellSize) || 1;
}

export function previewCellFromTopologyCell(
    cell: IndexedTopologyPaintableCell,
    stateValue: number,
): PreviewPaintCell {
    return {
        id: cell.id,
        kind: cell.kind,
        state: stateValue,
    };
}

export function cellCenter(
    state: AppState,
    cell: IndexedTopologyPaintableCell,
): { x: number; y: number } {
    const topologyVariantKey = currentTopologyVariantKey(state);
    return topologyCellCenter(
        cell,
        renderCellSize(state),
        topologyVariantKey,
        state.width,
        state.height,
        null,
        null,
        state.topology,
    );
}

export function resolveTopologyCell(
    state: AppState,
    cell: PaintableCell | null | undefined,
): IndexedTopologyPaintableCell | null {
    if (!state?.topologyIndex || !cell) {
        return null;
    }
    if (typeof cell.id === "string" && cell.id.length > 0) {
        return findTopologyCellById(state.topologyIndex, cell.id);
    }
    if (isRegularGeometry(currentTopologyVariantKey(state)) && Number.isFinite(cell.x) && Number.isFinite(cell.y)) {
        return findTopologyCellById(state.topologyIndex, regularCellId(cell.x ?? 0, cell.y ?? 0));
    }
    return null;
}

export function resolveSampledCell(
    state: AppState,
    offsetX: number,
    offsetY: number,
    geometryCache: GeometryCache | null,
): IndexedTopologyPaintableCell | null {
    const nextRenderCellSize = renderCellSize(state);
    const topologyVariantKey = currentTopologyVariantKey(state);
    const metrics = gridMetrics(state.width, state.height, nextRenderCellSize, topologyVariantKey, state.topology);
    return resolveTopologyCell(
        state,
        resolveCellFromCanvasOffset(
            offsetX,
            offsetY,
            state.width,
            state.height,
            nextRenderCellSize,
            topologyVariantKey,
            metrics,
            geometryCache,
        ),
    );
}

export function geometryCacheForState(state: AppState): GeometryCache | null {
    const nextRenderCellSize = renderCellSize(state);
    const topologyVariantKey = currentTopologyVariantKey(state);
    const metrics = gridMetrics(state.width, state.height, nextRenderCellSize, topologyVariantKey, state.topology);
    return resolveGeometryCache({
        existingKey: "",
        existingCache: null,
        width: state.width,
        height: state.height,
        cellSize: nextRenderCellSize,
        geometry: topologyVariantKey,
        metrics,
        topology: state.topology,
    }).geometryCache;
}
