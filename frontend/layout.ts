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

export function sameDimensions(
    left: ViewportDimensions,
    right: ViewportDimensions | null | undefined,
): boolean {
    if (!right) {
        return false;
    }
    return left.width === right.width && left.height === right.height;
}
