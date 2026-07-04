/**
 * Lightweight, eagerly-loaded entry point for compare mode. It renders only the
 * floating toggle button; the heavy compare panel module (charts, thumbnails,
 * seed pad/preview, styles) is dynamically imported the first time the user
 * opens it, keeping it out of the initial app-runtime bundle.
 */

import type { AppBootstrapData, PatternPayload } from "../types/domain.js";
import type { SimulationBackend } from "../types/controller.js";
import { FEATURED_COMPARE_DEMO } from "./compare-options.js";
import {
    CompareRunLinkDecodeError,
    decodeCompareRunFragment,
    readCompareRunBodyFromHash,
} from "./compare-run-link.js";
import type { ComparePanelHandle } from "./compare-panel.js";
import {
    hashHasCompareRoute,
    hashWithCompareRoute,
    hashWithoutCompareRoute,
} from "./compare-route.js";

const TOGGLE_STYLE_ID = "compare-toggle-styles";

// Just enough styling for the toggle to look right before the panel chunk (which
// also defines .compare-toggle) loads. Kept in sync with compare-styles.ts.
const TOGGLE_STYLES = `
.compare-toggle {
    position: fixed;
    right: 16px;
    bottom: 16px;
    z-index: 60;
    padding: 10px 14px;
    border-radius: 999px;
    border: 1px solid var(--btn-primary-line, rgba(0, 0, 0, 0.2));
    background: var(--btn-primary-bg, #bf5a36);
    color: var(--btn-primary-text, #fff);
    font-family: var(--sans, sans-serif);
    font-size: 13px;
    cursor: pointer;
    box-shadow: var(--shadow, 0 8px 24px rgba(0, 0, 0, 0.2));
}
.compare-toggle:hover { background: var(--btn-primary-hover, #a44928); }
.compare-toggle[disabled] { cursor: progress; opacity: 0.85; }
.compare-watch-banner {
    position: fixed;
    right: 16px;
    bottom: 60px;
    z-index: 60;
    padding: 10px 16px;
    border-radius: 999px;
    border: 1px solid var(--btn-primary-line, rgba(0, 0, 0, 0.2));
    background: var(--accent-strong, #2f6f6f);
    color: var(--btn-primary-text, #fff);
    font-family: var(--sans, sans-serif);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: var(--shadow, 0 8px 24px rgba(0, 0, 0, 0.2));
}
.compare-watch-banner:hover { filter: brightness(1.06); }
.compare-watch-banner[disabled] { cursor: progress; opacity: 0.85; }
`;

export interface MountCompareLauncherOptions {
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    host?: HTMLElement;
    onOpenPattern?: (pattern: PatternPayload) => void;
}

export interface CompareLauncherHandle {
    /** Open the workspace and start the curated, looping featured comparison. */
    openFeaturedDemo(): Promise<void>;
    dispose(): void;
}

function ensureToggleStyles(): void {
    if (document.getElementById(TOGGLE_STYLE_ID)) {
        return;
    }
    const style = document.createElement("style");
    style.id = TOGGLE_STYLE_ID;
    style.textContent = TOGGLE_STYLES;
    document.head.append(style);
}

export function mountCompareLauncher(options: MountCompareLauncherOptions): CompareLauncherHandle {
    ensureToggleStyles();
    const host = options.host ?? document.body;

    const toggle = document.createElement("button");
    toggle.className = "compare-toggle";
    toggle.type = "button";
    toggle.title = "Compare a seed across tilings";
    toggle.textContent = "⊞ Compare tilings";
    host.append(toggle);

    const watchBanner = document.createElement("button");
    watchBanner.className = "compare-watch-banner";
    watchBanner.type = "button";
    watchBanner.title = "Watch one seed evolve in lockstep across four tilings";
    watchBanner.textContent = "▶ Watch tilings compare";
    host.append(watchBanner);

    let panel: ComparePanelHandle | null = null;
    let loading = false;
    let lastAppliedRunBody: string | null = null;
    let disposed = false;

    async function applyRunFromHashIfPresent(): Promise<void> {
        const activePanel = panel;
        if (!activePanel || disposed) {
            return;
        }
        const body = readCompareRunBodyFromHash(window.location.hash);
        if (!body || body === lastAppliedRunBody) {
            return;
        }
        // Mark this body handled up front so a malformed link is reported once,
        // not re-processed on every later hashchange.
        lastAppliedRunBody = body;
        try {
            const config = decodeCompareRunFragment(window.location.hash);
            if (!config) {
                return;
            }
            await activePanel.applyRunConfig(config);
        } catch (error) {
            if (error instanceof CompareRunLinkDecodeError) {
                activePanel.reportRunLinkError(error.message);
            } else {
                console.error(error);
                activePanel.reportRunLinkError("This run link could not be opened.");
            }
        }
    }

    // The URL hash is the source of truth for whether compare is open, so it is
    // deep-linkable and back/forward navigable. Opening/closing the panel mirrors
    // the route into the hash; a hashchange (e.g. the back button) drives the panel.
    function navigateCompare(toCompare: boolean): void {
        const current = window.location.hash;
        const next = toCompare ? hashWithCompareRoute(current) : hashWithoutCompareRoute(current);
        if (next === current) {
            return;
        }
        if (next === "") {
            // Strip the hash without leaving a bare "#"; the panel is already
            // closed by the time this runs, so no re-sync is needed.
            window.history.replaceState(
                null,
                "",
                `${window.location.pathname}${window.location.search}`,
            );
        } else {
            window.location.hash = next;
        }
    }

    async function loadAndOpen(): Promise<void> {
        if (disposed) {
            return;
        }
        if (panel) {
            panel.open();
            await applyRunFromHashIfPresent();
            return;
        }
        if (loading) {
            return;
        }
        loading = true;
        toggle.disabled = true;
        try {
            const { mountComparePanel } = await import("./compare-panel.js");
            if (disposed) {
                return;
            }
            panel = mountComparePanel({
                backend: options.backend,
                bootstrapData: options.bootstrapData,
                host,
                ...(options.onOpenPattern ? { onOpenPattern: options.onOpenPattern } : {}),
                trigger: toggle,
                openOnMount: true,
                presentation: "workspace",
                onOpen: () => navigateCompare(true),
                onClose: () => navigateCompare(false),
            });
            await applyRunFromHashIfPresent();
        } finally {
            loading = false;
            toggle.disabled = false;
        }
    }

    function syncFromHash(): void {
        if (disposed) {
            return;
        }
        if (hashHasCompareRoute(window.location.hash)) {
            void loadAndOpen();
            return;
        }
        panel?.close();
    }

    async function openFeaturedDemo(): Promise<void> {
        watchBanner.disabled = true;
        try {
            await loadAndOpen();
            if (!disposed) {
                await panel?.runFeaturedDemo(FEATURED_COMPARE_DEMO);
            }
        } finally {
            watchBanner.disabled = false;
        }
    }

    // Kept (not {once}) so a failed first lazy load can be retried and later
    // clicks reopen the workspace through the same route-aware path.
    toggle.addEventListener("click", () => void loadAndOpen());
    watchBanner.addEventListener("click", () => void openFeaturedDemo());
    window.addEventListener("hashchange", syncFromHash);
    // Honour a deep link (e.g. #/compare) present on first load.
    syncFromHash();

    return {
        openFeaturedDemo,
        dispose(): void {
            disposed = true;
            window.removeEventListener("hashchange", syncFromHash);
            panel?.dispose();
            panel = null;
            toggle.remove();
            watchBanner.remove();
        },
    };
}
