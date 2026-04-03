import { beforeEach, describe, expect, it, vi } from "vitest";

import type { BootstrappedTopologyDefinition } from "./types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";

const NEW_PERIODIC_TILINGS = [
    { geometry: "rhombille", label: "Rhombille", defaultCellSize: 12, maxCellSize: 20 },
    { geometry: "tetrakis-square", label: "Tetrakis Square", defaultCellSize: 12, maxCellSize: 20 },
    { geometry: "triakis-triangular", label: "Triakis Triangular", defaultCellSize: 12, maxCellSize: 20 },
    { geometry: "deltoidal-trihexagonal", label: "Deltoidal Trihexagonal", defaultCellSize: 12, maxCellSize: 20 },
    { geometry: "prismatic-pentagonal", label: "Prismatic Pentagonal", defaultCellSize: 10, maxCellSize: 18 },
    { geometry: "floret-pentagonal", label: "Floret Pentagonal", defaultCellSize: 10, maxCellSize: 18 },
    { geometry: "snub-square-dual", label: "Snub Square Dual", defaultCellSize: 10, maxCellSize: 18 },
] as const;

const EXISTING_PERIODIC_TILINGS = [
    { geometry: "archimedean-4-8-8", label: "4.8.8" },
    { geometry: "archimedean-3-12-12", label: "3.12.12" },
    { geometry: "archimedean-3-4-6-4", label: "3.4.6.4" },
    { geometry: "archimedean-4-6-12", label: "4.6.12" },
    { geometry: "archimedean-3-3-4-3-4", label: "3.3.4.3.4" },
    { geometry: "archimedean-3-3-3-4-4", label: "3.3.3.4.4" },
    { geometry: "archimedean-3-3-3-3-6", label: "3.3.3.3.6" },
    { geometry: "trihexagonal-3-6-3-6", label: "3.6.3.6" },
    { geometry: "cairo-pentagonal", label: "Cairo Pentagonal" },
] as const;

function installPeriodicMixedGlobals(): void {
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
        ...NEW_PERIODIC_TILINGS.map((entry, index): BootstrappedTopologyDefinition => ({
            tiling_family: entry.geometry,
            label: entry.label,
            picker_group: "Periodic Mixed",
            picker_order: 200 + (index * 10),
            sizing_mode: "grid",
            family: "mixed",
            viewport_sync_mode: "backend-sync",
            supported_adjacency_modes: ["edge"],
            default_adjacency_mode: "edge",
            default_rules: { edge: "life-b2-s23" },
            geometry_keys: { edge: entry.geometry },
            sizing_policy: { control: "cell_size", default: entry.defaultCellSize, min: 8, max: entry.maxCellSize },
        })),
    ];
    window.APP_PERIODIC_FACE_TILINGS = [...EXISTING_PERIODIC_TILINGS, ...NEW_PERIODIC_TILINGS].map(
        (entry): PeriodicFaceTilingDescriptor => ({
            geometry: entry.geometry,
            label: entry.label,
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

describe("new periodic mixed tilings", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installPeriodicMixedGlobals();
    });

    it("appear in topology picker metadata with their geometry keys", async () => {
        const { tilingFamilyOptions, resolveTopologyVariantKey } = await import("./topology-catalog.js");

        const optionValues = new Set(tilingFamilyOptions().map((option) => option.value));
        for (const entry of NEW_PERIODIC_TILINGS) {
            expect(optionValues.has(entry.geometry)).toBe(true);
            expect(resolveTopologyVariantKey(entry.geometry, "edge")).toBe(entry.geometry);
        }
    });

    it("resolve through the periodic mixed geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");

        for (const entry of NEW_PERIODIC_TILINGS) {
            expect(isSupportedGeometry(entry.geometry)).toBe(true);
            expect(getGeometryAdapter(entry.geometry).geometry).toBe(entry.geometry);
            expect(getGeometryAdapter(entry.geometry).family).toBe("mixed");
        }
    });
});
