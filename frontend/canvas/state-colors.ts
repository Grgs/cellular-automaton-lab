import { DEFAULT_GEOMETRY, normalizeGeometry } from "../layout.js";
import {
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_488_GEOMETRY,
    CHAIR_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
    HAT_TILE_FAMILY,
    KAGOME_GEOMETRY,
    PINWHEEL_TILE_FAMILY,
    ROBINSON_THICK_KIND,
    ROBINSON_THIN_KIND,
    ROBINSON_TILE_FAMILY,
    SHIELD_SHIELD_KIND,
    SHIELD_SQUARE_KIND,
    SHIELD_TILE_FAMILY,
    SHIELD_TRIANGLE_KIND,
    TUEBINGEN_THICK_KIND,
    TUEBINGEN_THIN_KIND,
    TUEBINGEN_TILE_FAMILY,
} from "../topology.js";
import { triangleOrientation } from "./geometry-triangle.js";
import { DEFAULT_COLORS } from "./theme-colors.js";
import type { CanvasColors } from "../types/rendering.js";
import type { CellStateDefinition, TopologyCell } from "../types/domain.js";
import type { PaintableCell } from "../types/editor.js";

const MIXED_DEAD_ALT_CELL_KINDS = new Map<string, ReadonlySet<string>>([
    [ARCHIMEDEAN_488_GEOMETRY, new Set(["square"])],
    [ARCHIMEDEAN_31212_GEOMETRY, new Set(["triangle"])],
    [ARCHIMEDEAN_4612_GEOMETRY, new Set(["square"])],
    [KAGOME_GEOMETRY, new Set(["triangle-up", "triangle-down"])],
]);

const TUEBINGEN_DEAD_PALETTE = new Map<string, string>([
    [`${TUEBINGEN_THICK_KIND}:left`, "#f8f1e5"],
    [`${TUEBINGEN_THICK_KIND}:right`, "#d5bb8f"],
    [`${TUEBINGEN_THIN_KIND}:left`, "#efe4d0"],
    [`${TUEBINGEN_THIN_KIND}:right`, "#e1cdac"],
]);

const ROBINSON_DEAD_PALETTE = new Map<string, string>([
    [ROBINSON_THICK_KIND, "#f8f1e5"],
    [ROBINSON_THIN_KIND, "#d5bb8f"],
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

const DODECAGONAL_SQUARE_TRIANGLE_DEAD_PALETTE = new Map<string, string>([
    [`${DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND}:blue`, "#f8f1e5"],
    [`${DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND}:red`, "#ead6b6"],
    [`${DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND}:yellow`, "#d5bb8f"],
    [`${DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND}:blue`, "#efe4d0"],
    [`${DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND}:red`, "#e1cdac"],
    [`${DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND}:yellow`, "#c88d4b"],
]);

const PINWHEEL_DEAD_PALETTE = new Map<string, string>([
    ["left", "#efe4d0"],
    ["right", "#d5bb8f"],
]);

function resolveTuebingenDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== TUEBINGEN_TILE_FAMILY) {
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
    if (topologyCell?.tile_family !== ROBINSON_TILE_FAMILY) {
        return null;
    }
    const kind = typeof topologyCell.kind === "string" ? topologyCell.kind : "";
    return ROBINSON_DEAD_PALETTE.get(kind) || null;
}

function resolveHatDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== HAT_TILE_FAMILY) {
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
    if (topologyCell?.kind !== CHAIR_KIND) {
        return null;
    }
    const orientation = typeof topologyCell?.orientation_token === "string"
        ? topologyCell.orientation_token
        : "";
    return CHAIR_DEAD_PALETTE.get(orientation) || null;
}

function resolveDodecagonalSquareTriangleDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY) {
        return null;
    }
    const kind = typeof topologyCell.kind === "string" ? topologyCell.kind : "";
    const chirality = typeof topologyCell.chirality_token === "string"
        ? topologyCell.chirality_token
        : "";
    return DODECAGONAL_SQUARE_TRIANGLE_DEAD_PALETTE.get(`${kind}:${chirality}`) || null;
}

function resolvePinwheelDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== PINWHEEL_TILE_FAMILY) {
        return null;
    }
    const chirality = typeof topologyCell.chirality_token === "string"
        ? topologyCell.chirality_token
        : "";
    return PINWHEEL_DEAD_PALETTE.get(chirality) || null;
}

function resolveShieldDeadColor(
    cell: TopologyCell | PaintableCell | null | undefined,
    fallbackColors: CanvasColors = DEFAULT_COLORS,
): string | null {
    const topologyCell = cell as Partial<TopologyCell> | null | undefined;
    if (topologyCell?.tile_family !== SHIELD_TILE_FAMILY) {
        return null;
    }
    const kind = typeof topologyCell.kind === "string" ? topologyCell.kind : "";
    if (kind === SHIELD_SHIELD_KIND) {
        return fallbackColors.deadAlt;
    }
    if (kind === SHIELD_SQUARE_KIND) {
        return fallbackColors.dead;
    }
    if (kind === SHIELD_TRIANGLE_KIND) {
        return fallbackColors.accentStrong;
    }
    return null;
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
    const dodecagonalSquareTriangleDeadColor = resolveDodecagonalSquareTriangleDeadColor(cell);
    if (dodecagonalSquareTriangleDeadColor) {
        return dodecagonalSquareTriangleDeadColor;
    }
    const pinwheelDeadColor = resolvePinwheelDeadColor(cell);
    if (pinwheelDeadColor) {
        return pinwheelDeadColor;
    }
    const shieldDeadColor = resolveShieldDeadColor(cell, fallbackColors);
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
