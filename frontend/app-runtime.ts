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
import { wireShellThemeToggle } from "./shell/shell-theme.js";
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
let disposeThemeToggle: (() => void) | null = null;
let workspaceRouter: WorkspaceRouterHandle | null = null;

export function disposeApp(): void {
    workspaceRouter?.dispose();
    workspaceRouter = null;
    disposeReviewApi?.();
    disposeReviewApi = null;
    disposeThemeToggle?.();
    disposeThemeToggle = null;
    activeController?.dispose();
    activeController = null;
    window.__appReady = false;
}

/**
 * Boot the shell. The editor controller is lazy: a wall landing never runs
 * `controller.init()` — the router asks for it (via `ensureLabReady`) the
 * first time the hash resolves to the Lab. `window.__appReady` flips true only
 * after the initial route has settled, which on a `#/lab` or `#share=` landing
 * includes the controller boot so the Lab's bindings exist before tests and
 * tools start clicking.
 */
export async function initApp(options: InitAppOptions = {}): Promise<void> {
    window.__appReady = false;
    if (!elements.grid) {
        throw new Error("Missing grid canvas element.");
    }
    disposeApp();
    disposeThemeToggle = wireShellThemeToggle(elements);
    const backend = options.backend ?? createHttpSimulationBackend();
    const bootstrapData = options.bootstrapData ?? bootstrapDataFromWindow();
    const paneBaseSessionId = options.paneBaseSessionId ?? window.APP_SESSION_ID ?? null;

    let controllerPromise: Promise<AppController> | null = null;
    function ensureController(): Promise<AppController> {
        if (!controllerPromise) {
            controllerPromise = (async () => {
                const gridView = createCanvasGridView({ canvas: elements.grid! });
                const controller = createAppController({
                    elements,
                    gridView,
                    backend,
                    onError: handleAppError,
                });
                await controller.init();
                activeController = controller;
                disposeReviewApi = installReviewApi({ controller, gridView, elements });
                return controller;
            })();
        }
        return controllerPromise;
    }

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
        ...(options.paneForkCapacity === undefined
            ? {}
            : { forkCapacity: options.paneForkCapacity }),
    };

    workspaceRouter = mountWorkspaceRouter({
        backend,
        bootstrapData,
        wallHost: elements.wallRoot,
        labRoot: elements.labRoot,
        wallTrigger: elements.wallViewBtn,
        labTrigger: elements.openLabBtn,
        ensureLabReady: async () => {
            await ensureController();
        },
        focusPaneServices,
        getInitialRuleName: () => {
            if (!activeController) {
                return null;
            }
            const state = activeController.getState();
            return state.editorRuleName ?? state.activeRule?.name ?? null;
        },
        onOpenPattern: async (payload) => {
            try {
                const controller = await ensureController();
                await controller.loadPattern(payload);
            } catch (error) {
                handleAppError(error);
            }
        },
    });
    await workspaceRouter.initialRouteSettled();
    window.__appReady = true;
}
