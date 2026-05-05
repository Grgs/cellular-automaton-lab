import { disposeApp, initApp } from "./app-runtime.js";
import { createServerEnvironment } from "./server-environment.js";

const environment = createServerEnvironment();

function installPageLifecycleDisposal(): void {
    window.addEventListener("pagehide", () => {
        disposeApp();
    }, { once: true });
}

initApp({ backend: environment.backend, bootstrapData: environment.bootstrapData }).then(() => {
    installPageLifecycleDisposal();
}).catch((error) => {
    console.error("Failed to initialize app", error);
});
