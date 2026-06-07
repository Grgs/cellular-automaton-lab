import { describe, expect, it } from "vitest";

import {
    renderControlShell,
    renderEditorAndPatternSections,
    renderSelectionInspectorSection,
} from "./view-sections.js";
import type { DomElements } from "../types/dom.js";
import type { ControlsViewModel } from "../types/ui.js";

function createElements(): DomElements {
    const elements: Partial<DomElements> = {
        selectionInspectorSection: document.createElement("section"),
        selectionInspectorTitle: document.createElement("strong"),
        selectionInspectorSubtitle: document.createElement("span"),
        selectionInspectorHint: document.createElement("p"),
        selectionInspectorSummaryRows: document.createElement("div"),
        selectionInspectorAdvanced: document.createElement("details"),
        selectionInspectorAdvancedSummary: document.createElement("summary"),
        selectionInspectorAdvancedRows: document.createElement("div"),
    };
    return elements as DomElements;
}

function viewModel(selectionInspector: ControlsViewModel["selectionInspector"]): ControlsViewModel {
    return { selectionInspector } as ControlsViewModel;
}

describe("controls/view-sections selection inspector", () => {
    it("renders the empty-state hint and hides advanced details", () => {
        const elements = createElements();

        renderSelectionInspectorSection(
            elements,
            viewModel({
                mode: "empty",
                title: "No Cells Selected",
                subtitle: "",
                hintText: "Right-click a cell to inspect it. Right-drag to summarize a selection.",
                summaryRows: [],
                advancedRows: [],
                advancedVisible: false,
                advancedSummaryText: "Advanced Details",
            }),
        );

        expect(elements.selectionInspectorTitle?.textContent).toBe("No Cells Selected");
        expect(elements.selectionInspectorSubtitle?.hidden).toBe(true);
        expect(elements.selectionInspectorHint?.hidden).toBe(false);
        expect(elements.selectionInspectorSummaryRows?.childElementCount).toBe(0);
        expect(elements.selectionInspectorAdvanced?.hidden).toBe(true);
    });

    it("renders summary and advanced rows for a populated inspector", () => {
        const elements = createElements();

        renderSelectionInspectorSection(
            elements,
            viewModel({
                mode: "single",
                title: "1 Cell Selected",
                subtitle: "square | Dead (0)",
                hintText: "ignored",
                summaryRows: [
                    { label: "State", value: "Dead (0)" },
                    { label: "Kind", value: "square" },
                ],
                advancedRows: [{ label: "Neighbor IDs", value: "cell:b, cell:c" }],
                advancedVisible: true,
                advancedSummaryText: "Advanced Details",
            }),
        );

        expect(elements.selectionInspectorTitle?.textContent).toBe("1 Cell Selected");
        expect(elements.selectionInspectorSubtitle?.textContent).toBe("square | Dead (0)");
        expect(elements.selectionInspectorHint?.hidden).toBe(true);
        expect(elements.selectionInspectorSummaryRows?.childElementCount).toBe(2);
        expect(elements.selectionInspectorSummaryRows?.textContent).toContain("State");
        expect(elements.selectionInspectorSummaryRows?.textContent).toContain("Dead (0)");
        expect(elements.selectionInspectorAdvanced?.hidden).toBe(false);
        expect(elements.selectionInspectorAdvancedRows?.textContent).toContain("Neighbor IDs");
    });
});

describe("controls/view-sections control shell", () => {
    it("renders HUD board text and separated drawer message states", () => {
        const elements = {
            statusText: document.createElement("span"),
            generationText: document.createElement("span"),
            canvasHudTilingText: document.createElement("strong"),
            canvasHudAdjacencyText: document.createElement("span"),
            canvasHud: document.createElement("div"),
            canvasEditCue: document.createElement("div"),
            blockingActivityOverlay: document.createElement("div"),
            blockingActivityMessage: document.createElement("strong"),
            blockingActivityDetail: document.createElement("span"),
            gridViewport: document.createElement("div"),
            grid: document.createElement("canvas"),
            ruleText: document.createElement("strong"),
            gridSizeText: document.createElement("strong"),
            inspectorTilingText: document.createElement("strong"),
            inspectorRuleText: document.createElement("span"),
            topologyStatus: document.createElement("div"),
            quickStartHint: document.createElement("div"),
            quickStartHintText: document.createElement("span"),
            mainStage: document.createElement("main"),
            controlDrawer: document.createElement("aside"),
            drawerBackdrop: document.createElement("div"),
            drawerToggleBtn: document.createElement("button"),
        } as Partial<DomElements> as DomElements;

        renderControlShell(elements, {
            statusText: "Paused",
            generationText: "0",
            canvasHudTilingText: "Penrose P3 Rhombs",
            canvasHudAdjacencyText: "Edge adjacency",
            canvasHudAdjacencyVisible: true,
            hudVisible: true,
            canvasEditCueVisible: false,
            canvasEditCueText: "",
            blockingActivityVisible: false,
            blockingActivityMessage: "",
            blockingActivityDetail: "",
            gridEditMode: "idle",
            ruleText: "Life: B2/S23",
            gridSizeText: "Depth 4 • 173 tiles",
            inspectorTilingText: "Penrose P3 Rhombs",
            inspectorRuleText: "Life: B2/S23",
            topologyStatusVisible: true,
            topologyStatusTone: "info",
            topologyStatusLabel: "Aperiodic • Canonical patch",
            topologyStatusDetail: "Backend implementation and verification agree.",
            quickStartHintVisible: true,
            quickStartHintText: "Or click the grid to paint.",
            drawerVisible: true,
            backdropVisible: false,
            drawerToggleLabel: "Hide Inspector",
            drawerToggleTitle: "Hide the overlay inspector.",
            runToggle: {
                label: "Run",
                controlAction: "start",
                ariaLabel: "Run simulation",
                isRunning: false,
            },
        } as Partial<ControlsViewModel> as ControlsViewModel);

        expect(elements.gridSizeText?.textContent).toBe("Depth 4 • 173 tiles");
        expect(elements.topologyStatus?.hidden).toBe(false);
        expect(elements.topologyStatus?.dataset.tone).toBe("info");
        expect(elements.topologyStatus?.textContent).toContain("Aperiodic");
        expect(elements.topologyStatus?.textContent).toContain("Backend implementation");
        expect(elements.quickStartHint?.hidden).toBe(false);
        expect(elements.quickStartHintText?.textContent).toBe("Or click the grid to paint.");
    });

    it("renders pattern status as a separate drawer message state", () => {
        const elements = {
            unsafeSizingField: document.createElement("div"),
            unsafeSizingToggle: document.createElement("input"),
            editorTools: document.createElement("div"),
            brushSizeControls: document.createElement("div"),
            eraseBtn: document.createElement("button"),
            undoBtn: document.createElement("button"),
            redoBtn: document.createElement("button"),
            editorShortcutHint: document.createElement("p"),
            importPatternBtn: document.createElement("button"),
            copyPatternBtn: document.createElement("button"),
            exportPatternBtn: document.createElement("button"),
            pastePatternBtn: document.createElement("button"),
            patternStatus: document.createElement("div"),
            paintPalette: document.createElement("div"),
        } as Partial<DomElements> as DomElements;

        renderEditorAndPatternSections(elements, {
            unsafeSizingEnabled: false,
            editorTools: [],
            selectedEditorTool: "brush",
            brushSizeOptions: [],
            selectedBrushSize: 1,
            undoDisabled: true,
            redoDisabled: true,
            editorShortcutHint: "",
            importPatternLabel: "Import Pattern",
            importPatternTitle: "",
            copyPatternLabel: "Copy Pattern",
            copyPatternDisabled: false,
            copyPatternTitle: "",
            exportPatternLabel: "Export Pattern",
            exportPatternDisabled: false,
            exportPatternTitle: "",
            pastePatternLabel: "Paste Pattern",
            pastePatternDisabled: false,
            pastePatternTitle: "",
            patternStatusText: "Loaded shared board.",
            patternStatusTone: "success",
            paletteStates: [],
            selectedPaintState: null,
            theme: "light",
        } as Partial<ControlsViewModel> as ControlsViewModel);

        expect(elements.patternStatus?.hidden).toBe(false);
        expect(elements.patternStatus?.dataset.tone).toBe("success");
        expect(elements.patternStatus?.textContent).toBe("Loaded shared board.");
    });
});
