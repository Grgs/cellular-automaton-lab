import type {
    AdjacencyModeOption,
    PresetMetadata,
    TopologyOption,
} from "../types/domain.js";
import type { DomElements } from "../types/dom.js";
import type { RuleSelectOption } from "../types/ui.js";

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
