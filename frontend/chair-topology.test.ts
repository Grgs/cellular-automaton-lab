import { beforeEach, describe, expect, it, vi } from "vitest";

import type { BootstrappedTopologyDefinition } from "./types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";

const CHAIR_TOPOLOGY: BootstrappedTopologyDefinition = {
    tiling_family: "chair",
    label: "Chair",
    picker_group: "Experimental",
    picker_order: 290,
    sizing_mode: "patch_depth",
    family: "aperiodic",
    render_kind: "polygon_aperiodic",
    viewport_sync_mode: "presentation-only",
    supported_adjacency_modes: ["edge"],
    default_adjacency_mode: "edge",
    default_rules: { edge: "life-b2-s23" },
    geometry_keys: { edge: "chair" },
    sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 5 },
};

function installChairGlobals(): void {
    window.APP_TOPOLOGIES = [
        {
            tiling_family: "square",
            label: "Square",
            picker_group: "Classic",
            picker_order: 10,
            sizing_mode: "grid",
            family: "regular",
            render_kind: "regular_grid",
            viewport_sync_mode: "backend-sync",
            supported_adjacency_modes: ["edge"],
            default_adjacency_mode: "edge",
            default_rules: { edge: "conway" },
            geometry_keys: { edge: "square" },
            sizing_policy: { control: "cell_size", default: 12, min: 8, max: 24 },
        },
        CHAIR_TOPOLOGY,
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

describe("chair topology", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installChairGlobals();
    });

    it("appears in topology picker metadata with patch-depth sizing", async () => {
        const { getTopologyDefinition, resolveTopologyVariantKey, tilingFamilyOptions, topologyUsesPatchDepth } = await import("./topology-catalog.js");

        expect(new Set(tilingFamilyOptions().map((option) => option.value))).toContain("chair");
        expect(resolveTopologyVariantKey("chair", "edge")).toBe("chair");
        expect(getTopologyDefinition("chair")?.render_kind).toBe("polygon_aperiodic");
        expect(getTopologyDefinition("chair")?.picker_group).toBe("Experimental");
        expect(topologyUsesPatchDepth("chair")).toBe(true);
    });

    it("resolves through the render-kind geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");

        expect(isSupportedGeometry("chair")).toBe(true);
        expect(getGeometryAdapter("chair").geometry).toBe("chair");
        expect(getGeometryAdapter("chair").family).toBe("mixed");
    });
});
