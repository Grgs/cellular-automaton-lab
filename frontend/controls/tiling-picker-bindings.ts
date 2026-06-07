import { matchSorter, rankings } from "match-sorter";

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
    const selectedCard = tilingCards(menu).find((card) => card.classList.contains("is-selected"));
    const fallbackCard = tilingCards(menu)[0];
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

function focusTilingPickerSearch(menu: HTMLElement): boolean {
    const search = tilingPickerSearchInput(menu);
    if (!search) {
        return false;
    }
    search.focus({ preventScroll: true });
    return true;
}

function tilingCards(menu: HTMLElement): HTMLButtonElement[] {
    return Array.from(menu.querySelectorAll<HTMLButtonElement>(".tiling-preview-card")).filter(
        (card) => !card.hidden,
    );
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

function tilingPickerSearchInput(menu: HTMLElement): HTMLInputElement | null {
    return menu.querySelector<HTMLInputElement>(".tiling-picker-search");
}

function tilingSearchQueryForms(value: string): string[] {
    const normalized = value
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/&/g, " and ")
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
    if (!normalized) {
        return [];
    }
    const compact = normalized.replace(/\s+/g, "");
    return compact !== normalized && compact.length <= 5 ? [normalized, compact] : [normalized];
}

function filterTilingPreviewCards(menu: HTMLElement, rawQuery: string): void {
    const queries = tilingSearchQueryForms(rawQuery);
    const cards = Array.from(menu.querySelectorAll<HTMLButtonElement>(".tiling-preview-card"));
    const matchedCards = new Set(
        queries.length === 0
            ? cards
            : queries.flatMap((query) =>
                  matchSorter(cards, query, {
                      keys: [(card) => card.dataset.searchText ?? ""],
                      threshold: rankings.CONTAINS,
                  }),
              ),
    );
    let hasMatches = false;
    menu.querySelectorAll<HTMLElement>(".tiling-preview-group").forEach((group) => {
        let groupHasMatches = false;
        group.querySelectorAll<HTMLButtonElement>(".tiling-preview-card").forEach((card) => {
            const matches = matchedCards.has(card);
            card.hidden = !matches;
            groupHasMatches ||= matches;
        });
        group.hidden = !groupHasMatches;
        hasMatches ||= groupHasMatches;
    });
    const empty = menu.querySelector<HTMLElement>(".tiling-picker-empty");
    if (empty) {
        empty.hidden = hasMatches;
    }
}

function resetTilingPreviewFilter(menu: HTMLElement): void {
    const search = tilingPickerSearchInput(menu);
    if (search) {
        search.value = "";
    }
    filterTilingPreviewCards(menu, "");
}

export function bindTilingPreviewPicker(
    elements: DomElements,
    actions: Pick<AppActionSet, "changeTilingFamily">,
): void {
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
        resetTilingPreviewFilter(menu);
        setTilingPickerOpen(elements, true);
        if (!focusTilingPickerSearch(menu)) {
            focusSelectedTilingCard(menu);
        }
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
        const closeButton =
            event.target instanceof Element
                ? event.target.closest<HTMLButtonElement>(".tiling-picker-close")
                : null;
        if (closeButton) {
            close({ restoreFocus: true });
            return;
        }
        const target =
            event.target instanceof Element
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
        if (event.target === tilingPickerSearchInput(menu)) {
            if (event.key === "Escape") {
                event.preventDefault();
                close({ restoreFocus: true });
                return;
            }
            if (event.key === "ArrowDown") {
                event.preventDefault();
                focusEdgeTilingCard(menu, "first");
            }
            return;
        }
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

    menu.addEventListener("input", (event) => {
        if (!(event.target instanceof HTMLInputElement)) {
            return;
        }
        if (!event.target.classList.contains("tiling-picker-search")) {
            return;
        }
        filterTilingPreviewCards(menu, event.target.value);
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
