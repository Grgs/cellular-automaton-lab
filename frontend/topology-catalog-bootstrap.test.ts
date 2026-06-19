import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("bootstrapped topology catalog", () => {
    beforeEach(() => {
        vi.resetModules();
        installFrontendGlobals();
    });

    it("exposes every topology through the picker and its default geometry adapter", async () => {
        const definitions = window.APP_TOPOLOGIES;
        const { resolveTopologyVariantKey, tilingFamilyOptions } =
            await import("./topology-catalog.js");
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");
        const pickerValues = new Set(tilingFamilyOptions().map((option) => option.value));

        for (const definition of definitions) {
            const geometry = definition.geometry_keys[definition.default_adjacency_mode];

            expect(pickerValues, definition.tiling_family).toContain(definition.tiling_family);
            expect(resolveTopologyVariantKey(definition.tiling_family)).toBe(geometry);
            expect(isSupportedGeometry(geometry), geometry).toBe(true);
            expect(getGeometryAdapter(geometry).geometry).toBe(geometry);
        }
    });

    it("uses topology-catalog labels for periodic rendering descriptors", () => {
        for (const descriptor of window.APP_PERIODIC_FACE_TILINGS) {
            const definition = window.APP_TOPOLOGIES.find((candidate) =>
                Object.values(candidate.geometry_keys).includes(descriptor.geometry),
            );

            expect(definition, descriptor.geometry).toBeDefined();
            expect(descriptor.label).toBe(definition?.label);
        }
    });
});
