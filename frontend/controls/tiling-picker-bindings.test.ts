import { afterEach, describe, expect, it, vi } from "vitest";

import { bindTilingPreviewPicker } from "./tiling-picker-bindings.js";
import type { AppActionSet } from "../types/actions.js";
import type { DomElements } from "../types/dom.js";

type PickerActions = Pick<AppActionSet, "changeTilingFamily">;

function createElements(): DomElements {
    const select = document.createElement("select");
    select.append(
        new Option("Square", "square"),
        new Option("Hexagonal", "hex"),
        new Option("Square-Octagon", "archimedean-4-8-8"),
        new Option("Cairo Pentagonal", "cairo-pentagonal"),
        new Option("Chair", "chair"),
    );

    const menu = document.createElement("div");
    menu.hidden = true;
    const search = document.createElement("input");
    search.type = "search";
    search.className = "tiling-picker-search";
    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.className = "tiling-picker-close";

    const regularGroup = document.createElement("section");
    regularGroup.className = "tiling-preview-group";
    const squareButton = document.createElement("button");
    squareButton.type = "button";
    squareButton.className = "tiling-preview-card is-selected";
    squareButton.dataset.tilingFamily = "square";
    squareButton.dataset.searchText = "square regular grid";
    squareButton.textContent = "Square";
    regularGroup.append(squareButton);

    const mixedGroup = document.createElement("section");
    mixedGroup.className = "tiling-preview-group";
    const hexButton = document.createElement("button");
    hexButton.type = "button";
    hexButton.className = "tiling-preview-card";
    hexButton.dataset.tilingFamily = "hex";
    hexButton.dataset.searchText = "hexagonal regular grid honeycomb hexagon hexagons";
    hexButton.textContent = "Hexagonal";
    const squareOctagonButton = document.createElement("button");
    squareOctagonButton.type = "button";
    squareOctagonButton.className = "tiling-preview-card";
    squareOctagonButton.dataset.tilingFamily = "archimedean-4-8-8";
    squareOctagonButton.dataset.searchText =
        "square octagon squareoctagon archimedean 4 8 8 488 uniform";
    squareOctagonButton.textContent = "Square-Octagon";
    const cairoButton = document.createElement("button");
    cairoButton.type = "button";
    cairoButton.className = "tiling-preview-card";
    cairoButton.dataset.tilingFamily = "cairo-pentagonal";
    cairoButton.dataset.searchText = "cairo pentagonal pentagon pentagons";
    cairoButton.textContent = "Cairo Pentagonal";
    const chairButton = document.createElement("button");
    chairButton.type = "button";
    chairButton.className = "tiling-preview-card";
    chairButton.dataset.tilingFamily = "chair";
    chairButton.dataset.searchText = "chair l shape l shaped substitution";
    chairButton.textContent = "Chair";
    mixedGroup.append(hexButton, squareOctagonButton, cairoButton, chairButton);

    const empty = document.createElement("div");
    empty.className = "tiling-picker-empty";
    empty.hidden = true;
    empty.textContent = "No tilings match this search.";
    menu.append(closeButton, search, regularGroup, mixedGroup, empty);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.setAttribute("aria-expanded", "false");

    const topBar = document.createElement("header");
    topBar.append(toggle, menu);
    document.body.replaceChildren(topBar);
    const elements: Partial<DomElements> = {
        topBar,
        tilingFamilySelect: select,
        tilingPickerMenu: menu,
        tilingPickerToggle: toggle,
    };
    return elements as DomElements;
}

function createActions(changeTilingFamily: PickerActions["changeTilingFamily"]): PickerActions {
    return { changeTilingFamily };
}

describe("controls/tiling-picker-bindings", () => {
    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("opens the preview picker and applies a card selection", () => {
        const elements = createElements();
        const changeTilingFamily = vi.fn();

        bindTilingPreviewPicker(elements, createActions(changeTilingFamily));
        elements.tilingPickerToggle?.click();

        expect(elements.tilingPickerMenu?.hidden).toBe(false);
        expect(elements.tilingPickerToggle?.getAttribute("aria-expanded")).toBe("true");
        expect(elements.topBar?.classList.contains("is-tiling-picker-open")).toBe(true);

        elements.tilingPickerMenu
            ?.querySelector<HTMLButtonElement>("[data-tiling-family='hex']")
            ?.click();

        expect(elements.tilingFamilySelect?.value).toBe("hex");
        expect(elements.tilingPickerMenu?.hidden).toBe(true);
        expect(elements.tilingPickerToggle?.getAttribute("aria-expanded")).toBe("false");
        expect(elements.topBar?.classList.contains("is-tiling-picker-open")).toBe(false);
        expect(changeTilingFamily).toHaveBeenCalledWith("hex");
    });

    it("does not open the mobile keyboard when the compact picker opens", () => {
        vi.stubGlobal("matchMedia", (query: string) => ({
            matches: query === "(max-width: 860px)",
        }));
        vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
            callback(0);
            return 1;
        });
        const elements = createElements();

        bindTilingPreviewPicker(elements, createActions(vi.fn()));
        elements.tilingPickerToggle?.click();

        expect(document.activeElement).toBe(
            elements.tilingPickerMenu?.querySelector("[data-tiling-family='square']"),
        );
        expect(document.activeElement).not.toBe(
            elements.tilingPickerMenu?.querySelector(".tiling-picker-search"),
        );
    });

    it("closes the preview picker on Escape", () => {
        const elements = createElements();

        bindTilingPreviewPicker(elements, createActions(vi.fn()));
        elements.tilingPickerToggle?.click();
        elements.tilingPickerMenu?.dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
        );

        expect(elements.tilingPickerMenu?.hidden).toBe(true);
        expect(elements.tilingPickerToggle?.getAttribute("aria-expanded")).toBe("false");
    });

    it("closes the preview picker from the menu close button", () => {
        const elements = createElements();
        const changeTilingFamily = vi.fn();

        bindTilingPreviewPicker(elements, createActions(changeTilingFamily));
        elements.tilingPickerToggle?.click();
        elements.tilingPickerMenu
            ?.querySelector<HTMLButtonElement>(".tiling-picker-close")
            ?.click();

        expect(elements.tilingPickerMenu?.hidden).toBe(true);
        expect(elements.tilingPickerToggle?.getAttribute("aria-expanded")).toBe("false");
        expect(elements.tilingFamilySelect?.value).toBe("square");
        expect(changeTilingFamily).not.toHaveBeenCalled();
    });

    it("filters preview cards without selecting a hidden tiling", () => {
        const elements = createElements();
        const changeTilingFamily = vi.fn();

        bindTilingPreviewPicker(elements, createActions(changeTilingFamily));
        elements.tilingPickerToggle?.click();

        const search =
            elements.tilingPickerMenu?.querySelector<HTMLInputElement>(".tiling-picker-search");
        search!.value = "hex";
        search!.dispatchEvent(new Event("input", { bubbles: true }));

        const square = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='square']",
        );
        const hex = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='hex']",
        );
        const squareOctagon = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='archimedean-4-8-8']",
        );
        const cairo = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='cairo-pentagonal']",
        );
        const chair = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='chair']",
        );
        expect(square?.hidden).toBe(true);
        expect(hex?.hidden).toBe(false);
        expect(squareOctagon?.hidden).toBe(true);
        expect(cairo?.hidden).toBe(true);
        expect(chair?.hidden).toBe(true);
        expect(
            elements.tilingPickerMenu?.querySelector<HTMLElement>(".tiling-picker-empty")?.hidden,
        ).toBe(true);
        expect(elements.tilingFamilySelect?.value).toBe("square");
        expect(changeTilingFamily).not.toHaveBeenCalled();

        search!.value = "nope";
        search!.dispatchEvent(new Event("input", { bubbles: true }));
        expect(hex?.hidden).toBe(true);
        expect(
            elements.tilingPickerMenu?.querySelector<HTMLElement>(".tiling-picker-empty")?.hidden,
        ).toBe(false);
    });

    it("matches alias and punctuation-normalized tiling searches", () => {
        const elements = createElements();

        bindTilingPreviewPicker(elements, createActions(vi.fn()));
        elements.tilingPickerToggle?.click();

        const search =
            elements.tilingPickerMenu?.querySelector<HTMLInputElement>(".tiling-picker-search");
        const square = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='square']",
        );
        const hex = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='hex']",
        );
        const squareOctagon = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='archimedean-4-8-8']",
        );
        const cairo = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='cairo-pentagonal']",
        );
        const chair = elements.tilingPickerMenu?.querySelector<HTMLButtonElement>(
            "[data-tiling-family='chair']",
        );

        search!.value = "honeycomb";
        search!.dispatchEvent(new Event("input", { bubbles: true }));
        expect(square?.hidden).toBe(true);
        expect(hex?.hidden).toBe(false);
        expect(squareOctagon?.hidden).toBe(true);
        expect(cairo?.hidden).toBe(true);
        expect(chair?.hidden).toBe(true);

        search!.value = "4.8.8";
        search!.dispatchEvent(new Event("input", { bubbles: true }));
        expect(square?.hidden).toBe(true);
        expect(hex?.hidden).toBe(true);
        expect(squareOctagon?.hidden).toBe(false);

        search!.value = "488";
        search!.dispatchEvent(new Event("input", { bubbles: true }));
        expect(squareOctagon?.hidden).toBe(false);

        search!.value = "cairo";
        search!.dispatchEvent(new Event("input", { bubbles: true }));
        expect(square?.hidden).toBe(true);
        expect(hex?.hidden).toBe(true);
        expect(squareOctagon?.hidden).toBe(true);
        expect(cairo?.hidden).toBe(false);
        expect(chair?.hidden).toBe(true);
    });
});
