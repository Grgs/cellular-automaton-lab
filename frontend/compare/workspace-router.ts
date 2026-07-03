/**
 * Lightweight, eagerly-loaded router between the app's two destinations: the
 * comparison wall (the landing view) and the Lab (the single-board editor).
 *
 * The URL hash is the source of truth. A bare hash resolves to the wall, so a
 * newcomer lands on the synchronized side-by-side; `#/lab` (or a bare board
 * share link) resolves to the editor. The heavy compare panel module (charts,
 * thumbnails, seed pad/preview, styles) is dynamically imported the first time
 * the wall is shown, behind a minimal eager loading veil.
 *
 * On a first visit (no run/share slot, demo not yet seen) the wall autoplays
 * the curated featured comparison so the app opens on something alive.
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
    hashWithLabRoute,
    hashWithoutCompareRoute,
    hashWithoutFocus,
    hashWithoutLabRoute,
    resolveShellRoute,
    type ShellRoute,
} from "./compare-route.js";
import { clearShareFragment } from "../share-link.js";
import { isCompareDemoSeen, markCompareDemoSeen } from "./compare-storage.js";
import type { FocusPaneServices } from "../pane/pane-core.js";

const ROUTER_STYLE_ID = "workspace-router-styles";

// Just enough styling for the loading veil shown while the wall's panel chunk
// loads, so the first paint is not the editor flashing beneath the workspace.
const ROUTER_STYLES = `
.wall-loading-veil {
    position: fixed;
    inset: 0;
    z-index: 65;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--panel-strong, #fff);
    color: var(--muted, #6d756f);
    font-family: var(--sans, sans-serif);
    font-size: 14px;
}
.wall-loading-veil[hidden] { display: none; }
`;

export interface MountWorkspaceRouterOptions {
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    host?: HTMLElement;
    onOpenPattern?: (pattern: PatternPayload) => void;
    /** Top-bar button in the Lab that navigates back to the wall. */
    wallTrigger?: HTMLButtonElement | null;
    /** Server-only seams for the wall's live focus pane. */
    focusPaneServices?: FocusPaneServices;
    /** The Lab rule active when the wall is opened; used for the default wall setup. */
    getInitialRuleName?: () => string | null | undefined;
}

export interface WorkspaceRouterHandle {
    dispose(): void;
}

function ensureRouterStyles(): void {
    if (document.getElementById(ROUTER_STYLE_ID)) {
        return;
    }
    const style = document.createElement("style");
    style.id = ROUTER_STYLE_ID;
    style.textContent = ROUTER_STYLES;
    document.head.append(style);
}

export function mountWorkspaceRouter(options: MountWorkspaceRouterOptions): WorkspaceRouterHandle {
    ensureRouterStyles();
    const host = options.host ?? document.body;

    const loadingVeil = document.createElement("div");
    loadingVeil.className = "wall-loading-veil";
    loadingVeil.hidden = true;
    loadingVeil.setAttribute("aria-live", "polite");
    loadingVeil.textContent = "Preparing the comparison wall…";
    host.append(loadingVeil);

    let panel: ComparePanelHandle | null = null;
    let loading = false;
    let lastAppliedRunBody: string | null = null;
    let demoConsidered = false;
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

    function writeHash(next: string): void {
        const current = window.location.hash;
        if (next === current) {
            return;
        }
        if (next === "") {
            // Strip the hash without leaving a bare "#". This does not fire a
            // hashchange, but callers only reach it when the destination state
            // is already applied.
            window.history.replaceState(
                null,
                "",
                `${window.location.pathname}${window.location.search}`,
            );
        } else {
            window.location.hash = next;
        }
    }

    // The hash is the source of truth for which destination is active, so both
    // are deep-linkable and back/forward navigable. Opening/closing the panel
    // mirrors into the hash; a hashchange (e.g. the back button) drives the panel.
    function navigateTo(route: ShellRoute): void {
        const current = window.location.hash;
        if (route === "lab") {
            // Leaving the wall: the legacy /compare alias and the focus slot are
            // meaningless in the Lab.
            writeHash(hashWithLabRoute(hashWithoutFocus(hashWithoutCompareRoute(current))));
            return;
        }
        // Entering the wall: drop /lab, and drop any share slot — a bare share
        // link resolves to the Lab, so keeping it would bounce straight back.
        writeHash(clearShareFragment(hashWithoutLabRoute(current)));
    }

    /** First visit only: autoplay the curated demo so the landing is alive. */
    async function maybeRunFeaturedDemo(): Promise<void> {
        if (demoConsidered || disposed || !panel) {
            return;
        }
        demoConsidered = true;
        const hash = window.location.hash;
        if (resolveShellRoute(hash) !== "wall") {
            return;
        }
        // A run or share link is an explicit destination; don't play over it.
        if (readCompareRunBodyFromHash(hash) || hash.includes("share=")) {
            return;
        }
        if (isCompareDemoSeen()) {
            return;
        }
        // Mark seen before running so a failing demo never becomes a reload loop.
        markCompareDemoSeen();
        await panel.runFeaturedDemo(FEATURED_COMPARE_DEMO);
    }

    async function loadAndOpen(): Promise<void> {
        if (disposed) {
            return;
        }
        if (panel) {
            panel.open();
            await applyRunFromHashIfPresent();
            await maybeRunFeaturedDemo();
            return;
        }
        if (loading) {
            return;
        }
        loading = true;
        loadingVeil.hidden = false;
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
                ...(options.focusPaneServices
                    ? { focusPaneServices: options.focusPaneServices }
                    : {}),
                ...(options.getInitialRuleName
                    ? { getInitialRuleName: options.getInitialRuleName }
                    : {}),
                openOnMount: true,
                onOpen: () => writeHash(hashWithoutLabRoute(window.location.hash)),
                onClose: () => navigateTo("lab"),
            });
            await applyRunFromHashIfPresent();
            await maybeRunFeaturedDemo();
        } finally {
            loading = false;
            loadingVeil.hidden = true;
        }
    }

    function syncFromHash(): void {
        if (disposed) {
            return;
        }
        if (resolveShellRoute(window.location.hash) === "wall") {
            void loadAndOpen();
            return;
        }
        loadingVeil.hidden = true;
        panel?.close();
    }

    function onWallTriggerClick(): void {
        navigateTo("wall");
        // Entering the wall can strip the hash to empty via replaceState, which
        // fires no hashchange; resolve the destination explicitly.
        syncFromHash();
    }

    options.wallTrigger?.addEventListener("click", onWallTriggerClick);
    window.addEventListener("hashchange", syncFromHash);
    // Resolve the landing destination for the hash present on first load.
    syncFromHash();

    return {
        dispose(): void {
            disposed = true;
            window.removeEventListener("hashchange", syncFromHash);
            options.wallTrigger?.removeEventListener("click", onWallTriggerClick);
            panel?.dispose();
            panel = null;
            loadingVeil.remove();
        },
    };
}
