import type {
    AdjacencyModeOption,
    PresetMetadata,
    TopologyOption,
} from "./types/domain.js";
import type { DomElements } from "./types/dom.js";
import type { ThemeName } from "./theme.js";
import type {
    ControlsViewModel,
    LabeledOption,
    PaintPaletteState,
    RuleSelectOption,
} from "./types/ui.js";

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

function renderToggleButtons<TValue extends string | number>(
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
        button.setAttribute("aria-pressed", String(option.value) === String(selectedValue) ? "true" : "false");
        button.textContent = option.label;
        container.appendChild(button);
    });
}

function renderPaintPalette(
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
        button.setAttribute("aria-pressed", cellState.value === selectedPaintState ? "true" : "false");

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

function renderRangeControl({
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

    const label = isDark
        ? "Switch to light mode"
        : "Switch to dark mode";
    elements.themeToggleBtn.setAttribute("aria-label", label);
    elements.themeToggleBtn.title = label;
}

export function renderControls(elements: DomElements, viewModel: ControlsViewModel): void {
    elements.statusText!.textContent = viewModel.statusText;
    elements.generationText!.textContent = viewModel.generationText;
    if (elements.canvasHudTilingText) {
        elements.canvasHudTilingText.textContent = viewModel.canvasHudTilingText;
    }
    if (elements.canvasHudAdjacencyText) {
        elements.canvasHudAdjacencyText.textContent = viewModel.canvasHudAdjacencyText;
        elements.canvasHudAdjacencyText.hidden = !viewModel.canvasHudAdjacencyVisible;
    }
    if (elements.canvasHud) {
        elements.canvasHud.hidden = !viewModel.hudVisible;
    }
    if (elements.canvasEditCue) {
        elements.canvasEditCue.hidden = !viewModel.canvasEditCueVisible;
        elements.canvasEditCue.textContent = viewModel.canvasEditCueText || "";
    }
    if (elements.blockingActivityOverlay) {
        elements.blockingActivityOverlay.hidden = !viewModel.blockingActivityVisible;
        elements.blockingActivityOverlay.setAttribute(
            "aria-hidden",
            viewModel.blockingActivityVisible ? "false" : "true",
        );
    }
    if (elements.blockingActivityMessage) {
        elements.blockingActivityMessage.textContent = viewModel.blockingActivityMessage || "";
    }
    if (elements.blockingActivityDetail) {
        elements.blockingActivityDetail.hidden = !viewModel.blockingActivityDetail;
        elements.blockingActivityDetail.textContent = viewModel.blockingActivityDetail || "";
    }
    if (elements.gridViewport) {
        elements.gridViewport.dataset.loading = viewModel.blockingActivityVisible ? "true" : "false";
    }
    if (elements.grid) {
        elements.grid.dataset.editMode = viewModel.gridEditMode || "idle";
        elements.grid.dataset.loading = viewModel.blockingActivityVisible ? "true" : "false";
    }
    elements.ruleText!.textContent = viewModel.ruleText;
    elements.gridSizeText!.textContent = viewModel.gridSizeText;
    elements.gridSizePanelText!.textContent = viewModel.gridSizeText;
    if (elements.inspectorTilingText) {
        elements.inspectorTilingText.textContent = viewModel.inspectorTilingText;
    }
    if (elements.inspectorRuleText) {
        elements.inspectorRuleText.textContent = viewModel.inspectorRuleText;
    }
    if (elements.quickStartHint) {
        elements.quickStartHint.hidden = !viewModel.quickStartHintVisible;
    }
    if (elements.quickStartHintText) {
        elements.quickStartHintText.textContent = viewModel.quickStartHintText || "";
    }
    if (elements.ruleSummaryText) {
        elements.ruleSummaryText.textContent = viewModel.ruleSummaryText;
    }
    if (elements.mainStage) {
        elements.mainStage.classList.toggle("is-drawer-open", Boolean(viewModel.drawerVisible));
    }
    if (elements.controlDrawer) {
        elements.controlDrawer.dataset.open = String(Boolean(viewModel.drawerVisible));
        elements.controlDrawer.setAttribute("aria-hidden", viewModel.drawerVisible ? "false" : "true");
    }
    if (elements.drawerBackdrop) {
        elements.drawerBackdrop.hidden = !viewModel.backdropVisible;
    }
    if (elements.drawerToggleBtn) {
        elements.drawerToggleBtn.textContent = viewModel.drawerToggleLabel;
        elements.drawerToggleBtn.title = viewModel.drawerToggleTitle;
        elements.drawerToggleBtn.setAttribute("aria-expanded", viewModel.drawerVisible ? "true" : "false");
        elements.drawerToggleBtn.setAttribute("aria-pressed", viewModel.drawerVisible ? "true" : "false");
    }
    elements.speedInput!.value = viewModel.speedValue;
    elements.speedLabel!.textContent = viewModel.speedLabel;
    if (elements.tilingFamilySelect) {
        populateTilingFamilies(elements, viewModel.tilingFamilyOptions, viewModel.tilingFamilyValue);
    }
    if (elements.adjacencyModeSelect) {
        populateAdjacencyModes(elements, viewModel.adjacencyModeOptions, viewModel.adjacencyModeValue);
        elements.adjacencyModeSelect.hidden = !viewModel.adjacencyModeVisible;
        elements.adjacencyModeSelect.disabled = !viewModel.adjacencyModeVisible;
    }
    if (elements.adjacencyModeField) {
        elements.adjacencyModeField.hidden = !viewModel.adjacencyModeVisible;
    }
    renderRangeControl({
        field: elements.cellSizeField,
        input: elements.cellSizeInput,
        label: elements.cellSizeLabel,
        visible: viewModel.cellSizeVisible,
        value: viewModel.cellSizeValue,
        min: viewModel.cellSizeMin,
        max: viewModel.cellSizeMax,
        labelText: viewModel.cellSizeLabel,
    });
    renderRangeControl({
        field: elements.patchDepthField,
        input: elements.patchDepthInput,
        label: elements.patchDepthLabel,
        visible: viewModel.patchDepthVisible,
        value: viewModel.patchDepthValue,
        min: viewModel.patchDepthMin,
        max: viewModel.patchDepthMax,
        labelText: viewModel.patchDepthLabel,
    });
    populateOptions(elements.ruleSelect, viewModel.ruleOptions, "name", "displayName", viewModel.ruleSelectValue);
    elements.ruleDescription!.textContent = viewModel.ruleDescription;
    if (elements.randomBtn) {
        elements.randomBtn.hidden = !viewModel.randomResetVisible;
        elements.randomBtn.disabled = viewModel.randomResetDisabled;
        elements.randomBtn.title = viewModel.randomResetTitle;
    }
    if (elements.presetSeedBtn) {
        elements.presetSeedBtn.textContent = viewModel.presetSeedLabel;
        elements.presetSeedBtn.disabled = viewModel.presetSeedDisabled;
        elements.presetSeedBtn.title = viewModel.presetSeedTitle;
    }
    if (elements.presetHelperText) {
        elements.presetHelperText.textContent = viewModel.presetHelperText || "";
    }
    if (elements.presetSeedSelect) {
        populatePresetSeeds(elements, viewModel.presetSeedOptions, viewModel.presetSeedValue ?? "");
        elements.presetSeedSelect.hidden = !viewModel.presetSeedSelectVisible;
        elements.presetSeedSelect.disabled = !viewModel.presetSeedSelectVisible;
    }
    if (elements.presetSeedControls) {
        elements.presetSeedControls.classList.toggle("has-picker", viewModel.presetSeedSelectVisible);
    }
    renderToggleButtons(
        elements.editorTools,
        viewModel.editorTools || [],
        viewModel.selectedEditorTool,
        "editorTool",
        "editor-tool-button",
    );
    renderToggleButtons(
        elements.brushSizeControls,
        viewModel.brushSizeOptions || [],
        viewModel.selectedBrushSize,
        "brushSize",
        "brush-size-button",
    );
    if (elements.undoBtn) {
        elements.undoBtn.disabled = Boolean(viewModel.undoDisabled);
    }
    if (elements.redoBtn) {
        elements.redoBtn.disabled = Boolean(viewModel.redoDisabled);
    }
    if (elements.editorShortcutHint) {
        elements.editorShortcutHint.textContent = viewModel.editorShortcutHint || "";
    }
    if (elements.importPatternBtn) {
        elements.importPatternBtn.textContent = viewModel.importPatternLabel;
        elements.importPatternBtn.title = viewModel.importPatternTitle;
    }
    if (elements.copyPatternBtn) {
        elements.copyPatternBtn.textContent = viewModel.copyPatternLabel;
        elements.copyPatternBtn.disabled = Boolean(viewModel.copyPatternDisabled);
        elements.copyPatternBtn.title = viewModel.copyPatternTitle;
    }
    if (elements.exportPatternBtn) {
        elements.exportPatternBtn.textContent = viewModel.exportPatternLabel;
        elements.exportPatternBtn.disabled = viewModel.exportPatternDisabled;
        elements.exportPatternBtn.title = viewModel.exportPatternTitle;
    }
    if (elements.pastePatternBtn) {
        elements.pastePatternBtn.textContent = viewModel.pastePatternLabel;
        elements.pastePatternBtn.disabled = Boolean(viewModel.pastePatternDisabled);
        elements.pastePatternBtn.title = viewModel.pastePatternTitle;
    }
    if (elements.patternStatus) {
        elements.patternStatus.hidden = viewModel.patternStatusText === "";
        elements.patternStatus.textContent = viewModel.patternStatusText;
        elements.patternStatus.dataset.tone = viewModel.patternStatusTone;
    }
    if (elements.configSyncStatus) {
        elements.configSyncStatus.hidden = viewModel.syncStatusText === "";
        elements.configSyncStatus.textContent = viewModel.syncStatusText;
    }

    if (elements.runToggleBtn) {
        elements.runToggleBtn.textContent = viewModel.runToggle.label;
        elements.runToggleBtn.dataset.controlAction = viewModel.runToggle.controlAction;
        elements.runToggleBtn.setAttribute("aria-label", viewModel.runToggle.ariaLabel);
        elements.runToggleBtn.classList.toggle("is-running", viewModel.runToggle.isRunning);
    }

    renderPaintPalette(elements, viewModel.paletteStates, viewModel.selectedPaintState);
    renderThemeToggle(elements, viewModel.theme);
}
