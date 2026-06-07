import { describe, expect, it } from "vitest";

import { buildBoardThumbnailSvg, computeBounds, fitDimensions } from "./compare-thumbnail.js";
import type { TopologyPreview, TopologySpec } from "../types/domain.js";

function topologySpec(): TopologySpec {
    return {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 2,
        height: 1,
        patch_depth: 0,
    };
}

function preview(): TopologyPreview {
    return {
        topology_revision: "r",
        topology_spec: topologySpec(),
        cells: [
            {
                id: "a",
                kind: "square",
                center: { x: 0.5, y: 0.5 },
                vertices: [
                    { x: 0, y: 0 },
                    { x: 1, y: 0 },
                    { x: 1, y: 1 },
                    { x: 0, y: 1 },
                ],
            },
            {
                id: "b",
                kind: "square",
                center: { x: 1.5, y: 0.5 },
                vertices: [
                    { x: 1, y: 0 },
                    { x: 2, y: 0 },
                    { x: 2, y: 1 },
                    { x: 1, y: 1 },
                ],
            },
        ],
    };
}

describe("compare-thumbnail geometry", () => {
    it("computes a bounding box over every vertex", () => {
        expect(computeBounds(preview().cells)).toEqual({ minX: 0, minY: 0, maxX: 2, maxY: 1 });
    });

    it("falls back to a unit box when there are no cells", () => {
        expect(computeBounds([])).toEqual({ minX: 0, minY: 0, maxX: 1, maxY: 1 });
    });

    it("fits dimensions to the longer axis preserving aspect ratio", () => {
        expect(fitDimensions({ minX: 0, minY: 0, maxX: 2, maxY: 1 }, 100)).toEqual({
            width: 100,
            height: 50,
        });
        expect(fitDimensions({ minX: 0, minY: 0, maxX: 1, maxY: 4 }, 80)).toEqual({
            width: 20,
            height: 80,
        });
    });
});

describe("buildBoardThumbnailSvg", () => {
    it("renders one polygon per cell and marks live cells", () => {
        const svg = buildBoardThumbnailSvg(preview(), { a: 1 });
        const polygons = svg.querySelectorAll("polygon");
        expect(polygons).toHaveLength(2);
        expect(svg.getAttribute("viewBox")).toBe("0 0 2 1");
        const live = svg.querySelectorAll("polygon.is-live");
        expect(live).toHaveLength(1);
        expect(live[0]?.getAttribute("points")).toContain("0,0");
    });

    it("uses the provided live color for non-zero states", () => {
        const svg = buildBoardThumbnailSvg(preview(), { a: 2 }, { liveColor: () => "#abcdef" });
        const live = svg.querySelector("polygon.is-live");
        expect(live?.getAttribute("fill")).toBe("#abcdef");
    });
});
