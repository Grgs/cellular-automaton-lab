import { DEFAULT_PATCH_DEPTH } from "../../state/constants.js";
import {
    rememberedCellSizeForTilingFamily,
    rememberedPatchDepthForTilingFamily,
    normalizePatchDepthForTilingFamily,
} from "../../state/sizing-state.js";
import { currentTopologyVariantKey } from "../../state/simulation-state.js";
import {
    describeTopologySpec,
    resolveTopologyVariantKey,
    topologyUsesPatchDepth,
} from "../../topology-catalog.js";
import type { ResetControlBody, ViewportDimensions } from "../../types/controller.js";
import type { TopologySpec } from "../../types/domain.js";
import type { AppState } from "../../types/state.js";

interface SharedTopologyPlanningOptions {
    state: AppState;
    getViewportDimensions: (
        geometry: string,
        ruleName: string | null,
        cellSize: number,
    ) => ViewportDimensions;
}

interface TopologySelectionPlanOptions extends SharedTopologyPlanningOptions {
    nextTopologySpec: Partial<TopologySpec>;
    preserveRuleOnTopologySelection: boolean;
    resizeNonPatchDepthToViewport?: boolean;
    viewportRuleName?: string | null;
}

export type TopologySelectionPlanResult =
    | {
        kind: "noop";
        resolvedTopologySpec: TopologySpec;
        optimisticPatchDepth: number;
        optimisticCellSize: number;
        requestedRuleName: string | null;
    }
    | {
        kind: "apply";
        resolvedTopologySpec: TopologySpec;
        optimisticPatchDepth: number;
        optimisticCellSize: number;
        requestedRuleName: string | null;
        resetBody: ResetControlBody;
    };

export function resolveSelectedPatchDepthForTopology(
    state: AppState,
    nextTopologySpec: Partial<TopologySpec>,
): number {
    const resolved = describeTopologySpec(nextTopologySpec);
    if (!topologyUsesPatchDepth(resolved)) {
        return DEFAULT_PATCH_DEPTH;
    }
    if (nextTopologySpec.patch_depth != null) {
        return normalizePatchDepthForTilingFamily(resolved.tiling_family, nextTopologySpec.patch_depth);
    }
    return rememberedPatchDepthForTilingFamily(state, resolved.tiling_family);
}

export function resolveSelectedCellSizeForTopology(
    state: AppState,
    nextTopologySpec: Partial<TopologySpec>,
): number {
    const resolved = describeTopologySpec(nextTopologySpec);
    return rememberedCellSizeForTilingFamily(state, resolved.tiling_family);
}

export function buildCurrentTopologyResetPayload({
    state,
    getViewportDimensions,
    randomize,
}: SharedTopologyPlanningOptions & {
    randomize: boolean;
}): ResetControlBody {
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
    return {
        topology_spec: {
            ...state.topologySpec,
            width: desiredDimensions.width,
            height: desiredDimensions.height,
            patch_depth: DEFAULT_PATCH_DEPTH,
        },
        speed: state.speed,
        rule: state.activeRule?.name ?? null,
        randomize,
    };
}

function buildTopologySelectionResetBody(
    state: AppState,
    resolvedTopologySpec: TopologySpec,
    requestedRuleName: string | null,
): ResetControlBody {
    if (topologyUsesPatchDepth(resolvedTopologySpec)) {
        return {
            topology_spec: {
                ...resolvedTopologySpec,
                patch_depth: normalizePatchDepthForTilingFamily(
                    resolvedTopologySpec.tiling_family,
                    resolvedTopologySpec.patch_depth,
                ),
            },
            speed: state.speed,
            rule: requestedRuleName,
            randomize: false,
        };
    }
    return {
        topology_spec: {
            ...resolvedTopologySpec,
            width: resolvedTopologySpec.width,
            height: resolvedTopologySpec.height,
        },
        speed: state.speed,
        rule: requestedRuleName,
        randomize: false,
    };
}

function isNoopTopologySelection(
    state: AppState,
    resolvedTopologySpec: TopologySpec,
    optimisticPatchDepth: number,
): boolean {
    const nextGeometry = resolveTopologyVariantKey(
        resolvedTopologySpec.tiling_family,
        resolvedTopologySpec.adjacency_mode,
    );
    return (
        nextGeometry === currentTopologyVariantKey(state)
        && Number(resolvedTopologySpec.width) === Number(state.width)
        && Number(resolvedTopologySpec.height) === Number(state.height)
        && Number(resolvedTopologySpec.patch_depth) === Number(
            topologyUsesPatchDepth(state.topologySpec)
                ? optimisticPatchDepth
                : state.patchDepth,
        )
    );
}

export function planTopologySelection({
    state,
    nextTopologySpec,
    preserveRuleOnTopologySelection,
    getViewportDimensions,
    resizeNonPatchDepthToViewport = false,
    viewportRuleName = null,
}: TopologySelectionPlanOptions): TopologySelectionPlanResult {
    const describedTopologySpec = describeTopologySpec(nextTopologySpec);
    const optimisticPatchDepth = resolveSelectedPatchDepthForTopology(state, nextTopologySpec);
    const optimisticCellSize = resolveSelectedCellSizeForTopology(state, nextTopologySpec);
    const requestedRuleName = preserveRuleOnTopologySelection
        ? (state.activeRule?.name ?? null)
        : null;

    const resolvedTopologySpec: TopologySpec = topologyUsesPatchDepth(describedTopologySpec)
        ? {
            ...describedTopologySpec,
            patch_depth: optimisticPatchDepth,
        }
        : (() => {
            if (!resizeNonPatchDepthToViewport) {
                return describedTopologySpec;
            }
            const desiredDimensions = getViewportDimensions(
                resolveTopologyVariantKey(
                    describedTopologySpec.tiling_family,
                    describedTopologySpec.adjacency_mode,
                ),
                viewportRuleName,
                optimisticCellSize,
            );
            return {
                ...describedTopologySpec,
                width: desiredDimensions.width,
                height: desiredDimensions.height,
            };
        })();

    if (isNoopTopologySelection(state, resolvedTopologySpec, optimisticPatchDepth)) {
        return {
            kind: "noop",
            resolvedTopologySpec,
            optimisticPatchDepth,
            optimisticCellSize,
            requestedRuleName,
        };
    }

    return {
        kind: "apply",
        resolvedTopologySpec,
        optimisticPatchDepth,
        optimisticCellSize,
        requestedRuleName,
        resetBody: buildTopologySelectionResetBody(state, resolvedTopologySpec, requestedRuleName),
    };
}
