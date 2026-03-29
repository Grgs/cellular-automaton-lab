import { fetchBootstrapData, installBootstrapData } from "./bootstrap-data.js";
import { createStandaloneEnvironment } from "./standalone/worker-client.js";

let disposeStandaloneApp = (): void => {};

export function renderStartupError(error: unknown): void {
    const message = error instanceof Error ? error.message : String(error);
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
    const bootstrapData = installBootstrapData(
        await fetchBootstrapData(new URL(/* @vite-ignore */ "../standalone-bootstrap.json", import.meta.url).toString()),
    );
    const environment = await createStandaloneEnvironment(bootstrapData);
    const { disposeApp, initApp } = await import("./main.js");
    disposeStandaloneApp = disposeApp;
    await initApp({
        backend: environment.backend,
        bootstrapData: environment.bootstrapData,
    });
    installPageLifecycleDisposal();
}

startStandaloneApp().catch((error) => {
    console.error("Failed to initialize standalone app", error);
    renderStartupError(error);
});
