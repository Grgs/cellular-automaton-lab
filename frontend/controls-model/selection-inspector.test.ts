import { describe, expect, it } from "vitest";

import { buildSelectionInspectorViewModel } from "./selection-inspector.js";
import type { IndexedTopologyCell, RuleDefinition, TopologyIndex } from "../types/domain.js";

const activeRule: RuleDefinition = {
    name: "signal-rule",
    display_name: "Signal Rule",
    description: "Signal states",
    default_paint_state: 2,
    supports_randomize: false,
    rule_protocol: "test",
    supports_all_topologies: true,
    states: [
        { value: 0, label: "Dead", color: "#000000", paintable: false },
        { value: 2, label: "Signal", color: "#ff0000", paintable: true },
    ],
};

function topologyIndex(cells: IndexedTopologyCell[]): TopologyIndex {
    return {
        byId: new Map(cells.map((cell) => [cell.id, cell])),
    };
}

describe("controls-model/selection-inspector", () => {
    it("returns the empty-state hint when no selected cells resolve", () => {
        const inspector = buildSelectionInspectorViewModel({
            selectedCells: [{ id: "missing" }],
            topologyIndex: topologyIndex([]),
            cellStates: [],
            activeRule,
        });

        expect(inspector).toMatchObject({
            mode: "empty",
            title: "No Cells Selected",
            hintText: "Right-click a cell to inspect it. Right-drag to summarize a selection.",
            summaryRows: [],
            advancedVisible: false,
        });
    });

    it("falls back to a live-cell summary when no cells are selected", () => {
        const cells: IndexedTopologyCell[] = [
            {
                id: "cell:a",
                index: 0,
                kind: "triangle",
                neighbors: ["cell:b"],
                tile_family: "family-a",
                center: { x: 0, y: 1 },
                vertices: [
                    { x: 0, y: 0 },
                    { x: 1, y: 0 },
                ],
            },
            {
                id: "cell:b",
                index: 1,
                kind: "square",
                neighbors: ["cell:a", "cell:c"],
                tile_family: "family-b",
                center: { x: 2, y: 3 },
                vertices: [{ x: 0, y: 0 }],
            },
            {
                id: "cell:c",
                index: 2,
                kind: "square",
                neighbors: ["cell:b"],
                tile_family: "family-b",
            },
        ];

        const inspector = buildSelectionInspectorViewModel({
            selectedCells: [],
            topologyIndex: topologyIndex(cells),
            cellStates: [2, 2, 0],
            activeRule,
        });

        expect(inspector.mode).toBe("population");
        expect(inspector.title).toBe("Live Cells Summary");
        expect(inspector.subtitle).toBe("Current population overview");
        expect(inspector.summaryRows).toContainEqual({ label: "Live Cells", value: "2" });
        expect(inspector.summaryRows).toContainEqual({
            label: "State Mix",
            value: "Signal (2): 2",
        });
        expect(inspector.summaryRows).toContainEqual({
            label: "Kind Mix",
            value: "square: 1, triangle: 1",
        });
        expect(inspector.advancedRows).toContainEqual({
            label: "Neighbor Count Distribution",
            value: "1: 1, 2: 1",
        });
        expect(inspector.advancedRows.at(-1)).toEqual({
            label: "Live Cell IDs",
            value: "cell:a, cell:b",
        });
    });

    it("builds detailed rows for a single selected topology cell", () => {
        const cell: IndexedTopologyCell = {
            id: "cell:a",
            index: 0,
            kind: "square",
            neighbors: ["cell:b", null],
            slot: "alpha",
            center: { x: 1 / 3, y: 2 / 3 },
            vertices: [{ x: 0, y: 0 }],
            tile_family: "family-a",
            orientation_token: "north",
            chirality_token: "left",
            decoration_tokens: ["stripe", "dot"],
        };

        const inspector = buildSelectionInspectorViewModel({
            selectedCells: [{ id: "cell:a" }],
            topologyIndex: topologyIndex([cell]),
            cellStates: [2],
            activeRule,
        });

        expect(inspector.mode).toBe("single");
        expect(inspector.subtitle).toBe("square | Signal (2)");
        expect(inspector.summaryRows).toEqual([
            { label: "State", value: "Signal (2)" },
            { label: "Cell ID", value: "cell:a" },
            { label: "Kind", value: "square" },
            { label: "Neighbor Count", value: "1" },
            { label: "Tile Family", value: "family-a" },
            { label: "Orientation", value: "north" },
            { label: "Chirality", value: "left" },
            { label: "Decorations", value: "dot, stripe" },
            { label: "Center", value: "(0.333, 0.667)" },
            { label: "Vertex Count", value: "1" },
            { label: "Slot", value: "alpha" },
        ]);
    });

    it("builds stable aggregate rows and caps selected ids", () => {
        const cells: IndexedTopologyCell[] = Array.from({ length: 22 }, (_, index) => ({
            id: `cell:${String(index).padStart(2, "0")}`,
            index,
            kind: index % 2 === 0 ? "triangle" : "square",
            neighbors: index % 3 === 0 ? ["cell:x", "cell:y"] : ["cell:x"],
            center: { x: index, y: 22 - index },
            vertices: [
                { x: 0, y: 0 },
                { x: 1, y: 0 },
            ],
            tile_family: index % 2 === 0 ? "family-a" : "family-b",
        }));

        const inspector = buildSelectionInspectorViewModel({
            selectedCells: cells.map((cell) => ({ id: cell.id })),
            topologyIndex: topologyIndex(cells),
            cellStates: cells.map((_, index) => (index % 2 === 0 ? 2 : 0)),
            activeRule,
        });

        expect(inspector.mode).toBe("multi");
        expect(inspector.summaryRows).toContainEqual({
            label: "State Mix",
            value: "Dead (0): 11, Signal (2): 11",
        });
        expect(inspector.summaryRows).toContainEqual({
            label: "Kind Mix",
            value: "square: 11, triangle: 11",
        });
        expect(inspector.advancedRows).toContainEqual({
            label: "Neighbor Count Distribution",
            value: "1: 14, 2: 8",
        });
        expect(inspector.advancedRows.at(-1)).toEqual({
            label: "Selected Cell IDs",
            value: "cell:00, cell:01, cell:02, cell:03, cell:04, cell:05, cell:06, cell:07, cell:08, cell:09, cell:10, cell:11, cell:12, cell:13, cell:14, cell:15, cell:16, cell:17, cell:18, cell:19, +2 more",
        });
    });
});
