import { beforeEach, describe, expect, it, vi } from "vitest";

import { getFixtureTopologyDefinition, installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("Penrose P1 topology", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installFrontendGlobals();
    });

    it("appears as one picker family with construction modes", async () => {
        const {
            describeTopologySpec,
            resolveTopologyVariantKey,
            tilingFamilyOptions,
            topologyModeFieldLabel,
            topologyModeOptions,
            topologyUsesPatchDepth,
        } = await import("./topology-catalog.js");
        const penroseP1 = getFixtureTopologyDefinition("penrose-p1");
        const options = tilingFamilyOptions();
        const p1Options = options.filter((option) => option.value === "penrose-p1");

        expect(p1Options).toHaveLength(1);
        expect(p1Options[0]?.label).toBe("Penrose P1");
        expect(p1Options[0]?.previewKey).toBe("penrose-p1");
        expect(resolveTopologyVariantKey("penrose-p1")).toBe(penroseP1.geometry_keys.distributed);
        expect(resolveTopologyVariantKey("penrose-p1", "boat-star")).toBe(
            penroseP1.geometry_keys["boat-star"],
        );
        expect(topologyModeOptions("penrose-p1")).toEqual([
            { value: "distributed", label: "Distributed" },
            { value: "boat-star", label: "Boat-Star" },
        ]);
        expect(topologyModeFieldLabel("penrose-p1")).toBe("Construction");
        expect(topologyUsesPatchDepth("penrose-p1")).toBe(true);
        expect(
            describeTopologySpec({ tiling_family: "penrose-p1-pentagon-diamond" }),
        ).toMatchObject({
            tiling_family: "penrose-p1",
            adjacency_mode: "distributed",
        });
        expect(
            describeTopologySpec({ tiling_family: "penrose-p1-pentagon-boat-star" }),
        ).toMatchObject({
            tiling_family: "penrose-p1",
            adjacency_mode: "boat-star",
        });
    });
});
