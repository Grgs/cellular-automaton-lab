import type {
    AdjacencyModeOption,
    BootstrappedTopologyDefinition,
    SizingControl,
    SizingPolicy,
    TopologyDefinition,
    TopologyOption,
    TopologySpec,
} from "./types/domain.js";

function normalizeSizingPolicy(definition: Pick<TopologyDefinition, "sizing_mode" | "sizing_policy">): Readonly<SizingPolicy> {
    const sizingMode = definition.sizing_mode;
    const fallbackControl: SizingPolicy["control"] = sizingMode === "patch_depth"
        ? "patch_depth"
        : "cell_size";
    const policy = definition.sizing_policy;
    const control: SizingControl = String(policy.control) === "patch_depth"
        ? "patch_depth"
        : "cell_size";
    return Object.freeze({
        control,
        default: Number(policy.default),
        min: Number(policy.min),
        max: Number(policy.max),
    });
}

function normalizeTopologyDefinition(definition: BootstrappedTopologyDefinition): Readonly<TopologyDefinition> {
    const supportedAdjacencyModes = definition.supported_adjacency_modes.map((value) => String(value));
    return Object.freeze({
        tiling_family: definition.tiling_family,
        label: definition.label,
        picker_group: definition.picker_group,
        picker_order: definition.picker_order,
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

export function getTopologyDefinition(tilingFamily: string | null | undefined): TopologyDefinition | null {
    return TOPOLOGY_BY_FAMILY.get(String(tilingFamily)) ?? null;
}

export function getTopologySizingPolicy(tilingFamily: string | null | undefined): Readonly<SizingPolicy> {
    const definition = getTopologyDefinition(tilingFamily) ?? getTopologyDefinition("square");
    if (!definition) {
        throw new Error("Missing bootstrapped square topology definition.");
    }
    return definition.sizing_policy;
}

export function isSupportedTopologyFamily(tilingFamily: string | null | undefined): boolean {
    return TOPOLOGY_BY_FAMILY.has(String(tilingFamily));
}

export function resolveAdjacencyMode(
    tilingFamily: string | null | undefined,
    adjacencyMode: string | null = null,
): string {
    const definition = getTopologyDefinition(tilingFamily);
    if (!definition) {
        return "edge";
    }
    const normalized = String(adjacencyMode ?? "");
    if (definition.supported_adjacency_modes.includes(normalized)) {
        return normalized;
    }
    return definition.default_adjacency_mode;
}

export function resolveTopologyVariantKey(
    tilingFamily: string | null | undefined,
    adjacencyMode: string | null = null,
): string {
    const definition = getTopologyDefinition(tilingFamily);
    if (!definition) {
        return "square";
    }
    const resolvedAdjacencyMode = resolveAdjacencyMode(tilingFamily, adjacencyMode);
    return definition.geometry_keys[resolvedAdjacencyMode]
        || definition.geometry_keys[definition.default_adjacency_mode]
        || "square";
}

export function describeTopologySpec(topologySpec: Partial<TopologySpec> = {}): TopologySpec {
    const tilingFamily = String(topologySpec.tiling_family || "square");
    const adjacencyMode = resolveAdjacencyMode(tilingFamily, topologySpec.adjacency_mode || null);
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

export function tilingFamilyOptions(): TopologyOption[] {
    return FRONTEND_TOPOLOGY_CATALOG
        .slice()
        .sort((left, right) => (
            left.picker_order - right.picker_order
            || left.label.localeCompare(right.label)
        ))
        .map((definition) => ({
        value: definition.tiling_family,
        label: definition.label,
        group: definition.picker_group,
        order: definition.picker_order,
    }));
}

export function adjacencyModeOptions(tilingFamily: string | null | undefined): AdjacencyModeOption[] {
    const definition = getTopologyDefinition(tilingFamily);
    if (!definition) {
        return [];
    }
    return definition.supported_adjacency_modes.map((mode) => ({
        value: mode,
        label: mode.charAt(0).toUpperCase() + mode.slice(1),
    }));
}
