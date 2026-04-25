/**
 * Keep the URL hash in sync with the current board state.
 *
 * Called after each snapshot apply. The serializer reuses the existing
 * `buildPatternPayload` helper, which means the URL is only updated once the
 * topology and rule are populated. Before that we silently no-op.
 *
 * Updates use `history.replaceState` so the user's history stack is not
 * polluted with a new entry per generation.
 */

import { buildPatternPayload } from "./pattern-io.js";
import { PatternValidationError } from "./parsers/pattern.js";
import { buildHashFragmentForReplaceState } from "./share-link.js";
import type { AppState } from "./types/state.js";

export interface ShareLinkSyncOptions {
    historyApi?: Pick<History, "replaceState"> | null;
    locationApi?: Pick<Location, "hash" | "pathname" | "search"> | null;
}

export function syncShareLinkUrlFromState(
    state: AppState,
    {
        historyApi = typeof window !== "undefined" ? window.history : null,
        locationApi = typeof window !== "undefined" ? window.location : null,
    }: ShareLinkSyncOptions = {},
): void {
    if (!historyApi || !locationApi) {
        return;
    }
    let payload;
    try {
        payload = buildPatternPayload(state);
    } catch (error) {
        if (error instanceof PatternValidationError) {
            // State is not yet ready (no topology or no rule resolved).
            return;
        }
        throw error;
    }
    const nextHash = buildHashFragmentForReplaceState(payload, locationApi.hash);
    if (nextHash === locationApi.hash) {
        return;
    }
    const url = `${locationApi.pathname}${locationApi.search}${nextHash}`;
    historyApi.replaceState(null, "", url);
}
