import { beforeEach, describe, expect, it, vi } from "vitest";

import { getFixtureTopologyDefinition, installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("robinson triangles topology", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installFrontendGlobals();
    });

    it("appears in topology picker metadata with patch-depth sizing", async () => {
        const { getTopologyDefinition, resolveTopologyVariantKey, tilingFamilyOptions, topologyUsesPatchDepth } = await import("./topology-catalog.js");
        const robinson = getFixtureTopologyDefinition("robinson-triangles");

        expect(new Set(tilingFamilyOptions().map((option) => option.value))).toContain("robinson-triangles");
        expect(resolveTopologyVariantKey("robinson-triangles", "edge")).toBe(robinson.geometry_keys.edge);
        expect(getTopologyDefinition("robinson-triangles")?.render_kind).toBe("polygon_aperiodic");
        expect(topologyUsesPatchDepth("robinson-triangles")).toBe(true);
    });

    it("resolves through the render-kind geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");
        const geometry = getFixtureTopologyDefinition("robinson-triangles").geometry_keys.edge;

        expect(isSupportedGeometry(geometry)).toBe(true);
        expect(getGeometryAdapter(geometry).geometry).toBe(geometry);
        expect(getGeometryAdapter(geometry).family).toBe("mixed");
    });
});
