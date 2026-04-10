import { DEFAULT_GEOMETRY, normalizeGeometry } from "../layout.js";
import {
    COMPACT_RENDER_MAX_CELL_SIZE,
    STANDARD_RENDER_MAX_CELL_SIZE,
} from "./render-constants.js";
import { resolveCanvasOverlayStyle } from "./overlay-style.js";
import type {
    CanvasColors,
    CanvasRenderStyle,
    RenderStyle,
} from "../types/rendering.js";

export {
    DEFAULT_COLORS,
    parseColorChannels,
    readCanvasColors,
    relativeLuminance,
    withAlpha,
} from "./theme-colors.js";
export {
    buildStateColorLookup,
    resolveDeadCellColor,
    resolveRenderedCellColor,
    resolveStateColor,
} from "./state-colors.js";

export function resolveRenderDetailLevel(cellSize: number): RenderStyle["mode"] {
    if (cellSize <= COMPACT_RENDER_MAX_CELL_SIZE) {
        return "compact";
    }
    if (cellSize <= STANDARD_RENDER_MAX_CELL_SIZE) {
        return "standard";
    }
    return "detailed";
}

export function resolveRenderStyle(cellSize: number, geometry = DEFAULT_GEOMETRY): RenderStyle {
    const normalizedGeometry = normalizeGeometry(geometry);
    const mode = resolveRenderDetailLevel(cellSize);
    return {
        mode,
        geometry: normalizedGeometry,
        lineColorToken: mode === "detailed" ? "lineStrong" : "lineSoft",
        triangleStrokeEnabled: normalizedGeometry === "triangle" && mode === "detailed",
    };
}

export function resolveCanvasRenderStyle(
    cellSize: number,
    geometry: string,
    canvasColors: CanvasColors,
): CanvasRenderStyle {
    const renderStyle = resolveRenderStyle(cellSize, geometry);
    return {
        ...renderStyle,
        lineColor: renderStyle.lineColorToken === "lineStrong"
            ? canvasColors.lineStrong
            : canvasColors.lineSoft,
        aperiodicLineColor: canvasColors.lineAperiodic
            || canvasColors.lineStrong
            || canvasColors.line
            || canvasColors.lineSoft,
        ...resolveCanvasOverlayStyle(canvasColors),
    };
}
