export interface TraversalOption {
    value: string;
    label: string;
}

/** Mirrors backend.simulation.seeding.traversal.TRAVERSALS. */
export const TRAVERSAL_OPTIONS: readonly TraversalOption[] = [
    { value: "bfs", label: "BFS rings (universal)" },
    { value: "row-major", label: "Row-major (grid-like)" },
];

export interface SeedShapeOption {
    value: string;
    label: string;
}

/**
 * Seed source: "" is the bit-string seed (pad/preview); the rest mirror
 * backend.simulation.seeding.shapes.NAMED_PATTERNS — recognisable shapes placed
 * geometrically on each tiling (Policy A).
 */
export const SEED_SHAPE_OPTIONS: readonly SeedShapeOption[] = [
    { value: "", label: "Bits (draw / type)" },
    { value: "single", label: "Shape: single cell" },
    { value: "blinker", label: "Shape: blinker" },
    { value: "block", label: "Shape: block" },
    { value: "glider", label: "Shape: glider" },
    { value: "r-pentomino", label: "Shape: R-pentomino" },
    { value: "toad", label: "Shape: toad" },
    { value: "acorn", label: "Shape: acorn" },
];
