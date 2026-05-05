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

    it("applies shield seam hiding in draw space without mutating geometry vertices", async () => {
        const drawPolygonCellWithTransientOverlay = vi.fn();
        vi.doMock("../canvas/draw.js", async () => {
            const actual = await vi.importActual<typeof import("../canvas/draw.js")>("../canvas/draw.js");
            return {
                ...actual,
                drawPolygonCellWithTransientOverlay,
            };
        });

        const { createAperiodicPrototileGeometryAdapter } = await import("./aperiodic-prototile-adapter.js");
        const adapter = createAperiodicPrototileGeometryAdapter("shield");
        const topology = {
            topology_spec: {
                tiling_family: "shield",
                adjacency_mode: "edge",
                sizing_mode: "patch_depth",
                width: 0,
                height: 0,
                patch_depth: 3,
            },
            topology_revision: "fixture-shield-adapter-draw",
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
        const geometry = adapter.buildCellGeometry?.({
            cell: topology.cells[0]!,
            metrics,
            cache: null,
        });
        if (!geometry) {
            throw new Error("Expected shield geometry.");
        }

        adapter.drawCell({
            context: {} as CanvasRenderingContext2D,
            cell: topology.cells[0]!,
            stateValue: 0,
            metrics,
            cache: {
                type: "shield",
                cells: [geometry],
                cellsById: new Map([[geometry.cell.id, geometry]]),
                strokePath: null,
            },
            colors: {
                line: "#000",
                dead: "#fff",
                deadAlt: "#eee",
                lineSoft: "#111",
                lineStrong: "#222",
                lineAperiodic: "#333",
                live: "#444",
                accent: "#555",
                accentStrong: "#666",
                toneCream: "#f8f1e5",
                toneLinen: "#ead6b6",
                toneSand: "#efe4d0",
                toneFlax: "#e1cdac",
                toneTan: "#e5c089",
                toneStone: "#d5bb8f",
                toneRose: "#dbc1b2",
                toneClay: "#c88d4b",
                toneShadow: "#b89a6e",
            },
            colorLookup: new Map([[0, "#f8f1e5"]]),
            renderStyle: {
                mode: "standard",
                geometry: "shield",
                lineColorToken: "lineSoft",
                triangleStrokeEnabled: false,
                lineColor: "#111",
                aperiodicLineColor: "#222",
                hoverTintColor: "#333",
                hoverStrokeColor: "#444",
                selectionTintColor: "#555",
                selectionStrokeColor: "#666",
                gesturePaintStrokeColor: "#777",
                gestureEraseStrokeColor: "#888",
            },
            renderLayer: "committed",
            resolveRenderedCellColor: () => "#f8f1e5",
        });

        expect(drawPolygonCellWithTransientOverlay).toHaveBeenCalledTimes(1);
        expect(drawPolygonCellWithTransientOverlay.mock.calls[0]?.[0]).toMatchObject({
            committedStrokeColor: null,
            fillBridgeColor: "#f8f1e5",
            fillBridgeStrokeWidth: 1.25,
            vertices: geometry.vertices,
        });
    });
});
