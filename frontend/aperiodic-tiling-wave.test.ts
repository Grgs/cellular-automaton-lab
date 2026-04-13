import { beforeEach, describe, expect, it, vi } from "vitest";

import type { BootstrappedTopologyDefinition } from "./types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";

const NEW_TILINGS: ReadonlyArray<BootstrappedTopologyDefinition> = [
    {
        tiling_family: "hat-monotile",
        label: "Hat",
        picker_group: "Aperiodic",
        picker_order: 250,
        sizing_mode: "patch_depth",
        family: "aperiodic",
        render_kind: "polygon_aperiodic",
        viewport_sync_mode: "presentation-only",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "life-b2-s23" },
        geometry_keys: { edge: "hat-monotile" },
        sizing_policy: { control: "patch_depth", default: 2, min: 0, max: 3 },
    },
    {
        tiling_family: "tuebingen-triangle",
        label: "Tuebingen Triangle",
        picker_group: "Aperiodic",
        picker_order: 310,
        sizing_mode: "patch_depth",
        family: "aperiodic",
        render_kind: "polygon_aperiodic",
        viewport_sync_mode: "presentation-only",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "life-b2-s23" },
        geometry_keys: { edge: "tuebingen-triangle" },
        sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 5 },
    },
    {
        tiling_family: "dodecagonal-square-triangle",
        label: "Dodecagonal Square-Triangle",
        picker_group: "Experimental",
        picker_order: 320,
        sizing_mode: "patch_depth",
        family: "aperiodic",
        render_kind: "polygon_aperiodic",
        viewport_sync_mode: "presentation-only",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "life-b2-s23" },
        geometry_keys: { edge: "dodecagonal-square-triangle" },
        sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 4 },
    },
    {
        tiling_family: "shield",
        label: "Shield",
        picker_group: "Experimental",
        picker_order: 330,
        sizing_mode: "patch_depth",
        family: "aperiodic",
        render_kind: "polygon_aperiodic",
        viewport_sync_mode: "presentation-only",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "life-b2-s23" },
        geometry_keys: { edge: "shield" },
        sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 4 },
    },
    {
        tiling_family: "pinwheel",
        label: "Pinwheel",
        picker_group: "Experimental",
        picker_order: 340,
        sizing_mode: "patch_depth",
        family: "aperiodic",
        render_kind: "polygon_aperiodic",
        viewport_sync_mode: "presentation-only",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "life-b2-s23" },
        geometry_keys: { edge: "pinwheel" },
        sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 4 },
    },
];

function installGlobals(): void {
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
