import { DEFAULT_GEOMETRY, normalizeGeometry } from "../layout.js";
import { ARCHIMEDEAN_488_GEOMETRY, KAGOME_GEOMETRY } from "../topology.js";
import { triangleOrientation } from "./geometry-triangle.js";
import type {
    CanvasColors,
    CanvasRenderStyle,
    RenderStyle,
} from "../types/rendering.js";
import type { CellStateDefinition, TopologyCell } from "../types/domain.js";
import type { PaintableCell } from "../types/editor.js";

export const DEFAULT_COLORS: CanvasColors = {
    line: "rgba(31, 36, 48, 0.16)",
    dead: "#f8f1e5",
    deadAlt: "#d5bb8f",
    lineSoft: "rgba(31, 36, 48, 0.07)",
    lineStrong: "rgba(31, 36, 48, 0.14)",
    lineAperiodic: "rgba(31, 36, 48, 0.18)",
    live: "#1f2430",
};

const COMPACT_MAX_CELL_SIZE = 4;
const STANDARD_MAX_CELL_SIZE = 8;

export function readCanvasColors(
    canvas: HTMLElement,
    getComputedStyleFn: (node: Element) => CSSStyleDeclaration,
): CanvasColors {
    const rootStyle = getComputedStyleFn(document.documentElement);
    const canvasStyle = getComputedStyleFn(canvas);
    const dead = rootStyle.getPropertyValue("--cell-dead").trim()
        || rootStyle.getPropertyValue("--dead").trim()
        || DEFAULT_COLORS.dead;
    return {
        line: rootStyle.getPropertyValue("--line").trim() || canvasStyle.backgroundColor || DEFAULT_COLORS.line,
        dead,
        deadAlt: rootStyle.getPropertyValue("--cell-dead-alt").trim() || dead || DEFAULT_COLORS.deadAlt,
        lineSoft: rootStyle.getPropertyValue("--cell-line-soft").trim()
            || rootStyle.getPropertyValue("--line").trim()
            || canvasStyle.backgroundColor
            || DEFAULT_COLORS.lineSoft,
        lineStrong: rootStyle.getPropertyValue("--cell-line-strong").trim()
            || rootStyle.getPropertyValue("--line").trim()
            || canvasStyle.backgroundColor
            || DEFAULT_COLORS.lineStrong,
        lineAperiodic: rootStyle.getPropertyValue("--cell-line-aperiodic").trim()
            || rootStyle.getPropertyValue("--cell-line-strong").trim()
            || rootStyle.getPropertyValue("--line").trim()
            || canvasStyle.backgroundColor
            || DEFAULT_COLORS.lineAperiodic,
        live: rootStyle.getPropertyValue("--live").trim() || DEFAULT_COLORS.live,
    };
}

export function resolveRenderDetailLevel(cellSize: number): RenderStyle["mode"] {
    if (cellSize <= COMPACT_MAX_CELL_SIZE) {
        return "compact";
    }
    if (cellSize <= STANDARD_MAX_CELL_SIZE) {
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
    };
}

export function resolveDeadCellColor(
    stateValue: number,
    {
        geometry = DEFAULT_GEOMETRY,
        x = null,
        y = null,
        cell = null,
    }: {
        geometry?: string;
        x?: number | null;
        y?: number | null;
        cell?: TopologyCell | PaintableCell | null;
    } = {},
    fallbackColors = DEFAULT_COLORS,
): string | null {
    if (stateValue !== 0) {
        return null;
    }

    const normalizedGeometry = normalizeGeometry(geometry);
    if (normalizedGeometry === ARCHIMEDEAN_488_GEOMETRY && cell?.kind === "square") {
        return fallbackColors.deadAlt;
    }
    if (
        normalizedGeometry === KAGOME_GEOMETRY
        && cell
        && cell.kind !== "hexagon"
    ) {
        return fallbackColors.deadAlt;
    }
    if (
        normalizedGeometry === "triangle"
        && typeof x === "number"
        && typeof y === "number"
        && Number.isInteger(x)
        && Number.isInteger(y)
        && triangleOrientation(x, y) === "down"
    ) {
        return fallbackColors.deadAlt;
    }
    return fallbackColors.dead;
}

export function buildStateColorLookup(
    stateDefinitions: CellStateDefinition[] = [],
    fallbackColors = DEFAULT_COLORS,
): Map<number, string> {
    const colorLookup = new Map<number, string>();

    for (const stateDefinition of stateDefinitions) {
        if (typeof stateDefinition.color === "string") {
            colorLookup.set(stateDefinition.value, stateDefinition.color);
        }
    }
    if (!colorLookup.has(0)) {
        colorLookup.set(0, fallbackColors.dead);
    }
    if (!colorLookup.has(1)) {
        colorLookup.set(1, fallbackColors.live);
    }

    return colorLookup;
}

export function resolveStateColor(
    stateValue: number,
    colorLookup: Map<number, string>,
    fallbackColors = DEFAULT_COLORS,
): string {
    return colorLookup.get(stateValue) || (stateValue === 0 ? fallbackColors.dead : fallbackColors.live);
}

export function resolveRenderedCellColor(
    stateValue: number,
    colorLookup: Map<number, string>,
    fallbackColors: CanvasColors,
    {
        geometry = DEFAULT_GEOMETRY,
        x = null,
        y = null,
        cell = null,
    }: {
        geometry?: string;
        x?: number | null;
        y?: number | null;
        cell?: TopologyCell | PaintableCell | null;
    } = {},
): string {
    return resolveDeadCellColor(stateValue, { geometry, x, y, cell }, fallbackColors)
        || resolveStateColor(stateValue, colorLookup, fallbackColors);
}
