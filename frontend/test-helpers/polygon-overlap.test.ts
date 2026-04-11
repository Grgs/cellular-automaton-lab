import { describe, expect, it } from "vitest";

import {
    OVERLAP_AREA_EPSILON,
    findPositiveAreaPolygonOverlaps,
    representativePolygonCells,
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
});
