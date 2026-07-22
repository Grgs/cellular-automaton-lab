export type LatestSchedulerStatus = "idle" | "pending" | "updating" | "failed";

export interface LatestSchedulerState<TConfig> {
    readonly status: LatestSchedulerStatus;
    readonly config: TConfig | null;
    readonly error: unknown | null;
}

interface LatestConfigSchedulerOptions<TConfig> {
    delayMs?: number;
    validate?: (config: TConfig) => string | null;
    execute: (config: TConfig, signal: AbortSignal) => Promise<void>;
    onStateChange?: (state: LatestSchedulerState<TConfig>) => void;
    onInvalid?: (message: string) => void;
}

export interface LatestConfigScheduler<TConfig> {
    schedule(config: TConfig): void;
    runNow(config: TConfig): Promise<void>;
    /** Cancel matching queued/active work without disturbing other configurations. */
    cancel(predicate: (config: TConfig) => boolean): boolean;
    retry(): Promise<void>;
    whenIdle(): Promise<void>;
    dispose(): void;
}

/**
 * Debounces configuration changes while enforcing one active request and one
 * replaceable pending configuration. Aborting is advisory: runtimes that
 * cannot interrupt work may finish, but their stale completion is discarded.
 *
 * Status lifecycle: an accepted configuration emits `pending` (debouncing or
 * waiting on the active run), `updating` fires only when its execute call
 * actually starts, and the run settles to `idle` or `failed`.
 */
export function createLatestConfigScheduler<TConfig>(
    options: LatestConfigSchedulerOptions<TConfig>,
): LatestConfigScheduler<TConfig> {
    const delayMs = options.delayMs ?? 400;
    let timer: number | null = null;
    let pending: TConfig | null = null;
    let pendingReady = false;
    let active: { revision: number; controller: AbortController; config: TConfig } | null = null;
    let revision = 0;
    let disposed = false;
    let lastFailed: TConfig | null = null;
    let failed = false;
    const idleWaiters = new Set<() => void>();

    function emit(status: LatestSchedulerStatus, config: TConfig | null, error: unknown = null) {
        options.onStateChange?.({ status, config, error });
    }

    function clearTimer(): void {
        if (timer !== null) {
            window.clearTimeout(timer);
            timer = null;
        }
    }

    function settleIdle(): void {
        if (active || pending || timer !== null) {
            return;
        }
        if (!failed) {
            emit("idle", null);
        }
        idleWaiters.forEach((resolve) => resolve());
        idleWaiters.clear();
    }

    function validate(config: TConfig): string | null {
        const problem = options.validate?.(config) ?? null;
        return problem;
    }

    function launchPending(): void {
        if (disposed || active || !pending || !pendingReady) {
            return;
        }
        const config = pending;
        pending = null;
        pendingReady = false;
        const controller = new AbortController();
        const run = { revision, controller, config };
        active = run;
        emit("updating", config);
        void options
            .execute(config, controller.signal)
            .then(() => {
                if (run.revision === revision) {
                    lastFailed = null;
                    failed = false;
                }
            })
            .catch((error: unknown) => {
                if (run.revision !== revision || controller.signal.aborted || disposed) {
                    return;
                }
                lastFailed = config;
                failed = true;
                emit("failed", config, error);
            })
            .finally(() => {
                if (active === run) {
                    active = null;
                }
                launchPending();
                settleIdle();
            });
    }

    function setPending(config: TConfig, ready: boolean): boolean {
        if (disposed) {
            return false;
        }
        const problem = validate(config);
        if (problem) {
            revision += 1;
            clearTimer();
            pending = null;
            pendingReady = false;
            active?.controller.abort();
            options.onInvalid?.(problem);
            settleIdle();
            return false;
        }
        failed = false;
        revision += 1;
        pending = config;
        pendingReady = ready;
        clearTimer();
        emit("pending", config);
        if (ready) {
            active?.controller.abort();
            launchPending();
        }
        return true;
    }

    return {
        schedule(config): void {
            if (!setPending(config, false)) {
                return;
            }
            timer = window.setTimeout(() => {
                timer = null;
                pendingReady = true;
                active?.controller.abort();
                launchPending();
            }, delayMs);
        },
        async runNow(config): Promise<void> {
            if (setPending(config, true)) {
                await this.whenIdle();
            }
        },
        cancel(predicate): boolean {
            if (disposed) {
                return false;
            }
            let cancelled = false;
            const cancelledPending = pending !== null && predicate(pending);
            const cancelledActive = active !== null && predicate(active.config);
            if (cancelledPending) {
                clearTimer();
                pending = null;
                pendingReady = false;
                cancelled = true;
                // Scheduling the now-cancelled pending config made an older
                // active run stale. Restore that non-matching run as current.
                if (active && !cancelledActive) {
                    revision = active.revision;
                }
            }
            if (active && cancelledActive) {
                if (active.revision === revision) {
                    revision += 1;
                }
                active.controller.abort();
                cancelled = true;
            }
            if (lastFailed !== null && predicate(lastFailed)) {
                lastFailed = null;
                failed = false;
                cancelled = true;
            }
            if (!cancelled) {
                return false;
            }
            if (pending) {
                emit("pending", pending);
            } else if (active && !active.controller.signal.aborted) {
                emit("updating", active.config);
            } else {
                failed = false;
                emit("idle", null);
            }
            settleIdle();
            return true;
        },
        async retry(): Promise<void> {
            const config = pending ?? lastFailed;
            if (config) {
                await this.runNow(config);
            }
        },
        whenIdle(): Promise<void> {
            if (!active && !pending && timer === null) {
                return Promise.resolve();
            }
            return new Promise((resolve) => idleWaiters.add(resolve));
        },
        dispose(): void {
            if (disposed) {
                return;
            }
            disposed = true;
            revision += 1;
            clearTimer();
            pending = null;
            const activeRun = active;
            active = null;
            activeRun?.controller.abort();
            emit("idle", null);
            idleWaiters.forEach((resolve) => resolve());
            idleWaiters.clear();
        },
    };
}
