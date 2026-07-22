import { afterEach, describe, expect, it, vi } from "vitest";

import {
    createLatestConfigScheduler,
    type LatestSchedulerState,
} from "./latest-config-scheduler.js";

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

    it("cancels matching debounced work before it launches", async () => {
        vi.useFakeTimers();
        const execute = vi.fn(async (_config: { kind: string }) => {});
        const scheduler = createLatestConfigScheduler({ execute });

        scheduler.schedule({ kind: "analysis" });
        expect(scheduler.cancel((config) => config.kind === "analysis")).toBe(true);
        await vi.advanceTimersByTimeAsync(500);

        expect(execute).not.toHaveBeenCalled();
        await expect(scheduler.whenIdle()).resolves.toBeUndefined();
    });

    it("cancels queued analysis without aborting active filmstrip work", async () => {
        vi.useFakeTimers();
        const filmstrip = deferred<void>();
        const signals: AbortSignal[] = [];
        const execute = vi.fn(async (config: { kind: string }, signal: AbortSignal) => {
            signals.push(signal);
            if (config.kind === "filmstrip") {
                await filmstrip.promise;
            }
        });
        const scheduler = createLatestConfigScheduler({ execute });
        void scheduler.runNow({ kind: "filmstrip" });
        await vi.waitFor(() => expect(execute).toHaveBeenCalledTimes(1));

        scheduler.schedule({ kind: "analysis" });
        expect(scheduler.cancel((config) => config.kind === "analysis")).toBe(true);
        expect(signals[0]?.aborted).toBe(false);

        filmstrip.resolve();
        await scheduler.whenIdle();
        expect(execute).toHaveBeenCalledTimes(1);
    });

    it("aborts matching active work and ignores its eventual completion", async () => {
        const analysis = deferred<void>();
        const signals: AbortSignal[] = [];
        const applied: string[] = [];
        const scheduler = createLatestConfigScheduler<{ kind: string }>({
            execute: async (config, signal) => {
                signals.push(signal);
                await analysis.promise;
                if (!signal.aborted) {
                    applied.push(config.kind);
                }
            },
        });
        void scheduler.runNow({ kind: "analysis" });
        await vi.waitFor(() => expect(signals).toHaveLength(1));

        expect(scheduler.cancel((config) => config.kind === "analysis")).toBe(true);
        expect(signals[0]?.aborted).toBe(true);
        analysis.resolve();
        await scheduler.whenIdle();

        expect(applied).toEqual([]);
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

    it("stays pending through the debounce and updates only when execution starts", async () => {
        vi.useFakeTimers();
        const states: Array<[string, string | null]> = [];
        const scheduler = createLatestConfigScheduler<string>({
            execute: async () => {},
            onStateChange: (state: LatestSchedulerState<string>) => {
                states.push([state.status, state.config]);
            },
        });

        scheduler.schedule("first");
        scheduler.schedule("latest");
        expect(states).toEqual([
            ["pending", "first"],
            ["pending", "latest"],
        ]);

        await vi.advanceTimersByTimeAsync(400);
        await scheduler.whenIdle();
        expect(states).toEqual([
            ["pending", "first"],
            ["pending", "latest"],
            ["updating", "latest"],
            ["idle", null],
        ]);
    });

    it("reports pending, updating, then failed for an immediate failing run", async () => {
        const states: string[] = [];
        const scheduler = createLatestConfigScheduler<string>({
            execute: async () => {
                throw new Error("offline");
            },
            onStateChange: (state: LatestSchedulerState<string>) => {
                states.push(state.status);
            },
        });

        await scheduler.runNow("config");

        expect(states).toEqual(["pending", "updating", "failed"]);
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
