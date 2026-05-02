import { describe, expect, it } from "vitest";

import { populateTilingFamilies } from "./view-options.js";
import { createTilingPreviewThumbnail } from "./tiling-preview.js";
import type { TopologyOption } from "../types/domain.js";
import type { DomElements } from "../types/dom.js";

const FAMILIES: TopologyOption[] = [
    {
        value: "square",
        label: "Square",
        group: "Classic",
        order: 10,
        previewKey: "square",
        renderKind: "regular_grid",
        sizingMode: "grid",
    },
    {
        value: "hex",
        label: "Hexagonal",
        group: "Classic",
        order: 20,
        previewKey: "hex",
        renderKind: "regular_grid",
        sizingMode: "grid",
    },
    {
        value: "penrose-p3-rhombs",
        label: "Penrose P3 Rhombs",
        group: "Aperiodic",
        order: 220,
        previewKey: "penrose-p3-rhombs",
        renderKind: "polygon_aperiodic",
        sizingMode: "patch_depth",
    },
];

function createElements(): DomElements {
    return {
        tilingFamilySelect: document.createElement("select"),
        tilingPickerMenu: document.createElement("div"),
        tilingPickerCurrentPreview: document.createElement("span"),
    } as unknown as DomElements;
}

describe("controls/view-options tiling picker", () => {
    it("populates the native select and grouped preview cards from the same options", () => {
        const elements = createElements();

        populateTilingFamilies(elements, FAMILIES, "hex");

        expect(elements.tilingFamilySelect?.querySelectorAll("optgroup")).toHaveLength(2);
        expect(elements.tilingFamilySelect?.value).toBe("hex");
        expect(elements.tilingPickerMenu?.querySelectorAll(".tiling-preview-group")).toHaveLength(2);
        expect(elements.tilingPickerMenu?.querySelectorAll(".tiling-preview-card")).toHaveLength(3);
        expect(elements.tilingPickerMenu?.querySelector(".tiling-preview-card.is-selected")?.textContent).toContain("Hexagonal");
        expect(elements.tilingPickerCurrentPreview?.querySelector("svg")).not.toBeNull();
    });

    it("reuses preview card DOM when only the selected tiling changes", () => {
        const elements = createElements();

        populateTilingFamilies(elements, FAMILIES, "square");
        const firstRenderedGroup = elements.tilingPickerMenu?.firstElementChild;

        populateTilingFamilies(elements, FAMILIES, "penrose-p3-rhombs");

        expect(elements.tilingPickerMenu?.firstElementChild).toBe(firstRenderedGroup);
        expect(elements.tilingPickerMenu?.querySelector(".tiling-preview-card.is-selected")?.textContent).toContain(
            "Penrose P3 Rhombs",
        );
        expect(elements.tilingPickerCurrentPreview?.dataset.previewSignature).toBe(
            "penrose-p3-rhombs:penrose-p3-rhombs",
        );
    });

    it("renders sampled topology geometry for polygon tiling thumbnails", () => {
        const thumbnail = createTilingPreviewThumbnail({
            value: "archimedean-4-8-8",
            label: "Square-Octagon",
            group: "Periodic Mixed",
            order: 110,
            previewKey: "archimedean-4-8-8",
            renderKind: "polygon_periodic",
            sizingMode: "grid",
        });

        const polygons = Array.from(thumbnail.querySelectorAll("polygon"));
        expect(polygons.length).toBeGreaterThan(10);
        expect(polygons.every((polygon) => polygon.getAttribute("points")?.includes("NaN") === false)).toBe(true);
    });
});
