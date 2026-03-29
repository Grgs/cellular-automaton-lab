import { createCanvasGridView } from "./canvas-view.js";
import { elements } from "./dom.js";
import { createAppController } from "./app-controller.js";
import type { InitAppOptions } from "./types/controller.js";

function handleAppError(error: unknown): void {
    console.error(error);
}

export async function initApp(options: InitAppOptions = {}): Promise<void> {
    window.__appReady = false;
    if (!elements.grid) {
        throw new Error("Missing grid canvas element.");
    }
    const controller = createAppController({
        elements,
        gridView: createCanvasGridView({ canvas: elements.grid }),
        ...(options.backend === undefined ? {} : { backend: options.backend }),
        onError: handleAppError,
    });
    await controller.init();
    window.__appReady = true;
}
