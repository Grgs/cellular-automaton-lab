import { describe, expect, it } from "vitest";

import { pollDelayForSpeed } from "./polling.js";

describe("state/polling", () => {
    it("adapts the running poll cadence to target speed", () => {
        expect(pollDelayForSpeed(1)).toBe(1000);
        expect(pollDelayForSpeed(10)).toBe(100);
        expect(pollDelayForSpeed(30)).toBe(50);
    });

    it("falls back to the legacy cadence for invalid speeds", () => {
        expect(pollDelayForSpeed(0)).toBe(200);
        expect(pollDelayForSpeed(Number.NaN)).toBe(200);
    });
});
