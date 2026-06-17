import { createCanvasGridView } from "./canvas-view.js";
import { createHttpSimulationBackend } from "./api.js";
import { bootstrapDataFromWindow } from "./bootstrap-data.js";
import { elements } from "./dom.js";
import { buildEditorToolCells } from "./editor-operations.js";
import { createAppController } from "./app-controller.js";
import { mountCompareLauncher, type CompareLauncherHandle } from "./compare/compare-launcher.js";
import { getGeometryAdapter } from "./geometry/registry.js";
import { installReviewApi } from "./review-api.js";
import type { AppController, InitAppOptions } from "./types/controller-app.js";
import type {
    LiveCompareCellSizeOptions,
    LiveCompareWorkspaceHandle,
    LiveCompareWorkspaceOptions,
} from "./live-compare/live-compare.js";

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
    fitRenderCellSize?: (options: LiveCompareCellSizeOptions) => number;
}

function handleAppError(error: unknown): void {
    console.error(error);
}

let activeController: AppController | null = null;
let disposeReviewApi: (() => void) | null = null;
let compareLauncher: CompareLauncherHandle | null = null;
let liveCompareWorkspace: LiveCompareWorkspaceHandle | null = null;

function mountLazyLiveCompareWorkspace(
    options: LiveCompareWorkspaceOptions,
): LiveCompareWorkspaceHandle {
    const trigger = options.trigger;
    if (!trigger || !options.gridPanel) {
        return { dispose() {}, isOpen: () => false };
    }
    const triggerButton = trigger;
    if (!options.baseSessionId || options.bootstrapData.topology_catalog.length === 0) {
        triggerButton.disabled = true;
        triggerButton.title = "Live split view requires independent server sessions.";
        return { dispose() {}, isOpen: () => false };
    }

    let disposed = false;
    let workspace: LiveCompareWorkspaceHandle | null = null;
    let loading: Promise<LiveCompareWorkspaceHandle | null> | null = null;
    const initialText = triggerButton.textContent;
    const initialDisabled = triggerButton.disabled;
    const initialAriaBusy = triggerButton.getAttribute("aria-busy");

    function restoreTriggerLoadingState(): void {
        triggerButton.disabled = initialDisabled;
        if (initialAriaBusy === null) {
            triggerButton.removeAttribute("aria-busy");
        } else {
            triggerButton.setAttribute("aria-busy", initialAriaBusy);
        }
        if (!workspace) {
            triggerButton.textContent = initialText;
        }
    }

    async function loadWorkspace(): Promise<LiveCompareWorkspaceHandle | null> {
        if (workspace) {
            return workspace;
        }
        loading ??= import("./live-compare/live-compare.js")
            .then(({ mountLiveCompareWorkspace }) => {
                if (disposed) {
                    return null;
                }
                workspace = mountLiveCompareWorkspace(options);
                return workspace;
            })
            .finally(() => {
                loading = null;
                if (!disposed) {
                    restoreTriggerLoadingState();
                }
            });
        return loading;
    }

    const handleClick = (event: MouseEvent): void => {
        if (workspace || disposed) {
            return;
        }
        event.preventDefault();
        event.stopImmediatePropagation();
        triggerButton.disabled = true;
        triggerButton.setAttribute("aria-busy", "true");
        triggerButton.textContent = "Loading Split";
        void loadWorkspace()
            .then((loadedWorkspace) => {
                if (!disposed && loadedWorkspace && !loadedWorkspace.isOpen()) {
                    triggerButton.click();
                }
            })
            .catch((error) => {
                restoreTriggerLoadingState();
                (options.onError ?? handleAppError)(error);
            });
    };

    triggerButton.setAttribute("aria-pressed", "false");
    triggerButton.textContent = "Split View";
    triggerButton.addEventListener("click", handleClick, { capture: true });

    return {
        dispose(): void {
            disposed = true;
            triggerButton.removeEventListener("click", handleClick, true);
            workspace?.dispose();
            workspace = null;
            restoreTriggerLoadingState();
            triggerButton.textContent = "Split View";
            triggerButton.setAttribute("aria-pressed", "false");
        },
        isOpen: () => workspace?.isOpen() ?? false,
    };
}

export function disposeApp(): void {
    liveCompareWorkspace?.dispose();
    liveCompareWorkspace = null;
    compareLauncher?.dispose();
    compareLauncher = null;
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
        compareLauncher = mountCompareLauncher({
            backend,
            bootstrapData,
            onOpenPattern: (payload) => {
                void controller.loadPattern(payload);
            },
        });
        const liveCompareBaseSessionId =
            options.liveCompareBaseSessionId ?? window.APP_SESSION_ID ?? null;
        liveCompareWorkspace = mountLazyLiveCompareWorkspace({
            trigger: elements.splitViewToggleBtn,
            gridPanel: elements.gridPanel,
            bootstrapData,
            baseSessionId: liveCompareBaseSessionId,
            mainBackend: backend,
            disposeBackendsOnClose: options.liveCompareDisposeBackendsOnClose ?? false,
            ...(options.liveCompareBackendFactory
                ? { backendFactory: options.liveCompareBackendFactory }
                : {}),
            controls: {
                statusText: elements.statusText,
                generationText: elements.generationText,
                runToggleBtn: elements.runToggleBtn,
                stepBtn: elements.stepBtn,
                resetBtn: elements.resetBtn,
                randomBtn: elements.randomBtn,
                tilingFamilySelect: elements.tilingFamilySelect,
                tilingPickerMenu: elements.tilingPickerMenu,
                tilingPickerToggle: elements.tilingPickerToggle,
                tilingPickerCurrentLabel: elements.tilingPickerCurrentLabel,
            },
            onReturnToSingleView: () => controller.refreshState(),
            createGridView: (canvas) => createCanvasGridView({ canvas }),
            buildEditorToolCells,
            resolveViewportDimensions: (options) => {
                const adapter = getGeometryAdapter(options.geometry) as FitRenderCellSizeAdapter;
                const fitOptions = {
                    viewportWidth: options.viewportWidth,
                    viewportHeight: options.viewportHeight,
                    cellSize: options.cellSize,
                    fallbackDimensions: options.fallbackDimensions,
                    ...(options.maxCellCount !== undefined
                        ? { maxCellCount: options.maxCellCount }
                        : {}),
                };
                return adapter.fitViewport?.(fitOptions) ?? options.fallbackDimensions;
            },
            resolveCellSize: (options) => {
                const adapter = getGeometryAdapter(options.geometry) as FitRenderCellSizeAdapter;
                return adapter.fitRenderCellSize?.(options) ?? options.fallbackCellSize;
            },
        });
    } catch (error) {
        handleAppError(error);
    }
    window.__appReady = true;
    return controller;
}
