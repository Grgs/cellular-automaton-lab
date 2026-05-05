import type { DomElements } from "../types/dom.js";
import type { LabeledOption, PaintPaletteState } from "../types/ui.js";
import type { ThemeName } from "../theme.js";

export function renderToggleButtons<TValue extends string | number>(
    container: HTMLElement | null,
    options: readonly LabeledOption<TValue>[],
    selectedValue: TValue | string | number | null | undefined,
    dataAttribute: string,
    className: string,
): void {
    if (!container) {
        return;
    }

    container.innerHTML = "";
    options.forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = className;
        if (String(option.value) === String(selectedValue)) {
            button.classList.add("is-selected");
        }
        button.dataset[dataAttribute] = String(option.value);
        button.setAttribute(
            "aria-pressed",
            String(option.value) === String(selectedValue) ? "true" : "false",
        );
        button.textContent = option.label;
        container.appendChild(button);
    });
}

export function renderPaintPalette(
    elements: DomElements,
    paletteStates: readonly PaintPaletteState[],
    selectedPaintState: number | null,
): void {
    if (!elements.paintPalette) {
        return;
    }

    elements.paintPalette.innerHTML = "";
    paletteStates.forEach((cellState) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "paint-state-button";
        if (cellState.value === selectedPaintState) {
            button.classList.add("is-selected");
        }
        button.dataset.stateValue = String(cellState.value);
        button.setAttribute(
            "aria-pressed",
            cellState.value === selectedPaintState ? "true" : "false",
        );

        const swatch = document.createElement("span");
        swatch.className = "paint-state-swatch";
        swatch.style.backgroundColor = cellState.color;

        const label = document.createElement("span");
        label.className = "paint-state-label";
        label.textContent = cellState.label;

        button.appendChild(swatch);
        button.appendChild(label);
        elements.paintPalette?.appendChild(button);
    });
}

export function renderRangeControl({
    field,
    input,
    label,
    visible,
    value,
    min,
    max,
    labelText,
}: {
    field: HTMLElement | null;
    input: HTMLInputElement | null;
    label: HTMLElement | null;
    visible: boolean;
    value: string;
    min: string;
    max: string;
    labelText: string;
}): void {
    if (!visible) {
        if (field) {
            field.classList.remove("has-limit-cue");
            delete field.dataset.limitCueText;
            const cue = field.querySelector(".top-control-limit-cue") as HTMLElement | null;
            if (cue) {
                cue.hidden = true;
                cue.textContent = "";
            }
        }
        if (input) {
            input.classList.remove("is-limit-cue");
            input.removeAttribute("aria-invalid");
        }
        if (label) {
            label.classList.remove("is-limit-cue");
        }
    }
    if (field) {
        field.hidden = !visible;
    }
    if (input) {
        input.value = value;
        input.min = min;
        input.max = max;
        input.hidden = !visible;
        input.disabled = !visible;
    }
    if (label) {
        label.classList.remove("is-limit-cue");
        label.textContent = labelText;
        label.hidden = !visible;
    }
}

export function renderThemeToggle(elements: DomElements, theme: ThemeName): void {
    if (!elements.themeToggleBtn) {
        return;
    }

    const isDark = theme === "dark";
    elements.themeToggleBtn.dataset.theme = theme;
    elements.themeToggleBtn.setAttribute("aria-pressed", isDark ? "true" : "false");

    const label = isDark ? "Switch to light mode" : "Switch to dark mode";
    elements.themeToggleBtn.setAttribute("aria-label", label);
    elements.themeToggleBtn.title = label;
}
