import { beforeEach, describe, expect, it, vi } from "vitest";

import { getFixtureTopologyDefinition, installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("spectre topology", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installFrontendGlobals();
    });

    it("appears in topology picker metadata with a patch-depth topology variant", async () => {
        const {
            getTopologyDefinition,
            resolveTopologyVariantKey,
            tilingFamilyOptions,
            topologyUsesPatchDepth,
        } = await import("./topology-catalog.js");
        const spectre = getFixtureTopologyDefinition("spectre");

        expect(new Set(tilingFamilyOptions().map((option) => option.value))).toContain("spectre");
        expect(resolveTopologyVariantKey("spectre", "edge")).toBe(spectre.geometry_keys.edge);
        expect(getTopologyDefinition("spectre")?.picker_group).toBe("Aperiodic");
        expect(topologyUsesPatchDepth("spectre")).toBe(true);
    });

    it("resolves through the aperiodic geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");
        const geometry = getFixtureTopologyDefinition("spectre").geometry_keys.edge;

        expect(isSupportedGeometry(geometry)).toBe(true);
        expect(getGeometryAdapter(geometry).geometry).toBe(geometry);
        expect(getGeometryAdapter(geometry).family).toBe("mixed");
    });
});
