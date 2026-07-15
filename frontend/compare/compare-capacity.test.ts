import { describe, expect, it } from "vitest";

import {
    WALL_HARD_TILING_LIMIT,
    wallCapacityMessage,
    wallTilingCapacity,
} from "./compare-capacity.js";

describe("wallTilingCapacity", () => {
    it("uses the backend hard ceiling on capable, wide devices", () => {
        expect(wallTilingCapacity({ viewportWidth: 1280, hardwareConcurrency: 8 })).toBe(
            WALL_HARD_TILING_LIMIT,
        );
    });

    it("reduces the ceiling on narrow screens", () => {
        expect(wallTilingCapacity({ viewportWidth: 480, hardwareConcurrency: 8 })).toBe(4);
    });

    it("reduces the ceiling on low-compute devices", () => {
        expect(wallTilingCapacity({ viewportWidth: 1280, hardwareConcurrency: 2 })).toBe(4);
        expect(wallCapacityMessage(4)).toContain("screen or device");
    });
});
