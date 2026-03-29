import { createHttpSimulationBackend } from "./api.js";
import { bootstrapDataFromWindow } from "./bootstrap-data.js";

export function createServerEnvironment() {
    return {
        backend: createHttpSimulationBackend(),
        bootstrapData: bootstrapDataFromWindow(),
    };
}
