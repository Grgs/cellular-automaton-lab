import { afterEach, describe, expect, it, vi } from "vitest";

import { createLatestConfigScheduler } from "./latest-config-scheduler.js";

function deferred<T>() {
    let resolve!: (value: T) => void;
    let reject!: (error: unknown) => void;
    const promise = new Promise<T>((resolvePromise, rejectPromise) => {
        resolve = resolvePromise;
        reject = rejectPromise;
    });
    return { promise, resolve, reject };
}

afterEach(() => {
    vi.useRealTimers();
});

describe("latest config scheduler", () => {
    it("debounces to the latest configuration without a FIFO backlog", async () => {
        vi.useFakeTimers();
        const execute = vi.fn(async (_config: string) => {});
        const scheduler = createLatestConfigScheduler({ execute });

        scheduler.schedule("first");
        await vi.advanceTimersByTimeAsync(200);
        scheduler.schedule("second");
        scheduler.schedule("latest");
        await vi.advanceTimersByTimeAsync(399);
        expect(execute).not.toHaveBeenCalled();
        await vi.advanceTimersByTimeAsync(1);
        await scheduler.whenIdle();

        expect(execute).toHaveBeenCalledTimes(1);
        expect(execute.mock.calls[0]?.[0]).toBe("latest");
    });

    it("aborts HTTP work and discards a stale non-interruptible completion", async () => {
        vi.useFakeTimers();
        const first = deferred<void>();
        const applied: string[] = [];
        const signals: AbortSignal[] = [];
        const execute = vi.fn(async (config: string, signal: AbortSignal) => {
            signals.push(signal);
            if (config === "first") {
                await first.promise;
            }
            if (!signal.aborted) {
                applied.push(config);
            }
        });
        const scheduler = createLatestConfigScheduler({ execute });
        void scheduler.runNow("first");
        await vi.waitFor(() => expect(execute).toHaveBeenCalledTimes(1));

        scheduler.schedule("latest");
        await vi.advanceTimersByTimeAsync(400);
        expect(signals[0]?.aborted).toBe(true);
        expect(execute).toHaveBeenCalledTimes(1);

        first.resolve();
        await scheduler.whenIdle();
        expect(execute).toHaveBeenCalledTimes(2);
        expect(applied).toEqual(["latest"]);
    });

    it("reports invalid configuration without issuing a request", async () => {
        const execute = vi.fn(async () => {});
        const onInvalid = vi.fn();
        const scheduler = createLatestConfigScheduler({
            execute,
            validate: () => "Fix the setup.",
            onInvalid,
        });

        await scheduler.runNow("invalid");

        expect(execute).not.toHaveBeenCalled();
        expect(onInvalid).toHaveBeenCalledWith("Fix the setup.");
    });

    it("invalidates an earlier debounced request when the latest config is invalid", async () => {
        vi.useFakeTimers();
        const execute = vi.fn(async (_config: string) => {});
        const scheduler = createLatestConfigScheduler({
            execute,
            validate: (config) => (config === "invalid" ? "Fix the setup." : null),
        });

        scheduler.schedule("valid");
        scheduler.schedule("invalid");
        await vi.advanceTimersByTimeAsync(500);

        expect(execute).not.toHaveBeenCalled();
    });

    it("retries the most recent failed configuration", async () => {
        const execute = vi
            .fn<(config: string) => Promise<void>>()
            .mockRejectedValueOnce(new Error("offline"))
            .mockResolvedValueOnce();
        const scheduler = createLatestConfigScheduler({ execute });

        await scheduler.runNow("config");
        await scheduler.retry();

        expect(execute).toHaveBeenCalledTimes(2);
        expect(execute.mock.calls[1]?.[0]).toBe("config");
    });

    it("retries the latest pending configuration instead of the failed one", async () => {
        vi.useFakeTimers();
        const execute = vi
            .fn<(config: string) => Promise<void>>()
            .mockRejectedValueOnce(new Error("offline"))
            .mockResolvedValueOnce();
        const scheduler = createLatestConfigScheduler({ execute });
        await scheduler.runNow("failed");
        scheduler.schedule("latest");

        await scheduler.retry();

        expect(execute.mock.calls[1]?.[0]).toBe("latest");
    });
});
