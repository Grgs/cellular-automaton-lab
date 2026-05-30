export interface TraversalOption {
    value: string;
    label: string;
}

/** Mirrors backend.simulation.seeding.traversal.TRAVERSALS. */
export const TRAVERSAL_OPTIONS: readonly TraversalOption[] = [
    { value: "bfs", label: "BFS rings (universal)" },
    { value: "row-major", label: "Row-major (grid-like)" },
];
