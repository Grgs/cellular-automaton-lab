import { applyOverlayIntent, OVERLAY_INTENT_BOARD_REBUILT } from "../overlay-policy.js";
import { buildPresetSeed, getDefaultPresetId } from "../presets.js";
import { createActionMutationAdapter } from "./shared/mutation-adapter.js";
import {
    clearEditMode,
    dismissFirstRunHint,
    setPatternStatus,
} from "../state/overlay-state.js";
import {
    RULE_SELECTION_ORIGIN_DEFAULT,
} from "../state/constants.js";
import { rememberedCellSizeForTilingFamily } from "../state/sizing-state.js";
import {
    setRuleSelectionOrigin,
    setSelectedPresetId,
} from "../state/simulation-state.js";
import { BLOCKING_ACTIVITY_LOAD_DEMO } from "../blocking-activity.js";
import { describeTopologySpec, resolveTopologyVariantKey } from "../topology-catalog.js";
import { indexTopology, presetCellsToTopologyUpdates } from "../topology.js";
import type {
    ActionMutationAdapter,
    ResetRequestBody,
    ShowcaseActionOptions,
    ShowcaseActionSet,
    ShowcaseDefinition,
} from "../types/actions.js";
import type { SimulationMutations } from "../types/controller.js";
import type { CellStateUpdate, SimulationSnapshot } from "../types/domain.js";

const SHOWCASE_PENROSE_PATCH_DEPTH = 4;

const SHOWCASE_DEMOS: Readonly<Record<string, Readonly<ShowcaseDefinition>>> = Object.freeze({
    whirlpool: Object.freeze({
        tiling_family: "square",
        adjacency_mode: "edge",
        rule: "whirlpool",
        randomize: false,
        successMessage: "Loaded Whirlpool demo.",
    }),
    wireworld: Object.freeze({
        tiling_family: "square",
        adjacency_mode: "edge",
        rule: "wireworld",
        randomize: false,
        successMessage: "Loaded WireWorld demo.",
    }),
    penrose: Object.freeze({
        tiling_family: "penrose-p3-rhombs",
        adjacency_mode: "edge",
        rule: "life-b2-s23",
        patch_depth: SHOWCASE_PENROSE_PATCH_DEPTH,
        randomize: true,
        successMessage: "Loaded Penrose demo.",
    }),
});

function resolvedSpeed(elements: ShowcaseActionOptions["elements"], state: ShowcaseActionOptions["state"]): number {
    const requested = Number(elements.speedInput?.value);
    return Number.isFinite(requested) ? requested : Number(state.speed);
}

export function createShowcaseActions({
    state,
    elements,
    interactions,
    applySimulationState,
    postControlFn,
    setCellsRequestFn,
    renderControlPanel,
    refreshState,
    onError,
    getViewportDimensions,
    simulationMutations = null,
    getDefaultPresetIdFn = getDefaultPresetId,
    buildPresetSeedFn = buildPresetSeed,
    presetCellsToTopologyUpdatesFn = presetCellsToTopologyUpdates,
    applyOverlayIntentFn = applyOverlayIntent,
    dismissFirstRunHintFn = dismissFirstRunHint,
    clearEditModeFn = clearEditMode,
    setRuleSelectionOriginFn = setRuleSelectionOrigin,
    setPatternStatusFn = setPatternStatus,
    setSelectedPresetIdFn = setSelectedPresetId,
}: ShowcaseActionOptions & {
    getDefaultPresetIdFn?: typeof getDefaultPresetId;
    buildPresetSeedFn?: typeof buildPresetSeed;
    presetCellsToTopologyUpdatesFn?: typeof presetCellsToTopologyUpdates;
    applyOverlayIntentFn?: typeof applyOverlayIntent;
    dismissFirstRunHintFn?: typeof dismissFirstRunHint;
    clearEditModeFn?: typeof clearEditMode;
    setRuleSelectionOriginFn?: typeof setRuleSelectionOrigin;
    setPatternStatusFn?: typeof setPatternStatus;
    setSelectedPresetIdFn?: typeof setSelectedPresetId;
}): ShowcaseActionSet {
    const mutations: ActionMutationAdapter | SimulationMutations = simulationMutations
        || createActionMutationAdapter({ interactions, applySimulationState });

    function restoreOverlayAndExitEditMode(): void {
        dismissFirstRunHintFn(state);
        const overlayChanged = applyOverlayIntentFn(state, OVERLAY_INTENT_BOARD_REBUILT);
        const editChanged = clearEditModeFn(state);
        if (overlayChanged || editChanged) {
            renderControlPanel();
        }
    }

    function setShowcaseStatus(message: string, tone = "success"): void {
        setPatternStatusFn(state, message, tone);
        renderControlPanel();
    }

    function resetRequestForDemo(demo: ShowcaseDefinition): ResetRequestBody {
        const variantKey = resolveTopologyVariantKey(demo.tiling_family, demo.adjacency_mode);
        const desiredDimensions = getViewportDimensions(
            variantKey,
            demo.rule,
            rememberedCellSizeForTilingFamily(state, demo.tiling_family),
        );
        const topologySpec = describeTopologySpec({
            tiling_family: demo.tiling_family,
            adjacency_mode: demo.adjacency_mode,
            width: desiredDimensions.width,
            height: desiredDimensions.height,
            patch_depth: demo.patch_depth ?? state.patchDepth,
        });

        return {
            topology_spec: topologySpec,
            speed: resolvedSpeed(elements, state),
            rule: demo.rule,
            randomize: Boolean(demo.randomize),
        };
    }

    async function loadPresetBackedDemo(demo: ShowcaseDefinition): Promise<SimulationSnapshot> {
        const resetRequest = resetRequestForDemo(demo);
        const resetState = await postControlFn("/api/control/reset", resetRequest);
        const resolvedResetState = await mutations.applyRemoteState(
            resetState,
            { source: "external" },
        );

        const resetTopologySpec = describeTopologySpec(
            resolvedResetState.topology_spec || resetRequest.topology_spec,
        );
        const geometry = resolveTopologyVariantKey(
            resetTopologySpec.tiling_family,
            resetTopologySpec.adjacency_mode,
        );
        const presetId = getDefaultPresetIdFn(
            demo.rule,
            geometry,
            Number(resetTopologySpec.width) || 0,
            Number(resetTopologySpec.height) || 0,
        );
        if (!presetId) {
            throw new Error(`No preset is available for ${demo.rule}.`);
        }

        setSelectedPresetIdFn(state, demo.rule, presetId);
        const seedCells = buildPresetSeedFn({
            ruleName: demo.rule,
            geometry,
            width: Number(resetTopologySpec.width) || 0,
            height: Number(resetTopologySpec.height) || 0,
            presetId,
        });
        const topologyIndex = indexTopology(resolvedResetState.topology);
        const nextCells = presetCellsToTopologyUpdatesFn(topologyIndex, seedCells);
        if (nextCells.length === 0) {
            return resolvedResetState;
        }

        const seededState = await setCellsRequestFn(nextCells);
        await mutations.applyRemoteState(seededState, { source: "external" });
        return seededState;
    }

    function loadShowcaseDemo(demoId: string): Promise<SimulationSnapshot | null> {
        const demo = SHOWCASE_DEMOS[demoId as keyof typeof SHOWCASE_DEMOS];
        if (!demo) {
            return Promise.resolve(null);
        }

        restoreOverlayAndExitEditMode();
        return mutations.runSerialized(
            async () => {
                if (demo.randomize) {
                    const resetState = await postControlFn("/api/control/reset", resetRequestForDemo(demo));
                    return mutations.applyRemoteState(resetState, { source: "external" });
                }
                return loadPresetBackedDemo(demo);
            },
            {
                blockingActivity: BLOCKING_ACTIVITY_LOAD_DEMO,
                onError: (error) => {
                    const message = error instanceof Error ? error.message : String(error);
                    setShowcaseStatus(`Showcase failed: ${message}`, "error");
                    onError(error);
                },
                onRecover: refreshState,
            },
        ).then((result) => {
            if (result) {
                setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_DEFAULT);
                setShowcaseStatus(demo.successMessage, "success");
            }
            return result;
        }).catch(() => null);
    }

    return {
        loadShowcaseDemo: (demoId) => loadShowcaseDemo(demoId),
    };
}
