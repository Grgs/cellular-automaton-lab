import { createCanvasGridView } from "./canvas-view.js";
import { elements } from "./dom.js";
import { createAppController } from "./app-controller.js";

function handleAppError(error: unknown): void {
    console.error(error);
}

export async function initApp(): Promise<void> {
    window.__appReady = false;
    if (!elements.grid) {
        throw new Error("Missing grid canvas element.");
    }
    const controller = createAppController({
        elements,
        gridView: createCanvasGridView({ canvas: elements.grid }),
        onError: handleAppError,
    });
    await controller.init();
    window.__appReady = true;
}
