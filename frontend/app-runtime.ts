import { createCanvasGridView } from "./canvas-view.js";
import { createHttpSimulationBackend } from "./api.js";
import { bootstrapDataFromWindow } from "./bootstrap-data.js";
import { elements } from "./dom.js";
import { buildEditorToolCells } from "./editor-operations.js";
import { createAppController } from "./app-controller.js";
import { mountCompareLauncher, type CompareLauncherHandle } from "./compare/compare-launcher.js";
import { getGeometryAdapter } from "./geometry/registry.js";
import {
    mountLiveCompareWorkspace,
    type LiveCompareCellSizeOptions,
    type LiveCompareWorkspaceHandle,
} from "./live-compare/live-compare.js";
import { installReviewApi } from "./review-api.js";
import type { AppController, InitAppOptions } from "./types/controller-app.js";

interface FitRenderCellSizeAdapter {
    fitRenderCellSize?: (options: LiveCompareCellSizeOptions) => number;
}

function handleAppError(error: unknown): void {
    console.error(error);
}

let activeController: AppController | null = null;
let disposeReviewApi: (() => void) | null = null;
let compareLauncher: CompareLauncherHandle | null = null;
let liveCompareWorkspace: LiveCompareWorkspaceHandle | null = null;

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
        liveCompareWorkspace = mountLiveCompareWorkspace({
            trigger: elements.splitViewToggleBtn,
            gridPanel: elements.gridPanel,
            bootstrapData,
            baseSessionId: window.APP_SESSION_ID ?? null,
            mainBackend: backend,
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
