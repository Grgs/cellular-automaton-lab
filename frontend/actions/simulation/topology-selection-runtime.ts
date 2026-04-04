import { BLOCKING_ACTIVITY_BUILD_TILING } from "../../blocking-activity.js";
import { OVERLAY_INTENT_BOARD_REBUILT } from "../../overlay-policy.js";
import {
    setCellSize,
    setPatchDepth,
} from "../../state/sizing-state.js";
import { setTopologySpec } from "../../state/simulation-state.js";
import {
    getTopologyDefinition,
    resolveAdjacencyMode,
} from "../../topology-catalog.js";
import {
    buildCurrentTopologyResetPayload,
    planTopologySelection,
    resolveSelectedPatchDepthForTopology,
} from "./topology-selection-plan.js";
import type {
    InteractionController,
    ResetControlBody,
    ViewportDimensions,
} from "../../types/controller.js";
import type { SimulationActionRuntime } from "../../types/actions.js";
import type { SimulationSnapshot, TopologyDefinition, TopologySpec } from "../../types/domain.js";
import type { AppState } from "../../types/state.js";

interface CreateTopologySelectionRuntimeOptions {
    state: AppState;
    interactions: InteractionController;
    renderControlPanel: () => void;
    getViewportDimensions: (
        geometry: string,
        ruleName: string | null,
        cellSize: number,
    ) => ViewportDimensions;
    dismissHintsAndStatus: () => void;
    applyOverlayIntentAndRender: SimulationActionRuntime["applyOverlayIntentAndRender"];
    preserveRuleOnTopologySelection: () => boolean;
    reconcileTopologySelectionRuleOrigin: (
        simulationState: SimulationSnapshot | null | void,
        requestedRuleName?: string | null,
    ) => void;
    clearScheduledPatchDepthCommit: (options?: { clearPending?: boolean }) => void;
    setTopologySpecFn?: typeof setTopologySpec;
    setPatchDepthFn?: typeof setPatchDepth;
    setCellSizeFn?: typeof setCellSize;
}

export interface TopologySelectionRuntime {
    buildResetPayload(randomize: boolean): ResetControlBody;
    changeTilingFamily(nextTilingFamily: string): Promise<SimulationSnapshot | null | void>;
    changeAdjacencyMode(nextAdjacencyMode: string): Promise<SimulationSnapshot | null | void>;
}

export function createTopologySelectionRuntime({
    state,
    interactions,
    renderControlPanel,
    getViewportDimensions,
    dismissHintsAndStatus,
    applyOverlayIntentAndRender,
    preserveRuleOnTopologySelection,
    reconcileTopologySelectionRuleOrigin,
    clearScheduledPatchDepthCommit,
    setTopologySpecFn = setTopologySpec,
    setPatchDepthFn = setPatchDepth,
    setCellSizeFn = setCellSize,
}: CreateTopologySelectionRuntimeOptions): TopologySelectionRuntime {
    function buildResetPayload(randomize: boolean): ResetControlBody {
        clearScheduledPatchDepthCommit({ clearPending: true });
        return buildCurrentTopologyResetPayload({
            state,
            getViewportDimensions,
            randomize,
        });
    }

    function applyTopologySelection(
        nextTopologySpec: Partial<TopologySpec>,
        {
            resizeNonPatchDepthToViewport = false,
            viewportRuleName = null,
        }: {
            resizeNonPatchDepthToViewport?: boolean;
            viewportRuleName?: string | null;
        } = {},
    ): Promise<SimulationSnapshot | null | void> {
        const selectionPlan = planTopologySelection({
            state,
            nextTopologySpec,
            preserveRuleOnTopologySelection: preserveRuleOnTopologySelection(),
            getViewportDimensions,
            resizeNonPatchDepthToViewport,
            viewportRuleName,
        });
        if (selectionPlan.kind === "noop") {
            return Promise.resolve();
        }

        dismissHintsAndStatus();
        applyOverlayIntentAndRender(OVERLAY_INTENT_BOARD_REBUILT);
        clearScheduledPatchDepthCommit({ clearPending: true });
        const previousTopologySpec = state.topologySpec;
        const previousCellSize = state.cellSize;
        const previousPatchDepth = state.patchDepth;
        setTopologySpecFn(state, selectionPlan.resolvedTopologySpec);
        if (selectionPlan.resolvedTopologySpec.sizing_mode === "patch_depth") {
            setPatchDepthFn(
                state,
                selectionPlan.optimisticPatchDepth,
                selectionPlan.resolvedTopologySpec.tiling_family,
            );
        } else {
            setCellSizeFn(
                state,
                selectionPlan.optimisticCellSize,
                selectionPlan.resolvedTopologySpec.tiling_family,
            );
        }
        renderControlPanel();

        return interactions.sendControl("/api/control/reset", selectionPlan.resetBody, {
            blockingActivity: BLOCKING_ACTIVITY_BUILD_TILING,
        }).then((simulationState) => {
            reconcileTopologySelectionRuleOrigin(simulationState, selectionPlan.requestedRuleName);
            return simulationState;
        }).catch((error) => {
            setTopologySpecFn(state, previousTopologySpec);
            setPatchDepthFn(state, previousPatchDepth, previousTopologySpec?.tiling_family);
            setCellSizeFn(state, previousCellSize, previousTopologySpec?.tiling_family);
            renderControlPanel();
            throw error;
        });
    }

    function changeTilingFamily(nextTilingFamily: string): Promise<SimulationSnapshot | null | void> {
        const definition = getTopologyDefinition(nextTilingFamily) as TopologyDefinition | null;
        const adjacencyMode = resolveAdjacencyMode(
            nextTilingFamily,
            definition?.default_adjacency_mode || null,
        );
        if (!definition) {
            return Promise.resolve();
        }
        return applyTopologySelection({
            tiling_family: nextTilingFamily,
            adjacency_mode: adjacencyMode,
            width: state.width,
            height: state.height,
            patch_depth: resolveSelectedPatchDepthForTopology(state, {
                tiling_family: nextTilingFamily,
                adjacency_mode: adjacencyMode,
            }),
        }, {
            resizeNonPatchDepthToViewport: definition.sizing_mode !== "patch_depth",
        });
    }

    function changeAdjacencyMode(nextAdjacencyMode: string): Promise<SimulationSnapshot | null | void> {
        return applyTopologySelection({
            tiling_family: state.topologySpec?.tiling_family || "square",
            adjacency_mode: nextAdjacencyMode,
            width: state.width,
            height: state.height,
            patch_depth: resolveSelectedPatchDepthForTopology(state, {
                tiling_family: state.topologySpec?.tiling_family || "square",
                adjacency_mode: nextAdjacencyMode,
            }),
        });
    }

    return {
        buildResetPayload,
        changeTilingFamily,
        changeAdjacencyMode,
    };
}
