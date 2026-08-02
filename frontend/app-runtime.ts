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
import { wireShellMenu } from "./shell/shell-menu.js";
import type { AppController, InitAppOptions } from "./types/controller-app.js";
import type { AppRuntimeEnvironment } from "./types/controller-api.js";

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
let disposeShellMenu: (() => void) | null = null;
let workspaceRouter: WorkspaceRouterHandle | null = null;

function defaultRuntimeEnvironment(): AppRuntimeEnvironment {
    const sessionId = window.APP_SESSION_ID ?? null;
    if (sessionId) {
        return {
            liveForks: {
                kind: "supported",
                baseSessionId: sessionId,
                backendFactory: (childSessionId) =>
                    createHttpSimulationBackend({ sessionId: childSessionId }),
            },
            persistence: { scope: "server-session", guarantee: "debounced-durable" },
        };
    }
    return {
        liveForks: {
            kind: "fallback",
            behavior: "open-in-lab",
            explanation: "This host opens the selected board in the Lab.",
        },
        persistence: { scope: "none", guarantee: "ephemeral" },
    };
}

export function disposeApp(): void {
    workspaceRouter?.dispose();
    workspaceRouter = null;
    disposeReviewApi?.();
    disposeReviewApi = null;
    disposeShellMenu?.();
    disposeShellMenu = null;
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
    const backend = options.backend ?? createHttpSimulationBackend();
    const bootstrapData = options.bootstrapData ?? bootstrapDataFromWindow();
    const runtimeEnvironment: AppRuntimeEnvironment =
        options.runtimeEnvironment ?? defaultRuntimeEnvironment();

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
        liveForks: runtimeEnvironment.liveForks,
        createGridView: createPaneGridView,
        buildEditorToolCells,
        resolveCellSize: resolvePaneCellSize,
        resolveViewportDimensions: resolvePaneViewportDimensions,
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
    disposeShellMenu = wireShellMenu({
        wallTrigger: elements.wallViewBtn,
        labTrigger: elements.openLabBtn,
        executeCompareMenuCommand: (command) => workspaceRouter?.executeCompareMenuCommand(command),
    });
    await workspaceRouter.initialRouteSettled();
    window.__appReady = true;
}
