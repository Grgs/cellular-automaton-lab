import type { SimulationSnapshot } from "./domain.js";
import type { AppState } from "./state.js";

export type BrowserTimerId = number;
export type BrowserSetTimeout = (callback: () => void, delay: number) => BrowserTimerId;
export type BrowserClearTimeout = (timerId: BrowserTimerId) => void;
export type AsyncVoid = void | Promise<void>;

export interface MutationRunnerOptions {
    onError?: (error: unknown) => void;
    onRecover?: (error: unknown) => AsyncVoid;
}

export interface MutationRunner {
    run<T>(task: () => Promise<T>, options?: MutationRunnerOptions): Promise<T>;
    dispose(): void;
}

export interface BlockingActivityConfig {
    kind?: string | null;
    message?: string;
    detail?: string;
    delayMs?: number;
    escalateAfterMs?: number;
}

export interface SimulationMutationOptions extends MutationRunnerOptions {
    source?: string;
    recoverWithRefresh?: boolean;
    blockingActivity?: BlockingActivityConfig | null;
}

export interface CreateSimulationMutationsOptions {
    state?: AppState | null;
    mutationRunner: MutationRunner;
    onError?: (error: unknown) => void;
    applySimulationState?: (
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ) => void;
    resolveSimulationState?: (simulationState: SimulationSnapshot) => Promise<SimulationSnapshot>;
    refreshState?: () => Promise<void>;
    renderControlPanel?: () => void;
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
}

export interface SimulationMutations {
    applyState(
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ): SimulationSnapshot;
    applyRemoteState(
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ): Promise<SimulationSnapshot>;
    runSerialized<T>(task: () => Promise<T>, options?: SimulationMutationOptions): Promise<T>;
    runStateMutation(
        task: () => Promise<SimulationSnapshot>,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot>;
}

export interface CreateSimulationMutationsFunction {
    (options: CreateSimulationMutationsOptions): SimulationMutations;
}
