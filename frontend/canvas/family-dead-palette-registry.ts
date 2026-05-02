import familyDeadPaletteManifest from "./family-dead-palette-manifest.json";
import { DEFAULT_COLORS } from "./theme-colors.js";
import type { CanvasColors } from "../types/rendering.js";
import type { TopologyCell } from "../types/domain.js";

export type DeadPaletteColorToken =
    | "dead"
    | "deadAlt"
    | "accent"
    | "accentStrong"
    | "toneCream"
    | "toneLinen"
    | "toneSand"
    | "toneFlax"
    | "toneTan"
    | "toneStone"
    | "toneRose"
    | "toneClay"
    | "toneShadow";

export type DeadPaletteColorSpec = string | { token: DeadPaletteColorToken };

export interface FamilyDeadPaletteVariantSelector {
    kind?: string;
    tile_family?: string;
    chirality_token?: string;
    orientation_token?: string;
}

export interface PaletteBrowserAliasCoverageDefinition {
    fixturePath: string;
    selectorFields: readonly (keyof FamilyDeadPaletteVariantSelector)[];
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
    browserAliasCoverage?: PaletteBrowserAliasCoverageDefinition;
    variants: readonly FamilyDeadPaletteVariantDefinition[];
}

interface FamilyDeadPaletteManifestFile {
    families: Array<{
        geometry: string;
        browserAliasCoverage?: {
            fixturePath: string;
            selectorFields: string[];
        };
        variants: Array<{
            label: string;
            selector: FamilyDeadPaletteVariantSelector;
            color: DeadPaletteColorSpec;
            allowSharedDeadColor?: boolean;
        }>;
    }>;
}

const manifest = familyDeadPaletteManifest as FamilyDeadPaletteManifestFile;

function asSelectorField(
    field: string,
): keyof FamilyDeadPaletteVariantSelector {
    return field as keyof FamilyDeadPaletteVariantSelector;
}

export const FAMILY_DEAD_PALETTE_REGISTRY: readonly FamilyDeadPaletteDefinition[] = Object.freeze(
    manifest.families.map((familyPalette) => ({
        geometry: familyPalette.geometry,
        ...(familyPalette.browserAliasCoverage
            ? {
                browserAliasCoverage: {
                    fixturePath: familyPalette.browserAliasCoverage.fixturePath,
                    selectorFields: Object.freeze(
                        familyPalette.browserAliasCoverage.selectorFields.map(asSelectorField),
                    ),
                } satisfies PaletteBrowserAliasCoverageDefinition,
            }
            : {}),
        variants: Object.freeze(
            familyPalette.variants.map((variant) => ({
                geometry: familyPalette.geometry,
                label: variant.label,
                selector: { ...variant.selector },
                color: typeof variant.color === "string"
                    ? variant.color
                    : { token: variant.color.token },
                ...(variant.allowSharedDeadColor ? { allowSharedDeadColor: variant.allowSharedDeadColor } : {}),
            })),
        ),
    })),
);

export const PALETTE_BROWSER_ALIAS_COVERAGE: readonly {
    geometry: string;
    fixturePath: string;
    selectorFields: readonly (keyof FamilyDeadPaletteVariantSelector)[];
}[] = Object.freeze(
    FAMILY_DEAD_PALETTE_REGISTRY.flatMap((familyPalette) => (
        familyPalette.browserAliasCoverage
            ? [{
                geometry: familyPalette.geometry,
                fixturePath: familyPalette.browserAliasCoverage.fixturePath,
                selectorFields: familyPalette.browserAliasCoverage.selectorFields,
            }]
            : []
    )),
);

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
