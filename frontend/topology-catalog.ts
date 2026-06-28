import type {
    AdjacencyModeOption,
    BootstrappedTopologyDefinition,
    SizingControl,
    SizingPolicy,
    TopologyDefinition,
    TopologyOption,
    TopologySpec,
} from "./types/domain.js";
import { getAperiodicFamilyMetadata } from "./aperiodic-family-registry.js";

function normalizeSizingPolicy(
    definition: Pick<TopologyDefinition, "sizing_mode" | "sizing_policy">,
): Readonly<SizingPolicy> {
    const policy = definition.sizing_policy;
    const control: SizingControl =
        String(policy.control) === "patch_depth" ? "patch_depth" : "cell_size";
    const normalized: SizingPolicy = {
        control,
        default: Number(policy.default),
        min: Number(policy.min),
        max: Number(policy.max),
    };
    const unsafeMax = Number(policy.unsafe_max);
    if (Number.isFinite(unsafeMax)) {
        normalized.unsafe_max = unsafeMax;
    }
    return Object.freeze(normalized);
}

function normalizeTopologyDefinition(
    definition: BootstrappedTopologyDefinition,
): Readonly<TopologyDefinition> {
    const supportedAdjacencyModes = definition.supported_adjacency_modes.map((value) =>
        String(value),
    );
    return Object.freeze({
        tiling_family: definition.tiling_family,
        label: definition.label,
        picker_group: definition.picker_group,
        picker_order: definition.picker_order,
        mode_type: definition.mode_type || "adjacency",
        mode_label: definition.mode_label || "Mode",
        mode_labels: Object.freeze({ ...(definition.mode_labels || {}) }),
        sizing_mode: definition.sizing_mode,
        family: definition.family,
        render_kind: definition.render_kind,
        viewport_sync_mode: definition.viewport_sync_mode,
        supported_adjacency_modes: Object.freeze(supportedAdjacencyModes),
        default_adjacency_mode: definition.default_adjacency_mode,
        default_rules: Object.freeze({ ...definition.default_rules }),
        geometry_keys: Object.freeze({ ...definition.geometry_keys }),
        sizing_policy: normalizeSizingPolicy(definition),
    });
}

function bootstrappedTopologyCatalog(): readonly TopologyDefinition[] {
    const bootstrapped = window.APP_TOPOLOGIES;
    if (bootstrapped.length === 0) {
        throw new Error("Missing bootstrapped topology catalog.");
    }
    return Object.freeze(bootstrapped.map(normalizeTopologyDefinition));
}

export const FRONTEND_TOPOLOGY_CATALOG = bootstrappedTopologyCatalog();

const TOPOLOGY_BY_FAMILY = new Map<string, TopologyDefinition>(
    FRONTEND_TOPOLOGY_CATALOG.map((definition) => [definition.tiling_family, definition]),
);

const PENROSE_P1_FAMILY = "penrose-p1";
type TopologyFamilyAlias = Readonly<{
    tiling_family: string;
    adjacency_mode: string;
}>;
const LEGACY_TOPOLOGY_FAMILY_ALIASES: Readonly<Record<string, TopologyFamilyAlias>> = {
    "penrose-p1-pentagon-diamond": Object.freeze({
        tiling_family: PENROSE_P1_FAMILY,
        adjacency_mode: "distributed",
    }),
    "penrose-p1-pentagon-boat-star": Object.freeze({
        tiling_family: PENROSE_P1_FAMILY,
        adjacency_mode: "boat-star",
    }),
};

function canonicalizeTopologyIdentity(
    tilingFamily: string | null | undefined,
    adjacencyMode: string | null = null,
): { tilingFamily: string; adjacencyMode: string | null } {
    const normalizedFamily = String(tilingFamily || "");
    const alias = LEGACY_TOPOLOGY_FAMILY_ALIASES[normalizedFamily];
    if (!alias) {
        return {
            tilingFamily: normalizedFamily,
            adjacencyMode,
        };
    }
    return {
        tilingFamily: alias.tiling_family,
        adjacencyMode: alias.adjacency_mode,
    };
}

function definitionFromSpecOrFamily(
    topologySpecOrFamily: string | Partial<TopologySpec> | null | undefined,
): TopologyDefinition | null {
    if (typeof topologySpecOrFamily === "string") {
        return getTopologyDefinition(topologySpecOrFamily);
    }
    return getTopologyDefinition(topologySpecOrFamily?.tiling_family);
}

export function listTopologyDefinitions(): readonly TopologyDefinition[] {
    return FRONTEND_TOPOLOGY_CATALOG;
}

export function getTopologyDefinition(
    tilingFamily: string | null | undefined,
): TopologyDefinition | null {
    const canonical = canonicalizeTopologyIdentity(tilingFamily);
    return TOPOLOGY_BY_FAMILY.get(canonical.tilingFamily) ?? null;
}

export function getTopologySizingPolicy(
    tilingFamily: string | null | undefined,
): Readonly<SizingPolicy> {
    const definition = getTopologyDefinition(tilingFamily) ?? getTopologyDefinition("square");
    if (!definition) {
        throw new Error("Missing bootstrapped square topology definition.");
    }
    return definition.sizing_policy;
}

export function isSupportedTopologyFamily(tilingFamily: string | null | undefined): boolean {
    const canonical = canonicalizeTopologyIdentity(tilingFamily);
    return TOPOLOGY_BY_FAMILY.has(canonical.tilingFamily);
}

export function resolveAdjacencyMode(
    tilingFamily: string | null | undefined,
    adjacencyMode: string | null = null,
): string {
    const canonical = canonicalizeTopologyIdentity(tilingFamily, adjacencyMode);
    const definition = getTopologyDefinition(canonical.tilingFamily);
    if (!definition) {
        return "edge";
    }
    const normalized = String(canonical.adjacencyMode ?? "");
    if (definition.supported_adjacency_modes.includes(normalized)) {
        return normalized;
    }
    return definition.default_adjacency_mode;
}

export function resolveTopologyVariantKey(
    tilingFamily: string | null | undefined,
    adjacencyMode: string | null = null,
): string {
    const canonical = canonicalizeTopologyIdentity(tilingFamily, adjacencyMode);
    const definition = getTopologyDefinition(canonical.tilingFamily);
    if (!definition) {
        return "square";
    }
    const resolvedAdjacencyMode = resolveAdjacencyMode(
        canonical.tilingFamily,
        canonical.adjacencyMode,
    );
    return (
        definition.geometry_keys[resolvedAdjacencyMode] ||
        definition.geometry_keys[definition.default_adjacency_mode] ||
        "square"
    );
}

export function describeTopologySpec(topologySpec: Partial<TopologySpec> = {}): TopologySpec {
    const canonical = canonicalizeTopologyIdentity(
        topologySpec.tiling_family || "square",
        topologySpec.adjacency_mode || null,
    );
    const tilingFamily = canonical.tilingFamily;
    const adjacencyMode = resolveAdjacencyMode(tilingFamily, canonical.adjacencyMode);
    const definition = getTopologyDefinition(tilingFamily) || getTopologyDefinition("square");
    return {
        tiling_family: tilingFamily,
        adjacency_mode: adjacencyMode,
        sizing_mode: definition?.sizing_mode || "grid",
        width: Number(topologySpec.width) || 0,
        height: Number(topologySpec.height) || 0,
        patch_depth: Number(topologySpec.patch_depth) || 0,
    };
}

export function topologyUsesPatchDepth(
    topologySpecOrFamily: string | Partial<TopologySpec> | null | undefined,
    adjacencyMode: string | null = null,
): boolean {
    void adjacencyMode;
    const definition = definitionFromSpecOrFamily(topologySpecOrFamily);
    return definition?.sizing_mode === "patch_depth";
}

export function topologyUsesBackendViewportSync(
    topologySpecOrFamily: string | Partial<TopologySpec> | null | undefined,
): boolean {
    const definition = definitionFromSpecOrFamily(topologySpecOrFamily);
    return definition?.viewport_sync_mode === "backend-sync";
}

export function isPenroseTilingFamily(tilingFamily: string | null | undefined): boolean {
    return String(tilingFamily) === "penrose-p3-rhombs";
}

export function topologyVariantKeyFromSpec(topologySpec: Partial<TopologySpec> = {}): string {
    return resolveTopologyVariantKey(topologySpec.tiling_family, topologySpec.adjacency_mode);
}

function fallbackTopologyModeLabel(definition: TopologyDefinition | null, mode: string): string {
    const formattedMode = `${mode.charAt(0).toUpperCase()}${mode.slice(1)}`;
    if ((definition?.mode_type || "adjacency") === "adjacency") {
        return `${formattedMode} adjacency`;
    }
    return formattedMode;
}

export function topologyModeLabel(
    tilingFamily: string | null | undefined,
    mode: string | null | undefined,
): string {
    const normalizedMode = String(mode || "edge");
    const definition = getTopologyDefinition(tilingFamily);
    const catalogLabel = definition?.mode_labels?.[normalizedMode];
    if (catalogLabel) {
        return catalogLabel;
    }
    return fallbackTopologyModeLabel(definition, normalizedMode);
}

export function topologyModeFieldLabel(tilingFamily: string | null | undefined): string {
    return getTopologyDefinition(tilingFamily)?.mode_label || "Mode";
}

// Search aliases favor terms a newcomer might try after recognizing shapes
// in the picker preview, not just the formal catalog names.
const TILING_SEARCH_ALIASES: Readonly<Record<string, readonly string[]>> = {
    square: ["quadrilateral", "checkerboard", "grid", "lattice", "cartesian"],
    hex: ["hexagon", "hexagons", "honeycomb", "hexagonal grid", "beehive"],
    triangle: ["triangles", "equilateral", "triangular grid"],
    "archimedean-4-8-8": [
        "archimedean",
        "semiregular",
        "uniform",
        "truncated square",
        "square octagon",
        "octagon",
        "octagons",
        "4 8 8",
        "488",
    ],
    "trihexagonal-3-6-3-6": [
        "archimedean",
        "semiregular",
        "uniform",
        "trihexagonal",
        "kagome",
        "triangle hexagon",
        "triangles hexagons",
        "3 6 3 6",
        "3636",
    ],
    "archimedean-3-12-12": [
        "archimedean",
        "semiregular",
        "uniform",
        "truncated hexagonal",
        "triangle dodecagon",
        "triangles dodecagons",
        "3 12 12",
        "31212",
    ],
    "archimedean-3-4-6-4": [
        "archimedean",
        "semiregular",
        "uniform",
        "rhombitrihexagonal",
        "triangle square hexagon",
        "triangles squares hexagons",
        "3 4 6 4",
        "3464",
    ],
    "archimedean-4-6-12": [
        "archimedean",
        "semiregular",
        "uniform",
        "truncated trihexagonal",
        "square hexagon dodecagon",
        "4 6 12",
        "4612",
    ],
    "archimedean-3-3-4-3-4": [
        "archimedean",
        "semiregular",
        "uniform",
        "snub square",
        "triangle square",
        "triangles squares",
        "3 3 4 3 4",
        "33434",
    ],
    "archimedean-3-3-3-4-4": [
        "archimedean",
        "semiregular",
        "uniform",
        "elongated triangular",
        "triangle square",
        "triangles squares",
        "3 3 3 4 4",
        "33344",
    ],
    "archimedean-3-3-3-3-6": [
        "archimedean",
        "semiregular",
        "uniform",
        "snub trihexagonal",
        "triangle hexagon",
        "triangles hexagons",
        "3 3 3 3 6",
        "33336",
    ],
    "cairo-pentagonal": ["pentagon", "pentagons", "pentagonal", "cairo"],
    rhombille: ["rhomb", "rhombs", "rhombus", "lozenge", "diamond", "diamonds"],
    "deltoidal-trihexagonal": ["dual", "deltoid", "kite", "kites", "trihexagonal"],
    "deltoidal-hexagonal": ["dual", "deltoid", "kite", "kites", "hexagonal"],
    "snub-square-dual": ["dual", "snub square", "pentagon", "pentagons"],
    kisrhombille: ["dual", "triangle square hexagon", "rhombille"],
    "tetrakis-square": ["dual", "square", "triangles", "kite", "kites"],
    tiltwork: ["diamond", "diamonds", "square", "triangles", "invented"],
    pythagorean: ["squares", "unequal squares", "two squares", "1 2", "theorem"],
    herringbone: ["brick", "bricks", "parquet", "zigzag"],
    "triangular-square-2uniform": [
        "2 uniform",
        "two uniform",
        "uniform",
        "triangle square",
        "triangles squares",
        "semiregular",
    ],
    "triakis-triangular": ["dual", "triangle", "triangles", "triangular"],
    basketweave: ["brick", "bricks", "woven", "weave", "parquet"],
    "pentagon-crosses": ["pentagon", "pentagons", "pentagonal", "cross", "crosses"],
    "trihex-2uniform-3636-3366": [
        "2 uniform",
        "two uniform",
        "uniform",
        "trihex",
        "trihexagonal",
        "triangle hexagon",
        "triangles hexagons",
        "3 6 3 6",
        "3 3 6 6",
        "3636",
        "3366",
    ],
    "stein-14-pentagonal": [
        "pentagon",
        "pentagons",
        "pentagonal",
        "monohedral",
        "convex pentagon",
        "stein",
        "type 14",
    ],
    "prismatic-pentagonal": ["pentagon", "pentagons", "pentagonal", "prism"],
    "floret-pentagonal": ["pentagon", "pentagons", "pentagonal", "flower"],
    "type-7-pentagonal": ["pentagon", "pentagons", "pentagonal", "type 7"],
    "penrose-p1": [
        "penrose",
        "p1",
        "pentagon",
        "pentagons",
        "distributed",
        "diamond",
        "diamonds",
        "boat",
        "boats",
        "star",
        "stars",
        "sun",
        "decagon",
    ],
    "penrose-p2-kite-dart": ["penrose", "p2", "kite", "kites", "dart", "darts"],
    "penrose-p3-rhombs": [
        "penrose",
        "p3",
        "rhomb",
        "rhombs",
        "rhombus",
        "rhombi",
        "fat skinny",
        "thick thin",
        "diamond",
        "diamonds",
    ],
    "ammann-beenker": ["octagonal", "octagon", "octagons", "rhomb", "rhombs", "square"],
    spectre: ["monotile", "einstein", "aperiodic monotile", "chiral", "vampire"],
    "hat-monotile": ["hat", "monotile", "einstein", "aperiodic monotile", "polykite", "turtle"],
    "taylor-socolar": ["hexagon", "hexagons", "half hex", "substitution"],
    sphinx: ["reptile", "substitution"],
    chair: ["l shape", "l-shaped", "substitution"],
    "robinson-triangles": ["triangle", "triangles", "thick thin", "substitution"],
    "tuebingen-triangle": ["tubingen", "triangle", "triangles", "thick thin", "substitution"],
    "dodecagonal-square-triangle": [
        "experimental",
        "dodecagonal",
        "12 fold",
        "square triangle",
        "squares triangles",
    ],
    shield: ["monotile", "shield", "square triangle", "substitution"],
    pinwheel: ["experimental", "triangle", "triangles", "right triangle", "affine"],
    "pinwheel-2-1": [
        "experimental",
        "triangle",
        "triangles",
        "right triangle",
        "two one",
        "2 1",
        "affine",
    ],
};

export function tilingFamilyOptions(): TopologyOption[] {
    return FRONTEND_TOPOLOGY_CATALOG.slice()
        .sort(
            (left, right) =>
                left.picker_order - right.picker_order || left.label.localeCompare(right.label),
        )
        .map((definition) => {
            const aperiodicMetadata = getAperiodicFamilyMetadata(definition.tiling_family);
            const label = aperiodicMetadata?.experimental
                ? `${definition.label} (Experimental)`
                : definition.label;
            const defaultPreviewKey =
                definition.geometry_keys[definition.default_adjacency_mode] ||
                Object.values(definition.geometry_keys)[0] ||
                definition.tiling_family;
            const previewKey =
                definition.tiling_family === PENROSE_P1_FAMILY
                    ? definition.tiling_family
                    : defaultPreviewKey;
            return {
                value: definition.tiling_family,
                label,
                group: definition.picker_group,
                order: definition.picker_order,
                family: definition.family,
                previewKey,
                renderKind: definition.render_kind,
                sizingMode: definition.sizing_mode,
                searchAliases: TILING_SEARCH_ALIASES[definition.tiling_family] ?? [],
            };
        });
}

export function topologyModeOptions(
    tilingFamily: string | null | undefined,
): AdjacencyModeOption[] {
    const definition = getTopologyDefinition(tilingFamily);
    if (!definition) {
        return [];
    }
    return definition.supported_adjacency_modes.map((mode) => ({
        value: mode,
        label: topologyModeLabel(tilingFamily, mode),
    }));
}

export function adjacencyModeOptions(
    tilingFamily: string | null | undefined,
): AdjacencyModeOption[] {
    return topologyModeOptions(tilingFamily);
}
