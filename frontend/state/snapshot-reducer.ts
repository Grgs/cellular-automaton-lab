import { describeTopologySpec, topologyUsesPatchDepth } from "../topology-catalog.js";
import { DEFAULT_TOPOLOGY_SPEC } from "./constants.js";
import {
    clearPendingPatchDepth,
    rememberedCellSizeForTilingFamily,
    setCellSize,
    setPatchDepth,
} from "./sizing-state.js";
import { setActiveRule, setTopology, setTopologySpec } from "./simulation-state.js";
import type { SimulationSnapshot, TopologyPayload, TopologySpec } from "../types/domain.js";
import type { AppState } from "../types/state.js";

function nowMs(): number {
    return typeof performance !== "undefined" && typeof performance.now === "function"
        ? performance.now()
        : Date.now();
}

function updateMeasuredSpeed(state: AppState, simulationState: SimulationSnapshot): void {
    const generation = Number(simulationState.generation) || 0;
    if (!simulationState.running) {
        state.measuredSpeed = null;
        state.measuredSpeedSample = null;
        return;
    }

    const timestampMs = nowMs();
    const previousSample = state.measuredSpeedSample;
    if (!previousSample || generation < previousSample.generation) {
        state.measuredSpeedSample = { generation, timestampMs };
        state.measuredSpeed = null;
        return;
    }

    const generationDelta = generation - previousSample.generation;
    if (generationDelta <= 0) {
        return;
    }

    const elapsedSeconds = (timestampMs - previousSample.timestampMs) / 1000;
    if (elapsedSeconds <= 0) {
        state.measuredSpeedSample = { generation, timestampMs };
        return;
    }

    const nextMeasuredSpeed = generationDelta / elapsedSeconds;
    state.measuredSpeed =
        state.measuredSpeed === null
            ? nextMeasuredSpeed
            : state.measuredSpeed * 0.6 + nextMeasuredSpeed * 0.4;
    state.measuredSpeedSample = { generation, timestampMs };
}

function normalizeIncomingTopology(
    simulationState: SimulationSnapshot,
    topologySpec: TopologySpec,
): TopologyPayload {
    return {
        ...simulationState.topology,
        topology_spec: describeTopologySpec(
            simulationState.topology.topology_spec || topologySpec || DEFAULT_TOPOLOGY_SPEC,
        ),
    };
}

export function applySimulationSnapshot(
    state: AppState,
    simulationState: SimulationSnapshot,
): void {
    updateMeasuredSpeed(state, simulationState);
    state.previewTopology = null;
    state.previewTopologyRevision = null;
    state.previewCellStatesById = null;
    state.isRunning = simulationState.running;
    state.generation = simulationState.generation;
    state.speed = simulationState.speed;
    const topologySpec = describeTopologySpec(
        simulationState.topology_spec || DEFAULT_TOPOLOGY_SPEC,
    );
    const normalizedTopology = normalizeIncomingTopology(simulationState, topologySpec);
    setTopologySpec(state, topologySpec);
    setPatchDepth(state, topologySpec.patch_depth, topologySpec.tiling_family, {
        preserveOutOfRange: true,
    });
    if (Number(state.pendingPatchDepth) === Number(topologySpec.patch_depth)) {
        clearPendingPatchDepth(state);
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
    state.width = Number(topologySpec.width) || Number(normalizedTopology.topology_spec.width) || 0;
    state.height =
        Number(topologySpec.height) || Number(normalizedTopology.topology_spec.height) || 0;
    setTopology(state, normalizedTopology, simulationState.cell_states);
    setActiveRule(state, simulationState.rule);
}
