import { createCanvasGridView } from "./canvas-view.js";
import { createHttpSimulationBackend } from "./api.js";
import { bootstrapDataFromWindow } from "./bootstrap-data.js";
import { elements } from "./dom.js";
import { createAppController } from "./app-controller.js";
import { mountCompareLauncher, type CompareLauncherHandle } from "./compare/compare-launcher.js";
import { installReviewApi } from "./review-api.js";
import type { AppController, InitAppOptions } from "./types/controller-app.js";

function handleAppError(error: unknown): void {
    console.error(error);
}

let activeController: AppController | null = null;
let disposeReviewApi: (() => void) | null = null;
let compareLauncher: CompareLauncherHandle | null = null;

export function disposeApp(): void {
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
    } catch (error) {
        handleAppError(error);
    }
    window.__appReady = true;
    return controller;
}
