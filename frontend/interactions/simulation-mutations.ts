import {
    clearBlockingActivity,
    setBlockingActivity,
} from "../state/overlay-state.js";
import type {
    BlockingActivityConfig,
    BrowserClearTimeout,
    BrowserSetTimeout,
    BrowserTimerId,
    MutationRunner,
    SimulationMutationOptions,
    SimulationMutations,
} from "../types/controller.js";
import type { SimulationSnapshot } from "../types/domain.js";
import type { AppState } from "../types/state.js";

interface CreateSimulationMutationsOptions {
    state?: AppState | null;
    mutationRunner: MutationRunner;
    onError?: (error: unknown) => void;
    applySimulationState?: (
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ) => void;
    resolveSimulationState?: (
        simulationState: SimulationSnapshot,
    ) => Promise<SimulationSnapshot>;
    refreshState?: () => Promise<void>;
    renderControlPanel?: () => void;
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
}

export function createSimulationMutations({
    state = null,
    mutationRunner,
    onError = () => {},
    applySimulationState = () => {},
    resolveSimulationState = async (simulationState) => simulationState,
    refreshState = async () => {},
    renderControlPanel = () => {},
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
    clearTimeoutFn = (timerId) => window.clearTimeout(timerId),
}: CreateSimulationMutationsOptions): SimulationMutations {
    function resolveRecoverHandler({
        recoverWithRefresh = false,
        onRecover,
    }: SimulationMutationOptions = {}): (() => Promise<void> | void) | ((error: unknown) => Promise<void> | void) | undefined {
        if (typeof onRecover === "function") {
            return onRecover;
        }
        return recoverWithRefresh ? refreshState : undefined;
    }

    function applyState(
        simulationState: SimulationSnapshot,
        { source = "external" }: { source?: string } = {},
    ): SimulationSnapshot {
        applySimulationState(simulationState, { source });
        return simulationState;
    }

    async function applyRemoteState(
        simulationState: SimulationSnapshot,
        options: { source?: string } = {},
    ): Promise<SimulationSnapshot> {
        const resolvedSimulationState = await resolveSimulationState(simulationState);
        return applyState(resolvedSimulationState, options);
    }

    function startBlockingActivity(activity: BlockingActivityConfig | null = null): () => void {
        if (!state || !activity?.message) {
            return () => {};
        }

        const showDelayMs = Number.isFinite(activity.delayMs) ? Number(activity.delayMs) : 200;
        const escalateAfterMs = Number.isFinite(activity.escalateAfterMs)
            ? Number(activity.escalateAfterMs)
            : 1000;
        const startedAt = Date.now();
        let visible = false;
        let showTimerId: BrowserTimerId | null = null;

        setBlockingActivity(state, {
            kind: activity.kind,
            message: activity.message,
            detail: "",
            visible: false,
            startedAt,
        });

        const showBlockingActivity = (detail = ""): void => {
            visible = true;
            setBlockingActivity(state, {
                kind: activity.kind,
                message: activity.message,
                detail,
                visible: true,
                startedAt,
            });
            renderControlPanel();
        };

        if (showDelayMs <= 0) {
            showBlockingActivity();
        } else {
            showTimerId = setTimeoutFn(() => {
                showBlockingActivity();
            }, showDelayMs);
        }

        const detailTimerId = setTimeoutFn(() => {
            showBlockingActivity(activity.detail);
        }, escalateAfterMs);

        return () => {
            if (showTimerId !== null) {
                clearTimeoutFn(showTimerId);
            }
            clearTimeoutFn(detailTimerId);
            const hadActivity = Boolean(state.blockingActivityKind);
            const wasVisible = Boolean(state.blockingActivityVisible || visible);
            clearBlockingActivity(state);
            if (hadActivity || wasVisible) {
                renderControlPanel();
            }
        };
    }

    function runSerialized<T>(
        task: () => Promise<T>,
        options: SimulationMutationOptions = {},
    ): Promise<T> {
        return mutationRunner.run(async () => {
            const finishBlockingActivity = startBlockingActivity(options.blockingActivity);
            try {
                return await task();
            } finally {
                finishBlockingActivity();
            }
        }, {
            onError: options.onError ?? onError,
            onRecover: resolveRecoverHandler(options),
        });
    }

    function runStateMutation(
        task: () => Promise<SimulationSnapshot>,
        { source = "external", ...options }: SimulationMutationOptions = {},
    ): Promise<SimulationSnapshot> {
        return runSerialized(
            async () => applyRemoteState(await task(), { source }),
            options,
        );
    }

    return {
        applyState,
        applyRemoteState,
        runSerialized,
        runStateMutation,
    };
}
