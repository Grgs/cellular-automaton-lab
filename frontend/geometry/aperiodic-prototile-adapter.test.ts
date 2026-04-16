import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

describe("geometry/aperiodic-prototile-adapter", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installFrontendGlobals();
    });

    it("renders shield polygons edge-to-edge without an extra display shrink", async () => {
        const { createAperiodicPrototileGeometryAdapter } = await import("./aperiodic-prototile-adapter.js");
        const adapter = createAperiodicPrototileGeometryAdapter("shield");
        if (!adapter.buildCellGeometry) {
            throw new Error("Aperiodic adapter must expose buildCellGeometry for shield fixtures.");
        }
        const topology = {
            topology_spec: {
                tiling_family: "shield",
                adjacency_mode: "edge",
                sizing_mode: "patch_depth",
                width: 0,
                height: 0,
                patch_depth: 3,
            },
            topology_revision: "fixture-shield-adapter",
            cells: [
                {
                    id: "shield:test",
                    kind: "shield-square",
                    neighbors: [],
                    center: { x: 0, y: 0 },
                    vertices: [
                        { x: -2, y: -2 },
                        { x: 2, y: -2 },
                        { x: 2, y: 2 },
                        { x: -2, y: 2 },
                    ],
                    tile_family: "shield",
                    orientation_token: "0",
                },
            ],
        };
        const metrics = adapter.buildMetrics({
            width: 0,
            height: 0,
            cellSize: 10,
            topology,
        });
        const geometry = adapter.buildCellGeometry({
            cell: topology.cells[0]!,
            metrics,
            cache: null,
        });

        expect(geometry).not.toBeNull();
        expect((geometry?.maxX ?? 0) - (geometry?.minX ?? 0)).toBeCloseTo(140, 6);
        expect((geometry?.maxY ?? 0) - (geometry?.minY ?? 0)).toBeCloseTo(140, 6);
    });
});
