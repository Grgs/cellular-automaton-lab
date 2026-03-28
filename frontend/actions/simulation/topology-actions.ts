import type { SimulationActionRuntime, SimulationActionSet } from "../../types/actions.js";

export function createTopologyActions(runtime: SimulationActionRuntime): Pick<
    SimulationActionSet,
    "changeTilingFamily" | "changeAdjacencyMode"
> {
    return {
        changeTilingFamily(nextTilingFamily: string) {
            return runtime.changeTilingFamily(nextTilingFamily);
        },

        changeAdjacencyMode(nextAdjacencyMode: string) {
            return runtime.changeAdjacencyMode(nextAdjacencyMode);
        },
    };
}
