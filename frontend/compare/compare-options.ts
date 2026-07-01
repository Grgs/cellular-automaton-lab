import type { CompareRunConfig } from "./compare-run-link.js";

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

/**
 * Curated one-click "Watch tilings compare" demo. An excitable Greenberg-Hastings
 * seed run across four deliberately distinct topologies, with a short frame count
 * so the looping filmstrip replays only the lively wave bloom (not a long dead
 * tail). The wave front bends to each geometry -- the clearest one-glance
 * statement of what the app does. Tuned empirically; revisit the rule/length once
 * the loop cadence has been reviewed.
 */
export const FEATURED_COMPARE_DEMO: CompareRunConfig = {
    seed: "",
    rule: "penrose-greenberg-hastings",
    traversal: "bfs",
    grid_size: 22,
    // Only run as far as the wave bloom stays alive on all four boards; the loop
    // then replays the lively sub-window below rather than a long dead tail.
    frames: 12,
    geometries: ["square", "trihexagonal-3-6-3-6", "penrose-p3-rhombs", "hat-monotile"],
    pattern: "r-pentomino",
};

/**
 * Loop the demo over [loopStart, frames-1] only -- skipping the sparse seed
 * lead-in so the looping playback stays full on every board. Paired with a
 * slower speed so each cycle lasts a couple of seconds.
 */
export const FEATURED_COMPARE_DEMO_LOOP_START = 4;
export const FEATURED_COMPARE_DEMO_SPEED = 0.5;

/** A lively generation to rest on when reduced-motion disables autoplay. */
export const FEATURED_COMPARE_DEMO_STILL_FRAME = 8;
