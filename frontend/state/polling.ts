import type { AppState } from "../types/state.js";

const POLL_INTERVAL_MS = 200;
const MIN_RUNNING_POLL_INTERVAL_MS = 50;
const MAX_RUNNING_POLL_INTERVAL_MS = 1000;

export function pollDelayForSpeed(speed: number): number {
    const numericSpeed = Number(speed);
    if (!Number.isFinite(numericSpeed) || numericSpeed <= 0) {
        return POLL_INTERVAL_MS;
    }
    return Math.min(
        MAX_RUNNING_POLL_INTERVAL_MS,
        Math.max(MIN_RUNNING_POLL_INTERVAL_MS, Math.round(1000 / numericSpeed)),
    );
}

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

export function syncPolling(
    state: AppState,
    running: boolean,
    callback: () => Promise<void>,
): void {
    state.isRunning = running;
    if (running) {
        schedulePolling(state, callback, pollDelayForSpeed(state.speed));
        return;
    }
    stopPolling(state);
}
