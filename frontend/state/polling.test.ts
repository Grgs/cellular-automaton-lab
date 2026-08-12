import { afterEach, describe, expect, it, vi } from "vitest";

import type { AppState } from "../types/state.js";
import { pollDelayForSpeed, schedulePolling, stopPolling } from "./polling.js";

afterEach(() => {
    vi.useRealTimers();
});

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

    it("continues polling when a refresh completes without applying a snapshot", async () => {
        vi.useFakeTimers();
        const state = {
            isRunning: true,
            pollTimer: null,
            speed: 10,
        } as AppState;
        const callback = vi.fn(async () => {});

        schedulePolling(state, callback, 1);
        await vi.advanceTimersByTimeAsync(1);
        expect(callback).toHaveBeenCalledTimes(1);

        await vi.advanceTimersByTimeAsync(100);
        expect(callback).toHaveBeenCalledTimes(2);
        stopPolling(state);
    });
});
