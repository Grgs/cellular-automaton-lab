import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

describe("session parser", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("preserves unsafe sizing session values when the toggle is enabled", async () => {
        const { parseUiSession } = await import("./session.js");

        const session = parseUiSession(
            {
                unsafeSizingEnabled: true,
                cellSizeByTilingFamily: {
                    square: 40,
                },
                patchDepthByTilingFamily: {
                    spectre: 9,
                },
            },
            {
                disclosureIds: [],
                defaultTilingFamily: "square",
            },
        );

        expect(session.unsafeSizingEnabled).toBe(true);
        expect(session.cellSizeByTilingFamily.square).toBe(40);
        expect(session.patchDepthByTilingFamily.spectre).toBe(9);
    });

    it("lets unsafe dodecagonal patch depth grow past the safe cap up to the family unsafe ceiling", async () => {
        const { parseUiSession } = await import("./session.js");

        const session = parseUiSession(
            {
                unsafeSizingEnabled: true,
                patchDepthByTilingFamily: {
                    "dodecagonal-square-triangle": 50,
                },
            },
            {
                disclosureIds: [],
                defaultTilingFamily: "dodecagonal-square-triangle",
            },
        );

        expect(session.unsafeSizingEnabled).toBe(true);
        expect(session.patchDepthByTilingFamily["dodecagonal-square-triangle"]).toBe(50);
    });

    it("clamps unsafe dodecagonal patch depth to the family unsafe ceiling", async () => {
        const { parseUiSession } = await import("./session.js");

        const session = parseUiSession(
            {
                unsafeSizingEnabled: true,
                patchDepthByTilingFamily: {
                    "dodecagonal-square-triangle": 999,
                },
            },
            {
                disclosureIds: [],
                defaultTilingFamily: "dodecagonal-square-triangle",
            },
        );

        expect(session.unsafeSizingEnabled).toBe(true);
        expect(session.patchDepthByTilingFamily["dodecagonal-square-triangle"]).toBe(60);
    });
});
