import { createCanvasGridView } from "./canvas-view.js";
import { elements } from "./dom.js";
import { createAppController } from "./app-controller.js";
import { installReviewApi } from "./review-api.js";
import type { AppController, InitAppOptions } from "./types/controller-app.js";

function handleAppError(error: unknown): void {
    console.error(error);
}

let activeController: AppController | null = null;
let disposeReviewApi: (() => void) | null = null;

export function disposeApp(): void {
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
    const controller = createAppController({
        elements,
        gridView,
        ...(options.backend === undefined ? {} : { backend: options.backend }),
        onError: handleAppError,
    });
    await controller.init();
    activeController = controller;
    disposeReviewApi = installReviewApi({ controller, gridView, elements });
    window.__appReady = true;
    return controller;
}
