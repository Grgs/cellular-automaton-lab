import { beforeEach, describe, expect, it, vi } from "vitest";

import type { BootstrappedTopologyDefinition } from "../types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "../types/rendering.js";

function topologyEntry(
    tilingFamily: string,
    geometryKey: string,
    renderKind: string,
): BootstrappedTopologyDefinition {
    return {
        tiling_family: tilingFamily,
        label: tilingFamily,
        picker_group: "Fixture",
        picker_order: 1,
        sizing_mode: renderKind === "polygon_aperiodic" ? "patch_depth" : "grid",
        family: renderKind === "regular_grid" ? "regular" : renderKind === "polygon_aperiodic" ? "aperiodic" : "mixed",
        render_kind: renderKind,
        viewport_sync_mode: renderKind === "polygon_aperiodic" ? "presentation-only" : "backend-sync",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "life-b2-s23" },
        geometry_keys: { edge: geometryKey },
        sizing_policy: {
            control: renderKind === "polygon_aperiodic" ? "patch_depth" : "cell_size",
            default: 3,
            min: 0,
            max: 6,
        },
    };
}

describe("geometry registry render-kind dispatch", () => {
    beforeEach(() => {
        vi.resetModules();
        window.APP_TOPOLOGIES = [
            topologyEntry("square", "square", "regular_grid"),
            topologyEntry("fixture-periodic", "fixture-periodic", "polygon_periodic"),
            topologyEntry("fixture-aperiodic", "fixture-aperiodic", "polygon_aperiodic"),
        ];
        window.APP_PERIODIC_FACE_TILINGS = [
            {
                geometry: "fixture-periodic",
                label: "Fixture Periodic",
                metric_model: "pattern",
                base_edge: 52,
                unit_width: 100,
                unit_height: 100,
                min_dimension: 1,
                min_x: 0,
                min_y: 0,
                max_x: 100,
                max_y: 100,
                cell_count_per_unit: 1,
                row_offset_x: 0,
            } satisfies PeriodicFaceTilingDescriptor,
        ];
    });

    it("creates polygon adapters from bootstrapped render kinds", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./registry.js");

        expect(isSupportedGeometry("fixture-periodic")).toBe(true);
        expect(isSupportedGeometry("fixture-aperiodic")).toBe(true);
        expect(getGeometryAdapter("fixture-periodic").geometry).toBe("fixture-periodic");
        expect(getGeometryAdapter("fixture-aperiodic").geometry).toBe("fixture-aperiodic");
    });
});
