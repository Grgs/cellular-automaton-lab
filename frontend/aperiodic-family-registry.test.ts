import { beforeEach, describe, expect, it } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("aperiodic-family-registry", () => {
    beforeEach(() => {
        installFrontendGlobals();
    });

    it("builds a bootstrapped lookup keyed by tiling family", async () => {
        const {
            describeAperiodicFamilyStatus,
            getAperiodicFamilyMetadata,
            isExperimentalAperiodicFamily,
            listAperiodicFamilyMetadata,
        } = await import("./aperiodic-family-registry.js");

        expect(listAperiodicFamilyMetadata().length).toBeGreaterThan(0);
        expect(getAperiodicFamilyMetadata("penrose-p3-rhombs")?.label).toBe("Penrose P3 Rhombs");
        expect(getAperiodicFamilyMetadata("dodecagonal-square-triangle")?.label).toBe(
            "Schlottmann Square-Triangle",
        );
        expect(
            getAperiodicFamilyMetadata("dodecagonal-square-triangle")?.promotion_blocker,
        ).toBeFalsy();
        expect(isExperimentalAperiodicFamily("dodecagonal-square-triangle")).toBe(false);
        expect(isExperimentalAperiodicFamily("pinwheel-2-1")).toBe(false);
        expect(isExperimentalAperiodicFamily("pinwheel")).toBe(false);
        expect(isExperimentalAperiodicFamily("penrose-p3-rhombs")).toBe(false);
        expect(describeAperiodicFamilyStatus("dodecagonal-square-triangle")?.tone).toBe("info");
        expect(describeAperiodicFamilyStatus("pinwheel-2-1")?.tone).toBe("info");
        expect(describeAperiodicFamilyStatus("pinwheel")?.tone).toBe("info");
        expect(describeAperiodicFamilyStatus("penrose-p3-rhombs")?.tone).toBe("info");
    });

    it("surfaces the warning status path for an experimental family", async () => {
        // No shipped family is experimental right now; keep the warning path
        // covered with a synthetic bootstrapped definition.
        window.APP_APERIODIC_FAMILIES = [
            ...(window.APP_APERIODIC_FAMILIES ?? []),
            {
                tiling_family: "fixture-experimental",
                label: "Fixture Experimental",
                experimental: true,
                implementation_status: "canonical_patch",
                promotion_blocker: "Experimental until the fixture review passes.",
                public_cell_kinds: ["fixture-cell"],
            },
        ];
        const { describeAperiodicFamilyStatus, isExperimentalAperiodicFamily } =
            await import("./aperiodic-family-registry.js");

        expect(isExperimentalAperiodicFamily("fixture-experimental")).toBe(true);
        const status = describeAperiodicFamilyStatus("fixture-experimental");
        expect(status?.tone).toBe("warning");
        expect(status?.label).toContain("Experimental");
        expect(status?.detail).toContain("Experimental until");
    });
});
