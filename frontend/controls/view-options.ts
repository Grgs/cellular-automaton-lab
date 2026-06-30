import { matchSorter, rankings } from "match-sorter";

import type { AdjacencyModeOption, PresetMetadata, TopologyOption } from "../types/domain.js";
import type { DomElements } from "../types/dom.js";
import type { RuleSelectOption } from "../types/ui.js";
import { tilingSearchText } from "./tiling-search.js";
import { createTilingPreviewThumbnail } from "./tiling-preview.js";

interface RuleSelectRenderState {
    rules: readonly RuleSelectOption[];
    selectedValue: string;
}

const RULE_SEARCH_EXAMPLES = "Try signal, circuit, excitable, wave, replicator, or B3/S23";
const ruleSelectState = new WeakMap<HTMLSelectElement, RuleSelectRenderState>();

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
    if (!elements.ruleSelect) {
        return;
    }
    ruleSelectState.set(elements.ruleSelect, { rules, selectedValue });
    renderRuleOptions(elements, rules, selectedValue);
}

export function refreshRuleFilter(elements: DomElements): void {
    const selectElement = elements.ruleSelect;
    if (!selectElement) {
        return;
    }
    const renderState = ruleSelectState.get(selectElement);
    if (!renderState) {
        return;
    }
    renderRuleOptions(elements, renderState.rules, renderState.selectedValue);
}

function normalizedRuleSearchText(value: string): string {
    return value
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/&/g, " and ")
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
}

function ruleSearchForms(value: string): string[] {
    const normalized = normalizedRuleSearchText(value);
    if (!normalized) {
        return [];
    }
    const compact = normalized.replace(/\s+/g, "");
    return compact === normalized ? [normalized] : [normalized, compact];
}

function ruleQueryForms(value: string): string[] {
    const forms = ruleSearchForms(value);
    const compact = forms[forms.length - 1] ?? "";
    if (/^b\d+s\d+$/.test(compact)) {
        return [compact];
    }
    return forms;
}

function ruleSearchText(rule: RuleSelectOption): string {
    return [
        rule.searchText || `${rule.displayName} ${rule.name}`,
        ...ruleSearchForms(rule.searchText || `${rule.displayName} ${rule.name}`),
    ].join(" ");
}

function rulesMatchingSearch(
    rules: readonly RuleSelectOption[],
    query: string,
): RuleSelectOption[] {
    const queries = ruleQueryForms(query);
    if (queries.length === 0) {
        return [...rules];
    }
    const tokenMatchedRules = rules.filter((rule) => {
        const searchableText = normalizedRuleSearchText(ruleSearchText(rule));
        return queries.some((ruleQuery) =>
            ruleQuery.split(/\s+/).every((token) => searchableText.includes(token)),
        );
    });
    const rankedRules = queries.flatMap((ruleQuery) =>
        matchSorter(tokenMatchedRules, ruleQuery, {
            keys: [ruleSearchText],
            threshold: rankings.CONTAINS,
        }),
    );
    return [...new Set([...rankedRules, ...tokenMatchedRules])];
}

function renderRuleOptions(
    elements: DomElements,
    rules: readonly RuleSelectOption[],
    selectedValue: string,
): void {
    const selectElement = elements.ruleSelect;
    if (!selectElement) {
        return;
    }

    const rawQuery = elements.ruleSearchInput?.value.trim() ?? "";
    const query = normalizedRuleSearchText(rawQuery);
    const matchingRules = rulesMatchingSearch(rules, query);
    const selectedRule = rules.find((rule) => rule.name === selectedValue) ?? null;
    const selectedRuleAlreadyVisible = Boolean(
        selectedRule && matchingRules.some((rule) => rule.name === selectedRule.name),
    );
    const visibleRules =
        selectedRule && query && !selectedRuleAlreadyVisible
            ? [selectedRule, ...matchingRules]
            : matchingRules;

    selectElement.innerHTML = "";
    if (visibleRules.length === 0) {
        const optionElement = document.createElement("option");
        optionElement.value = "";
        optionElement.textContent = "No rules match this search";
        optionElement.disabled = true;
        optionElement.selected = true;
        selectElement.appendChild(optionElement);
    } else {
        visibleRules.forEach((rule) => {
            const optionElement = document.createElement("option");
            optionElement.value = rule.name;
            optionElement.textContent = rule.displayName;
            optionElement.title = rule.description;
            optionElement.disabled = rule.disabled === true;
            if (optionElement.value === selectedValue) {
                optionElement.selected = true;
            }
            selectElement.appendChild(optionElement);
        });
    }

    if (!elements.ruleSearchStatus) {
        return;
    }
    if (!query) {
        elements.ruleSearchStatus.textContent = `${rules.length} rules available · ${RULE_SEARCH_EXAMPLES}`;
        return;
    }
    if (matchingRules.length === 0 && selectedRule) {
        elements.ruleSearchStatus.textContent = `No matches for "${rawQuery}"; current rule remains selected`;
        return;
    }
    const keptCurrentText =
        selectedRule && !selectedRuleAlreadyVisible ? " · current rule kept" : "";
    elements.ruleSearchStatus.textContent = `Showing ${matchingRules.length} / ${rules.length} rules for "${rawQuery}"${keptCurrentText}`;
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
                family.family,
                family.previewKey,
                family.renderKind,
                family.sizingMode,
                family.searchAliases.join(","),
            ].join(":"),
        )
        .join("|");
}

function buildTilingPreviewCard(optionData: TopologyOption): HTMLButtonElement {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "tiling-preview-card";
    button.dataset.tilingFamily = optionData.value;
    button.dataset.searchText = tilingSearchText(optionData);
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
    const searchRow = document.createElement("div");
    searchRow.className = "tiling-picker-search-row";

    const searchHeader = document.createElement("div");
    searchHeader.className = "tiling-picker-search-header";

    const searchTitle = document.createElement("strong");
    searchTitle.className = "tiling-picker-search-title";
    searchTitle.textContent = "Choose tiling";

    const currentLabel = document.createElement("span");
    currentLabel.className = "tiling-picker-menu-current";

    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.className = "tiling-picker-close";
    closeButton.setAttribute("aria-label", "Close tiling picker");
    closeButton.title = "Close";
    closeButton.textContent = "×";

    const searchLabel = document.createElement("label");
    searchLabel.className = "tiling-picker-search-label";

    const searchAssistiveLabel = document.createElement("span");
    searchAssistiveLabel.className = "sr-only";
    searchAssistiveLabel.textContent = "Search tilings";

    const searchInput = document.createElement("input");
    searchInput.className = "tiling-picker-search";
    searchInput.type = "search";
    searchInput.placeholder = "Search tilings";
    searchInput.autocomplete = "off";

    searchHeader.append(searchTitle, currentLabel, closeButton);
    searchLabel.append(searchAssistiveLabel, searchInput);
    searchRow.append(searchHeader, searchLabel);
    fragment.appendChild(searchRow);

    const list = document.createElement("div");
    list.className = "tiling-picker-list";

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
        list.appendChild(group);
    });

    const empty = document.createElement("div");
    empty.className = "tiling-picker-empty";
    empty.hidden = true;
    empty.textContent = "No tilings match this search.";

    fragment.append(list, empty);
    menu.replaceChildren(fragment);
}

function syncTilingPreviewSelection(menu: HTMLElement, selectedValue: string): void {
    let selectedLabel = "";
    menu.querySelectorAll<HTMLButtonElement>(".tiling-preview-card").forEach((button) => {
        const selected = button.dataset.tilingFamily === selectedValue;
        button.classList.toggle("is-selected", selected);
        button.setAttribute("aria-pressed", selected ? "true" : "false");
        if (selected) {
            selectedLabel =
                button.querySelector<HTMLElement>(".tiling-preview-card-label")?.textContent ?? "";
            button.setAttribute("aria-current", "true");
            return;
        }
        button.removeAttribute("aria-current");
    });
    const currentLabel = menu.querySelector<HTMLElement>(".tiling-picker-menu-current");
    if (currentLabel) {
        currentLabel.textContent = selectedLabel ? `Current: ${selectedLabel}` : "";
    }
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
