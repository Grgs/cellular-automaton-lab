import {
    renderControlShell,
    renderEditorAndPatternSections,
    renderSelectionInspectorSection,
    renderSimulationSections,
} from "./controls/view-sections.js";
import {
    populateAdjacencyModes,
    populatePresetSeeds,
    populateRules,
    populateTilingFamilies,
} from "./controls/view-options.js";
import { renderThemeToggle } from "./controls/view-primitives.js";
import type { DomElements } from "./types/dom.js";
import type { ControlsViewModel } from "./types/ui.js";
import type { ThemeName } from "./theme.js";

export {
    populateAdjacencyModes,
    populatePresetSeeds,
    populateRules,
    populateTilingFamilies,
    renderThemeToggle,
};

export function renderControls(elements: DomElements, viewModel: ControlsViewModel): void {
    renderControlShell(elements, viewModel);
    renderSelectionInspectorSection(elements, viewModel);
    renderSimulationSections(elements, viewModel);
    renderEditorAndPatternSections(elements, viewModel);
}

export type { ThemeName };
