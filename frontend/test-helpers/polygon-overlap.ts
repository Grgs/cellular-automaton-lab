import * as polygonClipping from "polygon-clipping";

import type { Point2D, PolygonGeometryCell } from "../types/rendering.js";

// Keep the render-space overlap threshold tighter than the historical 1e-3
// helper tolerance while allowing current exact-path adapter noise for pinwheel.
const OVERLAP_AREA_EPSILON = 2e-4;
const SANITIZE_EPSILON = 1e-6;
const SANITIZE_DECIMALS = [6, 5, 4, 3] as const;

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

function pointsEqual(left: polygonClipping.Pair, right: polygonClipping.Pair, epsilon: number): boolean {
    return (
        Math.abs(left[0] - right[0]) <= epsilon
        && Math.abs(left[1] - right[1]) <= epsilon
    );
}

function crossProduct(
    left: polygonClipping.Pair,
    middle: polygonClipping.Pair,
    right: polygonClipping.Pair,
): number {
    return (
        ((middle[0] - left[0]) * (right[1] - middle[1]))
        - ((middle[1] - left[1]) * (right[0] - middle[0]))
    );
}

function sanitizeRing(vertices: readonly Point2D[], decimals: number): polygonClipping.Pair[] {
    const deduped: polygonClipping.Pair[] = [];
    for (const vertex of vertices) {
        const pair: polygonClipping.Pair = [
            Number(vertex.x.toFixed(decimals)),
            Number(vertex.y.toFixed(decimals)),
        ];
        const previous = deduped[deduped.length - 1];
        if (previous && pointsEqual(previous, pair, SANITIZE_EPSILON)) {
            continue;
        }
        deduped.push(pair);
    }
    if (
        deduped.length >= 2
        && pointsEqual(deduped[0] ?? [0, 0], deduped[deduped.length - 1] ?? [0, 0], SANITIZE_EPSILON)
    ) {
        deduped.pop();
    }

    let changed = true;
    while (changed && deduped.length >= 3) {
        changed = false;
        for (let index = 0; index < deduped.length; index += 1) {
            const previous = deduped[(index + deduped.length - 1) % deduped.length];
            const current = deduped[index];
            const next = deduped[(index + 1) % deduped.length];
            if (!previous || !current || !next) {
                continue;
            }
            if (Math.abs(crossProduct(previous, current, next)) <= SANITIZE_EPSILON) {
                deduped.splice(index, 1);
                changed = true;
                break;
            }
        }
    }
    return deduped;
}

function toPolygon(vertices: readonly Point2D[], decimals: number = SANITIZE_DECIMALS[0]): polygonClipping.Polygon | null {
    const ring = sanitizeRing(vertices, decimals);
    if (ring.length < 3) {
        return null;
    }
    return [ring];
}

function intersectPolygons(
    leftVertices: readonly Point2D[],
    rightVertices: readonly Point2D[],
    leftId: string,
    rightId: string,
): polygonClipping.MultiPolygon {
    let lastReason = "unknown polygon-clipping failure";
    for (const decimals of SANITIZE_DECIMALS) {
        const leftPolygon = toPolygon(leftVertices, decimals);
        const rightPolygon = toPolygon(rightVertices, decimals);
        if (!leftPolygon || !rightPolygon) {
            return [];
        }
        try {
            return polygonClipping.intersection(leftPolygon, rightPolygon);
        } catch (error) {
            lastReason = error instanceof Error ? error.message : String(error);
        }
    }
    throw new Error(
        `polygon-clipping failed for ${leftId} vs ${rightId}: ${lastReason}`,
    );
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
            const intersection = intersectPolygons(
                left.vertices,
                right.vertices,
                left.cell.id,
                right.cell.id,
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
