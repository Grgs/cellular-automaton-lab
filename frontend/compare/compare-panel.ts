/**
 * The modal presentation of the compare panel. This is a thin shell: it owns the
 * floating toggle, the backdrop/dialog chrome, focus handling, and Escape/
 * backdrop dismissal, and delegates all of the actual panel UI and behaviour to
 * `createComparePanelContent`. A future workspace route can reuse that same
 * content element full-page without any of this modal scaffolding.
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
    /** Modal keeps legacy overlay behavior; workspace fills the viewport behind the hash route. */
    presentation?: "modal" | "workspace";
    onOpen?: () => void;
    onClose?: () => void;
}

export interface ComparePanelHandle {
    open(): void;
    close(): void;
    isOpen(): boolean;
    applyRunConfig(config: CompareRunConfig): Promise<void>;
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
    const workspace = options.presentation === "workspace";
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

    const closeButton = workspace
        ? el("button", { class: "compare-close compare-back", type: "button" }, ["← Back to build"])
        : el("button", { class: "compare-close", type: "button", "aria-label": "Close" }, ["×"]);

    const dialog = el(
        "div",
        {
            class: workspace ? "compare-dialog compare-dialog--workspace" : "compare-dialog",
            role: "dialog",
            "aria-modal": workspace ? null : "true",
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
            class: workspace ? "compare-backdrop compare-backdrop--workspace" : "compare-backdrop",
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
    if (!workspace) {
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
