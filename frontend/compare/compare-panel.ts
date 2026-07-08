/**
 * The presentational surface for the comparison wall. It fills the shared
 * shell's content slot (the static header and its route switcher
 * belong to the shell, not to this module) and delegates all of the actual
 * panel UI and behaviour to `createComparePanelContent`. The workspace router
 * shows and hides it; this surface renders no trigger of its own.
 *
 * The wall is the page, not a dialog. Escape peels back one in-page layer (an
 * open menu, then the config sheet, then speaker view) but never leaves the
 * wall; Space and the arrow keys drive the docked filmstrip transport.
 */

import type { AppBootstrapData, PatternPayload } from "../types/domain.js";
import type { SimulationBackend } from "../types/controller.js";
import type { FocusPaneServices } from "../pane/pane-core.js";
import type { CompareRunConfig } from "./compare-run-link.js";
import {
    createComparePanelContent,
    ensureComparePanelStyles,
    type ComparePanelContentHandle,
} from "./compare-panel-content.js";

interface MountComparePanelOptions {
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    host?: HTMLElement;
    /** When provided, begin/end open into the current board instead of a new tab. */
    onOpenPattern?: (pattern: PatternPayload) => void;
    /** Show the wall immediately after mounting (e.g. right after a lazy load). */
    openOnMount?: boolean;
    /** Fired when the wall becomes visible (used to mirror the route into the hash). */
    onOpen?: () => void;
    /** Fired when the wall is hidden (used to clear the route from the hash). */
    onClose?: () => void;
    /** Server-only seams for the live focus pane (absent on the standalone build). */
    focusPaneServices?: FocusPaneServices;
    /** The Lab rule active when the wall is opened; used for the default wall setup. */
    getInitialRuleName?: () => string | null | undefined;
}

export interface ComparePanelHandle {
    open(): void;
    close(): void;
    isOpen(): boolean;
    applyRunConfig(config: CompareRunConfig): Promise<void>;
    runFeaturedDemo(config: CompareRunConfig): Promise<void>;
    runDefaultFilmstrip(config: CompareRunConfig): Promise<void>;
    reportRunLinkError(message: string): void;
    dispose(): void;
}

type ElementAttrs = Record<string, string | number | boolean | null | undefined>;

function el<K extends keyof HTMLElementTagNameMap>(
    tag: K,
    attrs: ElementAttrs = {},
    children: Array<Node | string> = [],
): HTMLElementTagNameMap[K] {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
        if (value === undefined || value === null || value === false) {
            continue;
        }
        if (key === "textContent" || key === "text") {
            node.textContent = String(value);
            continue;
        }
        node.setAttribute(key, value === true ? "" : String(value));
    }
    for (const child of children) {
        node.append(typeof child === "string" ? document.createTextNode(child) : child);
    }
    return node;
}

export function mountComparePanel(options: MountComparePanelOptions): ComparePanelHandle {
    ensureComparePanelStyles();
    const host = options.host ?? document.body;
    let lastFocus: HTMLElement | null = null;

    const content: ComparePanelContentHandle = createComparePanelContent({
        backend: options.backend,
        bootstrapData: options.bootstrapData,
        ...(options.onOpenPattern ? { onOpenPattern: options.onOpenPattern } : {}),
        ...(options.focusPaneServices ? { focusPaneServices: options.focusPaneServices } : {}),
        ...(options.getInitialRuleName ? { getInitialRuleName: options.getInitialRuleName } : {}),
        onRequestClose: () => close(),
    });

    const wallPage = el(
        "div",
        {
            class: "wall-page",
            role: "region",
            "aria-label": "Comparison wall",
            tabindex: "-1",
            hidden: true,
        },
        [content.element],
    );

    host.append(wallPage);

    function open(): void {
        if (!wallPage.hidden) {
            return;
        }
        lastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        wallPage.hidden = false;
        content.activate();
        wallPage.focus();
        options.onOpen?.();
    }

    function close(): void {
        if (wallPage.hidden) {
            return;
        }
        content.deactivate();
        wallPage.hidden = true;
        lastFocus?.focus();
        options.onClose?.();
    }

    function onKeydown(event: KeyboardEvent): void {
        if (wallPage.hidden) {
            return;
        }
        if (event.key === "Escape") {
            // Escape peels back one in-page layer at a time: an open action menu,
            // then the config sheet, then speaker view (back to the gallery). It
            // never leaves the wall -- the shell header's Lab route tab is
            // the only exit.
            if (content.handleEscape()) {
                return;
            }
            if (content.closeConfigIfOpen()) {
                return;
            }
            content.exitFocusIfAny();
            return;
        }
        // Space/arrows drive the docked transport once a filmstrip is live.
        if (content.handlePlaybackKey(event)) {
            event.preventDefault();
        }
    }

    document.addEventListener("keydown", onKeydown);

    if (options.openOnMount) {
        open();
    }

    return {
        open,
        close,
        isOpen: () => !wallPage.hidden,
        applyRunConfig: (config) => content.applyRunConfig(config),
        runFeaturedDemo: (config) => content.runFeaturedDemo(config),
        runDefaultFilmstrip: (config) => content.runDefaultFilmstrip(config),
        reportRunLinkError: (message) => content.reportRunLinkError(message),
        dispose(): void {
            document.removeEventListener("keydown", onKeydown);
            content.dispose();
            wallPage.remove();
        },
    };
}
