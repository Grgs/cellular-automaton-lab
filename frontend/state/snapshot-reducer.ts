import { describeTopologySpec, topologyUsesPatchDepth } from "../topology-catalog.js";
import { DEFAULT_TOPOLOGY_SPEC } from "./constants.js";
import {
    clearPendingPatchDepth,
    rememberedCellSizeForTilingFamily,
    setCellSize,
    setPatchDepth,
} from "./sizing-state.js";
import {
    setActiveRule,
    setTopology,
    setTopologySpec,
} from "./simulation-state.js";
import type {
    SimulationSnapshot,
    TopologyPayload,
    TopologySpec,
} from "../types/domain.js";
import type { AppState } from "../types/state.js";

function normalizeIncomingTopology(
    state: AppState,
    simulationState: SimulationSnapshot,
    topologySpec: TopologySpec,
): TopologyPayload | null {
    if (!simulationState.topology) {
        return null;
    }
    return {
        ...simulationState.topology,
        topology_spec: describeTopologySpec(
            simulationState.topology.topology_spec || topologySpec || state.topologySpec || DEFAULT_TOPOLOGY_SPEC,
        ),
    };
}

export function simulationSnapshotNeedsTopology(
    state: AppState,
    simulationState: SimulationSnapshot | null | undefined,
): boolean {
    return Boolean(
        simulationState
        && !simulationState.topology
        && (
            !state.topology
            || !simulationState.topology_revision
            || simulationState.topology_revision !== state.topologyRevision
        ),
    );
}

export function applySimulationSnapshot(state: AppState, simulationState: SimulationSnapshot): void {
    state.previewTopology = null;
    state.previewTopologyRevision = null;
    state.previewCellStatesById = null;
    state.isRunning = Boolean(simulationState.running);
    state.generation = Number(simulationState.generation ?? 0);
    state.speed = Number(simulationState.speed ?? state.speed);
    const topologySpec = describeTopologySpec(
        simulationState.topology_spec
        || simulationState.topology?.topology_spec
        || DEFAULT_TOPOLOGY_SPEC,
    );
    const normalizedTopology = normalizeIncomingTopology(state, simulationState, topologySpec);
    const reusesCurrentTopology = !normalizedTopology
        && Boolean(
            state.topology
            && simulationState.topology_revision
            && simulationState.topology_revision === state.topologyRevision
        );
    setTopologySpec(state, topologySpec);
    if (topologySpec.patch_depth !== undefined && topologySpec.patch_depth !== null) {
        setPatchDepth(state, topologySpec.patch_depth, topologySpec.tiling_family);
        if (Number(state.pendingPatchDepth) === Number(topologySpec.patch_depth)) {
            clearPendingPatchDepth(state);
        }
    } else if (!topologyUsesPatchDepth(topologySpec)) {
        clearPendingPatchDepth(state);
    }
    if (!topologyUsesPatchDepth(topologySpec)) {
        setCellSize(
            state,
            rememberedCellSizeForTilingFamily(state, topologySpec.tiling_family),
            topologySpec.tiling_family,
        );
    }
    state.width = Number(topologySpec.width) || Number(normalizedTopology?.topology_spec?.width) || 0;
    state.height = Number(topologySpec.height) || Number(normalizedTopology?.topology_spec?.height) || 0;
    if (reusesCurrentTopology) {
        state.cellStates = Array.isArray(simulationState.cell_states)
            ? simulationState.cell_states
            : state.cellStates;
    } else {
        setTopology(state, normalizedTopology, simulationState.cell_states ?? []);
    }
    setActiveRule(state, simulationState.rule ?? null);
}
