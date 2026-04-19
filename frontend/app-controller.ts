import {
    createHttpSimulationBackend,
} from "./api.js";
import { createAppControllerBootstrap } from "./app-controller-bootstrap.js";
import { createAppControllerSync } from "./app-controller-sync.js";
import { initializeAppController } from "./app-controller-startup.js";
import { indexTopology } from "./topology.js";
import type { AppActionSet } from "./types/actions.js";
import type {
    AppController,
    CreateAppControllerOptions,
    ReviewCellStateInput,
} from "./types/controller-app.js";
import type { ConfigSyncController, UiSessionController } from "./types/controller-sync-session.js";
import type { InteractionController, ViewportController } from "./types/controller-view.js";
import type { CellStateUpdate, SimulationSnapshot, TopologyPayload } from "./types/domain.js";

export function createAppController({
    elements,
    gridView,
    backend = createHttpSimulationBackend(),
    onError = (error: unknown) => console.error(error),
}: CreateAppControllerOptions): AppController {
    let interactions: InteractionController | null = null;
    let viewportController: ViewportController | null = null;
    let configSyncController: ConfigSyncController | null = null;
    let uiSessionController: UiSessionController | null = null;
    let controlActions: AppActionSet | null = null;
    let disposed = false;
    const controllerRefs = {
        configSyncController: null as ConfigSyncController | null,
        uiSessionController: null as UiSessionController | null,
    };
    const bootstrap = createAppControllerBootstrap({
        elements,
        gridView,
        getSyncState: () => (
            controllerRefs.configSyncController
                ? controllerRefs.configSyncController.getViewState()
                : {
                    pendingRuleName: null,
                    syncingRuleName: null,
                    pendingSpeed: null,
                    syncingSpeed: null,
                    isSyncing: false,
                    hasPendingRuleSync: false,
                    hasPendingSpeedSync: false,
                    shouldLockRule: false,
                    shouldLockSpeed: false,
                }
        ),
    });
    const { state, mutationRunner, appView } = bootstrap;
    let reviewBaselineSnapshot: SimulationSnapshot | null = null;
    const sync = createAppControllerSync({
        state,
        appView,
        onError,
        fetchRulesFn: () => backend.getRules(),
        fetchStateFn: () => backend.getState(),
        getConfigSyncController: () => controllerRefs.configSyncController,
        getUiSessionController: () => controllerRefs.uiSessionController,
        getRefreshState: () => sync.refreshState,
    });

    async function init(): Promise<void> {
        ({
            interactions,
            viewportController,
            configSyncController,
            uiSessionController,
            controlActions,
        } = await initializeAppController({
            state,
            elements,
            gridView,
            mutationRunner,
            appView,
            onError,
            postControlFn: backend.postControl.bind(backend),
            toggleCellRequestFn: backend.toggleCell.bind(backend),
            setCellRequestFn: backend.setCell.bind(backend),
            setCellsRequestFn: backend.setCells.bind(backend),
            sync,
            onConfigSyncController: (nextConfigSyncController) => {
                controllerRefs.configSyncController = nextConfigSyncController;
                configSyncController = nextConfigSyncController;
            },
            onUiSessionController: (nextUiSessionController) => {
                controllerRefs.uiSessionController = nextUiSessionController;
                uiSessionController = nextUiSessionController;
            },
        }));
    }

    function dispose(): void {
        if (disposed) {
            return;
        }
        disposed = true;
        viewportController?.dispose();
        configSyncController?.dispose();
        mutationRunner.dispose();
        void Promise.resolve(backend.dispose()).catch(onError);
        interactions = null;
        viewportController = null;
        configSyncController = null;
        uiSessionController = null;
        controlActions = null;
        controllerRefs.configSyncController = null;
        controllerRefs.uiSessionController = null;
        reviewBaselineSnapshot = null;
    }

    function activeRuleOrThrow() {
        const rule = state.activeRule ?? state.rules[0] ?? null;
        if (!rule) {
            throw new Error("Cannot apply review updates without an active rule.");
        }
        return rule;
    }

    function currentTopologyOrThrow(): TopologyPayload {
        if (!state.topology) {
            throw new Error("Cannot apply review updates without a loaded topology.");
        }
        return state.topology;
    }

    function cloneSimulationSnapshot(snapshot: SimulationSnapshot): SimulationSnapshot {
        return structuredClone(snapshot) as SimulationSnapshot;
    }

    function buildSimulationSnapshotFromState(
        topology: TopologyPayload,
        cellStates: number[],
        overrides: Partial<SimulationSnapshot> = {},
    ): SimulationSnapshot {
        return {
            topology_spec: topology.topology_spec,
            speed: Number(state.speed) || 0,
            running: Boolean(state.isRunning),
            generation: Number(state.generation) || 0,
            rule: activeRuleOrThrow(),
            topology_revision: String(state.topologyRevision || topology.topology_revision || ""),
            topology,
            cell_states: [...cellStates],
            ...overrides,
        };
    }

    function captureReviewBaselineIfNeeded(): void {
        if (reviewBaselineSnapshot !== null) {
            return;
        }
        const topology = currentTopologyOrThrow();
        reviewBaselineSnapshot = cloneSimulationSnapshot(
            buildSimulationSnapshotFromState(
                topology,
                Array.isArray(state.cellStates)
                    ? state.cellStates.map((cellState) => Number(cellState) || 0)
                    : new Array(topology.cells.length).fill(0),
            ),
        );
    }

    function normalizeReviewCellStateInput(reviewCellStates: ReviewCellStateInput): CellStateUpdate[] {
        if (Array.isArray(reviewCellStates)) {
            return reviewCellStates.map((cellState) => {
                if (typeof cellState?.id !== "string" || cellState.id.length === 0) {
                    throw new Error("Review cell-state updates must include a non-empty cell id.");
                }
                const nextState = Number(cellState.state);
                if (!Number.isFinite(nextState)) {
                    throw new Error(`Review cell-state update for ${cellState.id} had a non-finite state value.`);
                }
                return { id: cellState.id, state: nextState };
            });
        }
        if (!reviewCellStates || typeof reviewCellStates !== "object") {
            throw new Error("Review cell-state updates must be an object map or an array of updates.");
        }
        return Object.entries(reviewCellStates).map(([cellId, nextState]) => {
            const numericState = Number(nextState);
            if (!Number.isFinite(numericState)) {
                throw new Error(`Review cell-state update for ${cellId} had a non-finite state value.`);
            }
            return { id: cellId, state: numericState };
        });
    }

    function applyReviewTopology(topology: TopologyPayload): void {
        captureReviewBaselineIfNeeded();
        const nextSnapshot: SimulationSnapshot = {
            topology_spec: topology.topology_spec,
            speed: Number(state.speed) || 0,
            running: false,
            generation: 0,
            rule: activeRuleOrThrow(),
            topology_revision: topology.topology_revision,
            topology,
            cell_states: new Array(topology.cells.length).fill(0),
        };
        sync.applySimulationState(nextSnapshot, { source: "review-topology" });
    }

    function applyReviewCellStates(reviewCellStates: ReviewCellStateInput): void {
        captureReviewBaselineIfNeeded();
        const topology = currentTopologyOrThrow();
        const updates = normalizeReviewCellStateInput(reviewCellStates);
        const topologyIndex = state.topologyIndex ?? indexTopology(topology);
        const nextCellStates = Array.from(
            { length: topology.cells.length },
            (_, index) => Number(state.cellStates[index] ?? 0) || 0,
        );
        updates.forEach(({ id, state: nextState }) => {
            const resolvedCell = topologyIndex.byId.get(id) ?? null;
            if (!resolvedCell) {
                throw new Error(`Review cell-state update targeted an unknown cell id: ${id}`);
            }
            nextCellStates[resolvedCell.index] = nextState;
        });
        sync.applySimulationState(
            buildSimulationSnapshotFromState(
                topology,
                nextCellStates,
                {
                    running: false,
                    topology_revision: topology.topology_revision,
                },
            ),
            { source: "review-cell-states" },
        );
    }

    function resetReviewState(): void {
        if (reviewBaselineSnapshot === null) {
            return;
        }
        const baselineSnapshot = cloneSimulationSnapshot(reviewBaselineSnapshot);
        reviewBaselineSnapshot = null;
        sync.applySimulationState(baselineSnapshot, { source: "review-reset" });
    }

    return {
        init,
        dispose,
        refreshState: sync.refreshState,
        loadRules: sync.loadRules,
        applySimulationState: sync.applySimulationState,
        applyCellSize: (nextCellSize) => controlActions?.setCellSize?.(nextCellSize),
        applyPaintState: (nextPaintState) => controlActions?.setPaintState(nextPaintState),
        applyReviewTopology,
        applyReviewCellStates,
        resetReviewState,
        getState: () => state,
        getRenderDiagnostics: () => gridView.getRenderDiagnostics?.() ?? null,
        getRenderedCellCenter: (cellId) => gridView.getRenderedCellCenter?.(cellId) ?? null,
        getInteractions: () => interactions,
        getViewportController: () => viewportController,
        getConfigSyncController: () => configSyncController,
        getUiSessionController: () => uiSessionController,
    };
}
