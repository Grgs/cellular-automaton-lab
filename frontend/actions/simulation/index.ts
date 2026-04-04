import { createPatchDepthActions } from "./patch-depth-actions.js";
import { createRuleActions } from "./rule-actions.js";
import { createRunActions } from "./run-actions.js";
import { createSimulationActionRuntime } from "./shared.js";
import { createTopologyActions } from "./topology-actions.js";
import type { SimulationActionRuntime, SimulationActionSet } from "../../types/actions.js";

export function createSimulationActions(
    dependencies: Parameters<typeof createSimulationActionRuntime>[0],
): SimulationActionSet {
    const runtime: SimulationActionRuntime = createSimulationActionRuntime(dependencies);
    return {
        ...createRunActions(runtime),
        ...createTopologyActions(runtime),
        ...createRuleActions(runtime),
        ...createPatchDepthActions(runtime),
    };
}
