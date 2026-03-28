import type { AppState } from "../types/state.js";

const POLL_INTERVAL_MS = 200;

export function stopPolling(state: AppState): void {
    if (state.pollTimer !== null) {
        window.clearTimeout(state.pollTimer);
        state.pollTimer = null;
    }
}

export function schedulePolling(
    state: AppState,
    callback: () => Promise<void>,
    delay = POLL_INTERVAL_MS,
): void {
    if (!state.isRunning || state.pollTimer !== null) {
        return;
    }

    state.pollTimer = window.setTimeout(async () => {
        state.pollTimer = null;
        await callback();
    }, delay);
}

export function syncPolling(state: AppState, running: boolean, callback: () => Promise<void>): void {
    state.isRunning = running;
    if (running) {
        schedulePolling(state, callback);
        return;
    }
    stopPolling(state);
}
