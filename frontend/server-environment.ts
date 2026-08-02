import { createHttpSimulationBackend } from "./api.js";
import { bootstrapDataFromWindow } from "./bootstrap-data.js";
import { getOrCreateServerSessionId } from "./session-id.js";
import type { AppRuntimeEnvironment } from "./types/controller-api.js";

export function createServerEnvironment() {
    const sessionId = getOrCreateServerSessionId();
    window.APP_SESSION_ID = sessionId;
    const runtimeEnvironment: AppRuntimeEnvironment = {
        liveForks: {
            kind: "supported",
            baseSessionId: sessionId,
            backendFactory: (childSessionId) =>
                createHttpSimulationBackend({ sessionId: childSessionId }),
        },
        persistence: { scope: "server-session", guarantee: "debounced-durable" },
    };
    return {
        backend: createHttpSimulationBackend({ sessionId }),
        bootstrapData: bootstrapDataFromWindow(),
        runtimeEnvironment,
    };
}
