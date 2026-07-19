import { describe, expect, it } from "vitest";

import { buildPolygonSpatialIndex } from "../geometry/polygon-spatial-index.js";
import { indexTopology } from "../topology-index.js";
import type { TopologyPayload } from "../types/domain.js";
import type { PolygonGeometryCache, PolygonGeometryCell } from "../types/rendering.js";
import { resolvePolygonDirtyRegionPlan } from "./polygon-dirty-region.js";

function geometryCell(id: string, x: number, y: number): PolygonGeometryCell {
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

function fixture(
    columns = 8,
    rows = 8,
): {
    topology: TopologyPayload;
    cache: PolygonGeometryCache;
} {
    const cells = Array.from({ length: rows }, (_, y) =>
        Array.from({ length: columns }, (_, x) => geometryCell(`cell:${x}:${y}`, x, y)),
    ).flat();
    const topology: TopologyPayload = {
        cells: cells.map(({ cell }) => ({ id: cell.id, kind: "cell", neighbors: [] })),
        topology_revision: "test:polygon",
        topology_spec: {
            tiling_family: "test",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: columns,
            height: rows,
            patch_depth: 0,
        },
        width: columns,
        height: rows,
    };
    return {
        topology,
        cache: {
            type: "test",
            cells,
            cellsById: new Map(cells.map((cell) => [cell.cell.id, cell])),
            strokePath: null,
            spatialIndex: buildPolygonSpatialIndex(cells),
        },
    };
}

describe("polygon dirty-region planning", () => {
    it("returns every intersection in stable topology order", () => {
        const { topology, cache } = fixture();
        const changedIndex = 3 * 8 + 3;

        const plan = resolvePolygonDirtyRegionPlan({
            topology,
            topologyIndex: indexTopology(topology),
            geometryCache: cache,
            changedCellIndexes: [changedIndex],
            canvasWidth: 8,
            canvasHeight: 8,
            dirtyPadding: 0,
            candidatePadding: 0,
        });

        expect(plan?.cellIndexes).toEqual([
            2 * 8 + 2,
            2 * 8 + 3,
            2 * 8 + 4,
            3 * 8 + 2,
            3 * 8 + 3,
            3 * 8 + 4,
            4 * 8 + 2,
            4 * 8 + 3,
            4 * 8 + 4,
        ]);
    });

    it("falls back when candidates exceed 25 percent of cells", () => {
        const { topology, cache } = fixture();

        expect(
            resolvePolygonDirtyRegionPlan({
                topology,
                topologyIndex: indexTopology(topology),
                geometryCache: cache,
                changedCellIndexes: [0, 7, 56, 63],
                canvasWidth: 8,
                canvasHeight: 8,
                dirtyPadding: 0,
                candidatePadding: 0,
            }),
        ).toBeNull();
    });

    it("falls back when the dirty bounding area exceeds 35 percent", () => {
        const { topology, cache } = fixture();

        expect(
            resolvePolygonDirtyRegionPlan({
                topology,
                topologyIndex: indexTopology(topology),
                geometryCache: cache,
                changedCellIndexes: [0, 36],
                canvasWidth: 8,
                canvasHeight: 8,
                dirtyPadding: 0,
                candidatePadding: 0,
            }),
        ).toBeNull();
    });

    it("falls back when no spatial index is available", () => {
        const { topology, cache } = fixture(4, 4);

        expect(
            resolvePolygonDirtyRegionPlan({
                topology,
                topologyIndex: indexTopology(topology),
                geometryCache: cache,
                changedCellIndexes: [0],
                canvasWidth: 4,
                canvasHeight: 4,
                dirtyPadding: 0,
                candidatePadding: 0,
            }),
        ).toBeNull();
    });
});
