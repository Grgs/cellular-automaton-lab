import * as polygonClipping from "polygon-clipping";

import type { Point2D, PolygonGeometryCell } from "../types/rendering.js";

// Keep the render-space overlap threshold tighter than the historical 1e-3
// helper tolerance while allowing current exact-path adapter noise for pinwheel.
export const OVERLAP_AREA_EPSILON = 1e-4;
const SANITIZE_EPSILON = 1e-6;
const SANITIZE_DECIMALS = [6, 5, 4, 3, 2, 1] as const;

export interface PolygonOverlap {
    leftId: string;
    rightId: string;
    area: number;
}

export interface PolygonOverlapPairSummary extends PolygonOverlap {
    leftKind: string | null;
    rightKind: string | null;
}

export interface PolygonOverlapKindPairSummary {
    kindPair: string;
    count: number;
}

export interface PolygonOverlapHotspotSummary {
    representativeCellCount: number;
    sampledOverlapCount: number;
    maxSampledArea: number;
    topOverlapPairs: PolygonOverlapPairSummary[];
    topKindPairs: PolygonOverlapKindPairSummary[];
    transformSampleHits: string[];
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

function canonicalRingSignature(ring: readonly polygonClipping.Pair[]): string {
    if (ring.length === 0) {
        return "";
    }
    const candidateSignatures: string[] = [];
    const forward = [...ring];
    const backward = [...ring].reverse();
    for (const candidate of [forward, backward]) {
        for (let index = 0; index < candidate.length; index += 1) {
            const rotated = candidate
                .slice(index)
                .concat(candidate.slice(0, index))
                .map(([x, y]) => `${x},${y}`)
                .join("|");
            candidateSignatures.push(rotated);
        }
    }
    candidateSignatures.sort();
    return candidateSignatures[0] ?? "";
}

function toPolygon(vertices: readonly Point2D[], decimals: number = SANITIZE_DECIMALS[0]): polygonClipping.Polygon | null {
    const ring = sanitizeRing(vertices, decimals);
    if (ring.length < 3) {
        return null;
    }
    return [ring];
}

export function representativePolygonCells(
    cells: readonly PolygonGeometryCell[],
    decimals: number = SANITIZE_DECIMALS[0],
): PolygonGeometryCell[] {
    const seenSignatures = new Set<string>();
    const representatives: PolygonGeometryCell[] = [];
    for (const cell of cells) {
        const ring = sanitizeRing(cell.vertices, decimals);
        if (ring.length < 3) {
            continue;
        }
        const signature = canonicalRingSignature(ring);
        if (seenSignatures.has(signature)) {
            continue;
        }
        seenSignatures.add(signature);
        representatives.push(cell);
    }
    return representatives;
}

function effectiveOverlapArea(
    left: PolygonGeometryCell,
    right: PolygonGeometryCell,
): number {
    let minimumArea = Number.POSITIVE_INFINITY;
    let sawSuccessfulIntersection = false;

    for (const decimals of SANITIZE_DECIMALS) {
        const leftPolygon = toPolygon(left.vertices, decimals);
        const rightPolygon = toPolygon(right.vertices, decimals);
        if (!leftPolygon || !rightPolygon) {
            minimumArea = Math.min(minimumArea, 0);
            sawSuccessfulIntersection = true;
            continue;
        }
        try {
            const intersection = polygonClipping.intersection(leftPolygon, rightPolygon);
            const area = multiPolygonArea(intersection);
            minimumArea = Math.min(minimumArea, area);
            sawSuccessfulIntersection = true;
            continue;
        } catch (error) {
            if (decimals === SANITIZE_DECIMALS[SANITIZE_DECIMALS.length - 1]) {
                throw new Error(
                    `polygon-clipping failed for ${left.cell.id} vs ${right.cell.id}: ${
                        error instanceof Error ? error.message : String(error)
                    }`,
                );
            }
        }
    }

    return sawSuccessfulIntersection ? minimumArea : 0;
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
            const area = effectiveOverlapArea(left, right);
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

function sortedKindPair(leftKind: string | null, rightKind: string | null): string {
    return [leftKind ?? "unknown", rightKind ?? "unknown"].sort().join(" / ");
}

export function summarizePositiveAreaPolygonOverlaps(
    cells: readonly PolygonGeometryCell[],
    options: {
        areaEpsilon?: number;
        maxStoredPairs?: number;
        transformSampleIds?: readonly string[];
    } = {},
): PolygonOverlapHotspotSummary {
    const {
        areaEpsilon = OVERLAP_AREA_EPSILON,
        maxStoredPairs = 50,
        transformSampleIds = [],
    } = options;
    const representativeCells = representativePolygonCells(cells);
    const representativeCellCount = representativeCells.length;
    let sampledOverlapCount = 0;
    let maxSampledArea = 0;
    const topOverlapPairs: PolygonOverlapPairSummary[] = [];
    const kindPairCounts = new Map<string, number>();
    const transformHitIds = new Set<string>();
    const transformSampleIdSet = new Set(transformSampleIds);

    for (let leftIndex = 0; leftIndex < representativeCells.length; leftIndex += 1) {
        const left = representativeCells[leftIndex];
        if (!left) {
            continue;
        }
        for (let rightIndex = leftIndex + 1; rightIndex < representativeCells.length; rightIndex += 1) {
            const right = representativeCells[rightIndex];
            if (!right || !boundsOverlap(left, right)) {
                continue;
            }
            const area = effectiveOverlapArea(left, right);
            if (area <= areaEpsilon) {
                continue;
            }
            sampledOverlapCount += 1;
            maxSampledArea = Math.max(maxSampledArea, area);
            const leftKind = typeof left.cell.kind === "string" ? left.cell.kind : null;
            const rightKind = typeof right.cell.kind === "string" ? right.cell.kind : null;
            const kindPair = sortedKindPair(leftKind, rightKind);
            kindPairCounts.set(kindPair, (kindPairCounts.get(kindPair) ?? 0) + 1);
            if (transformSampleIdSet.has(left.cell.id)) {
                transformHitIds.add(left.cell.id);
            }
            if (transformSampleIdSet.has(right.cell.id)) {
                transformHitIds.add(right.cell.id);
            }
            topOverlapPairs.push({
                leftId: left.cell.id,
                rightId: right.cell.id,
                area,
                leftKind,
                rightKind,
            });
        }
    }

    topOverlapPairs.sort((left, right) => {
        const areaDelta = right.area - left.area;
        if (areaDelta !== 0) {
            return areaDelta;
        }
        const leftKey = `${left.leftId}:${left.rightId}`;
        const rightKey = `${right.leftId}:${right.rightId}`;
        return leftKey.localeCompare(rightKey);
    });

    return {
        representativeCellCount,
        sampledOverlapCount,
        maxSampledArea,
        topOverlapPairs: topOverlapPairs.slice(0, maxStoredPairs),
        topKindPairs: [...kindPairCounts.entries()]
            .map(([kindPair, count]) => ({ kindPair, count }))
            .sort((left, right) => {
                const countDelta = right.count - left.count;
                return countDelta !== 0 ? countDelta : left.kindPair.localeCompare(right.kindPair);
            }),
        transformSampleHits: [...transformHitIds].sort(),
    };
}
