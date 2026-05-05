import { fetchBootstrapData, installBootstrapData } from "./bootstrap-data.js";
import { createStandaloneEnvironment } from "./standalone/worker-client.js";

let disposeStandaloneApp = (): void => {};

interface StartupStage {
    message: string;
    detail: string;
}

const STARTUP_STAGE_LOADING_DATA: StartupStage = {
    message: "Loading app data",
    detail: "Reading bundled defaults and topology catalog.",
};

const STARTUP_STAGE_STARTING_PYTHON: StartupStage = {
    message: "Starting Python runtime",
    detail: "Loading Pyodide, bundled Python sources, and the first board.",
};

function startupOverlayElements(): {
    overlay: HTMLElement | null;
    message: HTMLElement | null;
    detail: HTMLElement | null;
} {
    return {
        overlay: document.getElementById("standalone-startup-overlay"),
        message: document.getElementById("standalone-startup-message"),
        detail: document.getElementById("standalone-startup-detail"),
    };
}

function setStartupPending(isPending: boolean): void {
    const appFrame = document.getElementById("app-frame");
    if (!appFrame) {
        return;
    }
    appFrame.classList.toggle("standalone-startup-pending", isPending);
    appFrame.toggleAttribute("inert", isPending);
    appFrame.setAttribute("aria-busy", isPending ? "true" : "false");
}

function showStartupOverlay(stage: StartupStage): void {
    const { overlay, message, detail } = startupOverlayElements();
    setStartupPending(true);
    if (overlay) {
        overlay.hidden = false;
        overlay.setAttribute("aria-hidden", "false");
        overlay.classList.remove("is-error");
    }
    if (message) {
        message.textContent = stage.message;
    }
    if (detail) {
        detail.textContent = stage.detail;
        detail.hidden = false;
    }
}

function hideStartupOverlay(): void {
    const { overlay } = startupOverlayElements();
    setStartupPending(false);
    if (!overlay) {
        return;
    }
    overlay.hidden = true;
    overlay.setAttribute("aria-hidden", "true");
    overlay.classList.remove("is-error");
}

export function renderStartupError(error: unknown): void {
    const message = error instanceof Error ? error.message : String(error);
    const { overlay, message: overlayMessage, detail } = startupOverlayElements();
    setStartupPending(true);
    if (overlay) {
        overlay.hidden = false;
        overlay.setAttribute("aria-hidden", "false");
        overlay.classList.add("is-error");
    }
    if (overlayMessage) {
        overlayMessage.textContent = "Standalone runtime failed to initialize";
    }
    if (detail) {
        detail.textContent = message;
        detail.hidden = false;
    }
    const container = document.getElementById("app-startup-error") ?? document.body;
    container.removeAttribute("hidden");
    container.textContent = `Standalone runtime failed to initialize: ${message}`;
    container.classList.add("startup-error-visible");
}

function installPageLifecycleDisposal(): void {
    window.addEventListener("pagehide", () => {
        disposeStandaloneApp();
    }, { once: true });
}

export async function startStandaloneApp(): Promise<void> {
    showStartupOverlay(STARTUP_STAGE_LOADING_DATA);
    const bootstrapData = installBootstrapData(
        await fetchBootstrapData(new URL(/* @vite-ignore */ "../standalone-bootstrap.json", import.meta.url).toString()),
    );
    showStartupOverlay(STARTUP_STAGE_STARTING_PYTHON);
    const environment = await createStandaloneEnvironment(bootstrapData);
    const { disposeApp, initApp } = await import("./app-runtime.js");
    disposeStandaloneApp = disposeApp;
    await initApp({
        backend: environment.backend,
        bootstrapData: environment.bootstrapData,
    });
    hideStartupOverlay();
    installPageLifecycleDisposal();
}

startStandaloneApp().catch((error) => {
    console.error("Failed to initialize standalone app", error);
    renderStartupError(error);
});
