import { beforeEach, describe, expect, it, vi } from "vitest";

import { getFixtureTopologyDefinition, installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("chair topology", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installFrontendGlobals();
    });

    it("appears in topology picker metadata with patch-depth sizing", async () => {
        const {
            getTopologyDefinition,
            resolveTopologyVariantKey,
            tilingFamilyOptions,
            topologyUsesPatchDepth,
        } = await import("./topology-catalog.js");
        const chair = getFixtureTopologyDefinition("chair");

        expect(new Set(tilingFamilyOptions().map((option) => option.value))).toContain("chair");
        expect(resolveTopologyVariantKey("chair", "edge")).toBe(chair.geometry_keys.edge);
        expect(getTopologyDefinition("chair")?.render_kind).toBe("polygon_aperiodic");
        expect(getTopologyDefinition("chair")?.picker_group).toBe("Aperiodic");
        expect(topologyUsesPatchDepth("chair")).toBe(true);
    });

    it("resolves through the render-kind geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");
        const geometry = getFixtureTopologyDefinition("chair").geometry_keys.edge;

        expect(isSupportedGeometry(geometry)).toBe(true);
        expect(getGeometryAdapter(geometry).geometry).toBe(geometry);
        expect(getGeometryAdapter(geometry).family).toBe("mixed");
    });
});
