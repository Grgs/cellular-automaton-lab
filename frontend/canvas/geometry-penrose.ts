import type { GridMetrics, Point2D, PolygonGeometryCell, RenderableTopologyCell } from "../types/rendering.js";

function transformPenrosePoint(point: Point2D, metrics: GridMetrics): Point2D {
    const scale = Number(metrics.scale ?? 0);
    return {
        x: metrics.xInset + (Number(point.x) * scale),
        y: metrics.yInset - (Number(point.y) * scale),
    };
}

export function penroseCellGeometry(
    cell: RenderableTopologyCell,
    metrics: GridMetrics,
): PolygonGeometryCell | null {
    const vertices = Array.isArray(cell?.vertices)
        ? cell.vertices.map((vertex) => transformPenrosePoint(vertex, metrics))
        : [];
    const center = cell?.center
        ? transformPenrosePoint(cell.center, metrics)
        : { x: 0, y: 0 };
    const minX = vertices.length > 0 ? Math.min(...vertices.map((vertex) => vertex.x)) : center.x;
    const maxX = vertices.length > 0 ? Math.max(...vertices.map((vertex) => vertex.x)) : center.x;
    const minY = vertices.length > 0 ? Math.min(...vertices.map((vertex) => vertex.y)) : center.y;
    const maxY = vertices.length > 0 ? Math.max(...vertices.map((vertex) => vertex.y)) : center.y;
    return {
        cell,
        vertices,
        centerX: center.x,
        centerY: center.y,
        minX,
        maxX,
        minY,
        maxY,
    };
}
