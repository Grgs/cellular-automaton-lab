import { beforeEach, describe, expect, it, vi } from "vitest";

import {
    buildPolygonSpatialIndex,
    polygonSpatialIndexCandidates,
    polygonSpatialIndexIntersectionCandidates,
} from "./polygon-spatial-index.js";
import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type { PolygonGeometryCache, PolygonGeometryCell } from "../types/rendering.js";

function squareCell(x: number, y: number, id = `cell:${x}:${y}`): PolygonGeometryCell {
    return {
        cell: { id, neighbors: [] },
        vertices: [
            { x, y },
            { x: x + 1, y },
            { x: x + 1, y: y + 1 },
            { x, y: y + 1 },
        ],
        centerX: x + 0.5,
        centerY: y + 0.5,
        minX: x,
        maxX: x + 1,
        minY: y,
        maxY: y + 1,
    };
}

describe("polygon spatial index", () => {
    beforeEach(() => {
        vi.resetModules();
        installFrontendGlobals();
    });

    it("narrows large polygon fields to a small point-local candidate set", () => {
        const cells = Array.from({ length: 100 }, (_, y) =>
            Array.from({ length: 100 }, (_, x) => squareCell(x, y)),
        ).flat();

        const index = buildPolygonSpatialIndex(cells);

        expect(index).not.toBeNull();
        const candidates = polygonSpatialIndexCandidates(index!, 50.5, 40.5);
        expect(candidates.length).toBeLessThan(100);
        expect(candidates).toContain(cells[40 * 100 + 50]);
    });

    it("uses the index for hit testing without changing polygon resolution", async () => {
        const { resolveMixedCellFromOffset } = await import("../canvas/geometry-mixed.js");
        const cells = Array.from({ length: 10 }, (_, y) =>
            Array.from({ length: 10 }, (_, x) => squareCell(x, y)),
        ).flat();
        const cache: PolygonGeometryCache = {
            type: "test",
            cells,
            cellsById: new Map(cells.map((cell) => [cell.cell.id, cell])),
            strokePath: null,
            spatialIndex: buildPolygonSpatialIndex(cells),
        };

        expect(resolveMixedCellFromOffset(7.5, 3.5, cache)).toEqual({ id: "cell:7:3" });
        expect(resolveMixedCellFromOffset(-1, -1, cache)).toBeNull();
    });

    it("preserves source order when indexed polygons overlap", async () => {
        const { resolveMixedCellFromOffset } = await import("../canvas/geometry-mixed.js");
        const first = squareCell(0, 0, "first");
        const cells = [first, ...Array.from({ length: 39 }, () => squareCell(0, 0, "later"))];
        const cache: PolygonGeometryCache = {
            type: "test",
            cells,
            cellsById: new Map(cells.map((cell) => [cell.cell.id, cell])),
            strokePath: null,
            spatialIndex: buildPolygonSpatialIndex(cells),
        };

        expect(resolveMixedCellFromOffset(0.5, 0.5, cache)).toEqual({ id: "first" });
    });

    it("falls back instead of expanding very broad polygons across the full index", () => {
        const cells = Array.from({ length: 1_000 }, (_, index) =>
            squareCell(0, 0, `overlap:${index}`),
        );

        expect(buildPolygonSpatialIndex(cells)).toBeNull();
    });

    it("returns deduplicated rectangle intersections in source order", () => {
        const cells = Array.from({ length: 100 }, (_, index) =>
            squareCell(index % 10, Math.floor(index / 10), `cell:${index}`),
        );
        const index = buildPolygonSpatialIndex(cells);

        const candidates = polygonSpatialIndexIntersectionCandidates(index!, {
            minX: 4.25,
            maxX: 5.75,
            minY: 4.25,
            maxY: 5.75,
        });

        expect(candidates.map((candidate) => candidate.cell.id)).toEqual([
            "cell:44",
            "cell:45",
            "cell:54",
            "cell:55",
        ]);
    });

    it("returns no rectangle candidates outside the indexed extent", () => {
        const cells = Array.from({ length: 100 }, (_, index) =>
            squareCell(index % 10, Math.floor(index / 10)),
        );
        const index = buildPolygonSpatialIndex(cells);

        expect(
            polygonSpatialIndexIntersectionCandidates(index!, {
                minX: 20,
                maxX: 21,
                minY: 20,
                maxY: 21,
            }),
        ).toEqual([]);
    });
});
