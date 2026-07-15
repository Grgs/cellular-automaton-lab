/**
 * Lightweight, eagerly-loaded router between the app's two destinations: the
 * comparison wall (the landing view) and the Lab (the single-board editor).
 * Both render inside the same static shell (header + content + dock); this
 * router owns which root is visible and which header route tab is active.
 *
 * The URL hash is the source of truth. A bare hash resolves to the wall, so a
 * newcomer lands on the synchronized side-by-side; `#/lab` (or a bare board
 * share link) resolves to the editor. Both destinations are lazy: the heavy
 * compare panel module is dynamically imported the first time the wall is
 * shown, and the editor controller boots (via `ensureLabReady`) the first time
 * the hash resolves to the Lab — a wall landing never boots the editor.
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

// Just enough styling for the loading veil shown while a destination gets
// ready (the wall's panel chunk, or the Lab's first controller boot).
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

/* The Lab backdrop lives outside #lab-root so its fixed sheet can cover the
   viewport. Suspend it by route as well as by drawer state: late Lab renders
   must not make it interactive over the comparison wall. */
:root[data-workspace-route="wall"] #drawer-backdrop {
    display: none !important;
    pointer-events: none !important;
}
`;

export interface MountWorkspaceRouterOptions {
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    /** The static shell host the compare panel mounts into. */
    wallHost?: HTMLElement | null;
    /** The static shell root that contains the Lab (editor) world. */
    labRoot?: HTMLElement | null;
    onOpenPattern?: (pattern: PatternPayload) => void;
    /** Header button that navigates to the wall. */
    wallTrigger?: HTMLButtonElement | null;
    /** Header button that navigates to the Lab. */
    labTrigger?: HTMLButtonElement | null;
    /** Boot the editor controller; awaited before the Lab is interactive. */
    ensureLabReady?: () => Promise<void>;
    /** Server-only seams for the wall's live focus pane. */
    focusPaneServices?: FocusPaneServices;
    /** The Lab rule active when the wall is opened; used for the default wall setup. */
    getInitialRuleName?: () => string | null | undefined;
}

export interface WorkspaceRouterHandle {
    /** Resolves once the landing route is displayed and interactive. */
    initialRouteSettled(): Promise<void>;
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
    const wallHost = options.wallHost ?? document.body;
    const labRoot = options.labRoot ?? null;
    const previousWorkspaceRoute = document.documentElement.getAttribute("data-workspace-route");

    const loadingVeil = document.createElement("div");
    loadingVeil.className = "wall-loading-veil";
    loadingVeil.hidden = true;
    loadingVeil.setAttribute("aria-live", "polite");
    document.body.append(loadingVeil);

    let panel: ComparePanelHandle | null = null;
    let loading = false;
    let labReadyPromise: Promise<void> | null = null;
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
    // are deep-linkable and back/forward navigable. Navigation mirrors into the
    // hash; a hashchange (e.g. the back button) drives the display.
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

    function showRoute(route: ShellRoute): void {
        document.documentElement.dataset.workspaceRoute = route;
        const routeContext = document.getElementById("shell-route-context");
        const sharedBoardOpen = route === "lab" && window.location.hash.includes("share=");
        if (routeContext) {
            routeContext.hidden = !sharedBoardOpen;
            routeContext.textContent = sharedBoardOpen ? "Shared board" : "";
        }
        if (labRoot) {
            labRoot.hidden = route !== "lab";
        }
        if (wallHost !== document.body) {
            wallHost.hidden = route !== "wall";
        }
        if (options.labTrigger) {
            options.labTrigger.hidden = false;
            options.labTrigger.classList.toggle("is-active", route === "lab");
            options.labTrigger.setAttribute("aria-pressed", route === "lab" ? "true" : "false");
            if (route === "lab") {
                options.labTrigger.setAttribute("aria-current", "page");
            } else {
                options.labTrigger.removeAttribute("aria-current");
            }
        }
        if (options.wallTrigger) {
            options.wallTrigger.hidden = false;
            options.wallTrigger.classList.toggle("is-active", route === "wall");
            options.wallTrigger.setAttribute("aria-pressed", route === "wall" ? "true" : "false");
            if (route === "wall") {
                options.wallTrigger.setAttribute("aria-current", "page");
            } else {
                options.wallTrigger.removeAttribute("aria-current");
            }
        }
    }

    /** Keep the wall populated; first visit autoplays, later visits load paused. */
    async function maybeRunDefaultFilmstrip(): Promise<void> {
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
            await panel.runDefaultFilmstrip(FEATURED_COMPARE_DEMO);
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
            void maybeRunDefaultFilmstrip();
            return;
        }
        if (loading) {
            return;
        }
        loading = true;
        loadingVeil.textContent = "Preparing the comparison wall…";
        loadingVeil.hidden = false;
        try {
            const { mountComparePanel } = await import("./compare-panel.js");
            if (disposed) {
                return;
            }
            // The user may have navigated to the Lab while the chunk loaded;
            // mount closed in that case so opening does not rewrite the route.
            const stillOnWall = resolveShellRoute(window.location.hash) === "wall";
            panel = mountComparePanel({
                backend: options.backend,
                bootstrapData: options.bootstrapData,
                host: wallHost,
                ...(options.onOpenPattern ? { onOpenPattern: options.onOpenPattern } : {}),
                ...(options.focusPaneServices
                    ? { focusPaneServices: options.focusPaneServices }
                    : {}),
                ...(options.getInitialRuleName
                    ? { getInitialRuleName: options.getInitialRuleName }
                    : {}),
                openOnMount: stillOnWall,
                onOpen: () => writeHash(hashWithoutLabRoute(window.location.hash)),
                onClose: () => {
                    navigateTo("lab");
                    // Closing can strip slots via replaceState (no hashchange);
                    // resolve the destination explicitly.
                    void syncFromHash();
                },
            });
            await applyRunFromHashIfPresent();
            // The featured demo (or the paused default filmstrip) is real
            // compute; the route counts as settled once the wall is on screen.
            void maybeRunDefaultFilmstrip();
        } finally {
            loading = false;
            if (resolveShellRoute(window.location.hash) === "wall") {
                loadingVeil.hidden = true;
            }
        }
    }

    /** Boot the Lab (once) behind the veil, then reveal it. */
    async function openLab(): Promise<void> {
        if (!labReadyPromise && options.ensureLabReady) {
            loadingVeil.textContent = "Preparing the Lab…";
            loadingVeil.hidden = false;
            labReadyPromise = options.ensureLabReady();
        }
        try {
            await labReadyPromise;
        } finally {
            if (!disposed && resolveShellRoute(window.location.hash) === "lab") {
                loadingVeil.hidden = true;
            }
        }
    }

    /**
     * Resolve the destination for the current hash. Returns a promise that
     * settles when the destination is displayed and interactive (used for the
     * initial landing; later transitions are fire-and-forget).
     */
    function syncFromHash(): Promise<void> {
        if (disposed) {
            return Promise.resolve();
        }
        const route = resolveShellRoute(window.location.hash);
        showRoute(route);
        if (route === "wall") {
            return loadAndOpen();
        }
        panel?.close();
        return openLab();
    }

    function onHashChange(): void {
        void syncFromHash();
    }

    function onWallTriggerClick(): void {
        navigateTo("wall");
        // Entering the wall can strip the hash to empty via replaceState, which
        // fires no hashchange; resolve the destination explicitly.
        void syncFromHash();
    }

    function onLabTriggerClick(): void {
        navigateTo("lab");
        void syncFromHash();
    }

    options.wallTrigger?.addEventListener("click", onWallTriggerClick);
    options.labTrigger?.addEventListener("click", onLabTriggerClick);
    window.addEventListener("hashchange", onHashChange);
    // Resolve the landing destination for the hash present on first load.
    const initialSettled = syncFromHash();

    return {
        initialRouteSettled: () => initialSettled,
        dispose(): void {
            disposed = true;
            window.removeEventListener("hashchange", onHashChange);
            options.wallTrigger?.removeEventListener("click", onWallTriggerClick);
            options.labTrigger?.removeEventListener("click", onLabTriggerClick);
            panel?.dispose();
            panel = null;
            loadingVeil.remove();
            if (previousWorkspaceRoute === null) {
                document.documentElement.removeAttribute("data-workspace-route");
            } else {
                document.documentElement.setAttribute(
                    "data-workspace-route",
                    previousWorkspaceRoute,
                );
            }
        },
    };
}
