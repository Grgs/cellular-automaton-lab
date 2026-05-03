import type { AppActionSet } from "../types/actions.js";
import type { DomElements } from "../types/dom.js";

function setTilingPickerOpen(elements: DomElements, open: boolean): void {
    if (elements.tilingPickerMenu) {
        elements.tilingPickerMenu.hidden = !open;
    }
    if (elements.tilingPickerToggle) {
        elements.tilingPickerToggle.setAttribute("aria-expanded", open ? "true" : "false");
    }
}

function focusSelectedTilingCard(menu: HTMLElement): void {
    const selectedCard = menu.querySelector<HTMLButtonElement>(".tiling-preview-card.is-selected");
    const fallbackCard = menu.querySelector<HTMLButtonElement>(".tiling-preview-card");
    const target = selectedCard ?? fallbackCard;
    if (!target) {
        return;
    }
    window.requestAnimationFrame(() => {
        target.focus({ preventScroll: true });
        if (typeof target.scrollIntoView === "function") {
            target.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
    });
}

function tilingCards(menu: HTMLElement): HTMLButtonElement[] {
    return Array.from(menu.querySelectorAll<HTMLButtonElement>(".tiling-preview-card"));
}

function focusRelativeTilingCard(menu: HTMLElement, offset: number): void {
    const cards = tilingCards(menu);
    if (cards.length === 0) {
        return;
    }
    const activeIndex = Math.max(0, cards.indexOf(document.activeElement as HTMLButtonElement));
    const nextIndex = (activeIndex + offset + cards.length) % cards.length;
    cards[nextIndex]?.focus();
}

function focusEdgeTilingCard(menu: HTMLElement, edge: "first" | "last"): void {
    const cards = tilingCards(menu);
    const target = edge === "first" ? cards[0] : cards[cards.length - 1];
    target?.focus();
}

export function bindTilingPreviewPicker(elements: DomElements, actions: Pick<AppActionSet, "changeTilingFamily">): void {
    const menu = elements.tilingPickerMenu;
    const toggle = elements.tilingPickerToggle;
    if (!menu || !toggle) {
        return;
    }

    const close = ({ restoreFocus = false }: { restoreFocus?: boolean } = {}) => {
        setTilingPickerOpen(elements, false);
        if (restoreFocus) {
            toggle.focus();
        }
    };

    const open = () => {
        setTilingPickerOpen(elements, true);
        focusSelectedTilingCard(menu);
    };

    toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        if (menu.hidden) {
            open();
            return;
        }
        close();
    });

    menu.addEventListener("click", (event) => {
        const target = event.target instanceof Element
            ? event.target.closest<HTMLButtonElement>(".tiling-preview-card")
            : null;
        const tilingFamily = target?.dataset.tilingFamily ?? "";
        if (!tilingFamily) {
            return;
        }
        if (elements.tilingFamilySelect) {
            elements.tilingFamilySelect.value = tilingFamily;
        }
        close({ restoreFocus: true });
        void actions.changeTilingFamily(tilingFamily);
    });

    menu.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            event.preventDefault();
            close({ restoreFocus: true });
            return;
        }
        if (event.key === "ArrowRight" || event.key === "ArrowDown") {
            event.preventDefault();
            focusRelativeTilingCard(menu, 1);
            return;
        }
        if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
            event.preventDefault();
            focusRelativeTilingCard(menu, -1);
            return;
        }
        if (event.key === "Home") {
            event.preventDefault();
            focusEdgeTilingCard(menu, "first");
            return;
        }
        if (event.key === "End") {
            event.preventDefault();
            focusEdgeTilingCard(menu, "last");
        }
    });

    elements.tilingFamilySelect?.addEventListener("change", () => {
        close();
    });

    document.addEventListener("pointerdown", (event) => {
        if (menu.hidden || !(event.target instanceof Node)) {
            return;
        }
        if (menu.contains(event.target) || toggle.contains(event.target)) {
            return;
        }
        close();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !menu.hidden) {
            close({ restoreFocus: true });
        }
    });
}
