import { describe, expect, it } from "vitest";

import {
    OVERLAP_AREA_EPSILON,
    findPositiveAreaPolygonOverlaps,
    representativePolygonCells,
    summarizePositiveAreaPolygonOverlaps,
} from "./polygon-overlap.js";
import type { PolygonGeometryCell } from "../types/rendering.js";

function polygonCell(
    id: string,
    vertices: Array<[number, number]>,
): PolygonGeometryCell {
    const xs = vertices.map(([x]) => x);
    const ys = vertices.map(([, y]) => y);
    return {
        cell: { id, kind: "fixture-polygon", neighbors: [] },
        vertices: vertices.map(([x, y]) => ({ x, y })),
        centerX: (Math.min(...xs) + Math.max(...xs)) / 2,
        centerY: (Math.min(...ys) + Math.max(...ys)) / 2,
        minX: Math.min(...xs),
        maxX: Math.max(...xs),
        minY: Math.min(...ys),
        maxY: Math.max(...ys),
    };
}

describe("test-helpers/polygon-overlap", () => {
    it("collapses exact duplicate rendered polygons to one representative geometry", () => {
        const duplicateA = polygonCell("shared-id", [
            [0, 0],
            [1, 0],
            [0, 1],
        ]);
        const duplicateB = polygonCell("different-id", [
            [0, 0],
            [1, 0],
            [0, 1],
        ]);

        expect(representativePolygonCells([duplicateA, duplicateB])).toEqual([duplicateA]);
    });

    it("preserves distinct polygons that share the same id", () => {
        const left = polygonCell("shared-id", [
            [0, 0],
            [1, 0],
            [0, 1],
        ]);
        const right = polygonCell("shared-id", [
            [2, 0],
            [3, 0],
            [2, 1],
        ]);

        expect(representativePolygonCells([left, right])).toEqual([left, right]);
    });

    it("reports synthetic real positive-area overlap under the tighter threshold", () => {
        const left = polygonCell("left", [
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 1],
        ]);
        const right = polygonCell("right", [
            [0.5, 0.5],
            [1.5, 0.5],
            [1.5, 1.5],
            [0.5, 1.5],
        ]);

        const overlaps = findPositiveAreaPolygonOverlaps([left, right]);

        expect(overlaps).toHaveLength(1);
        expect(overlaps[0]?.leftId).toBe("left");
        expect(overlaps[0]?.rightId).toBe("right");
        expect(overlaps[0]?.area).toBeGreaterThan(OVERLAP_AREA_EPSILON);
    });

    it("stays deterministic across repeated evaluations", () => {
        const left = polygonCell("left", [
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 1],
        ]);
        const right = polygonCell("right", [
            [0.5, 0.5],
            [1.5, 0.5],
            [1.5, 1.5],
            [0.5, 1.5],
        ]);

        const first = findPositiveAreaPolygonOverlaps([left, right]);
        const second = findPositiveAreaPolygonOverlaps([left, right]);

        expect(second).toEqual(first);
    });

    it("summarizes overlap hotspots and cross-references transform sample ids", () => {
        const triangle = polygonCell("shield:ref:1378", [
            [0, 0],
            [2, 0],
            [1, 2],
        ]);
        triangle.cell.kind = "shield-triangle";
        const square = polygonCell("shield:ref:1400", [
            [0.5, 0.25],
            [2.5, 0.25],
            [2.5, 2.25],
            [0.5, 2.25],
        ]);
        square.cell.kind = "shield-square";
        const distant = polygonCell("shield:ref:2007", [
            [10, 10],
            [12, 10],
            [12, 12],
            [10, 12],
        ]);
        distant.cell.kind = "shield-shield";

        const summary = summarizePositiveAreaPolygonOverlaps(
            [triangle, square, distant],
            { transformSampleIds: ["shield:ref:1378", "shield:ref:2007"] },
        );

        expect(summary.representativeCellCount).toBe(3);
        expect(summary.sampledOverlapCount).toBe(1);
        expect(summary.maxSampledArea).toBeGreaterThan(OVERLAP_AREA_EPSILON);
        expect(summary.topOverlapPairs).toHaveLength(1);
        expect(summary.topKindPairs).toEqual([
            {
                kindPair: "shield-square / shield-triangle",
                count: 1,
            },
        ]);
        expect(summary.transformSampleHits).toEqual(["shield:ref:1378"]);
    });
});
