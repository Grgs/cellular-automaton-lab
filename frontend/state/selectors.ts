import { findRule } from "./simulation-state.js";
import type { RuleDefinition } from "../types/domain.js";
import type { AppState, TopologyRenderPayload } from "../types/state.js";

function hasTopologyPreview(state: AppState): boolean {
    return Boolean(
        state.previewTopology
        && state.previewTopologyRevision
        && state.previewTopologyRevision === state.topologyRevision
    );
}

export function currentEditorRule(state: AppState): RuleDefinition | null {
    const editorRule = findRule(state, state.editorRuleName);
    if (editorRule) {
        return editorRule;
    }
    if (state.activeRule) {
        return state.activeRule;
    }
    return state.rules[0] || null;
}

export function currentDimensions(state: AppState): { width: number; height: number } {
    if (hasTopologyPreview(state)) {
        return {
            width: Number(state.previewTopology?.topology_spec?.width) || 0,
            height: Number(state.previewTopology?.topology_spec?.height) || 0,
        };
    }
    return {
        width: state.width,
        height: state.height,
    };
}

export function currentPaintState(state: AppState): number {
    const rule = currentEditorRule(state);
    if (!rule) {
        return 1;
    }
    return state.selectedPaintState ?? rule.default_paint_state ?? 1;
}

export function topologyRenderPayload(state: AppState): TopologyRenderPayload {
    const previewActive = hasTopologyPreview(state);
    const topology = previewActive ? state.previewTopology : state.topology;
    const previewCellStatesById = previewActive ? (state.previewCellStatesById || {}) : null;
    const cellStates = previewActive && Array.isArray(topology?.cells)
        ? topology.cells.map((cell) => Number(previewCellStatesById?.[cell.id] ?? 0))
        : state.cellStates;
    return {
        topology,
        cellStates,
        previewCellStatesById,
    };
}
