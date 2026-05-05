import { beforeEach, describe, expect, it, vi } from "vitest";

import {
    getFixtureAperiodicFamilyDefinition,
    getFixtureTopologyDefinition,
    installFrontendGlobals,
} from "./test-helpers/bootstrap.js";

const NEW_TILING_IDS = [
    "hat-monotile",
    "tuebingen-triangle",
    "dodecagonal-square-triangle",
    "shield",
    "pinwheel",
] as const;

describe("next aperiodic tiling wave", () => {
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

        const optionValues = new Set(tilingFamilyOptions().map((option) => option.value));
        for (const tilingFamily of NEW_TILING_IDS) {
            const definition = getFixtureTopologyDefinition(tilingFamily);
            expect(optionValues).toContain(tilingFamily);
            expect(resolveTopologyVariantKey(tilingFamily, "edge")).toBe(
                definition.geometry_keys.edge,
            );
            expect(getTopologyDefinition(tilingFamily)?.render_kind).toBe("polygon_aperiodic");
            expect(topologyUsesPatchDepth(tilingFamily)).toBe(true);
        }

        const pinwheelMetadata = getFixtureAperiodicFamilyDefinition("pinwheel");
        if (pinwheelMetadata.experimental) {
            expect(
                tilingFamilyOptions().find((option) => option.value === "pinwheel")?.label,
            ).toContain("Experimental");
        }
    });

    it("resolves through the render-kind geometry registry", async () => {
        const { getGeometryAdapter, isSupportedGeometry } = await import("./geometry/registry.js");

        for (const tilingFamily of NEW_TILING_IDS) {
            const geometry = getFixtureTopologyDefinition(tilingFamily).geometry_keys.edge;
            expect(isSupportedGeometry(geometry)).toBe(true);
            expect(getGeometryAdapter(geometry).geometry).toBe(geometry);
            expect(getGeometryAdapter(geometry).family).toBe("mixed");
        }
    });
});
