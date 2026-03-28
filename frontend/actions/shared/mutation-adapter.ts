import type { MutationRunnerOptions, SimulationMutationOptions } from "../../types/controller.js";
import type { SimulationSnapshot } from "../../types/domain.js";

interface ActionMutationAdapterOptions {
    interactions: {
        runSerialized<T>(task: () => Promise<T>, options?: MutationRunnerOptions): Promise<T>;
    };
    applySimulationState: (
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ) => void;
}

interface ActionMutationAdapter {
    applyState(
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ): SimulationSnapshot;
    applyRemoteState(
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ): Promise<SimulationSnapshot>;
    runSerialized<T>(task: () => Promise<T>, options?: SimulationMutationOptions): Promise<T>;
}

export function createActionMutationAdapter({
    interactions,
    applySimulationState,
}: ActionMutationAdapterOptions): ActionMutationAdapter {
    return {
        applyState(simulationState, options = {}) {
            applySimulationState(simulationState, options);
            return simulationState;
        },
        async applyRemoteState(simulationState, options = {}) {
            return this.applyState(simulationState, options);
        },
        runSerialized(task, options = {}) {
            const nextOptions: MutationRunnerOptions = {};
            if (typeof options.onError === "function") {
                nextOptions.onError = options.onError;
            }
            if (typeof options.onRecover === "function") {
                nextOptions.onRecover = options.onRecover;
            }
            return interactions.runSerialized(task, nextOptions);
        },
    };
}
