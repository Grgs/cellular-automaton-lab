import type { AdjacencyModeOption, PresetMetadata, TopologyOption } from "../types/domain.js";
import type { DomElements } from "../types/dom.js";
import type { RuleSelectOption } from "../types/ui.js";
import { createTilingPreviewThumbnail } from "./tiling-preview.js";

function populateOptions<
    TOption extends object,
    TValueKey extends keyof TOption,
    TLabelKey extends keyof TOption,
>(
    selectElement: HTMLSelectElement | null,
    options: readonly TOption[],
    valueKey: TValueKey,
    labelKey: TLabelKey,
    selectedValue = "",
): void {
    if (!selectElement) {
        return;
    }
    selectElement.innerHTML = "";
    options.forEach((optionData) => {
        const optionElement = document.createElement("option");
        optionElement.value = String(optionData[valueKey] ?? "");
        optionElement.textContent = String(optionData[labelKey] ?? "");
        if (optionElement.value === selectedValue) {
            optionElement.selected = true;
        }
        selectElement.appendChild(optionElement);
    });
}

export function populateRules(
    elements: DomElements,
    rules: readonly RuleSelectOption[],
    selectedValue = "",
): void {
    populateOptions(elements.ruleSelect, rules, "name", "displayName", selectedValue);
}

export function populateTilingFamilies(
    elements: DomElements,
    families: readonly TopologyOption[],
    selectedValue = "",
): void {
    if (!elements.tilingFamilySelect) {
        return;
    }
    const selectElement = elements.tilingFamilySelect;
    selectElement.innerHTML = "";

    const groups = new Map<string, TopologyOption[]>();
    families.forEach((family) => {
        const groupName = family.group || "Other";
        if (!groups.has(groupName)) {
            groups.set(groupName, []);
        }
        const group = groups.get(groupName);
        if (group) {
            group.push(family);
        }
    });

    groups.forEach((options, groupName) => {
        const optgroup = document.createElement("optgroup");
        optgroup.label = groupName;
        options.forEach((optionData) => {
            const optionElement = document.createElement("option");
            optionElement.value = optionData.value;
            optionElement.textContent = optionData.label;
            if (optionElement.value === selectedValue) {
                optionElement.selected = true;
            }
            optgroup.appendChild(optionElement);
        });
        selectElement.appendChild(optgroup);
    });
    populateTilingPreviewPicker(elements, families, selectedValue);
}

function tilingOptionsSignature(families: readonly TopologyOption[]): string {
    return families
        .map((family) =>
            [
                family.group,
                family.value,
                family.label,
                family.previewKey,
                family.renderKind,
                family.sizingMode,
            ].join(":"),
        )
        .join("|");
}

function buildTilingPreviewCard(optionData: TopologyOption): HTMLButtonElement {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "tiling-preview-card";
    button.dataset.tilingFamily = optionData.value;
    button.setAttribute("aria-pressed", "false");

    const thumbnail = document.createElement("span");
    thumbnail.className = "tiling-preview-card-thumb";
    thumbnail.setAttribute("aria-hidden", "true");
    thumbnail.appendChild(createTilingPreviewThumbnail(optionData));

    const copy = document.createElement("span");
    copy.className = "tiling-preview-card-copy";

    const label = document.createElement("span");
    label.className = "tiling-preview-card-label";
    label.textContent = optionData.label;

    const meta = document.createElement("span");
    meta.className = "tiling-preview-card-meta";
    meta.textContent = optionData.sizingMode === "patch_depth" ? "Patch" : "Grid";

    copy.append(label, meta);
    button.append(thumbnail, copy);
    return button;
}

function populateTilingPreviewMenu(menu: HTMLElement, families: readonly TopologyOption[]): void {
    const groups = new Map<string, TopologyOption[]>();
    families.forEach((family) => {
        const groupName = family.group || "Other";
        if (!groups.has(groupName)) {
            groups.set(groupName, []);
        }
        groups.get(groupName)?.push(family);
    });

    const fragment = document.createDocumentFragment();
    groups.forEach((options, groupName) => {
        const group = document.createElement("section");
        group.className = "tiling-preview-group";

        const title = document.createElement("h2");
        title.className = "tiling-preview-group-title";
        title.textContent = groupName;

        const grid = document.createElement("div");
        grid.className = "tiling-preview-grid";
        options.forEach((optionData) => {
            grid.appendChild(buildTilingPreviewCard(optionData));
        });

        group.append(title, grid);
        fragment.appendChild(group);
    });
    menu.replaceChildren(fragment);
}

function syncTilingPreviewSelection(menu: HTMLElement, selectedValue: string): void {
    menu.querySelectorAll<HTMLButtonElement>(".tiling-preview-card").forEach((button) => {
        const selected = button.dataset.tilingFamily === selectedValue;
        button.classList.toggle("is-selected", selected);
        button.setAttribute("aria-pressed", selected ? "true" : "false");
        if (selected) {
            button.setAttribute("aria-current", "true");
            return;
        }
        button.removeAttribute("aria-current");
    });
}

function syncSelectedTilingPreview(
    previewElement: HTMLElement | null,
    labelElement: HTMLElement | null,
    families: readonly TopologyOption[],
    selectedValue: string,
): void {
    if (!previewElement && !labelElement) {
        return;
    }
    const selectedOption =
        families.find((family) => family.value === selectedValue) ?? families[0] ?? null;
    if (!selectedOption) {
        previewElement?.replaceChildren();
        if (previewElement) {
            previewElement.dataset.previewSignature = "";
        }
        if (labelElement) {
            labelElement.textContent = "";
        }
        return;
    }
    if (labelElement) {
        labelElement.textContent = selectedOption.label;
    }
    if (!previewElement) {
        return;
    }
    const signature = `${selectedOption.value}:${selectedOption.previewKey}`;
    if (previewElement.dataset.previewSignature === signature) {
        return;
    }
    previewElement.replaceChildren(
        createTilingPreviewThumbnail(selectedOption, "tiling-selected-preview-svg"),
    );
    previewElement.dataset.previewSignature = signature;
}

function populateTilingPreviewPicker(
    elements: DomElements,
    families: readonly TopologyOption[],
    selectedValue: string,
): void {
    const menu = elements.tilingPickerMenu;
    if (!menu) {
        syncSelectedTilingPreview(
            elements.tilingPickerCurrentPreview,
            elements.tilingPickerCurrentLabel,
            families,
            selectedValue,
        );
        return;
    }
    const signature = tilingOptionsSignature(families);
    if (menu.dataset.optionsSignature !== signature) {
        populateTilingPreviewMenu(menu, families);
        menu.dataset.optionsSignature = signature;
    }
    syncTilingPreviewSelection(menu, selectedValue);
    syncSelectedTilingPreview(
        elements.tilingPickerCurrentPreview,
        elements.tilingPickerCurrentLabel,
        families,
        selectedValue,
    );
}

export function populateAdjacencyModes(
    elements: DomElements,
    modes: readonly AdjacencyModeOption[],
    selectedValue = "",
): void {
    if (!elements.adjacencyModeSelect) {
        return;
    }
    populateOptions(elements.adjacencyModeSelect, modes, "value", "label", selectedValue);
}

export function populatePresetSeeds(
    elements: DomElements,
    presets: readonly PresetMetadata[],
    selectedValue = "",
): void {
    if (!elements.presetSeedSelect) {
        return;
    }
    populateOptions(elements.presetSeedSelect, presets, "id", "label", selectedValue);
}
