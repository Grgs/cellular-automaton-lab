import { createCanvasGridView } from "./canvas-view.js";
import { createHttpSimulationBackend } from "./api.js";
import { bootstrapDataFromWindow } from "./bootstrap-data.js";
import { elements } from "./dom.js";
import { buildEditorToolCells } from "./editor-operations.js";
import { createAppController } from "./app-controller.js";
import { mountWorkspaceRouter, type WorkspaceRouterHandle } from "./compare/workspace-router.js";
import type {
    FocusPaneServices,
    PaneCellSizeOptions,
    PaneViewportDimensionsOptions,
} from "./pane/pane-core.js";
import { getGeometryAdapter } from "./geometry/registry.js";
import { installReviewApi } from "./review-api.js";
import type { AppController, InitAppOptions } from "./types/controller-app.js";

interface FitRenderCellSizeAdapter {
    fitViewport?: (options: {
        viewportWidth: number;
        viewportHeight: number;
        cellSize: number;
        fallbackDimensions?: { width: number; height: number };
        maxCellCount?: number;
    }) => {
        width: number;
        height: number;
    };
    fitRenderCellSize?: (options: PaneCellSizeOptions) => number;
}

function handleAppError(error: unknown): void {
    console.error(error);
}

let activeController: AppController | null = null;
let disposeReviewApi: (() => void) | null = null;
let workspaceRouter: WorkspaceRouterHandle | null = null;

export function disposeApp(): void {
    workspaceRouter?.dispose();
    workspaceRouter = null;
    disposeReviewApi?.();
    disposeReviewApi = null;
    activeController?.dispose();
    activeController = null;
    window.__appReady = false;
}

export async function initApp(options: InitAppOptions = {}): Promise<AppController> {
    window.__appReady = false;
    if (!elements.grid) {
        throw new Error("Missing grid canvas element.");
    }
    disposeApp();
    const gridView = createCanvasGridView({ canvas: elements.grid });
    const backend = options.backend ?? createHttpSimulationBackend();
    const controller = createAppController({
        elements,
        gridView,
        backend,
        onError: handleAppError,
    });
    await controller.init();
    activeController = controller;
    disposeReviewApi = installReviewApi({ controller, gridView, elements });
    try {
        const bootstrapData = options.bootstrapData ?? bootstrapDataFromWindow();
        const paneBaseSessionId = options.paneBaseSessionId ?? window.APP_SESSION_ID ?? null;

        // Seams for the wall's live focus pane: an independent backend session, a
        // canvas grid view, and the editor geometry helpers.
        const paneBackendFactory =
            options.paneBackendFactory ??
            ((sessionId: string) => createHttpSimulationBackend({ sessionId }));
        const createPaneGridView = (canvas: HTMLCanvasElement) => createCanvasGridView({ canvas });
        const resolvePaneViewportDimensions = (paneOptions: PaneViewportDimensionsOptions) => {
            const adapter = getGeometryAdapter(paneOptions.geometry) as FitRenderCellSizeAdapter;
            const fitOptions = {
                viewportWidth: paneOptions.viewportWidth,
                viewportHeight: paneOptions.viewportHeight,
                cellSize: paneOptions.cellSize,
                fallbackDimensions: paneOptions.fallbackDimensions,
                ...(paneOptions.maxCellCount !== undefined
                    ? { maxCellCount: paneOptions.maxCellCount }
                    : {}),
            };
            return adapter.fitViewport?.(fitOptions) ?? paneOptions.fallbackDimensions;
        };
        const resolvePaneCellSize = (paneOptions: PaneCellSizeOptions) => {
            const adapter = getGeometryAdapter(paneOptions.geometry) as FitRenderCellSizeAdapter;
            return adapter.fitRenderCellSize?.(paneOptions) ?? paneOptions.fallbackCellSize;
        };

        const focusPaneServices: FocusPaneServices = {
            baseSessionId: paneBaseSessionId,
            backendFactory: paneBackendFactory,
            createGridView: createPaneGridView,
            buildEditorToolCells,
            resolveCellSize: resolvePaneCellSize,
            resolveViewportDimensions: resolvePaneViewportDimensions,
        };

        workspaceRouter = mountWorkspaceRouter({
            backend,
            bootstrapData,
            wallTrigger: elements.wallViewBtn,
            focusPaneServices,
            onOpenPattern: (payload) => {
                void controller.loadPattern(payload);
            },
        });
    } catch (error) {
        handleAppError(error);
    }
    window.__appReady = true;
    return controller;
}
