import { describe, expect, it } from "vitest";

import { renderSelectionInspectorSection } from "./view-sections.js";
import type { DomElements } from "../types/dom.js";
import type { ControlsViewModel } from "../types/ui.js";

function createElements(): DomElements {
    return {
        selectionInspectorSection: document.createElement("section"),
        selectionInspectorTitle: document.createElement("strong"),
        selectionInspectorSubtitle: document.createElement("span"),
        selectionInspectorHint: document.createElement("p"),
        selectionInspectorSummaryRows: document.createElement("div"),
        selectionInspectorAdvanced: document.createElement("details"),
        selectionInspectorAdvancedSummary: document.createElement("summary"),
        selectionInspectorAdvancedRows: document.createElement("div"),
    } as unknown as DomElements;
}

function viewModel(selectionInspector: ControlsViewModel["selectionInspector"]): ControlsViewModel {
    return { selectionInspector } as ControlsViewModel;
}

describe("controls/view-sections selection inspector", () => {
    it("renders the empty-state hint and hides advanced details", () => {
        const elements = createElements();

        renderSelectionInspectorSection(elements, viewModel({
            mode: "empty",
            title: "No Cells Selected",
            subtitle: "",
            hintText: "Right-click a cell to inspect it. Right-drag to summarize a selection.",
            summaryRows: [],
            advancedRows: [],
            advancedVisible: false,
            advancedSummaryText: "Advanced Details",
        }));

        expect(elements.selectionInspectorTitle?.textContent).toBe("No Cells Selected");
        expect(elements.selectionInspectorSubtitle?.hidden).toBe(true);
        expect(elements.selectionInspectorHint?.hidden).toBe(false);
        expect(elements.selectionInspectorSummaryRows?.childElementCount).toBe(0);
        expect(elements.selectionInspectorAdvanced?.hidden).toBe(true);
    });

    it("renders summary and advanced rows for a populated inspector", () => {
        const elements = createElements();

        renderSelectionInspectorSection(elements, viewModel({
            mode: "single",
            title: "1 Cell Selected",
            subtitle: "square | Dead (0)",
            hintText: "ignored",
            summaryRows: [
                { label: "State", value: "Dead (0)" },
                { label: "Kind", value: "square" },
            ],
            advancedRows: [
                { label: "Neighbor IDs", value: "cell:b, cell:c" },
            ],
            advancedVisible: true,
            advancedSummaryText: "Advanced Details",
        }));

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
