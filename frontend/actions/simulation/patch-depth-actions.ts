import type { SimulationActionRuntime, SimulationActionSet } from "../../types/actions.js";

export function createPatchDepthActions(
    runtime: SimulationActionRuntime,
): Pick<SimulationActionSet, "changePatchDepth" | "commitPatchDepth"> {
    return {
        changePatchDepth(nextPatchDepth: number) {
            return runtime.requestPatchDepth(nextPatchDepth);
        },

        commitPatchDepth(nextPatchDepth: number) {
            return runtime.requestPatchDepth(nextPatchDepth, { immediate: true });
        },
    };
}
