import {
    CHAIR_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
    HAT_TILE_FAMILY,
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
import { DEFAULT_COLORS } from "./theme-colors.js";
import type { CanvasColors } from "../types/rendering.js";
import type { TopologyCell } from "../types/domain.js";

export type DeadPaletteColorToken = "dead" | "deadAlt" | "accent" | "accentStrong";

export type DeadPaletteColorSpec = string | { token: DeadPaletteColorToken };

export interface FamilyDeadPaletteVariantSelector {
    kind?: string;
    tile_family?: string;
    chirality_token?: string;
    orientation_token?: string;
}

export interface FamilyDeadPaletteVariantDefinition {
    geometry: string;
    label: string;
    selector: FamilyDeadPaletteVariantSelector;
    color: DeadPaletteColorSpec;
    allowSharedDeadColor?: boolean;
}

export interface FamilyDeadPaletteDefinition {
    geometry: string;
    variants: readonly FamilyDeadPaletteVariantDefinition[];
}

function tokenColor(token: DeadPaletteColorToken): { token: DeadPaletteColorToken } {
    return { token };
}

export const FAMILY_DEAD_PALETTE_REGISTRY: readonly FamilyDeadPaletteDefinition[] = Object.freeze([
    {
        geometry: "tuebingen-triangle",
        variants: Object.freeze([
            {
                geometry: "tuebingen-triangle",
                label: "tuebingen-thick-left",
                selector: { kind: TUEBINGEN_THICK_KIND, tile_family: TUEBINGEN_TILE_FAMILY, chirality_token: "left" },
                color: "#f8f1e5",
            },
            {
                geometry: "tuebingen-triangle",
                label: "tuebingen-thick-right",
                selector: { kind: TUEBINGEN_THICK_KIND, tile_family: TUEBINGEN_TILE_FAMILY, chirality_token: "right" },
                color: "#d5bb8f",
            },
            {
                geometry: "tuebingen-triangle",
                label: "tuebingen-thin-left",
                selector: { kind: TUEBINGEN_THIN_KIND, tile_family: TUEBINGEN_TILE_FAMILY, chirality_token: "left" },
                color: "#efe4d0",
            },
            {
                geometry: "tuebingen-triangle",
                label: "tuebingen-thin-right",
                selector: { kind: TUEBINGEN_THIN_KIND, tile_family: TUEBINGEN_TILE_FAMILY, chirality_token: "right" },
                color: "#e1cdac",
            },
        ]),
    },
    {
        geometry: "robinson-triangles",
        variants: Object.freeze([
            {
                geometry: "robinson-triangles",
                label: "robinson-thick",
                selector: { kind: ROBINSON_THICK_KIND, tile_family: ROBINSON_TILE_FAMILY },
                color: "#f8f1e5",
            },
            {
                geometry: "robinson-triangles",
                label: "robinson-thin",
                selector: { kind: ROBINSON_THIN_KIND, tile_family: ROBINSON_TILE_FAMILY },
                color: "#d5bb8f",
            },
        ]),
    },
    {
        geometry: "hat-monotile",
        variants: Object.freeze([
            {
                geometry: "hat-monotile",
                label: "hat-left",
                selector: { tile_family: HAT_TILE_FAMILY, chirality_token: "left" },
                color: "#f8f1e5",
            },
            {
                geometry: "hat-monotile",
                label: "hat-right",
                selector: { tile_family: HAT_TILE_FAMILY, chirality_token: "right" },
                color: "#c88d4b",
            },
        ]),
    },
    {
        geometry: "chair",
        variants: Object.freeze([
            {
                geometry: "chair",
                label: "chair-0",
                selector: { kind: CHAIR_KIND, orientation_token: "0" },
                color: "#f8f1e5",
            },
            {
                geometry: "chair",
                label: "chair-1",
                selector: { kind: CHAIR_KIND, orientation_token: "1" },
                color: "#e5c089",
            },
            {
                geometry: "chair",
                label: "chair-2",
                selector: { kind: CHAIR_KIND, orientation_token: "2" },
                color: "#c88d4b",
            },
            {
                geometry: "chair",
                label: "chair-3",
                selector: { kind: CHAIR_KIND, orientation_token: "3" },
                color: "#dbc1b2",
            },
        ]),
    },
    {
        geometry: "dodecagonal-square-triangle",
        variants: Object.freeze([
            {
                geometry: "dodecagonal-square-triangle",
                label: "dst-square-blue",
                selector: {
                    kind: DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                    tile_family: DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
                    chirality_token: "blue",
                },
                color: "#f8f1e5",
            },
            {
                geometry: "dodecagonal-square-triangle",
                label: "dst-square-red",
                selector: {
                    kind: DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                    tile_family: DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
                    chirality_token: "red",
                },
                color: "#ead6b6",
            },
            {
                geometry: "dodecagonal-square-triangle",
                label: "dst-square-yellow",
                selector: {
                    kind: DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
                    tile_family: DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
                    chirality_token: "yellow",
                },
                color: "#d5bb8f",
            },
            {
                geometry: "dodecagonal-square-triangle",
                label: "dst-triangle-blue",
                selector: {
                    kind: DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                    tile_family: DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
                    chirality_token: "blue",
                },
                color: "#efe4d0",
            },
            {
                geometry: "dodecagonal-square-triangle",
                label: "dst-triangle-red",
                selector: {
                    kind: DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                    tile_family: DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
                    chirality_token: "red",
                },
                color: "#e1cdac",
            },
            {
                geometry: "dodecagonal-square-triangle",
                label: "dst-triangle-yellow",
                selector: {
                    kind: DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
                    tile_family: DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
                    chirality_token: "yellow",
                },
                color: "#c88d4b",
            },
        ]),
    },
    {
        geometry: "pinwheel",
        variants: Object.freeze([
            {
                geometry: "pinwheel",
                label: "pinwheel-left",
                selector: { tile_family: PINWHEEL_TILE_FAMILY, chirality_token: "left" },
                color: "#efe4d0",
            },
            {
                geometry: "pinwheel",
                label: "pinwheel-right",
                selector: { tile_family: PINWHEEL_TILE_FAMILY, chirality_token: "right" },
                color: "#d5bb8f",
            },
        ]),
    },
    {
        geometry: "shield",
        variants: Object.freeze([
            {
                geometry: "shield",
                label: "shield-shield",
                selector: { kind: SHIELD_SHIELD_KIND, tile_family: SHIELD_TILE_FAMILY },
                color: tokenColor("deadAlt"),
            },
            {
                geometry: "shield",
                label: "shield-square",
                selector: { kind: SHIELD_SQUARE_KIND, tile_family: SHIELD_TILE_FAMILY },
                color: tokenColor("dead"),
            },
            {
                geometry: "shield",
                label: "shield-triangle",
                selector: { kind: SHIELD_TRIANGLE_KIND, tile_family: SHIELD_TILE_FAMILY },
                color: tokenColor("accentStrong"),
            },
        ]),
    },
]);

export const FAMILY_DEAD_PALETTE_VARIANTS: readonly FamilyDeadPaletteVariantDefinition[] = Object.freeze(
    FAMILY_DEAD_PALETTE_REGISTRY.flatMap((familyPalette) => familyPalette.variants),
);

export function resolveDeadPaletteColorSpec(
    color: DeadPaletteColorSpec,
    fallbackColors: CanvasColors = DEFAULT_COLORS,
): string {
    if (typeof color === "string") {
        return color;
    }
    return fallbackColors[color.token];
}

export function matchesFamilyDeadPaletteVariant(
    cell: TopologyCell | null | undefined,
    variant: FamilyDeadPaletteVariantDefinition,
): boolean {
    if (!cell) {
        return false;
    }
    const selectorEntries = Object.entries(variant.selector) as Array<
        [keyof FamilyDeadPaletteVariantSelector, string | undefined]
    >;
    return selectorEntries.every(([field, expectedValue]) => {
        if (expectedValue === undefined) {
            return true;
        }
        return cell[field] === expectedValue;
    });
}

export function resolveRegisteredFamilyDeadColor(
    cell: TopologyCell | null | undefined,
    fallbackColors: CanvasColors = DEFAULT_COLORS,
): string | null {
    for (const variant of FAMILY_DEAD_PALETTE_VARIANTS) {
        if (matchesFamilyDeadPaletteVariant(cell, variant)) {
            return resolveDeadPaletteColorSpec(variant.color, fallbackColors);
        }
    }
    return null;
}

export function buildFamilyDeadPaletteTestCell(
    variant: FamilyDeadPaletteVariantDefinition,
): TopologyCell & { state: number } {
    return {
        id: variant.label,
        state: 0,
        kind: variant.selector.kind || "palette-test-cell",
        neighbors: [],
        ...(variant.selector.tile_family ? { tile_family: variant.selector.tile_family } : {}),
        ...(variant.selector.chirality_token ? { chirality_token: variant.selector.chirality_token } : {}),
        ...(variant.selector.orientation_token ? { orientation_token: variant.selector.orientation_token } : {}),
    };
}
