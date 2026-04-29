import { indexTopology } from "./topology.js";
import type { AppController } from "./types/controller-app.js";
import type { GridView } from "./types/controller-view.js";
import type { DomElements } from "./types/dom.js";
import type { CellStateUpdate, RuleDefinition, SimulationSnapshot, TopologyPayload } from "./types/domain.js";
import type { RenderDiagnosticsSnapshot } from "./types/rendering.js";
import type { AppState } from "./types/state.js";

type ReviewCellStateInput = Record<string, number> | CellStateUpdate[];

type ReviewableAppController = Pick<AppController, "applySimulationState" | "getState">;

interface InstallReviewApiOptions {
    controller: ReviewableAppController;
    gridView: GridView;
    elements: DomElements;
}

function activeRuleOrThrow(state: AppState): RuleDefinition {
    const rule = state.activeRule ?? state.rules[0] ?? null;
    if (!rule) {
        throw new Error("Cannot apply review updates without an active rule.");
    }
    return rule;
}

function currentTopologyOrThrow(state: AppState): TopologyPayload {
    if (!state.topology) {
        throw new Error("Cannot apply review updates without a loaded topology.");
    }
    return state.topology;
}

function cloneSimulationSnapshot(snapshot: SimulationSnapshot): SimulationSnapshot {
    return structuredClone(snapshot) as SimulationSnapshot;
}

function buildSimulationSnapshotFromState(
    state: AppState,
    topology: TopologyPayload,
    cellStates: number[],
    overrides: Partial<SimulationSnapshot> = {},
): SimulationSnapshot {
    return {
        topology_spec: topology.topology_spec,
        speed: Number(state.speed) || 0,
        running: Boolean(state.isRunning),
        generation: Number(state.generation) || 0,
        rule: activeRuleOrThrow(state),
        topology_revision: String(state.topologyRevision || topology.topology_revision || ""),
        topology,
        cell_states: [...cellStates],
        ...overrides,
    };
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

function readText(element: HTMLElement | null): string {
    return element?.textContent?.trim() || "";
}

function errorMessage(error: unknown): string {
    return error instanceof Error ? error.message : String(error);
}

function buildAppDiagnosticsSnapshot(
    controller: ReviewableAppController,
    gridView: GridView,
    elements: DomElements,
) {
    const state = controller.getState();
    const topologySpec = state.topologySpec || null;
    const topology = state.topology || null;
    const diagnosticErrors: string[] = [];
    let renderDiagnostics: RenderDiagnosticsSnapshot | null = null;
    try {
        renderDiagnostics = gridView.getRenderDiagnostics?.() ?? null;
    } catch (error) {
        diagnosticErrors.push(errorMessage(error));
    }
    return {
        tilingFamily: typeof topologySpec?.tiling_family === "string" ? topologySpec.tiling_family : null,
        patchDepth: Number.isFinite(Number(topologySpec?.patch_depth))
            ? Number(topologySpec?.patch_depth)
            : null,
        topologyCellCount: Array.isArray(topology?.cells) ? topology.cells.length : 0,
        width: Number.isFinite(Number(topologySpec?.width)) ? Number(topologySpec?.width) : null,
        height: Number.isFinite(Number(topologySpec?.height)) ? Number(topologySpec?.height) : null,
        topologyRevision: typeof state.topologyRevision === "string" ? state.topologyRevision : null,
        transformReport: renderDiagnostics,
        diagnosticErrors,
        readiness: {
            appReady: window.__appReady === true,
            blockingActivityVisible: Boolean(state.blockingActivityVisible),
            blockingActivityKind: state.blockingActivityKind || null,
            blockingActivityMessage: state.blockingActivityMessage || "",
            blockingActivityDetail: state.blockingActivityDetail || "",
            blockingActivityStartedAt: Number.isFinite(Number(state.blockingActivityStartedAt))
                ? Number(state.blockingActivityStartedAt)
                : null,
            topologyRevision: typeof state.topologyRevision === "string" ? state.topologyRevision : null,
            topologyCellCount: Array.isArray(topology?.cells) ? topology.cells.length : 0,
            patchDepth: Number.isFinite(Number(topologySpec?.patch_depth))
                ? Number(topologySpec?.patch_depth)
                : null,
            renderCellSize: Number.isFinite(Number(renderDiagnostics?.renderMetrics.renderCellSize))
                ? Number(renderDiagnostics?.renderMetrics.renderCellSize)
                : (
                    Number.isFinite(Number(state.renderCellSize))
                        ? Number(state.renderCellSize)
                        : null
                ),
            gridSizeText: readText(elements.gridSizeText),
            generationText: readText(elements.generationText),
            statusText: readText(elements.statusText),
        },
    };
}

function sampleRenderedCellPixel(
    gridView: GridView,
    elements: DomElements,
    cellId: string,
): [number, number, number, number] | null {
    const renderedCenter = gridView.getRenderedCellCenter?.(cellId) ?? null;
    if (!renderedCenter) {
        return null;
    }
    const context = elements.grid?.getContext("2d");
    if (!context) {
        return null;
    }
    const imageData = context.getImageData(
        Math.round(renderedCenter.x),
        Math.round(renderedCenter.y),
        1,
        1,
    ).data;
    return [
        Number(imageData[0] ?? 0),
        Number(imageData[1] ?? 0),
        Number(imageData[2] ?? 0),
        Number(imageData[3] ?? 0),
    ];
}

export function installReviewApi({
    controller,
    gridView,
    elements,
}: InstallReviewApiOptions): () => void {
    let reviewBaselineSnapshot: SimulationSnapshot | null = null;

    function captureReviewBaselineIfNeeded(): void {
        if (reviewBaselineSnapshot !== null) {
            return;
        }
        const state = controller.getState();
        const topology = currentTopologyOrThrow(state);
        reviewBaselineSnapshot = cloneSimulationSnapshot(
            buildSimulationSnapshotFromState(
                state,
                topology,
                Array.isArray(state.cellStates)
                    ? state.cellStates.map((cellState) => Number(cellState) || 0)
                    : new Array(topology.cells.length).fill(0),
            ),
        );
    }

    window.__reviewApi = {
        getDiagnostics: () => buildAppDiagnosticsSnapshot(controller, gridView, elements),
        applyTopology: async (topologyPayload) => {
            captureReviewBaselineIfNeeded();
            const state = controller.getState();
            controller.applySimulationState(
                {
                    topology_spec: topologyPayload.topology_spec,
                    speed: Number(state.speed) || 0,
                    running: false,
                    generation: 0,
                    rule: activeRuleOrThrow(state),
                    topology_revision: topologyPayload.topology_revision,
                    topology: topologyPayload,
                    cell_states: new Array(topologyPayload.cells.length).fill(0),
                },
                { source: "review-topology" },
            );
        },
        applyCellStates: async (reviewCellStates) => {
            captureReviewBaselineIfNeeded();
            const state = controller.getState();
            const topology = currentTopologyOrThrow(state);
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
            controller.applySimulationState(
                buildSimulationSnapshotFromState(
                    state,
                    topology,
                    nextCellStates,
                    {
                        running: false,
                        topology_revision: topology.topology_revision,
                    },
                ),
                { source: "review-cell-states" },
            );
        },
        resetState: async () => {
            if (reviewBaselineSnapshot === null) {
                return;
            }
            controller.applySimulationState(
                cloneSimulationSnapshot(reviewBaselineSnapshot),
                { source: "review-reset" },
            );
            reviewBaselineSnapshot = null;
        },
        sampleRenderedCellPixel: (cellId) => sampleRenderedCellPixel(gridView, elements, cellId),
    };

    return () => {
        reviewBaselineSnapshot = null;
        window.__reviewApi = null;
    };
}
