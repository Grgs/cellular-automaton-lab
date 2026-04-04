import * as polygonClipping from "polygon-clipping";

import type { Point2D, PolygonGeometryCell } from "../types/rendering.js";

const OVERLAP_AREA_EPSILON = 1e-4;

export interface PolygonOverlap {
    leftId: string;
    rightId: string;
    area: number;
}

function ringArea(vertices: readonly polygonClipping.Pair[]): number {
    let area = 0;
    for (let index = 0; index < vertices.length; index += 1) {
        const [x1, y1] = vertices[index] ?? [0, 0];
        const [x2, y2] = vertices[(index + 1) % vertices.length] ?? [0, 0];
        area += (x1 * y2) - (x2 * y1);
    }
    return area / 2;
}

function multiPolygonArea(multiPolygon: polygonClipping.MultiPolygon): number {
    let area = 0;
    for (const polygon of multiPolygon) {
        const [outerRing, ...innerRings] = polygon;
        if (!outerRing || outerRing.length < 3) {
            continue;
        }
        area += Math.abs(ringArea(outerRing));
        for (const ring of innerRings) {
            if (ring.length < 3) {
                continue;
            }
            area -= Math.abs(ringArea(ring));
        }
    }
    return area;
}

function boundsOverlap(left: PolygonGeometryCell, right: PolygonGeometryCell): boolean {
    return !(
        left.maxX < right.minX
        || right.maxX < left.minX
        || left.maxY < right.minY
        || right.maxY < left.minY
    );
}

function toPolygon(vertices: readonly Point2D[]): polygonClipping.Polygon {
    return [vertices.map((vertex) => [vertex.x, vertex.y] as polygonClipping.Pair)];
}

export function findPositiveAreaPolygonOverlaps(
    cells: readonly PolygonGeometryCell[],
    areaEpsilon: number = OVERLAP_AREA_EPSILON,
    maxResults: number = Number.POSITIVE_INFINITY,
): PolygonOverlap[] {
    const overlaps: PolygonOverlap[] = [];
    for (let leftIndex = 0; leftIndex < cells.length; leftIndex += 1) {
        const left = cells[leftIndex];
        if (!left) {
            continue;
        }
        for (let rightIndex = leftIndex + 1; rightIndex < cells.length; rightIndex += 1) {
            const right = cells[rightIndex];
            if (!right || !boundsOverlap(left, right)) {
                continue;
            }
            const intersection = polygonClipping.intersection(
                toPolygon(left.vertices),
                toPolygon(right.vertices),
            );
            const area = multiPolygonArea(intersection);
            if (area > areaEpsilon) {
                overlaps.push({
                    leftId: left.cell.id,
                    rightId: right.cell.id,
                    area,
                });
                if (overlaps.length >= maxResults) {
                    return overlaps;
                }
            }
        }
    }
    return overlaps;
}
