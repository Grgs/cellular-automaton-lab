import { DEFAULT_GEOMETRY, normalizeGeometry } from "../layout.js";
import {
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_488_GEOMETRY,
    KAGOME_GEOMETRY,
} from "../topology.js";
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
const MIXED_DEAD_ALT_CELL_KINDS = new Map<string, ReadonlySet<string>>([
    [ARCHIMEDEAN_488_GEOMETRY, new Set(["square"])],
    [ARCHIMEDEAN_31212_GEOMETRY, new Set(["triangle"])],
    [ARCHIMEDEAN_4612_GEOMETRY, new Set(["square"])],
    [KAGOME_GEOMETRY, new Set(["triangle-up", "triangle-down"])],
]);

const TUEBINGEN_DEAD_PALETTE = new Map<string, string>([
    ["tuebingen-thick:left", "#f8f1e5"],
    ["tuebingen-thick:right", "#d5bb8f"],
    ["tuebingen-thin:left", "#efe4d0"],
    ["tuebingen-thin:right", "#e1cdac"],
]);

const ROBINSON_DEAD_PALETTE = new Map<string, string>([
    ["robinson-thick", "#f8f1e5"],
    ["robinson-thin", "#d5bb8f"],
]);

const HAT_DEAD_PALETTE = new Map<string, string>([
    ["left", "#f8f1e5"],
    ["right", "#c88d4b"],
]);

const CHAIR_DEAD_PALETTE = new Map<string, string>([
    ["0", "#f8f1e5"],
    ["1", "#e5c089"],
    ["2", "#c88d4b"],
    ["3", "#dbc1b2"],
]);

const SQUARE_TRIANGLE_DEAD_PALETTE = new Map<string, string>([
    ["square-triangle-square:blue", "#f8f1e5"],
    ["square-triangle-square:red", "#ead6b6"],
    ["square-triangle-square:yellow", "#d5bb8f"],
    ["square-triangle-triangle:blue", "#efe4d0"],
    ["square-triangle-triangle:red", "#e1cdac"],
    ["square-triangle-triangle:yellow", "#c88d4b"],
]);

const PINWHEEL_DEAD_PALETTE = new Map<string, string>([
    ["left", "#efe4d0"],
    ["right", "#d5bb8f"],
]);

const SHIELD_DEAD_PALETTE = new Map<string, string>([
    ["shield-shield", "#d5bb8f"],
    ["shield-square", "#f8f1e5"],
    ["shield-triangle", "#c88d4b"],
]);

function resolveTuebingenDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== "tuebingen") {
        return null;
    }
    const kind = typeof topologyCell.kind === "string" ? topologyCell.kind : "";
    const chirality = typeof topologyCell.chirality_token === "string" ? topologyCell.chirality_token : "";
    return TUEBINGEN_DEAD_PALETTE.get(`${kind}:${chirality}`) || null;
}

function resolveRobinsonDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== "robinson") {
        return null;
    }
    const kind = typeof topologyCell.kind === "string" ? topologyCell.kind : "";
    return ROBINSON_DEAD_PALETTE.get(kind) || null;
}

function resolveHatDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== "hat") {
        return null;
    }
    const chirality = typeof topologyCell.chirality_token === "string"
        ? topologyCell.chirality_token
        : "";
    return HAT_DEAD_PALETTE.get(chirality) || null;
}

function resolveChairDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.kind !== "chair") {
        return null;
    }
    const orientation = typeof topologyCell.orientation_token === "string"
        ? topologyCell.orientation_token
        : "";
    return CHAIR_DEAD_PALETTE.get(orientation) || null;
}

function resolveSquareTriangleDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== "square-triangle") {
        return null;
    }
    const kind = typeof topologyCell.kind === "string" ? topologyCell.kind : "";
    const chirality = typeof topologyCell.chirality_token === "string"
        ? topologyCell.chirality_token
        : "";
    return SQUARE_TRIANGLE_DEAD_PALETTE.get(`${kind}:${chirality}`) || null;
}

function resolvePinwheelDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== "pinwheel") {
        return null;
    }
    const chirality = typeof topologyCell.chirality_token === "string"
        ? topologyCell.chirality_token
        : "";
    return PINWHEEL_DEAD_PALETTE.get(chirality) || null;
}

function resolveShieldDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== "shield") {
        return null;
    }
    const kind = typeof topologyCell.kind === "string" ? topologyCell.kind : "";
    return SHIELD_DEAD_PALETTE.get(kind) || null;
}

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

function parseColorChannels(color: string): { r: number; g: number; b: number; a: number } | null {
    const normalized = color.trim().toLowerCase();
    const hexMatch = normalized.match(/^#([0-9a-f]{3,8})$/i);
    if (hexMatch) {
        const hex = hexMatch[1] ?? "";
        if (hex.length === 3 || hex.length === 4) {
            const chars = hex.split("");
            const r = chars[0] ?? "0";
            const g = chars[1] ?? "0";
            const b = chars[2] ?? "0";
            const a = chars[3] ?? "f";
            return {
                r: Number.parseInt(r + r, 16),
                g: Number.parseInt(g + g, 16),
                b: Number.parseInt(b + b, 16),
                a: Number.parseInt(a + a, 16) / 255,
            };
        }
        if (hex.length === 6 || hex.length === 8) {
            return {
                r: Number.parseInt(hex.slice(0, 2), 16),
                g: Number.parseInt(hex.slice(2, 4), 16),
                b: Number.parseInt(hex.slice(4, 6), 16),
                a: hex.length === 8 ? Number.parseInt(hex.slice(6, 8), 16) / 255 : 1,
            };
        }
        return null;
    }

    const rgbMatch = normalized.match(/^rgba?\(([^)]+)\)$/);
    if (!rgbMatch) {
        return null;
    }
    const rgbBody = rgbMatch[1] ?? "";
    const parts = rgbBody.split(",").map((part) => part.trim());
    if (parts.length < 3) {
        return null;
    }
    const red = parts[0];
    const green = parts[1];
    const blue = parts[2];
    if (!red || !green || !blue) {
        return null;
    }
    return {
        r: Number.parseFloat(red),
        g: Number.parseFloat(green),
        b: Number.parseFloat(blue),
        a: parts.length >= 4 && parts[3] ? Number.parseFloat(parts[3]) : 1,
    };
}

function relativeLuminance({ r, g, b }: { r: number; g: number; b: number }): number {
    const toLinear = (channel: number) => {
        const srgb = channel / 255;
        return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
    };
    return (0.2126 * toLinear(r)) + (0.7152 * toLinear(g)) + (0.0722 * toLinear(b));
}

function withAlpha(color: string, alpha: number): string {
    const parsed = parseColorChannels(color);
    if (!parsed) {
        return color;
    }
    return `rgba(${parsed.r}, ${parsed.g}, ${parsed.b}, ${alpha})`;
}

function isDarkThemeHoverPalette(canvasColors: CanvasColors): boolean {
    const parsed = parseColorChannels(canvasColors.lineStrong);
    return parsed ? relativeLuminance(parsed) > 0.6 : false;
}

export function resolveCanvasRenderStyle(
    cellSize: number,
    geometry: string,
    canvasColors: CanvasColors,
): CanvasRenderStyle {
    const renderStyle = resolveRenderStyle(cellSize, geometry);
    const useDarkHoverPalette = isDarkThemeHoverPalette(canvasColors);
    return {
        ...renderStyle,
        lineColor: renderStyle.lineColorToken === "lineStrong"
            ? canvasColors.lineStrong
            : canvasColors.lineSoft,
        aperiodicLineColor: canvasColors.lineAperiodic
            || canvasColors.lineStrong
            || canvasColors.line
            || canvasColors.lineSoft,
        hoverTintColor: useDarkHoverPalette
            ? withAlpha(canvasColors.lineAperiodic || canvasColors.line || canvasColors.live, 0.18)
            : canvasColors.lineStrong,
        hoverStrokeColor: useDarkHoverPalette
            ? withAlpha(canvasColors.lineAperiodic || canvasColors.line || canvasColors.live, 0.9)
            : canvasColors.live,
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

    const tuebingenDeadColor = resolveTuebingenDeadColor(cell);
    if (tuebingenDeadColor) {
        return tuebingenDeadColor;
    }
    const robinsonDeadColor = resolveRobinsonDeadColor(cell);
    if (robinsonDeadColor) {
        return robinsonDeadColor;
    }
    const hatDeadColor = resolveHatDeadColor(cell);
    if (hatDeadColor) {
        return hatDeadColor;
    }
    const chairDeadColor = resolveChairDeadColor(cell);
    if (chairDeadColor) {
        return chairDeadColor;
    }
    const squareTriangleDeadColor = resolveSquareTriangleDeadColor(cell);
    if (squareTriangleDeadColor) {
        return squareTriangleDeadColor;
    }
    const pinwheelDeadColor = resolvePinwheelDeadColor(cell);
    if (pinwheelDeadColor) {
        return pinwheelDeadColor;
    }
    const shieldDeadColor = resolveShieldDeadColor(cell);
    if (shieldDeadColor) {
        return shieldDeadColor;
    }

    const normalizedGeometry = normalizeGeometry(geometry);
    const alternateMixedKinds = MIXED_DEAD_ALT_CELL_KINDS.get(normalizedGeometry);
    if (alternateMixedKinds && typeof cell?.kind === "string" && alternateMixedKinds.has(cell.kind)) {
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
