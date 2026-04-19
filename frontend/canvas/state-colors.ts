import { DEFAULT_GEOMETRY, normalizeGeometry } from "../layout.js";
import {
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_488_GEOMETRY,
    KAGOME_GEOMETRY,
} from "../topology.js";
import { triangleOrientation } from "./geometry-triangle.js";
import { resolveRegisteredFamilyDeadColor } from "./family-dead-palette-registry.js";
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

    const registeredFamilyDeadColor = resolveRegisteredFamilyDeadColor(
        (cell as TopologyCell | null | undefined) ?? null,
        fallbackColors,
    );
    if (registeredFamilyDeadColor) {
        return registeredFamilyDeadColor;
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
