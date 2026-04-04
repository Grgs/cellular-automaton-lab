import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

describe("session parser", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("preserves unsafe sizing session values when the toggle is enabled", async () => {
        const { parseUiSession } = await import("./session.js");

        const session = parseUiSession({
            unsafeSizingEnabled: true,
            cellSizeByTilingFamily: {
                square: 40,
            },
            patchDepthByTilingFamily: {
                spectre: 9,
            },
        }, {
            disclosureIds: [],
            defaultTilingFamily: "square",
        });

        expect(session.unsafeSizingEnabled).toBe(true);
        expect(session.cellSizeByTilingFamily.square).toBe(40);
        expect(session.patchDepthByTilingFamily.spectre).toBe(9);
    });
});
