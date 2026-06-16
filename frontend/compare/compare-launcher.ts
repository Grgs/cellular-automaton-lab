/**
 * Lightweight, eagerly-loaded entry point for compare mode. It renders only the
 * floating toggle button; the heavy compare panel module (charts, thumbnails,
 * seed pad/preview, styles) is dynamically imported the first time the user
 * opens it, keeping it out of the initial app-runtime bundle.
 */

import type { AppBootstrapData, PatternPayload } from "../types/domain.js";
import type { SimulationBackend } from "../types/controller.js";
import {
    addCompareRouteToHash,
    decodeCompareRunFragment,
    hashHasCompareRoute,
    readCompareRunBodyFromHash,
    removeCompareRouteFromHash,
} from "./compare-run-link.js";
import type { ComparePanelHandle } from "./compare-panel.js";

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
`;

export interface MountCompareLauncherOptions {
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    host?: HTMLElement;
    onOpenPattern?: (pattern: PatternPayload) => void;
}

export interface CompareLauncherHandle {
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

    let panel: ComparePanelHandle | null = null;
    let loading = false;
    let lastAppliedRunBody: string | null = null;
    let disposed = false;

    function setCompareRoute(open: boolean): void {
        const currentHash = window.location.hash;
        const nextHash = open
            ? addCompareRouteToHash(currentHash)
            : removeCompareRouteFromHash(currentHash);
        if (nextHash === currentHash) {
            return;
        }
        if (!nextHash) {
            window.history.replaceState(
                null,
                "",
                `${window.location.pathname}${window.location.search}`,
            );
            return;
        }
        window.location.hash = nextHash;
    }

    async function applyRunFromHashIfPresent(): Promise<void> {
        if (!panel || disposed) {
            return;
        }
        const body = readCompareRunBodyFromHash(window.location.hash);
        if (!body || body === lastAppliedRunBody) {
            return;
        }
        try {
            const config = decodeCompareRunFragment(window.location.hash);
            if (!config) {
                return;
            }
            await panel.applyRunConfig(config);
            lastAppliedRunBody = body;
        } catch (error) {
            console.error(error);
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
                onOpen: () => setCompareRoute(true),
                onClose: () => setCompareRoute(false),
            });
            await applyRunFromHashIfPresent();
        } finally {
            loading = false;
            toggle.disabled = false;
        }
    }

    function onHashChange(): void {
        if (disposed) {
            return;
        }
        if (hashHasCompareRoute(window.location.hash)) {
            void loadAndOpen();
            return;
        }
        panel?.close();
    }

    // Kept (not {once}) so a failed first lazy load can be retried and later
    // clicks reopen the workspace through the same route-aware path.
    toggle.addEventListener("click", () => void loadAndOpen());
    window.addEventListener("hashchange", onHashChange);
    onHashChange();

    return {
        dispose(): void {
            disposed = true;
            window.removeEventListener("hashchange", onHashChange);
            panel?.dispose();
            panel = null;
            toggle.remove();
        },
    };
}
