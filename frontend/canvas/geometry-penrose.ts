import { buildTransformedPolygonGeometryCell } from "../geometry/polygon-adapter-shared.js";
import type {
    GridMetrics,
    Point2D,
    PolygonGeometryCell,
    RenderableTopologyCell,
} from "../types/rendering.js";

export function penroseCellGeometry(
    cell: RenderableTopologyCell,
    metrics: GridMetrics,
): PolygonGeometryCell | null {
    const transformPoint = (point: Point2D): Point2D => {
        const scale = Number(metrics.scale ?? 0);
        return {
            x: metrics.xInset + Number(point.x) * scale,
            y: metrics.yInset - Number(point.y) * scale,
        };
    };

    return buildTransformedPolygonGeometryCell(
        cell,
        (vertex) => transformPoint(vertex),
        (center) => (center ? transformPoint(center) : null),
    );
}
