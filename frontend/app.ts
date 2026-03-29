import { initApp } from "./main.js";
import { createServerEnvironment } from "./server-environment.js";

const environment = createServerEnvironment();

initApp({ backend: environment.backend, bootstrapData: environment.bootstrapData }).catch((error) => {
    console.error("Failed to initialize app", error);
});
