import { describe, expect, it } from "vitest";

import { sampleRenderDiagnostics } from "./render-diagnostics.js";
import type { TopologyPayload } from "../types/domain.js";
import type { PolygonGeometryCache, PolygonGeometryCell } from "../types/rendering.js";

describe("canvas/render-diagnostics", () => {
    it("samples diagnostics for large polygon topologies without spreading vertices", () => {
        const cells = Array.from({ length: 20_000 }, (_, index) => {
            const x = index % 200;
            const y = Math.floor(index / 200);
            return {
                id: `cell:${index}`,
                kind: "tile",
                center: { x: x + 0.5, y: y + 0.5 },
                vertices: [
                    { x, y },
                    { x: x + 1, y },
                    { x: x + 1, y: y + 1 },
                    { x, y: y + 1 },
                ],
                neighbors: [],
            };
        });
        const topology: TopologyPayload = {
            topology_revision: "large-polygon",
            topology_spec: {
                tiling_family: "archimedean-3-3-3-3-6",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 200,
                height: 100,
                patch_depth: 3,
            },
            cells,
        };
        const geometryCells: PolygonGeometryCell[] = cells.map((cell) => {
            const vertices = cell.vertices;
            return {
                cell,
                vertices,
                centerX: cell.center.x,
                centerY: cell.center.y,
                minX: vertices[0]!.x,
                maxX: vertices[1]!.x,
                minY: vertices[0]!.y,
                maxY: vertices[2]!.y,
            };
        });
        const geometryCache: PolygonGeometryCache = {
            type: "mixed",
            cells: geometryCells,
            cellsById: new Map(geometryCells.map((cell) => [cell.cell.id, cell])),
            strokePath: null,
        };

        expect(
            sampleRenderDiagnostics(topology, geometryCache, {
                geometry: "archimedean-3-3-3-3-6",
                adapterFamily: "mixed",
                metrics: {
                    geometry: "archimedean-3-3-3-3-6",
                    width: 200,
                    height: 100,
                    cellSize: 12,
                    gap: 0,
                    xInset: 0,
                    yInset: 0,
                    cssWidth: 200,
                    cssHeight: 100,
                    pixelWidth: 200,
                    pixelHeight: 100,
                    dpr: 1,
                },
                cellSize: 12,
            })?.topologyBounds,
        ).toEqual({
            minX: 0,
            maxX: 200,
            minY: 0,
            maxY: 100,
            width: 200,
            height: 100,
        });
    });
});
