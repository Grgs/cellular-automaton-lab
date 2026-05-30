import { describe, expect, it } from "vitest";

import {
    buildClassificationGrid,
    buildPhasePortraitModel,
    buildPhasePortraitSvg,
    classificationStyle,
    familyColor,
    normalizedSeries,
} from "./compare-charts.js";
import type { SeedComparisonResult, TopologyComparisonResultPayload } from "../types/domain.js";

function result(
    overrides: Partial<TopologyComparisonResultPayload>,
): TopologyComparisonResultPayload {
    return {
        geometry: "square",
        tiling_family: "square",
        family: "regular",
        cell_count: 100,
        seed_bits: 5,
        seed_cells: 3,
        initial_population: 3,
        final_population: 3,
        normalized_population: 1,
        classification: "still-life",
        period: 1,
        steps_run: 2,
        extinction_step: null,
        note: null,
        population: [3, 3, 3],
        change_rate: [0, 0],
        ...overrides,
    };
}

function comparison(results: TopologyComparisonResultPayload[]): SeedComparisonResult {
    return {
        rule_name: "conway",
        seed: "111",
        seed_bits: 3,
        traversal: "bfs",
        steps: 2,
        grid_size: 16,
        degenerate: false,
        results,
    };
}

describe("compare-charts helpers", () => {
    it("colours by family with a fallback", () => {
        expect(familyColor("regular")).toBe("#bf5a36");
        expect(familyColor("aperiodic")).toBe("#3a5a9f");
        expect(familyColor("nonsense")).toBe("#6d756f");
    });

    it("maps classifications to readable labels", () => {
        expect(classificationStyle("extinct").label).toBe("Extinct");
        expect(classificationStyle("still-life").label).toBe("Still life");
        expect(classificationStyle("oscillator-p2").label).toBe("Oscillator (p2)");
        expect(classificationStyle("error").label).toBe("Error");
        expect(classificationStyle("custom").label).toBe("custom");
    });

    it("normalises population against the initial live count", () => {
        expect(normalizedSeries(result({ population: [4, 2, 1] }))).toEqual([1, 0.5, 0.25]);
        expect(normalizedSeries(result({ population: [0, 0] }))).toEqual([0, 0]);
    });
});

describe("buildPhasePortraitModel", () => {
    it("excludes error rows and scales to the observed maximum", () => {
        const model = buildPhasePortraitModel(
            comparison([
                result({ geometry: "square", population: [2, 4] }),
                result({ geometry: "broken", classification: "error", population: [] }),
            ]),
            { width: 100, height: 100, padding: 10 },
        );
        expect(model.series).toHaveLength(1);
        expect(model.series[0]?.geometry).toBe("square");
        // First point sits on the baseline (live(t)/live(0) = 1), final point doubles to 2.
        expect(model.yMax).toBe(2);
        const points = model.series[0]?.points ?? [];
        expect(points[0]?.[0]).toBeCloseTo(10); // x at generation 0 == left padding
        expect(points[1]?.[1]).toBeCloseTo(10); // y at value 2 (== yMax) == top padding
    });
});

describe("DOM builders", () => {
    it("renders one polyline per non-error tiling with a geometry hook", () => {
        const svg = buildPhasePortraitSvg(
            comparison([
                result({ geometry: "square", population: [3, 2, 1] }),
                result({ geometry: "hex", population: [3, 3, 3] }),
            ]),
        );
        const lines = svg.querySelectorAll(".compare-portrait__line");
        expect(lines).toHaveLength(2);
        expect(svg.querySelector("[data-geometry='square']")).not.toBeNull();
    });

    it("builds a classification grid sorted by family then geometry", () => {
        const grid = buildClassificationGrid(
            comparison([
                result({ geometry: "spectre", family: "aperiodic", classification: "extinct" }),
                result({ geometry: "square", family: "regular" }),
            ]),
        );
        const names = [...grid.querySelectorAll(".compare-grid__name")].map((n) => n.textContent);
        expect(names).toEqual(["spectre", "square"]);
        expect(grid.querySelectorAll(".compare-chip")).toHaveLength(2);
    });
});
