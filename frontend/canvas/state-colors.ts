import { DEFAULT_GEOMETRY, normalizeGeometry } from "../layout.js";
import { triangleOrientation } from "./geometry-triangle.js";
import { resolveRegisteredFamilyDeadColor } from "./family-dead-palette-registry.js";
import { DEFAULT_COLORS } from "./theme-colors.js";
import type { CanvasColors } from "../types/rendering.js";
import type { CellStateDefinition, TopologyCell } from "../types/domain.js";
import type { PaintableCell } from "../types/editor.js";

export function resolveDeadCellColor(
    stateValue: number,
    {
        geometry = DEFAULT_GEOMETRY,
        x = null,
        y = null,
        cell = null,
        tileColorsEnabled = true,
    }: {
        geometry?: string;
        x?: number | null;
        y?: number | null;
        cell?: TopologyCell | PaintableCell | null;
        tileColorsEnabled?: boolean;
    } = {},
    fallbackColors = DEFAULT_COLORS,
): string | null {
    if (stateValue !== 0) {
        return null;
    }

    const normalizedGeometry = normalizeGeometry(geometry);
    if (tileColorsEnabled) {
        const registeredFamilyDeadColor = resolveRegisteredFamilyDeadColor(
            (cell as TopologyCell | null | undefined) ?? null,
            fallbackColors,
            normalizedGeometry,
        );
        if (registeredFamilyDeadColor) {
            return registeredFamilyDeadColor;
        }
    }

    if (
        normalizedGeometry === "triangle" &&
        typeof x === "number" &&
        typeof y === "number" &&
        Number.isInteger(x) &&
        Number.isInteger(y) &&
        triangleOrientation(x, y) === "down"
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
    return (
        colorLookup.get(stateValue) ||
        (stateValue === 0 ? fallbackColors.dead : fallbackColors.live)
    );
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
        tileColorsEnabled = true,
    }: {
        geometry?: string;
        x?: number | null;
        y?: number | null;
        cell?: TopologyCell | PaintableCell | null;
        tileColorsEnabled?: boolean;
    } = {},
): string {
    return (
        resolveDeadCellColor(
            stateValue,
            { geometry, x, y, cell, tileColorsEnabled },
            fallbackColors,
        ) || resolveStateColor(stateValue, colorLookup, fallbackColors)
    );
}
