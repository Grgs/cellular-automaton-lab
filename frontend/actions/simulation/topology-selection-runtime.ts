import { DEFAULT_PATCH_DEPTH } from "../../state/constants.js";
import { BLOCKING_ACTIVITY_BUILD_TILING } from "../../blocking-activity.js";
import { OVERLAY_INTENT_BOARD_REBUILT } from "../../overlay-policy.js";
import {
    rememberedCellSizeForTilingFamily,
    rememberedPatchDepthForTilingFamily,
    normalizePatchDepthForTilingFamily,
    setCellSize,
    setPatchDepth,
} from "../../state/sizing-state.js";
import { currentTopologyVariantKey, setTopologySpec } from "../../state/simulation-state.js";
import {
    describeTopologySpec,
    getTopologyDefinition,
    resolveAdjacencyMode,
    resolveTopologyVariantKey,
    topologyUsesPatchDepth,
} from "../../topology-catalog.js";
import type {
    ConfigSyncBody,
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
    function resolveSelectedPatchDepth(nextTopologySpec: Partial<TopologySpec>): number {
        const resolved = describeTopologySpec(nextTopologySpec);
        if (!topologyUsesPatchDepth(resolved)) {
            return DEFAULT_PATCH_DEPTH;
        }
        return rememberedPatchDepthForTilingFamily(state, resolved.tiling_family);
    }

    function resolveSelectedCellSize(nextTopologySpec: Partial<TopologySpec>): number {
        const resolved = describeTopologySpec(nextTopologySpec);
        return rememberedCellSizeForTilingFamily(state, resolved.tiling_family);
    }

    function buildResetPayload(randomize: boolean): ResetControlBody {
        clearScheduledPatchDepthCommit({ clearPending: true });
        if (topologyUsesPatchDepth(state.topologySpec)) {
            const targetPatchDepth = normalizePatchDepthForTilingFamily(
                state.topologySpec?.tiling_family,
                state.patchDepth,
            );
            return {
                topology_spec: {
                    ...state.topologySpec,
                    patch_depth: targetPatchDepth,
                },
                speed: state.speed,
                rule: state.activeRule?.name ?? null,
                randomize,
            };
        }
        const desiredDimensions = getViewportDimensions(
            currentTopologyVariantKey(state),
            state.activeRule?.name ?? null,
            state.cellSize,
        );
        const viewportPayload: ConfigSyncBody = {
            speed: state.speed,
            rule: state.activeRule?.name ?? null,
            topology_spec: {
                width: desiredDimensions.width,
                height: desiredDimensions.height,
            },
        };
        return {
            ...viewportPayload,
            topology_spec: {
                ...state.topologySpec,
                width: viewportPayload.topology_spec?.width ?? state.width,
                height: viewportPayload.topology_spec?.height ?? state.height,
                patch_depth: DEFAULT_PATCH_DEPTH,
            },
            speed: viewportPayload.speed ?? state.speed,
            rule: viewportPayload.rule ?? state.activeRule?.name ?? null,
            randomize,
        };
    }

    function applyTopologySelection(
        nextTopologySpec: Partial<TopologySpec>,
    ): Promise<SimulationSnapshot | null | void> {
        const resolved = describeTopologySpec(nextTopologySpec);
        const nextGeometry = resolveTopologyVariantKey(
            resolved.tiling_family,
            resolved.adjacency_mode,
        );
        const targetPatchDepth = resolveSelectedPatchDepth(resolved);
        const targetCellSize = resolveSelectedCellSize(resolved);
        if (
            nextGeometry === currentTopologyVariantKey(state)
            && Number(resolved.width) === Number(state.width)
            && Number(resolved.height) === Number(state.height)
            && Number(
                topologyUsesPatchDepth(resolved)
                    ? (resolved.patch_depth ?? targetPatchDepth)
                    : resolved.patch_depth,
            ) === Number(
                topologyUsesPatchDepth(state.topologySpec)
                    ? targetPatchDepth
                    : state.patchDepth,
            )
        ) {
            return Promise.resolve();
        }

        dismissHintsAndStatus();
        applyOverlayIntentAndRender(OVERLAY_INTENT_BOARD_REBUILT);
        clearScheduledPatchDepthCommit({ clearPending: true });
        const previousTopologySpec = state.topologySpec;
        const previousCellSize = state.cellSize;
        const previousPatchDepth = state.patchDepth;
        setTopologySpecFn(state, resolved);
        if (topologyUsesPatchDepth(resolved)) {
            setPatchDepthFn(
                state,
                resolved.patch_depth ?? targetPatchDepth,
                resolved.tiling_family,
            );
        } else {
            setCellSizeFn(state, targetCellSize, resolved.tiling_family);
        }
        renderControlPanel();
        const requestedRuleName = preserveRuleOnTopologySelection()
            ? (state.activeRule?.name ?? null)
            : null;

        const body: ResetControlBody = {
            topology_spec: topologyUsesPatchDepth(resolved)
                ? {
                    ...resolved,
                    patch_depth: normalizePatchDepthForTilingFamily(
                        resolved.tiling_family,
                        resolved.patch_depth ?? targetPatchDepth,
                    ),
                }
                : {
                    ...resolved,
                    width: resolved.width,
                    height: resolved.height,
                },
            speed: state.speed,
            rule: requestedRuleName,
            randomize: false,
        };

        return interactions.sendControl("/api/control/reset", body, {
            blockingActivity: BLOCKING_ACTIVITY_BUILD_TILING,
        }).then((simulationState) => {
            reconcileTopologySelectionRuleOrigin(simulationState, requestedRuleName);
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
        const baseTopologySpec = {
            tiling_family: nextTilingFamily,
            adjacency_mode: adjacencyMode,
            patch_depth: resolveSelectedPatchDepth({
                tiling_family: nextTilingFamily,
                adjacency_mode: adjacencyMode,
            }),
            width: state.width,
            height: state.height,
        };
        if (definition.sizing_mode === "patch_depth") {
            return applyTopologySelection(baseTopologySpec);
        }
        const desiredDimensions = getViewportDimensions(
            resolveTopologyVariantKey(nextTilingFamily, adjacencyMode),
            null,
            resolveSelectedCellSize(baseTopologySpec),
        );
        return applyTopologySelection({
            ...baseTopologySpec,
            width: desiredDimensions.width,
            height: desiredDimensions.height,
        });
    }

    function changeAdjacencyMode(nextAdjacencyMode: string): Promise<SimulationSnapshot | null | void> {
        return applyTopologySelection({
            tiling_family: state.topologySpec?.tiling_family || "square",
            adjacency_mode: nextAdjacencyMode,
            width: state.width,
            height: state.height,
            patch_depth: resolveSelectedPatchDepth({
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
