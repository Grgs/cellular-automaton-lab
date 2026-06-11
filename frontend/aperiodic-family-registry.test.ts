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
        expect(getAperiodicFamilyMetadata("pinwheel-2-1")?.promotion_blocker).toContain(
            "manual visual review",
        );
        expect(isExperimentalAperiodicFamily("pinwheel-2-1")).toBe(true);
        expect(isExperimentalAperiodicFamily("pinwheel")).toBe(false);
        expect(isExperimentalAperiodicFamily("penrose-p3-rhombs")).toBe(false);
        expect(describeAperiodicFamilyStatus("pinwheel-2-1")?.tone).toBe("warning");
        expect(describeAperiodicFamilyStatus("pinwheel")?.tone).toBe("info");
        expect(describeAperiodicFamilyStatus("penrose-p3-rhombs")?.tone).toBe("info");
    });
});
