import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("presets", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("lists source-driven whirlpool presets and builds a default seed", async () => {
        const { buildPresetSeed, getDefaultPresetId, listAvailablePresets } = await import("./presets.js");

        const presets = listAvailablePresets("whirlpool", "square", 30, 20);
        const defaultPresetId = getDefaultPresetId("whirlpool", "square", 30, 20);
        const seed = buildPresetSeed({
            ruleName: "whirlpool",
            geometry: "square",
            width: 30,
            height: 20,
            presetId: null,
        });

        expect(presets.map((preset) => preset.id)).toContain("anchored-source-vortex");
        expect(defaultPresetId).toBe("anchored-source-vortex");
        expect(seed.length).toBeGreaterThan(0);
        expect(seed.some((cell) => cell.state === 4)).toBe(true);
    });
});
