import { appendPolygonPath } from "./draw.js";
import type { GeometryCache, Point2D, PolygonGeometryCell, RenderableTopologyCell } from "../types/rendering.js";
import type { PaintableCell } from "../types/editor.js";
import type { TopologyPayload } from "../types/domain.js";

export function pointInPolygon(offsetX: number, offsetY: number, vertices: readonly Point2D[]): boolean {
    let inside = false;
    for (let index = 0, previous = vertices.length - 1; index < vertices.length; previous = index, index += 1) {
        const left = vertices[index];
        const right = vertices[previous];
        if (!left || !right) {
            continue;
        }
        const intersects = (
            ((left.y > offsetY) !== (right.y > offsetY))
            && (
                offsetX
                < ((right.x - left.x) * (offsetY - left.y)) / ((right.y - left.y) || 1e-9) + left.x
            )
        );
        if (intersects) {
            inside = !inside;
        }
    }
    return inside;
}

export function buildMixedTopologyGeometryCache(
    topology: TopologyPayload | null,
    buildCellGeometry: (cell: RenderableTopologyCell) => PolygonGeometryCell | null,
): GeometryCache {
    const cells = (topology?.cells ?? [])
        .map((cell) => buildCellGeometry(cell as RenderableTopologyCell))
        .filter((cell): cell is PolygonGeometryCell => Boolean(cell));
    const strokePath = typeof Path2D === "undefined" ? null : new Path2D();

    if (strokePath) {
        cells.forEach((cell) => {
            appendPolygonPath(strokePath, cell.vertices);
        });
    }

    return {
        type: typeof topology?.geometry === "string" ? topology.geometry : "mixed",
        cells,
        cellsById: new Map(cells.map((cell) => [cell.cell.id, cell])),
        strokePath,
    };
}

export function resolveMixedCellFromOffset(
    offsetX: number,
    offsetY: number,
    geometryCache: GeometryCache | null,
): PaintableCell | null {
    if (!geometryCache?.cellsById) {
        return null;
    }

    const cachedCells = Array.isArray(geometryCache.cells) ? geometryCache.cells as PolygonGeometryCell[] : [];
    for (const cachedCell of cachedCells) {
        if (
            offsetX < cachedCell.minX
            || offsetX > cachedCell.maxX
            || offsetY < cachedCell.minY
            || offsetY > cachedCell.maxY
        ) {
            continue;
        }
        if (pointInPolygon(offsetX, offsetY, cachedCell.vertices)) {
            return cachedCell.cell.kind
                ? { id: cachedCell.cell.id, kind: cachedCell.cell.kind }
                : { id: cachedCell.cell.id };
        }
    }
    return null;
}
