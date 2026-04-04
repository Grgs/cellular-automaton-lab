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

const SHIELD_SHIELD_DEAD_PALETTE = new Map<string, string>([
    ["arrow:ring-0", "#d5bb8f"],
    ["arrow:ring-1", "#c7a574"],
    ["fill:ring-0", "#efe4d0"],
    ["fill:ring-1", "#e1cdac"],
]);

const SHIELD_TRIANGLE_DEAD_PALETTE = new Map<string, string>([
    ["phase-0:left", "#f8f1e5"],
    ["phase-0:right", "#ead6b6"],
    ["phase-1:left", "#efe4d0"],
    ["phase-1:right", "#dcc39a"],
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
    const decorations = Array.isArray(topologyCell.decoration_tokens)
        ? topologyCell.decoration_tokens
        : [];
    if (kind === "shield-shield") {
        const first = decorations[0] ?? "";
        const ring = decorations.find((token) => token.startsWith("ring-")) ?? "ring-0";
        const key = `${first.startsWith("fill-") ? "fill" : "arrow"}:${ring}`;
        return SHIELD_SHIELD_DEAD_PALETTE.get(key) || null;
    }
    if (kind === "shield-triangle") {
        const phase = decorations.find((token) => token.startsWith("phase-")) ?? "phase-0";
        const chirality = typeof topologyCell.chirality_token === "string" ? topologyCell.chirality_token : "";
        return SHIELD_TRIANGLE_DEAD_PALETTE.get(`${phase}:${chirality}`) || null;
    }
    return null;
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
