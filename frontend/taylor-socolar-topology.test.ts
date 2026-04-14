import { beforeEach, describe, expect, it, vi } from "vitest";

import { buildSingleVariantBootstrappedTopologyDefinition } from "./test-helpers/topology-catalog-fixtures.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";

const TAYLOR_SOCOLAR_TOPOLOGY = buildSingleVariantBootstrappedTopologyDefinition("taylor-socolar", {
    geometryKey: "taylor-socolar",
    renderKind: "polygon_aperiodic",
    defaultRule: "life-b2-s23",
    sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 5 },
});

const PERIODIC_MIXED_GEOMETRIES = [
    "archimedean-4-8-8",
    "archimedean-3-12-12",
    "archimedean-3-4-6-4",
    "archimedean-4-6-12",
    "archimedean-3-3-4-3-4",
    "archimedean-3-3-3-4-4",
    "archimedean-3-3-3-3-6",
    "trihexagonal-3-6-3-6",
    "cairo-pentagonal",
    "rhombille",
    "deltoidal-trihexagonal",
    "tetrakis-square",
    "triakis-triangular",
    "prismatic-pentagonal",
    "floret-pentagonal",
    "snub-square-dual",
] as const;

function installTaylorSocolarGlobals(): void {
    window.APP_TOPOLOGIES = [
        buildSingleVariantBootstrappedTopologyDefinition("square", {
            geometryKey: "square",
            renderKind: "regular_grid",
            defaultRule: "conway",
            sizingPolicy: { control: "cell_size", default: 12, min: 8, max: 24 },
        }),
        TAYLOR_SOCOLAR_TOPOLOGY,
    ];
    window.APP_PERIODIC_FACE_TILINGS = PERIODIC_MIXED_GEOMETRIES.map(
        (geometry): PeriodicFaceTilingDescriptor => ({
            geometry,
            label: geometry,
            metric_model: "pattern",
            base_edge: 52,
            unit_width: 100,
            unit_height: 100,
            min_dimension: 1,
            min_x: -10,
            min_y: -10,
            max_x: 110,
            max_y: 110,
            cell_count_per_unit: 4,
            row_offset_x: 0,
        }),
    );
}

describe("taylor-socolar topology", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installTaylorSocolarGlobals();
    });

    it("appears in topology picker metadata with a patch-depth topology variant", async () => {
        const { getTopologyDefinition, resolveTopologyVariantKey, tilingFamilyOptions, topologyUsesPatchDepth } = await import("./topology-catalog.js");

        expect(new Set(tilingFamilyOptions().map((option) => option.value))).toContain("taylor-socolar");
        expect(resolveTopologyVariantKey("taylor-socolar", "edge")).toBe("taylor-socolar");
        expect(getTopologyDefinition("taylor-socolar")?.picker_group).toBe("Aperiodic");
        expect(topologyUsesPatchDepth("taylor-socolar")).toBe(true);
    });

    it("resolves through the aperiodic geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");

        expect(isSupportedGeometry("taylor-socolar")).toBe(true);
        expect(getGeometryAdapter("taylor-socolar").geometry).toBe("taylor-socolar");
        expect(getGeometryAdapter("taylor-socolar").family).toBe("mixed");
    });
});
