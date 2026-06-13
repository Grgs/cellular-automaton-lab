import { describe, expect, it } from "vitest";

import { populateRules, populateTilingFamilies, refreshRuleFilter } from "./view-options.js";
import { createTilingPreviewThumbnail } from "./tiling-preview.js";
import type { TopologyOption } from "../types/domain.js";
import type { DomElements } from "../types/dom.js";
import type { RuleSelectOption } from "../types/ui.js";

const FAMILIES: TopologyOption[] = [
    {
        value: "square",
        label: "Square",
        group: "Classic",
        order: 10,
        family: "regular",
        previewKey: "square",
        renderKind: "regular_grid",
        sizingMode: "grid",
        searchAliases: [],
    },
    {
        value: "hex",
        label: "Hexagonal",
        group: "Classic",
        order: 20,
        family: "regular",
        previewKey: "hex",
        renderKind: "regular_grid",
        sizingMode: "grid",
        searchAliases: ["honeycomb"],
    },
    {
        value: "penrose-p3-rhombs",
        label: "Penrose P3 Rhombs",
        group: "Aperiodic",
        order: 220,
        family: "aperiodic",
        previewKey: "penrose-p3-rhombs",
        renderKind: "polygon_aperiodic",
        sizingMode: "patch_depth",
        searchAliases: ["fat skinny rhombs"],
    },
];

const RULES: RuleSelectOption[] = [
    {
        name: "conway",
        displayName: "Conway Life",
        description: "Classic binary survival rule.",
        searchText: "conway Conway Life classic binary survival dead live B3/S23",
    },
    {
        name: "wireworld",
        displayName: "WireWorld",
        description: "Signal circuits with conductor wires.",
        searchText: "wireworld WireWorld signal circuits conductor electron head tail",
    },
    {
        name: "penrose-gh",
        displayName: "Penrose Greenberg-Hastings",
        description: "Excitable waves for aperiodic tilings.",
        searchText:
            "penrose-gh Penrose Greenberg-Hastings excitable waves resting excited refractory",
    },
];

const NOTATION_RULES: RuleSelectOption[] = [
    {
        name: "conway",
        displayName: "Life: Conway (B3/S23)",
        description: "Classic Game of Life with births on 3 neighbors and survival on 2 or 3.",
        searchText: "conway Life Conway B3/S23 b3s23 classic game of life",
    },
    {
        name: "highlife",
        displayName: "Life: HighLife (B36/S23)",
        description: "Life variant with births on 3 or 6 neighbors.",
        searchText: "highlife Life HighLife B36/S23 b36s23 replicator",
    },
];

function createElements(): DomElements {
    const elements: Partial<DomElements> = {
        tilingFamilySelect: document.createElement("select"),
        tilingPickerMenu: document.createElement("div"),
        tilingPickerCurrentPreview: document.createElement("span"),
        tilingPickerCurrentLabel: document.createElement("span"),
    };
    return elements as DomElements;
}

function createRuleElements(): DomElements {
    const elements: Partial<DomElements> = {
        ruleSelect: document.createElement("select"),
        ruleSearchInput: document.createElement("input"),
        ruleSearchStatus: document.createElement("span"),
    };
    return elements as DomElements;
}

describe("controls/view-options tiling picker", () => {
    it("populates the native select and grouped preview cards from the same options", () => {
        const elements = createElements();

        populateTilingFamilies(elements, FAMILIES, "hex");

        expect(elements.tilingFamilySelect?.querySelectorAll("optgroup")).toHaveLength(2);
        expect(elements.tilingFamilySelect?.value).toBe("hex");
        expect(elements.tilingPickerMenu?.querySelectorAll(".tiling-preview-group")).toHaveLength(
            2,
        );
        expect(elements.tilingPickerMenu?.querySelectorAll(".tiling-preview-card")).toHaveLength(3);
        expect(
            elements.tilingPickerMenu?.querySelector(".tiling-preview-card.is-selected")
                ?.textContent,
        ).toContain("Hexagonal");
        expect(
            elements.tilingPickerMenu?.querySelector(".tiling-picker-menu-current")?.textContent,
        ).toBe("Current: Hexagonal");
        expect(elements.tilingPickerMenu?.querySelector(".tiling-picker-close")).not.toBeNull();
        expect(elements.tilingPickerCurrentPreview?.querySelector("svg")).not.toBeNull();
        expect(elements.tilingPickerCurrentLabel?.textContent).toBe("Hexagonal");
    });

    it("reuses preview card DOM when only the selected tiling changes", () => {
        const elements = createElements();

        populateTilingFamilies(elements, FAMILIES, "square");
        const firstRenderedGroup = elements.tilingPickerMenu?.firstElementChild;

        populateTilingFamilies(elements, FAMILIES, "penrose-p3-rhombs");

        expect(elements.tilingPickerMenu?.firstElementChild).toBe(firstRenderedGroup);
        expect(
            elements.tilingPickerMenu?.querySelector(".tiling-preview-card.is-selected")
                ?.textContent,
        ).toContain("Penrose P3 Rhombs");
        expect(
            elements.tilingPickerMenu?.querySelector(".tiling-picker-menu-current")?.textContent,
        ).toBe("Current: Penrose P3 Rhombs");
        expect(elements.tilingPickerCurrentPreview?.dataset.previewSignature).toBe(
            "penrose-p3-rhombs:penrose-p3-rhombs",
        );
        expect(elements.tilingPickerCurrentLabel?.textContent).toBe("Penrose P3 Rhombs");
    });

    it("renders sampled topology geometry for polygon tiling thumbnails", () => {
        const thumbnail = createTilingPreviewThumbnail({
            value: "archimedean-4-8-8",
            label: "Square-Octagon",
            group: "Periodic Mixed",
            order: 110,
            family: "mixed",
            previewKey: "archimedean-4-8-8",
            renderKind: "polygon_periodic",
            sizingMode: "grid",
            searchAliases: ["4 8 8", "488"],
        });

        const polygons = Array.from(thumbnail.querySelectorAll("polygon"));
        expect(polygons.length).toBeGreaterThan(10);
        expect(
            polygons.every((polygon) => polygon.getAttribute("points")?.includes("NaN") === false),
        ).toBe(true);
    });

    it("renders dodecagonal square-triangle thumbnails with sampled geometry and palette tokens", () => {
        const thumbnail = createTilingPreviewThumbnail({
            value: "dodecagonal-square-triangle",
            label: "Dodecagonal Square-Triangle",
            group: "Aperiodic",
            order: 270,
            family: "aperiodic",
            previewKey: "dodecagonal-square-triangle",
            renderKind: "polygon_aperiodic",
            sizingMode: "patch_depth",
            searchAliases: ["square triangle"],
        });

        const polygons = Array.from(thumbnail.querySelectorAll("polygon"));
        const sideCounts = new Set(
            polygons.map((polygon) => polygon.getAttribute("points")?.split(" ").length ?? 0),
        );

        expect(polygons).toHaveLength(5);
        expect(sideCounts.has(3)).toBe(true);
        expect(sideCounts.has(4)).toBe(true);
        expect(thumbnail.querySelector("[data-fill-token='toneClay']")).not.toBeNull();
        expect(thumbnail.querySelector("[data-fill-token='toneFlax']")).not.toBeNull();
    });

    it("keeps Type 7 pentagonal thumbnails on the neutral single-prototile fill", () => {
        const thumbnail = createTilingPreviewThumbnail({
            value: "type-7-pentagonal",
            label: "Type 7 Pentagonal",
            group: "Periodic",
            order: 180,
            family: "periodic",
            previewKey: "type-7-pentagonal",
            renderKind: "polygon_periodic",
            sizingMode: "grid",
            searchAliases: ["pentagon"],
        });

        const polygons = Array.from(thumbnail.querySelectorAll("polygon"));
        const fillClasses = new Set(
            polygons.flatMap((polygon) =>
                Array.from(polygon.classList).filter((className) =>
                    className.startsWith("tiling-preview-fill-"),
                ),
            ),
        );

        expect(polygons.length).toBeGreaterThan(10);
        expect(fillClasses).toEqual(new Set(["tiling-preview-fill-a"]));
        expect(thumbnail.querySelector("[data-fill-token]")).toBeNull();
    });
});

describe("controls/view-options rule picker", () => {
    it("filters rules by display name, internal key, description, and state labels", () => {
        const elements = createRuleElements();

        populateRules(elements, RULES, "conway");
        expect(elements.ruleSelect?.querySelectorAll("option")).toHaveLength(3);
        expect(elements.ruleSearchStatus?.textContent).toBe(
            "3 rules available · Try signal, circuit, excitable, wave, replicator, or B3/S23",
        );

        elements.ruleSearchInput!.value = "conductor";
        refreshRuleFilter(elements);

        expect(Array.from(elements.ruleSelect!.options).map((option) => option.value)).toEqual([
            "conway",
            "wireworld",
        ]);
        expect(elements.ruleSelect?.value).toBe("conway");
        expect(elements.ruleSearchStatus?.textContent).toBe(
            'Showing 1 / 3 rules for "conductor" · current rule kept',
        );

        elements.ruleSearchInput!.value = "excited";
        refreshRuleFilter(elements);

        expect(Array.from(elements.ruleSelect!.options).map((option) => option.value)).toEqual([
            "conway",
            "penrose-gh",
        ]);

        elements.ruleSearchInput!.value = "head wire";
        refreshRuleFilter(elements);

        expect(Array.from(elements.ruleSelect!.options).map((option) => option.value)).toEqual([
            "conway",
            "wireworld",
        ]);

        elements.ruleSearchInput!.value = "B3/S23";
        refreshRuleFilter(elements);

        expect(Array.from(elements.ruleSelect!.options).map((option) => option.value)).toEqual([
            "conway",
        ]);
        expect(elements.ruleSearchStatus?.textContent).toBe('Showing 1 / 3 rules for "B3/S23"');
    });

    it("does not mutate selection when no rules match the search", () => {
        const elements = createRuleElements();

        populateRules(elements, RULES, "wireworld");
        elements.ruleSearchInput!.value = "not a rule";
        refreshRuleFilter(elements);

        expect(Array.from(elements.ruleSelect!.options).map((option) => option.value)).toEqual([
            "wireworld",
        ]);
        expect(elements.ruleSelect?.value).toBe("wireworld");
        expect(elements.ruleSearchStatus?.textContent).toBe(
            'No matches for "not a rule"; current rule remains selected',
        );
    });

    it("treats life notation queries as exact compact matches", () => {
        const elements = createRuleElements();

        populateRules(elements, NOTATION_RULES, "conway");
        elements.ruleSearchInput!.value = "B3/S23";
        refreshRuleFilter(elements);

        expect(Array.from(elements.ruleSelect!.options).map((option) => option.value)).toEqual([
            "conway",
        ]);

        elements.ruleSearchInput!.value = "B36/S23";
        refreshRuleFilter(elements);

        expect(Array.from(elements.ruleSelect!.options).map((option) => option.value)).toEqual([
            "conway",
            "highlife",
        ]);
        expect(elements.ruleSearchStatus?.textContent).toBe(
            'Showing 1 / 2 rules for "B36/S23" · current rule kept',
        );
    });
});
