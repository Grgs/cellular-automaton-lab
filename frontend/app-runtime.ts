import { createCanvasGridView } from "./canvas-view.js";
import { elements } from "./dom.js";
import { createAppController } from "./app-controller.js";
import type { AppController, InitAppOptions } from "./types/controller-app.js";

interface ReviewApi {
    getDiagnostics(): ReturnType<typeof buildAppDiagnosticsSnapshot>;
    applyTopology(topologyPayload: Parameters<AppController["applyReviewTopology"]>[0]): Promise<void>;
    applyCellStates(reviewCellStates: Parameters<AppController["applyReviewCellStates"]>[0]): Promise<void>;
    resetState(): Promise<void>;
    getRenderedCellCenter(cellId: string): ReturnType<AppController["getRenderedCellCenter"]>;
    sampleRenderedCellPixel(cellId: string): [number, number, number, number] | null;
}

function handleAppError(error: unknown): void {
    console.error(error);
}

let activeController: AppController | null = null;

function buildAppDiagnosticsSnapshot(controller: AppController) {
    const state = controller.getState();
    const topologySpec = state.topologySpec || null;
    const topology = state.topology || null;
    const renderDiagnostics = controller.getRenderDiagnostics();
    const readText = (element: HTMLElement | null) => element?.textContent?.trim() || "";
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

function sampleRenderedCellPixel(controller: AppController, cellId: string): [number, number, number, number] | null {
    const renderedCenter = controller.getRenderedCellCenter(cellId);
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

function installReviewApi(controller: AppController): void {
    const reviewApi: ReviewApi = {
        getDiagnostics: () => buildAppDiagnosticsSnapshot(controller),
        applyTopology: async (topologyPayload) => {
            controller.applyReviewTopology(topologyPayload);
        },
        applyCellStates: async (reviewCellStates) => {
            controller.applyReviewCellStates(reviewCellStates);
        },
        resetState: async () => {
            controller.resetReviewState();
        },
        getRenderedCellCenter: (cellId) => controller.getRenderedCellCenter(cellId),
        sampleRenderedCellPixel: (cellId) => sampleRenderedCellPixel(controller, cellId),
    };
    window.__reviewApi = reviewApi;
    window.__appDiagnostics = reviewApi.getDiagnostics;
    window.__applyReviewTopology = reviewApi.applyTopology;
    window.__resolveRenderedCellCenter = async (cellId) => reviewApi.getRenderedCellCenter(cellId);
}

export function disposeApp(): void {
    activeController?.dispose();
    activeController = null;
    window.__reviewApi = null;
    window.__appDiagnostics = null;
    window.__applyReviewTopology = null;
    window.__resolveRenderedCellCenter = null;
    window.__appReady = false;
}

export async function initApp(options: InitAppOptions = {}): Promise<AppController> {
    window.__appReady = false;
    if (!elements.grid) {
        throw new Error("Missing grid canvas element.");
    }
    disposeApp();
    const controller = createAppController({
        elements,
        gridView: createCanvasGridView({ canvas: elements.grid }),
        ...(options.backend === undefined ? {} : { backend: options.backend }),
        onError: handleAppError,
    });
    await controller.init();
    activeController = controller;
    installReviewApi(controller);
    window.__appReady = true;
    return controller;
}
