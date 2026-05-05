import { describe, expect, it, vi } from "vitest";

import { bindTilingPreviewPicker } from "./tiling-picker-bindings.js";
import type { AppActionSet } from "../types/actions.js";
import type { DomElements } from "../types/dom.js";

type PickerActions = Pick<AppActionSet, "changeTilingFamily">;

function createElements(): DomElements {
    const select = document.createElement("select");
    select.append(new Option("Square", "square"), new Option("Hexagonal", "hex"));

    const menu = document.createElement("div");
    menu.hidden = true;
    const squareButton = document.createElement("button");
    squareButton.type = "button";
    squareButton.className = "tiling-preview-card is-selected";
    squareButton.dataset.tilingFamily = "square";
    squareButton.textContent = "Square";

    const hexButton = document.createElement("button");
    hexButton.type = "button";
    hexButton.className = "tiling-preview-card";
    hexButton.dataset.tilingFamily = "hex";
    hexButton.textContent = "Hexagonal";
    menu.append(squareButton, hexButton);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.setAttribute("aria-expanded", "false");

    document.body.replaceChildren(toggle, menu);
    const elements: Partial<DomElements> = {
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
    it("opens the preview picker and applies a card selection", () => {
        const elements = createElements();
        const changeTilingFamily = vi.fn();

        bindTilingPreviewPicker(elements, createActions(changeTilingFamily));
        elements.tilingPickerToggle?.click();

        expect(elements.tilingPickerMenu?.hidden).toBe(false);
        expect(elements.tilingPickerToggle?.getAttribute("aria-expanded")).toBe("true");

        elements.tilingPickerMenu?.querySelector<HTMLButtonElement>("[data-tiling-family='hex']")?.click();

        expect(elements.tilingFamilySelect?.value).toBe("hex");
        expect(elements.tilingPickerMenu?.hidden).toBe(true);
        expect(elements.tilingPickerToggle?.getAttribute("aria-expanded")).toBe("false");
        expect(changeTilingFamily).toHaveBeenCalledWith("hex");
    });

    it("closes the preview picker on Escape", () => {
        const elements = createElements();

        bindTilingPreviewPicker(elements, createActions(vi.fn()));
        elements.tilingPickerToggle?.click();
        elements.tilingPickerMenu?.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));

        expect(elements.tilingPickerMenu?.hidden).toBe(true);
        expect(elements.tilingPickerToggle?.getAttribute("aria-expanded")).toBe("false");
    });
});
