import { beforeEach, describe, expect, it, vi } from "vitest";

import { getFixtureTopologyDefinition, installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("sphinx topology", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installFrontendGlobals();
    });

    it("appears in topology picker metadata with patch-depth sizing", async () => {
        const {
            getTopologyDefinition,
            adjacencyModeOptions,
            resolveTopologyVariantKey,
            tilingFamilyOptions,
            topologyModeFieldLabel,
            topologyUsesPatchDepth,
        } = await import("./topology-catalog.js");
        const sphinx = getFixtureTopologyDefinition("sphinx");

        expect(new Set(tilingFamilyOptions().map((option) => option.value))).toContain("sphinx");
        expect(resolveTopologyVariantKey("sphinx", "edge")).toBe(sphinx.geometry_keys.edge);
        expect(resolveTopologyVariantKey("sphinx", "compact")).toBe(sphinx.geometry_keys.compact);
        expect(resolveTopologyVariantKey("sphinx", "wide")).toBe(sphinx.geometry_keys.wide);
        expect(getTopologyDefinition("sphinx")?.render_kind).toBe("polygon_aperiodic");
        expect(adjacencyModeOptions("sphinx")).toEqual([
            { value: "edge", label: "Balanced seed" },
            { value: "compact", label: "Compact seed" },
            { value: "wide", label: "Wide seed" },
        ]);
        expect(topologyModeFieldLabel("sphinx")).toBe("Seed");
        expect(topologyUsesPatchDepth("sphinx")).toBe(true);
    });

    it("resolves through the render-kind geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");
        const geometry = getFixtureTopologyDefinition("sphinx").geometry_keys.edge;

        expect(isSupportedGeometry(geometry)).toBe(true);
        expect(getGeometryAdapter(geometry).geometry).toBe(geometry);
        expect(getGeometryAdapter(geometry).family).toBe("mixed");
    });
});
