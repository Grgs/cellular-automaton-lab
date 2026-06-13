import { createHttpSimulationBackend } from "./api.js";
import { bootstrapDataFromWindow } from "./bootstrap-data.js";
import { getOrCreateServerSessionId } from "./session-id.js";

export function createServerEnvironment() {
    const sessionId = getOrCreateServerSessionId();
    window.APP_SESSION_ID = sessionId;
    return {
        backend: createHttpSimulationBackend({ sessionId }),
        bootstrapData: bootstrapDataFromWindow(),
    };
}
