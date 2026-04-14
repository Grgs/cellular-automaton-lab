import { beforeEach, describe, expect, it, vi } from "vitest";

import {
    buildSingleVariantBootstrappedTopologyDefinition,
} from "./test-helpers/topology-catalog-fixtures.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";

const NEW_TILINGS = [
    buildSingleVariantBootstrappedTopologyDefinition("hat-monotile", {
        geometryKey: "hat-monotile",
        renderKind: "polygon_aperiodic",
        defaultRule: "life-b2-s23",
        sizingPolicy: { control: "patch_depth", default: 2, min: 0, max: 3 },
    }),
    buildSingleVariantBootstrappedTopologyDefinition("tuebingen-triangle", {
        geometryKey: "tuebingen-triangle",
        renderKind: "polygon_aperiodic",
        defaultRule: "life-b2-s23",
        sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 5 },
    }),
    buildSingleVariantBootstrappedTopologyDefinition("dodecagonal-square-triangle", {
        geometryKey: "dodecagonal-square-triangle",
        renderKind: "polygon_aperiodic",
        defaultRule: "life-b2-s23",
        sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 4 },
    }),
    buildSingleVariantBootstrappedTopologyDefinition("shield", {
        geometryKey: "shield",
        renderKind: "polygon_aperiodic",
        defaultRule: "life-b2-s23",
        sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 4 },
    }),
    buildSingleVariantBootstrappedTopologyDefinition("pinwheel", {
        geometryKey: "pinwheel",
        renderKind: "polygon_aperiodic",
        defaultRule: "life-b2-s23",
        sizingPolicy: { control: "patch_depth", default: 3, min: 0, max: 4 },
    }),
] as const;

function installGlobals(): void {
    window.APP_TOPOLOGIES = [
        buildSingleVariantBootstrappedTopologyDefinition("square", {
            geometryKey: "square",
            renderKind: "regular_grid",
            defaultRule: "conway",
            sizingPolicy: { control: "cell_size", default: 12, min: 8, max: 24 },
        }),
        ...NEW_TILINGS,
    ];
    window.APP_PERIODIC_FACE_TILINGS = [
        {
            geometry: "deltoidal-hexagonal",
            label: "Deltoidal Hexagonal",
            metric_model: "pattern",
            base_edge: 73.539105,
            unit_width: 104,
            unit_height: 104,
            min_dimension: 1,
            min_x: 0,
            min_y: 0,
            max_x: 104,
            max_y: 104,
            cell_count_per_unit: 2,
            row_offset_x: 0,
        } satisfies PeriodicFaceTilingDescriptor,
    ];
}

describe("next aperiodic tiling wave", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installGlobals();
    });

    it("appears in topology picker metadata with patch-depth sizing", async () => {
        const { getTopologyDefinition, resolveTopologyVariantKey, tilingFamilyOptions, topologyUsesPatchDepth } = await import("./topology-catalog.js");

        const optionValues = new Set(tilingFamilyOptions().map((option) => option.value));
        for (const definition of NEW_TILINGS) {
            expect(optionValues).toContain(definition.tiling_family);
            expect(resolveTopologyVariantKey(definition.tiling_family, "edge")).toBe(definition.geometry_keys.edge);
            expect(getTopologyDefinition(definition.tiling_family)?.render_kind).toBe("polygon_aperiodic");
            expect(topologyUsesPatchDepth(definition.tiling_family)).toBe(true);
        }
    });

    it("resolves through the render-kind geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");

        for (const definition of NEW_TILINGS) {
            const geometry = definition.geometry_keys.edge;
            expect(isSupportedGeometry(geometry)).toBe(true);
            expect(getGeometryAdapter(geometry).geometry).toBe(geometry);
            expect(getGeometryAdapter(geometry).family).toBe("mixed");
        }
    });
});
