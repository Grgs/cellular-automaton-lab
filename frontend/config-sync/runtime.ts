import type {
    ConfigSyncBody,
    CreateSimulationMutationsOptions,
    MutationRunner,
    MutationRunnerOptions,
    PostControlFunction,
    SimulationMutations,
} from "../types/controller.js";
import type { SimulationSnapshot } from "../types/domain.js";
import { createSimulationMutations } from "../interactions/simulation-mutations.js";

export interface ConfigSyncMutationRuntime {
    mutations: SimulationMutations;
    normalizeConfigBody(body?: ConfigSyncBody | null): ConfigSyncBody;
    runConfigMutation(
        task: () => Promise<SimulationSnapshot>,
        options?: { onFailure?: () => void },
    ): Promise<void>;
}

export function createConfigSyncMutationRuntime({
    mutationRunner,
    simulationMutations = null,
    onError,
    applySimulationState,
    refreshState,
}: {
    mutationRunner: MutationRunner;
    simulationMutations?: SimulationMutations | null;
    onError: (error: unknown) => void;
    applySimulationState: (simulationState: SimulationSnapshot, options?: { source?: string }) => void;
    refreshState: () => Promise<void>;
}): ConfigSyncMutationRuntime {
    const mutations = simulationMutations || createSimulationMutations({
        mutationRunner,
        onError,
        applySimulationState,
        refreshState,
    } satisfies CreateSimulationMutationsOptions);

    function normalizeConfigBody(body: ConfigSyncBody | null = null): ConfigSyncBody {
        if (!body) {
            return {};
        }
        const nextBody: ConfigSyncBody = { ...body };
        if (body.topology_spec && Object.keys(body.topology_spec).length > 0) {
            nextBody.topology_spec = { ...body.topology_spec };
        }
        return nextBody;
    }

    async function runConfigMutation(
        task: () => Promise<SimulationSnapshot>,
        { onFailure }: { onFailure?: () => void } = {},
    ): Promise<void> {
        try {
            await mutations.runSerialized(
                async () => mutations.applyRemoteState(await task()),
                {
                    onRecover: async () => {
                        onFailure?.();
                        await refreshState();
                    },
                } satisfies MutationRunnerOptions,
            );
        } catch {
            // The shared mutation runner already reported and recovered.
        }
    }

    return {
        mutations,
        normalizeConfigBody,
        runConfigMutation,
    };
}
