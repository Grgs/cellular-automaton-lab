/**
 * The presentational shell for the comparison wall. It owns the full-page
 * workspace chrome, focus handling, and dismissal, and delegates all of the
 * actual panel UI and behaviour to `createComparePanelContent`. The workspace
 * router opens and closes it; this shell renders no trigger of its own.
 *
 * The workspace fills the viewport and offers an "Open the Lab" affordance. It
 * has no "outside" to click, so it dismisses via that affordance or Escape;
 * Space and the arrow keys drive the docked filmstrip transport.
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
    /** Open the dialog immediately after mounting (e.g. right after a lazy load). */
    openOnMount?: boolean;
    /** Fired when the dialog becomes visible (used to mirror the route into the hash). */
    onOpen?: () => void;
    /** Fired when the dialog is dismissed (used to clear the route from the hash). */
    onClose?: () => void;
    /** Server-only seams for the live focus pane (absent on the standalone build). */
    focusPaneServices?: FocusPaneServices;
}

export interface ComparePanelHandle {
    open(): void;
    close(): void;
    isOpen(): boolean;
    applyRunConfig(config: CompareRunConfig): Promise<void>;
    runFeaturedDemo(config: CompareRunConfig): Promise<void>;
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
        onRequestClose: () => close(),
    });

    const closeButton = el(
        "button",
        {
            class: "compare-close compare-back",
            type: "button",
            title: "Open the single-board editor",
        },
        ["Open the Lab →"],
    );

    const dialog = el(
        "div",
        {
            class: "compare-dialog compare-dialog--workspace",
            role: "dialog",
            "aria-label": "Compare tilings",
            tabindex: "-1",
        },
        [
            el("div", { class: "compare-header" }, [
                el("h2", { class: "compare-title", textContent: "Compare seed across tilings" }),
                closeButton,
            ]),
            content.element,
        ],
    );

    const backdrop = el(
        "div",
        {
            class: "compare-backdrop compare-backdrop--workspace",
            hidden: true,
        },
        [dialog],
    );

    host.append(backdrop);

    function open(): void {
        if (!backdrop.hidden) {
            return;
        }
        lastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        backdrop.hidden = false;
        content.activate();
        dialog.focus();
        options.onOpen?.();
    }

    function close(): void {
        if (backdrop.hidden) {
            return;
        }
        backdrop.hidden = true;
        lastFocus?.focus();
        options.onClose?.();
    }

    function onKeydown(event: KeyboardEvent): void {
        if (backdrop.hidden) {
            return;
        }
        if (event.key === "Escape") {
            // Escape peels back one layer at a time: an open action menu first,
            // then speaker view (back to the gallery), then the dialog itself.
            if (content.handleEscape()) {
                return;
            }
            if (content.exitFocusIfAny()) {
                return;
            }
            close();
            return;
        }
        // Space/arrows drive the docked transport once a filmstrip is live.
        if (content.handlePlaybackKey(event)) {
            event.preventDefault();
        }
    }

    closeButton.addEventListener("click", close);
    // The full-page workspace has no "outside" to click, so a backdrop click is
    // not a dismissal; use the Lab affordance or Escape instead.
    document.addEventListener("keydown", onKeydown);

    if (options.openOnMount) {
        open();
    }

    return {
        open,
        close,
        isOpen: () => !backdrop.hidden,
        applyRunConfig: (config) => content.applyRunConfig(config),
        runFeaturedDemo: (config) => content.runFeaturedDemo(config),
        reportRunLinkError: (message) => content.reportRunLinkError(message),
        dispose(): void {
            document.removeEventListener("keydown", onKeydown);
            content.dispose();
            backdrop.remove();
        },
    };
}
