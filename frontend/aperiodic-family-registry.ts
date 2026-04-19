import type { BootstrappedAperiodicFamilyDefinition } from "./types/domain.js";

let cachedSource: ReadonlyArray<BootstrappedAperiodicFamilyDefinition> | null = null;
let cachedFamilies: readonly Readonly<BootstrappedAperiodicFamilyDefinition>[] | null = null;
let cachedByTilingFamily: ReadonlyMap<string, Readonly<BootstrappedAperiodicFamilyDefinition>> | null = null;

function normalizeAperiodicFamilyDefinition(
    definition: BootstrappedAperiodicFamilyDefinition,
): Readonly<BootstrappedAperiodicFamilyDefinition> {
    return Object.freeze({
        tiling_family: definition.tiling_family,
        label: definition.label,
        experimental: Boolean(definition.experimental),
        public_cell_kinds: Object.freeze([...definition.public_cell_kinds]),
    });
}

function ensureAperiodicFamilyRegistry(): {
    families: readonly Readonly<BootstrappedAperiodicFamilyDefinition>[];
    byTilingFamily: ReadonlyMap<string, Readonly<BootstrappedAperiodicFamilyDefinition>>;
} {
    const bootstrapped = window.APP_APERIODIC_FAMILIES;
    if (cachedSource === bootstrapped && cachedFamilies !== null && cachedByTilingFamily !== null) {
        return {
            families: cachedFamilies,
            byTilingFamily: cachedByTilingFamily,
        };
    }
    if (!Array.isArray(bootstrapped)) {
        throw new Error("Missing bootstrapped aperiodic family metadata.");
    }
    const families = Object.freeze(bootstrapped.map(normalizeAperiodicFamilyDefinition));
    const byTilingFamily = new Map(
        families.map((definition) => [definition.tiling_family, definition] as const),
    );
    cachedSource = bootstrapped;
    cachedFamilies = families;
    cachedByTilingFamily = byTilingFamily;
    return {
        families,
        byTilingFamily,
    };
}

export function listAperiodicFamilyMetadata(): readonly Readonly<BootstrappedAperiodicFamilyDefinition>[] {
    return ensureAperiodicFamilyRegistry().families;
}

export function getAperiodicFamilyMetadata(
    tilingFamily: string | null | undefined,
): Readonly<BootstrappedAperiodicFamilyDefinition> | null {
    return ensureAperiodicFamilyRegistry().byTilingFamily.get(String(tilingFamily)) ?? null;
}

export function isExperimentalAperiodicFamily(tilingFamily: string | null | undefined): boolean {
    return getAperiodicFamilyMetadata(tilingFamily)?.experimental === true;
}
