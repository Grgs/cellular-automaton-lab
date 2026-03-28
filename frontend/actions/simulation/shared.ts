import {
    BLOCKING_ACTIVITY_BUILD_TILING,
} from "../../blocking-activity.js";
import {
    clearEditMode,
    clearPatternStatus,
    dismissFirstRunHint,
} from "../../state/overlay-state.js";
import {
    DEFAULT_PATCH_DEPTH,
    RULE_SELECTION_ORIGIN_DEFAULT,
    RULE_SELECTION_ORIGIN_USER,
} from "../../state/constants.js";
import {
    clearPendingPatchDepth,
    normalizePatchDepthForTilingFamily,
    rememberedCellSizeForTilingFamily,
    rememberedPatchDepthForTilingFamily,
    rememberPatchDepthForTilingFamily,
    setCellSize,
    setPatchDepth,
    setPendingPatchDepth,
} from "../../state/sizing-state.js";
import { parsePatchDepth } from "../../parsers/sizing.js";
import {
    currentRuleSelectionOrigin,
    currentTopologyVariantKey,
    setEditorRule,
    setRuleSelectionOrigin,
    setTopologySpec,
} from "../../state/simulation-state.js";
import {
    applyOverlayIntent,
    OVERLAY_INTENT_BOARD_REBUILT,
} from "../../overlay-policy.js";
import { ruleRequiresSquareDimensions } from "../../rule-constraints.js";
import {
    describeTopologySpec,
    getTopologyDefinition,
    resolveAdjacencyMode,
    resolveTopologyVariantKey,
    topologyUsesPatchDepth,
} from "../../topology-catalog.js";
import type {
    BrowserClearTimeout,
    BrowserSetTimeout,
    BrowserTimerId,
    ConfigSyncBody,
    ResetControlBody,
} from "../../types/controller.js";
import type { SimulationActionRuleSyncOptions, SimulationActionRuntime } from "../../types/actions.js";
import type { SimulationSnapshot, TopologyDefinition, TopologySpec } from "../../types/domain.js";
import type { AppState } from "../../types/state.js";

interface CreateSimulationActionRuntimeOptions {
    state: AppState;
    interactions: SimulationActionRuntime["interactions"];
    viewportController: SimulationActionRuntime["viewportController"];
    configSyncController: SimulationActionRuntime["configSyncController"];
    uiSessionController: SimulationActionRuntime["uiSessionController"];
    renderControlPanel: () => void;
    getViewportDimensions: SimulationActionRuntime["getViewportDimensions"];
    setEditorRuleFn?: typeof setEditorRule;
    setRuleSelectionOriginFn?: typeof setRuleSelectionOrigin;
    setPendingPatchDepthFn?: typeof setPendingPatchDepth;
    clearPendingPatchDepthFn?: typeof clearPendingPatchDepth;
    dismissFirstRunHintFn?: typeof dismissFirstRunHint;
    clearPatternStatusFn?: typeof clearPatternStatus;
    setCellSizeFn?: typeof setCellSize;
    setPatchDepthFn?: typeof setPatchDepth;
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
    patchDepthDebounceMs?: number;
    applyOverlayIntentFn?: typeof applyOverlayIntent;
    clearEditModeFn?: typeof clearEditMode;
}

export function createSimulationActionRuntime({
    state,
    interactions,
    viewportController,
    configSyncController,
    uiSessionController,
    renderControlPanel,
    getViewportDimensions,
    setEditorRuleFn = setEditorRule,
    setRuleSelectionOriginFn = setRuleSelectionOrigin,
    setPendingPatchDepthFn = setPendingPatchDepth,
    clearPendingPatchDepthFn = clearPendingPatchDepth,
    dismissFirstRunHintFn = dismissFirstRunHint,
    clearPatternStatusFn = clearPatternStatus,
    setCellSizeFn = setCellSize,
    setPatchDepthFn = setPatchDepth,
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
    clearTimeoutFn = (timerId) => window.clearTimeout(timerId),
    patchDepthDebounceMs = 180,
    applyOverlayIntentFn = applyOverlayIntent,
    clearEditModeFn = clearEditMode,
}: CreateSimulationActionRuntimeOptions): SimulationActionRuntime {
    let patchDepthTimer: BrowserTimerId | null = null;
    let inflightPatchDepth: number | null = null;

    function clearScheduledPatchDepthCommit({ clearPending = false }: { clearPending?: boolean } = {}): void {
        if (patchDepthTimer !== null) {
            clearTimeoutFn(patchDepthTimer);
            patchDepthTimer = null;
        }
        if (clearPending) {
            clearPendingPatchDepthFn(state);
        }
    }

    function clearSharedStatus(): boolean {
        if (state.patternStatus?.message) {
            clearPatternStatusFn(state);
            return true;
        }
        return false;
    }

    function dismissHintsAndStatus(): void {
        dismissFirstRunHintFn(state);
        clearSharedStatus();
    }

    function preserveRuleOnTopologySelection(): boolean {
        return currentRuleSelectionOrigin(state) === RULE_SELECTION_ORIGIN_USER;
    }

    function reconcileTopologySelectionRuleOrigin(
        simulationState: SimulationSnapshot | null | void,
        requestedRuleName: string | null = null,
    ): void {
        if (requestedRuleName && simulationState?.rule?.name === requestedRuleName) {
            setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_USER);
            return;
        }
        setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_DEFAULT);
    }

    function persistAppliedPatchDepth(simulationState: SimulationSnapshot | null | void): void {
        const topologySpec = describeTopologySpec(
            simulationState?.topology_spec || state.topologySpec,
        );
        if (!topologyUsesPatchDepth(topologySpec)) {
            return;
        }
        const patchDepth = normalizePatchDepthForTilingFamily(
            topologySpec.tiling_family,
            topologySpec.patch_depth,
        );
        rememberPatchDepthForTilingFamily(state, topologySpec.tiling_family, patchDepth);
        uiSessionController.persistPatchDepthForTilingFamily?.(topologySpec.tiling_family, patchDepth);
    }

    function applyOverlayIntentAndRender(intent: Parameters<typeof applyOverlayIntent>[1]): boolean {
        const changed = applyOverlayIntentFn(state, intent);
        const editChanged = clearEditModeFn(state);
        if (changed || editChanged) {
            renderControlPanel();
        }
        return changed || editChanged;
    }

    async function commitPendingPatchDepth(): Promise<boolean> {
        const targetDepth = normalizePatchDepthForTilingFamily(
            state.topologySpec?.tiling_family,
            parsePatchDepth(state.pendingPatchDepth ?? state.patchDepth),
        );
        if (
            !topologyUsesPatchDepth(state.topologySpec)
            || !Number.isFinite(targetDepth)
            || targetDepth === Number(state.patchDepth)
        ) {
            clearPendingPatchDepthFn(state);
            renderControlPanel();
            return false;
        }
        if (inflightPatchDepth !== null) {
            return false;
        }

        dismissHintsAndStatus();
        applyOverlayIntentAndRender(OVERLAY_INTENT_BOARD_REBUILT);
        inflightPatchDepth = targetDepth;
        try {
            const simulationState = await interactions.sendControl(
                "/api/control/reset",
                {
                    topology_spec: {
                        ...state.topologySpec,
                        patch_depth: targetDepth,
                    },
                    speed: state.speed,
                    rule: state.activeRule?.name ?? null,
                    randomize: false,
                },
                {
                    blockingActivity: BLOCKING_ACTIVITY_BUILD_TILING,
                },
            );
            persistAppliedPatchDepth(simulationState);
            reconcileTopologySelectionRuleOrigin(simulationState, null);
            return true;
        } finally {
            inflightPatchDepth = null;
            if (
                Number(state.pendingPatchDepth) === targetDepth
                && Number(state.patchDepth) === targetDepth
            ) {
                clearPendingPatchDepthFn(state);
                renderControlPanel();
            } else if (
                Number.isFinite(state.pendingPatchDepth)
                && Number(state.pendingPatchDepth) !== Number(state.patchDepth)
            ) {
                queuePatchDepthCommit({ immediate: true });
            }
        }
    }

    function queuePatchDepthCommit({ immediate = false }: { immediate?: boolean } = {}): void {
        clearScheduledPatchDepthCommit();
        if (immediate) {
            void commitPendingPatchDepth();
            return;
        }
        patchDepthTimer = setTimeoutFn(() => {
            patchDepthTimer = null;
            void commitPendingPatchDepth();
        }, patchDepthDebounceMs);
    }

    function requestPatchDepth(
        nextPatchDepth: number,
        { immediate = false }: { immediate?: boolean } = {},
    ): Promise<boolean> {
        if (!topologyUsesPatchDepth(state.topologySpec)) {
            return Promise.resolve(false);
        }
        setPendingPatchDepthFn(state, nextPatchDepth);
        renderControlPanel();

        if (Number(state.pendingPatchDepth) === Number(state.patchDepth)) {
            clearScheduledPatchDepthCommit({ clearPending: true });
            renderControlPanel();
            return Promise.resolve(false);
        }

        queuePatchDepthCommit({ immediate });
        return Promise.resolve(true);
    }

    function applyRuleSelection(nextRuleName: string | null): void {
        dismissHintsAndStatus();
        setEditorRuleFn(state, nextRuleName);
        setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_USER);
        uiSessionController.restorePaintStateForCurrentRule();
        renderControlPanel();
        const options: SimulationActionRuleSyncOptions = { running: state.isRunning };
        if (ruleRequiresSquareDimensions(nextRuleName)) {
            options.body = {
                topology_spec: {
                    ...getViewportDimensions(currentTopologyVariantKey(state), nextRuleName, state.cellSize),
                },
            };
        }
        configSyncController.requestRuleSync(nextRuleName, options);
    }

    function applySpeedSelection(nextSpeed: number): void {
        configSyncController.scheduleSpeedSync(nextSpeed);
        renderControlPanel();
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
        setTopologySpec(state, resolved);
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
            setTopologySpec(state, previousTopologySpec);
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

    function resetRuleSelectionOrigin(): void {
        setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_DEFAULT);
    }

    return {
        state,
        interactions,
        viewportController,
        configSyncController,
        uiSessionController,
        renderControlPanel,
        getViewportDimensions,
        dismissHintsAndStatus,
        applyOverlayIntentAndRender,
        buildResetPayload,
        applyRuleSelection,
        applySpeedSelection,
        requestPatchDepth,
        changeTilingFamily,
        changeAdjacencyMode,
        resetRuleSelectionOrigin,
    };
}
