import type { SimulationActionRuntime, SimulationActionSet } from "../../types/actions.js";

export function createRuleActions(
    runtime: SimulationActionRuntime,
): Pick<SimulationActionSet, "changeRule"> {
    return {
        changeRule(nextRuleName: string | null) {
            runtime.applyRuleSelection(nextRuleName);
        },
    };
}
