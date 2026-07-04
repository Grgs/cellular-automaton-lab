import { describe, expect, it, vi } from "vitest";

import type { TopologyOption } from "../types/domain.js";

// Load a pristine copy of the module so the lazily-loaded polygon data starts
// unloaded for each test (the data is cached at module scope once resolved).
async function freshPreviewModule() {
    vi.resetModules();
    return import("./tiling-preview.js");
}

const DODECAGONAL_OPTION: TopologyOption = {
    value: "dodecagonal-square-triangle",
    label: "Schlottmann Square-Triangle",
    group: "Aperiodic",
    order: 270,
    family: "aperiodic",
    previewKey: "dodecagonal-square-triangle",
    renderKind: "polygon_aperiodic",
    sizingMode: "patch_depth",
    searchAliases: ["square triangle"],
};

const HEX_OPTION: TopologyOption = {
    value: "hex",
    label: "Hexagonal",
    group: "Classic",
    order: 10,
    family: "regular",
    previewKey: "hex",
    renderKind: "regular_grid",
    sizingMode: "grid",
    searchAliases: [],
};

describe("controls/tiling-preview lazy polygon data", () => {
    it("does not permanently cache a failed preview-data chunk load", async () => {
        vi.doMock("./tiling-preview-data.js", () => {
            return {
                get POLYGON_PREVIEW_DATA(): Readonly<Record<string, string>> {
                    throw new Error("preview chunk unavailable");
                },
            };
        });
        try {
            const { ensureTilingPreviewData } = await freshPreviewModule();

            const firstAttempt = ensureTilingPreviewData();
            await expect(firstAttempt).rejects.toThrow("preview chunk unavailable");
            const secondAttempt = ensureTilingPreviewData();

            expect(secondAttempt).not.toBe(firstAttempt);
            await expect(secondAttempt).rejects.toThrow("preview chunk unavailable");
        } finally {
            vi.doUnmock("./tiling-preview-data.js");
        }
    });

    it("shows a placeholder synchronously then re-renders the thumbnail in place once data loads", async () => {
        const { createTilingPreviewThumbnail, ensureTilingPreviewData } =
            await freshPreviewModule();

        const svg = createTilingPreviewThumbnail(DODECAGONAL_OPTION);

        // Before the async chunk resolves the thumbnail is the neutral square
        // placeholder: numeric fill classes only, no palette fill tokens.
        expect(svg.querySelector("[data-fill-token]")).toBeNull();
        expect(svg.querySelectorAll("polygon").length).toBeGreaterThan(0);

        await ensureTilingPreviewData();

        // The same element is re-rendered in place with the sampled geometry and
        // palette tokens once the data module has loaded.
        expect(svg.querySelectorAll("polygon")).toHaveLength(5);
        expect(svg.querySelector("[data-fill-token='toneCream']")).not.toBeNull();
    });

    it("renders inline regular-grid thumbnails without waiting on the data chunk", async () => {
        const { createTilingPreviewThumbnail } = await freshPreviewModule();

        const svg = createTilingPreviewThumbnail(HEX_OPTION);

        expect(svg.querySelectorAll("polygon").length).toBeGreaterThan(0);
        expect(svg.querySelector("[data-fill-token]")).toBeNull();
    });
});
