import { beforeEach, describe, expect, it, vi } from "vitest";

import { getFixtureTopologyDefinition, installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("taylor-socolar topology", () => {
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
        const taylorSocolar = getFixtureTopologyDefinition("taylor-socolar");

        expect(new Set(tilingFamilyOptions().map((option) => option.value))).toContain(
            "taylor-socolar",
        );
        expect(resolveTopologyVariantKey("taylor-socolar", "edge")).toBe(
            taylorSocolar.geometry_keys.edge,
        );
        expect(getTopologyDefinition("taylor-socolar")?.picker_group).toBe("Aperiodic");
        expect(topologyUsesPatchDepth("taylor-socolar")).toBe(true);
    });

    it("resolves through the aperiodic geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");
        const geometry = getFixtureTopologyDefinition("taylor-socolar").geometry_keys.edge;

        expect(isSupportedGeometry(geometry)).toBe(true);
        expect(getGeometryAdapter(geometry).geometry).toBe(geometry);
        expect(getGeometryAdapter(geometry).family).toBe("mixed");
    });
});
