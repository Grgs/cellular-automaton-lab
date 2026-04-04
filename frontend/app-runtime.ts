import { createCanvasGridView } from "./canvas-view.js";
import { elements } from "./dom.js";
import { createAppController } from "./app-controller.js";
import type { AppController, InitAppOptions } from "./types/controller-app.js";

function handleAppError(error: unknown): void {
    console.error(error);
}

let activeController: AppController | null = null;

export function disposeApp(): void {
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
    const controller = createAppController({
        elements,
        gridView: createCanvasGridView({ canvas: elements.grid }),
        ...(options.backend === undefined ? {} : { backend: options.backend }),
        onError: handleAppError,
    });
    await controller.init();
    activeController = controller;
    window.__appReady = true;
    return controller;
}
