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
        implementation_status: definition.implementation_status,
        promotion_blocker: definition.promotion_blocker,
        public_cell_kinds: Object.freeze([...definition.public_cell_kinds]),
    });
}

function ensureAperiodicFamilyRegistry(): {
    families: readonly Readonly<BootstrappedAperiodicFamilyDefinition>[];
    byTilingFamily: ReadonlyMap<string, Readonly<BootstrappedAperiodicFamilyDefinition>>;
} {
    const bootstrapped = Array.isArray(window.APP_APERIODIC_FAMILIES)
        ? window.APP_APERIODIC_FAMILIES
        : [];
    if (cachedSource === bootstrapped && cachedFamilies !== null && cachedByTilingFamily !== null) {
        return {
            families: cachedFamilies,
            byTilingFamily: cachedByTilingFamily,
        };
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

function humanizeImplementationStatus(status: BootstrappedAperiodicFamilyDefinition["implementation_status"]): string {
    switch (status) {
        case "true_substitution":
            return "True substitution";
        case "exact_affine":
            return "Exact affine";
        case "canonical_patch":
            return "Canonical patch";
        case "known_deviation":
            return "Known deviation";
        default:
            return "Implementation status";
    }
}

export function describeAperiodicFamilyStatus(
    tilingFamily: string | null | undefined,
): {
    label: string;
    detail: string;
    tone: "info" | "warning";
    experimental: boolean;
} | null {
    const metadata = getAperiodicFamilyMetadata(tilingFamily);
    if (metadata === null) {
        return null;
    }
    if (metadata.experimental) {
        return {
            label: `Experimental • ${humanizeImplementationStatus(metadata.implementation_status)}`,
            detail: metadata.promotion_blocker || "This aperiodic family remains experimental.",
            tone: "warning",
            experimental: true,
        };
    }
    return {
        label: `Aperiodic • ${humanizeImplementationStatus(metadata.implementation_status)}`,
        detail: "Backend implementation and verification agree on this shipped aperiodic family.",
        tone: "info",
        experimental: false,
    };
}
