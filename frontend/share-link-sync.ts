/**
 * Keep the URL hash in sync with the current board state.
 *
 * Called after each snapshot apply. The serializer reuses the existing
 * `buildPatternPayload` helper, which means the URL is only updated once the
 * topology and rule are populated. Before that we silently no-op.
 *
 * The board mirror only runs while the hash addresses the Lab: the wall owns
 * its own hash slots (`run=`, `focus=`), and a `share=` slot written under the
 * wall would re-route the next reload into the Lab. Once booted, the editor
 * controller keeps applying snapshots even after the user returns to the wall,
 * so this guard is what keeps the two URL vocabularies apart.
 *
 * Updates use `history.replaceState` so the user's history stack is not
 * polluted with a new entry per generation.
 */

import { buildPatternPayload } from "./pattern-io.js";
import { PatternValidationError } from "./parsers/pattern.js";
import { buildHashFragmentForReplaceState } from "./share-link.js";
import { resolveShellRoute } from "./compare/compare-route.js";
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
    if (resolveShellRoute(locationApi.hash) !== "lab") {
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
