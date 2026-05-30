import { createCanvasGridView } from "./canvas-view.js";
import { createHttpSimulationBackend } from "./api.js";
import { bootstrapDataFromWindow } from "./bootstrap-data.js";
import { elements } from "./dom.js";
import { createAppController } from "./app-controller.js";
import { mountComparePanel, type ComparePanelHandle } from "./compare/compare-panel.js";
import { installReviewApi } from "./review-api.js";
import type { AppController, InitAppOptions } from "./types/controller-app.js";

function handleAppError(error: unknown): void {
    console.error(error);
}

let activeController: AppController | null = null;
let disposeReviewApi: (() => void) | null = null;
let comparePanel: ComparePanelHandle | null = null;

export function disposeApp(): void {
    comparePanel?.dispose();
    comparePanel = null;
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
        comparePanel = mountComparePanel({ backend, bootstrapData });
    } catch (error) {
        handleAppError(error);
    }
    window.__appReady = true;
    return controller;
}
