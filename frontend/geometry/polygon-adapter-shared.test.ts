import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

describe("geometry/polygon-adapter-shared", () => {
    beforeEach(() => {
        vi.resetModules();
        installFrontendGlobals();
    });

    it("measures large topology bounds without spreading vertices into the call stack", async () => {
        const { measurePolygonBounds } = await import("./polygon-adapter-shared.js");
        const points = Array.from({ length: 80_000 }, (_, index) => ({
            x: (index % 400) - 200,
            y: Math.floor(index / 400) - 100,
        }));

        expect(measurePolygonBounds(points)).toEqual({
            minX: -200,
            maxX: 199,
            minY: -100,
            maxY: 99,
        });
    });
});
