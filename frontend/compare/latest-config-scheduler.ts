export type LatestSchedulerStatus = "idle" | "updating" | "failed";

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
    retry(): Promise<void>;
    whenIdle(): Promise<void>;
    dispose(): void;
}

/**
 * Debounces configuration changes while enforcing one active request and one
 * replaceable pending configuration. Aborting is advisory: runtimes that
 * cannot interrupt work may finish, but their stale completion is discarded.
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
        emit("updating", config);
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
