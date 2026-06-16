/**
 * The presentational shell for the compare panel. It owns the floating toggle,
 * the backdrop/dialog chrome, focus handling, and dismissal, and delegates all
 * of the actual panel UI and behaviour to `createComparePanelContent`.
 *
 * Two presentations share this shell: the default centred `modal`, and the
 * full-page `workspace` (used by the `#/compare` route) which fills the viewport
 * and offers a "Back to build" affordance instead of a corner close button.
 */

import type { AppBootstrapData, PatternPayload } from "../types/domain.js";
import type { SimulationBackend } from "../types/controller.js";
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
    /**
     * Pre-existing toggle button to bind to (used by the lazy launcher so the
     * toggle can render before this module loads). When omitted the panel
     * creates and appends its own toggle.
     */
    trigger?: HTMLButtonElement;
    /** Open the dialog immediately after mounting (e.g. right after a lazy load). */
    openOnMount?: boolean;
    /** Fired when the dialog becomes visible (used to mirror the route into the hash). */
    onOpen?: () => void;
    /** Fired when the dialog is dismissed (used to clear the route from the hash). */
    onClose?: () => void;
    /** "modal" (default) centres a card; "workspace" fills the viewport as a page. */
    presentation?: "modal" | "workspace";
}

export interface ComparePanelHandle {
    open(): void;
    close(): void;
    isOpen(): boolean;
    applyRunConfig(config: CompareRunConfig): Promise<void>;
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
    const isWorkspace = options.presentation === "workspace";
    let lastFocus: HTMLElement | null = null;

    const ownsToggle = options.trigger === undefined;
    const toggleButton =
        options.trigger ??
        el(
            "button",
            { class: "compare-toggle", type: "button", title: "Compare a seed across tilings" },
            ["⊞ Compare tilings"],
        );

    const content: ComparePanelContentHandle = createComparePanelContent({
        backend: options.backend,
        bootstrapData: options.bootstrapData,
        ...(options.onOpenPattern ? { onOpenPattern: options.onOpenPattern } : {}),
        onRequestClose: () => close(),
    });

    const closeButton = isWorkspace
        ? el("button", { class: "compare-close compare-back", type: "button" }, ["← Back to build"])
        : el("button", { class: "compare-close", type: "button", "aria-label": "Close" }, ["×"]);

    const dialog = el(
        "div",
        {
            class: isWorkspace ? "compare-dialog compare-dialog--workspace" : "compare-dialog",
            role: "dialog",
            "aria-modal": isWorkspace ? null : "true",
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
            class: isWorkspace
                ? "compare-backdrop compare-backdrop--workspace"
                : "compare-backdrop",
            hidden: true,
        },
        [dialog],
    );

    if (ownsToggle) {
        host.append(toggleButton, backdrop);
    } else {
        host.append(backdrop);
    }

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
        if (event.key === "Escape" && !backdrop.hidden) {
            // Let an open action menu swallow Escape first; only close the dialog
            // when no menu consumed it.
            if (content.handleEscape()) {
                return;
            }
            close();
        }
    }

    toggleButton.addEventListener("click", open);
    closeButton.addEventListener("click", close);
    // The full-page workspace has no "outside" to click; only the modal dismisses
    // on a backdrop click.
    if (!isWorkspace) {
        backdrop.addEventListener("click", (event) => {
            if (event.target === backdrop) {
                close();
            }
        });
    }
    document.addEventListener("keydown", onKeydown);

    if (options.openOnMount) {
        open();
    }

    return {
        open,
        close,
        isOpen: () => !backdrop.hidden,
        applyRunConfig: (config) => content.applyRunConfig(config),
        reportRunLinkError: (message) => content.reportRunLinkError(message),
        dispose(): void {
            document.removeEventListener("keydown", onKeydown);
            content.dispose();
            if (ownsToggle) {
                toggleButton.remove();
            }
            backdrop.remove();
        },
    };
}
