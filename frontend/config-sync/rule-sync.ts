import type { PostControlFunction, RuleSyncRequestOptions } from "../types/controller.js";
import type { ConfigSyncMutationRuntime } from "./runtime.js";
import type { ConfigSyncStateManager } from "./state.js";

export interface ConfigRuleSyncRequester {
    requestRuleSync(nextRuleName: string | null, options?: RuleSyncRequestOptions): void;
}

export function createConfigRuleSyncRequester({
    stateManager,
    runtime,
    postControl,
}: {
    stateManager: ConfigSyncStateManager;
    runtime: ConfigSyncMutationRuntime;
    postControl: PostControlFunction;
}): ConfigRuleSyncRequester {
    async function syncRuleChange(
        nextRuleName: string | null,
        { running = false, body = undefined }: RuleSyncRequestOptions = {},
    ): Promise<void> {
        stateManager.beginRuleSync(nextRuleName);

        await runtime.runConfigMutation(
            async () => {
                if (running) {
                    const pausedState = await postControl("/api/control/pause");
                    await runtime.mutations.applyRemoteState(pausedState);
                }
                return postControl("/api/config", {
                    rule: nextRuleName,
                    ...runtime.normalizeConfigBody(body),
                });
            },
            {
                onFailure: () => {
                    stateManager.clearRuleSync();
                },
            },
        );
    }

    function requestRuleSync(
        nextRuleName: string | null,
        options: RuleSyncRequestOptions = {},
    ): void {
        stateManager.markPendingRule(nextRuleName);
        void syncRuleChange(nextRuleName, options);
    }

    return { requestRuleSync };
}
