import { getTopologyFamilyMetadata } from "../topology-family-metadata.js";
import type { BootstrappedTopologyDefinition, SizingPolicy } from "../types/domain.js";

type VariantFields = Pick<
    BootstrappedTopologyDefinition,
    | "render_kind"
    | "supported_adjacency_modes"
    | "default_adjacency_mode"
    | "default_rules"
    | "geometry_keys"
    | "sizing_policy"
>;

function requireTopologyFamilyMetadata(tilingFamily: string) {
    const metadata = getTopologyFamilyMetadata(tilingFamily);
    if (!metadata) {
        throw new Error(`Missing topology family metadata for "${tilingFamily}".`);
    }
    return metadata;
}

export function buildBootstrappedTopologyDefinition(
    tilingFamily: string,
    variantFields: VariantFields,
): BootstrappedTopologyDefinition {
    const metadata = requireTopologyFamilyMetadata(tilingFamily);
    return {
        tiling_family: tilingFamily,
        label: metadata.label,
        picker_group: metadata.pickerGroup,
        picker_order: metadata.pickerOrder,
        sizing_mode: metadata.sizingMode,
        family: metadata.family,
        viewport_sync_mode: metadata.viewportSyncMode,
        ...variantFields,
    };
}

export function buildSingleVariantBootstrappedTopologyDefinition(
    tilingFamily: string,
    {
        geometryKey,
        renderKind,
        defaultRule,
        sizingPolicy,
        adjacencyMode = "edge",
    }: {
        geometryKey: string;
        renderKind: BootstrappedTopologyDefinition["render_kind"];
        defaultRule: string;
        sizingPolicy: Readonly<SizingPolicy>;
        adjacencyMode?: string;
    },
): BootstrappedTopologyDefinition {
    return buildBootstrappedTopologyDefinition(tilingFamily, {
        render_kind: renderKind,
        supported_adjacency_modes: [adjacencyMode],
        default_adjacency_mode: adjacencyMode,
        default_rules: { [adjacencyMode]: defaultRule },
        geometry_keys: { [adjacencyMode]: geometryKey },
        sizing_policy: sizingPolicy,
    });
}
