import { beforeEach, describe, expect, it, vi } from "vitest";

import type { BootstrappedTopologyDefinition } from "./types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";

const SPECTRE_TOPOLOGY: BootstrappedTopologyDefinition = {
    tiling_family: "spectre",
    label: "Spectre",
    picker_group: "Aperiodic",
    picker_order: 240,
    sizing_mode: "patch_depth",
    family: "aperiodic",
    viewport_sync_mode: "presentation-only",
    supported_adjacency_modes: ["edge"],
    default_adjacency_mode: "edge",
    default_rules: { edge: "life-b2-s23" },
    geometry_keys: { edge: "spectre" },
    sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 3 },
};

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

function installSpectreGlobals(): void {
    window.APP_TOPOLOGIES = [
        {
            tiling_family: "square",
            label: "Square",
            picker_group: "Classic",
            picker_order: 10,
            sizing_mode: "grid",
            family: "regular",
            viewport_sync_mode: "backend-sync",
            supported_adjacency_modes: ["edge"],
            default_adjacency_mode: "edge",
            default_rules: { edge: "conway" },
            geometry_keys: { edge: "square" },
            sizing_policy: { control: "cell_size", default: 12, min: 8, max: 24 },
        },
        SPECTRE_TOPOLOGY,
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

describe("spectre topology", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installSpectreGlobals();
    });

    it("appears in topology picker metadata with a patch-depth topology variant", async () => {
        const { getTopologyDefinition, resolveTopologyVariantKey, tilingFamilyOptions, topologyUsesPatchDepth } = await import("./topology-catalog.js");

        expect(new Set(tilingFamilyOptions().map((option) => option.value))).toContain("spectre");
        expect(resolveTopologyVariantKey("spectre", "edge")).toBe("spectre");
        expect(getTopologyDefinition("spectre")?.picker_group).toBe("Aperiodic");
        expect(topologyUsesPatchDepth("spectre")).toBe(true);
    });

    it("resolves through the aperiodic geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");

        expect(isSupportedGeometry("spectre")).toBe(true);
        expect(getGeometryAdapter("spectre").geometry).toBe("spectre");
        expect(getGeometryAdapter("spectre").family).toBe("mixed");
    });
});
