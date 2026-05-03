import { renderThemeToggle, renderPaintPalette, renderRangeControl, renderToggleButtons } from "./view-primitives.js";
import { populateAdjacencyModes, populatePresetSeeds, populateRules, populateTilingFamilies } from "./view-options.js";
import type { DomElements } from "../types/dom.js";
import type { ControlsViewModel, SelectionInspectorSummaryRow } from "../types/ui.js";

function renderSelectionInspectorRows(container: HTMLElement | null, rows: readonly SelectionInspectorSummaryRow[]): void {
    if (!container) {
        return;
    }
    container.replaceChildren(
        ...rows.map((row) => {
            const rowElement = document.createElement("div");
            rowElement.className = "selection-inspector-row";

            const labelElement = document.createElement("span");
            labelElement.className = "selection-inspector-row-label";
            labelElement.textContent = row.label;

            const valueElement = document.createElement("span");
            valueElement.className = "selection-inspector-row-value";
            valueElement.textContent = row.value;

            rowElement.append(labelElement, valueElement);
            return rowElement;
        }),
    );
}

export function renderSelectionInspectorSection(elements: DomElements, viewModel: ControlsViewModel): void {
    const inspector = viewModel.selectionInspector;
    if (elements.selectionInspectorTitle) {
        elements.selectionInspectorTitle.textContent = inspector.title;
    }
    if (elements.selectionInspectorSubtitle) {
        elements.selectionInspectorSubtitle.textContent = inspector.subtitle;
        elements.selectionInspectorSubtitle.hidden = inspector.subtitle === "";
    }
    if (elements.selectionInspectorHint) {
        elements.selectionInspectorHint.textContent = inspector.hintText;
        elements.selectionInspectorHint.hidden = inspector.mode !== "empty";
    }
    renderSelectionInspectorRows(elements.selectionInspectorSummaryRows, inspector.summaryRows);
    renderSelectionInspectorRows(elements.selectionInspectorAdvancedRows, inspector.advancedRows);
    if (elements.selectionInspectorAdvancedSummary) {
        elements.selectionInspectorAdvancedSummary.textContent = inspector.advancedSummaryText;
    }
    if (elements.selectionInspectorAdvanced) {
        elements.selectionInspectorAdvanced.hidden = !inspector.advancedVisible;
        if (!inspector.advancedVisible) {
            elements.selectionInspectorAdvanced.open = false;
        }
    }
}

export function renderControlShell(elements: DomElements, viewModel: ControlsViewModel): void {
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
    if (elements.topologyStatus) {
        elements.topologyStatus.hidden = !viewModel.topologyStatusVisible;
        elements.topologyStatus.dataset.tone = viewModel.topologyStatusTone;
        elements.topologyStatus.innerHTML = "";
        if (viewModel.topologyStatusVisible) {
            const labelElement = document.createElement("strong");
            labelElement.className = "topology-status-label";
            labelElement.textContent = viewModel.topologyStatusLabel;

            const detailElement = document.createElement("span");
            detailElement.className = "topology-status-detail";
            detailElement.textContent = viewModel.topologyStatusDetail;

            elements.topologyStatus.append(labelElement, detailElement);
        }
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
}

export function renderSimulationSections(elements: DomElements, viewModel: ControlsViewModel): void {
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
    populateRules(elements, viewModel.ruleOptions, viewModel.ruleSelectValue);
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
    if (elements.runToggleBtn) {
        elements.runToggleBtn.textContent = viewModel.runToggle.label;
        elements.runToggleBtn.dataset.controlAction = viewModel.runToggle.controlAction;
        elements.runToggleBtn.setAttribute("aria-label", viewModel.runToggle.ariaLabel);
        elements.runToggleBtn.classList.toggle("is-running", viewModel.runToggle.isRunning);
    }
    if (elements.configSyncStatus) {
        elements.configSyncStatus.hidden = viewModel.syncStatusText === "";
        elements.configSyncStatus.textContent = viewModel.syncStatusText;
    }
}

export function renderEditorAndPatternSections(elements: DomElements, viewModel: ControlsViewModel): void {
    if (elements.unsafeSizingField) {
        elements.unsafeSizingField.hidden = false;
    }
    if (elements.unsafeSizingToggle) {
        elements.unsafeSizingToggle.checked = Boolean(viewModel.unsafeSizingEnabled);
    }
    if (elements.tileColorsField) {
        elements.tileColorsField.hidden = false;
    }
    if (elements.tileColorsToggle) {
        elements.tileColorsToggle.checked = viewModel.tileColorsEnabled !== false;
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
    if (elements.eraseBtn) {
        const eraseState = viewModel.paletteStates.find((state) => state.value === 0) ?? null;
        const eraseSelected = viewModel.selectedPaintState === 0;
        elements.eraseBtn.hidden = viewModel.selectedPaintState === null;
        elements.eraseBtn.disabled = viewModel.selectedPaintState === null;
        elements.eraseBtn.textContent = "Erase";
        elements.eraseBtn.title = eraseState
            ? `Select ${eraseState.label} for erasing.`
            : "Select state 0 for erasing.";
        elements.eraseBtn.setAttribute("aria-pressed", eraseSelected ? "true" : "false");
        elements.eraseBtn.classList.toggle("is-selected", eraseSelected);
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

    renderPaintPalette(elements, viewModel.paletteStates, viewModel.selectedPaintState);
    renderThemeToggle(elements, viewModel.theme);
}
