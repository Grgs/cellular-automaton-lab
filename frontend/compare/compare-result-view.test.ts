import { afterEach, describe, expect, it, vi } from "vitest";

import type {
    PatternPayload,
    SeedComparisonResult,
    TopologyComparisonResultPayload,
    TopologyPreview,
} from "../types/domain.js";
import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

installFrontendGlobals();

function result(
    overrides: Partial<TopologyComparisonResultPayload> = {},
): TopologyComparisonResultPayload {
    return {
        geometry: "square",
        tiling_family: "square",
        family: "regular",
        cell_count: 100,
        seed_bits: 3,
        seed_cells: 3,
        initial_population: 3,
        final_population: 2,
        normalized_population: 0.67,
        classification: "still-life",
        period: 1,
        steps_run: 2,
        extinction_step: null,
        note: null,
        population: [3, 2, 2],
        change_rate: [0.04, 0],
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 16,
            height: 16,
            patch_depth: 0,
        },
        initial_cells_by_id: { "c:1:1": 1, "c:2:1": 1, "c:1:2": 1 },
        final_cells_by_id: { "c:1:1": 1, "c:2:1": 1 },
        ...overrides,
    };
}

function comparison(row: TopologyComparisonResultPayload = result()): SeedComparisonResult {
    return {
        rule_name: "conway",
        seed: "111",
        seed_bits: 3,
        traversal: "bfs",
        steps: 2,
        grid_size: 16,
        degenerate: false,
        results: [row],
    };
}

const preview: TopologyPreview = {
    topology_revision: "preview",
    topology_spec: {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 16,
        height: 16,
        patch_depth: 0,
    },
    cells: [
        {
            id: "c:1:1",
            kind: "square",
            center: { x: 0.5, y: 0.5 },
            vertices: [
                { x: 0, y: 0 },
                { x: 1, y: 0 },
                { x: 1, y: 1 },
                { x: 0, y: 1 },
            ],
        },
    ],
};

const mountedDisposers: Array<() => void> = [];

async function mountResultView(
    overrides: {
        previewTopology?: () => Promise<TopologyPreview>;
        openPattern?: (pattern: PatternPayload) => void | Promise<void>;
    } = {},
) {
    const { createCompareResultView } = await import("./compare-result-view.js");
    const openPattern = vi.fn(overrides.openPattern ?? (() => {}));
    const previewTopology = vi.fn(overrides.previewTopology ?? (async () => preview));
    const requestClose = vi.fn();
    const status = document.createElement("div");
    const [element, render, open, closeMenu, dispose] = createCompareResultView(
        { previewTopology },
        new Map([["square", "Square"]]),
        () => () => "#123456",
        vi.fn(),
        status,
        openPattern,
        requestClose,
    );
    const view = { element, render, open, closeMenu, dispose };
    mountedDisposers.push(dispose);
    document.body.append(element);
    return { view, openPattern, previewTopology, requestClose };
}

function menu(label: string): HTMLDetailsElement {
    const found = [...document.querySelectorAll<HTMLDetailsElement>(".compare-action-menu")].find(
        (candidate) => candidate.querySelector("summary")?.textContent === label,
    );
    if (!found) {
        throw new Error(`Missing ${label} menu`);
    }
    return found;
}

afterEach(() => {
    mountedDisposers.splice(0).forEach((dispose) => dispose());
    document.body.replaceChildren();
    vi.restoreAllMocks();
});

describe("createCompareResultView", () => {
    it("renders catalog labels and routes begin/end actions through the host", async () => {
        const { view, openPattern, requestClose } = await mountResultView();
        view.render(comparison());

        expect(view.element.querySelector(".compare-grid__name")?.textContent).toBe("Square");
        expect(
            [...view.element.querySelectorAll(".compare-row-actions .compare-link")].map(
                (node) => node.textContent,
            ),
        ).toEqual(["Open", "Copy", "▸ preview"]);

        const openMenu = menu("Open");
        const beginButton = [...openMenu.querySelectorAll<HTMLButtonElement>("button")].find(
            (button) => button.textContent === "Begin",
        );
        expect(beginButton?.title).toBe("Load the seed on this tiling into the board");
        beginButton?.click();
        expect(openPattern).toHaveBeenCalledTimes(1);
        expect(openPattern.mock.calls[0]?.[0]?.cells_by_id).toEqual({
            "c:1:1": 1,
            "c:2:1": 1,
            "c:1:2": 1,
        });
        await vi.waitFor(() => expect(requestClose).toHaveBeenCalledTimes(1));
    });

    it("caches topology previews while toggling detail rows", async () => {
        const { view, previewTopology } = await mountResultView();
        view.render(comparison());

        const previewButton = [...view.element.querySelectorAll<HTMLButtonElement>("button")].find(
            (button) => button.textContent === "▸ preview",
        );
        previewButton?.click();
        await vi.waitFor(() =>
            expect(view.element.querySelectorAll(".compare-thumb-block")).toHaveLength(2),
        );
        expect(previewTopology).toHaveBeenCalledTimes(1);

        previewButton?.click();
        previewButton?.click();
        await vi.waitFor(() =>
            expect(view.element.querySelectorAll(".compare-thumb-block")).toHaveLength(2),
        );
        expect(previewTopology).toHaveBeenCalledTimes(1);
    });

    it("owns action-menu dismissal and removes its document listener on dispose", async () => {
        const { view } = await mountResultView();
        view.render(comparison());
        const openMenu = menu("Open");

        openMenu.open = true;
        document.body.dispatchEvent(new Event("pointerdown", { bubbles: true }));
        expect(openMenu.open).toBe(false);

        openMenu.open = true;
        expect(view.closeMenu()).toBe(true);
        expect(view.closeMenu()).toBe(false);

        openMenu.open = true;
        view.dispose();
        document.body.dispatchEvent(new Event("pointerdown", { bubbles: true }));
        expect(openMenu.open).toBe(true);
    });

    it("explains when a result is too large to preview", async () => {
        const { view, previewTopology } = await mountResultView();
        view.render(comparison(result({ cell_count: 50000 })));

        const note = view.element.querySelector<HTMLElement>(".compare-row-note");
        expect(note?.textContent).toBe("preview too large");
        expect(note?.title).toContain("50,000");
        expect(previewTopology).not.toHaveBeenCalled();
    });
});
