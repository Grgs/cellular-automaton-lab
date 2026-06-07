import { afterEach, describe, expect, it, vi } from "vitest";

import { createSeedPreview, placeSeedOnOrder } from "./compare-seed-preview.js";
import type { SimulationBackend } from "../types/controller.js";
import type { SimulationSnapshot, TopologyPreview, TopologySpec } from "../types/domain.js";

function topologySpec(): TopologySpec {
    return {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 4,
        height: 4,
        patch_depth: 0,
    };
}

function previewWith(order: string[]): TopologyPreview {
    return {
        topology_revision: "t",
        topology_spec: topologySpec(),
        order,
        cells: order.map((id, index) => ({
            id,
            kind: "square",
            center: { x: index + 0.5, y: 0.5 },
            vertices: [
                { x: index, y: 0 },
                { x: index + 1, y: 0 },
                { x: index + 1, y: 1 },
                { x: index, y: 1 },
            ],
        })),
    };
}

function backendReturning(preview: TopologyPreview): {
    backend: SimulationBackend;
    previewTopology: ReturnType<typeof vi.fn>;
} {
    const snapshot = {} as SimulationSnapshot;
    const previewTopology = vi.fn(async () => preview);
    const backend: SimulationBackend = {
        getState: async () => snapshot,
        getRules: async () => ({ rules: [] }),
        dispose: () => {},
        postControl: async () => snapshot,
        toggleCell: async () => snapshot,
        setCell: async () => snapshot,
        setCells: async () => snapshot,
        compareSeed: async () => ({
            rule_name: "conway",
            seed: "",
            seed_bits: 0,
            traversal: "bfs",
            steps: 1,
            grid_size: 16,
            degenerate: false,
            results: [],
        }),
        previewTopology,
    };
    return { backend, previewTopology };
}

describe("placeSeedOnOrder", () => {
    it("paints cells at the set bit positions in order", () => {
        expect(placeSeedOnOrder(["a", "b", "c", "d"], "1010")).toEqual({ a: 1, c: 1 });
    });

    it("ignores bits beyond the available cells", () => {
        expect(placeSeedOnOrder(["a", "b"], "1111")).toEqual({ a: 1, b: 1 });
    });

    it("is empty for an empty seed", () => {
        expect(placeSeedOnOrder(["a", "b"], "")).toEqual({});
    });
});

describe("createSeedPreview", () => {
    afterEach(() => {
        document.body.innerHTML = "";
    });

    it("renders a placement thumbnail per tiling and requests grid_size + traversal", async () => {
        const { backend, previewTopology } = backendReturning(previewWith(["a", "b", "c", "d"]));
        const preview = createSeedPreview({
            backend,
            getSeed: () => "1010", // places a and c
            getTraversal: () => "bfs",
            getGridSize: () => 4,
            getTilings: () => [
                { geometry: "square", label: "Square" },
                { geometry: "hex", label: "Hex" },
            ],
        });
        document.body.append(preview.element);
        preview.refresh();

        await vi.waitFor(() => {
            expect(preview.element.querySelectorAll(".compare-thumb")).toHaveLength(2);
        });
        // 2 tilings × 2 live cells (a, c)
        expect(preview.element.querySelectorAll(".compare-thumb polygon.is-live")).toHaveLength(4);

        const request = previewTopology.mock.calls.at(0)?.[0];
        expect(request).toMatchObject({ geometry: "square", grid_size: 4, traversal: "bfs" });
    });

    it("wraps placement thumbnails in links when a preview href is provided", async () => {
        const { backend } = backendReturning(previewWith(["a", "b", "c", "d"]));
        const preview = createSeedPreview({
            backend,
            getSeed: () => "1010",
            getTraversal: () => "bfs",
            getGridSize: () => 4,
            getTilings: () => [{ geometry: "square", label: "Square" }],
            getPreviewHref: ({ cellsById, preview: topologyPreview }) => {
                expect(cellsById).toEqual({ a: 1, c: 1 });
                expect(topologyPreview.topology_spec.tiling_family).toBe("square");
                return "#share=v1.seed";
            },
        });
        document.body.append(preview.element);
        preview.refresh();

        await vi.waitFor(() => {
            expect(preview.element.querySelector(".compare-thumb-link")).not.toBeNull();
        });
        const link = preview.element.querySelector<HTMLAnchorElement>(".compare-thumb-link");
        expect(link?.getAttribute("href")).toBe("#share=v1.seed");
        expect(link?.querySelector(".compare-thumb")).not.toBeNull();
    });

    it("renders shape_cells and requests a pattern (not a traversal) in shape mode", async () => {
        const shapePreview: TopologyPreview = {
            ...previewWith(["a", "b", "c", "d"]),
            shape_cells: { b: 1, d: 1 },
        };
        const { backend, previewTopology } = backendReturning(shapePreview);
        const preview = createSeedPreview({
            backend,
            getSeed: () => "0000", // ignored in shape mode
            getTraversal: () => "bfs",
            getGridSize: () => 4,
            getPattern: () => "blinker",
            getTilings: () => [{ geometry: "square", label: "Square" }],
        });
        document.body.append(preview.element);
        preview.refresh();

        await vi.waitFor(() => {
            expect(preview.element.querySelectorAll(".compare-thumb")).toHaveLength(1);
        });
        // Live cells come from shape_cells (b, d), not the seed bit-string.
        expect(preview.element.querySelectorAll(".compare-thumb polygon.is-live")).toHaveLength(2);

        const request = previewTopology.mock.calls.at(0)?.[0];
        expect(request).toMatchObject({ geometry: "square", grid_size: 4, pattern: "blinker" });
        expect(request).not.toHaveProperty("traversal");
    });

    it("caps the number of previewed tilings", async () => {
        const { backend } = backendReturning(previewWith(["a", "b"]));
        const preview = createSeedPreview({
            backend,
            getSeed: () => "11",
            getTraversal: () => "bfs",
            getGridSize: () => 4,
            getTilings: () =>
                ["a", "b", "c", "d", "e", "f"].map((g) => ({ geometry: g, label: g })),
            maxTilings: 3,
        });
        document.body.append(preview.element);
        preview.refresh();
        await vi.waitFor(() => {
            expect(preview.element.querySelectorAll(".compare-seedpreview-item")).toHaveLength(3);
        });
    });
});
