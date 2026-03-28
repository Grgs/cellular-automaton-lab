export {
    DEFAULT_GEOMETRY,
    MIN_GRID_DIMENSION,
    MAX_GRID_DIMENSION,
    DEFAULT_GRID_DIMENSIONS,
    normalizeGeometry,
    getCellGap,
    clampGridDimension,
    gridMetrics,
    computeViewportGridSize,
} from "./geometry-core.js";
import type { ViewportDimensions } from "./types/controller.js";

type GridRow = number[];
type GridMatrix = GridRow[];

export function currentGridDimensions(grid: GridMatrix): ViewportDimensions {
    const firstRow = grid[0];
    return {
        width: firstRow ? firstRow.length : 0,
        height: grid.length,
    };
}

export function sameDimensions(
    left: ViewportDimensions,
    right: ViewportDimensions | null | undefined,
): boolean {
    if (!right) {
        return false;
    }
    return left.width === right.width && left.height === right.height;
}

export function resizeGrid(grid: GridMatrix, newWidth: number, newHeight: number): GridMatrix {
    const resized = Array.from({ length: newHeight }, () => Array<number>(newWidth).fill(0));
    const oldHeight = grid.length;
    const firstRow = grid[0];
    const oldWidth = firstRow ? firstRow.length : 0;

    for (let y = 0; y < Math.min(oldHeight, newHeight); y += 1) {
        const sourceRow = grid[y];
        const targetRow = resized[y];
        if (!sourceRow || !targetRow) {
            continue;
        }
        for (let x = 0; x < Math.min(oldWidth, newWidth); x += 1) {
            targetRow[x] = sourceRow[x] ?? 0;
        }
    }

    return resized;
}
