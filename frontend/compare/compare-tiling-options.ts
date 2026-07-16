import type { AppBootstrapData, TopologyOption } from "../types/domain.js";

export interface CompareTilingOption {
    geometry: string;
    tilingFamily: string;
    label: string;
    family: string;
    group: string;
    order: number;
    renderKind: string;
    sizingMode: string;
}

export function comparisonTilingOptions(bootstrapData: AppBootstrapData): CompareTilingOption[] {
    return bootstrapData.topology_catalog
        .map((definition) => ({
            geometry: definition.geometry_keys[definition.default_adjacency_mode] ?? "",
            tilingFamily: definition.tiling_family,
            label: definition.label,
            family: definition.family,
            group: definition.picker_group,
            order: definition.picker_order,
            renderKind: definition.render_kind,
            sizingMode: definition.sizing_mode,
        }))
        .filter((option): option is CompareTilingOption => option.geometry.length > 0);
}

export function wallTilingPickerOptions(options: readonly CompareTilingOption[]): TopologyOption[] {
    return options.map((option) => ({
        value: option.geometry,
        label: option.label,
        group: option.group,
        order: option.order,
        family: option.family,
        previewKey: option.geometry,
        renderKind: option.renderKind,
        sizingMode: option.sizingMode,
        searchAliases: [],
    }));
}

export function defaultComparisonSelection(options: CompareTilingOption[]): Set<string> {
    const selection = new Set<string>();
    const seenFamilies = new Set<string>();
    for (const option of options) {
        if (option.family === "regular") selection.add(option.geometry);
        else if (!seenFamilies.has(option.family)) {
            seenFamilies.add(option.family);
            selection.add(option.geometry);
        }
    }
    return selection;
}
