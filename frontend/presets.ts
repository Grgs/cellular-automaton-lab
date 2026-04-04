import { uniqueCells } from "./presets/core.js";
import { listRulePresets } from "./presets/registry.js";
import type { PresetSeedBuildRequest } from "./types/actions.js";
import type { CartesianSeedCell, PresetBuildContext, PresetMetadata } from "./types/domain.js";

interface RulePresetDefinition extends PresetMetadata {
    supportedGeometry: string;
    minWidth: number;
    minHeight: number;
    build: (context: PresetBuildContext) => CartesianSeedCell[];
}

function withMetadata(preset: RulePresetDefinition): PresetMetadata {
    return {
        id: preset.id,
        label: preset.label,
        description: preset.description ?? null,
    };
}

function supportsDimensions(preset: RulePresetDefinition, width: number, height: number): boolean {
    return width >= preset.minWidth && height >= preset.minHeight;
}

export function listAvailablePresets(
    ruleName: string,
    geometry: string,
    width: number,
    height: number,
): PresetMetadata[] {
    return (listRulePresets(ruleName) as RulePresetDefinition[])
        .filter((preset) => preset.supportedGeometry === geometry)
        .filter((preset) => supportsDimensions(preset, width, height))
        .map(withMetadata);
}

export function getDefaultPresetId(
    ruleName: string,
    geometry: string,
    width: number,
    height: number,
): string | null {
    return listAvailablePresets(ruleName, geometry, width, height)[0]?.id ?? null;
}

export function buildPresetSeed({
    ruleName,
    geometry,
    width,
    height,
    presetId = null,
}: PresetSeedBuildRequest & { presetId?: string | null }): CartesianSeedCell[] {
    const rulePresets = (listRulePresets(ruleName) as RulePresetDefinition[])
        .filter((preset) => preset.supportedGeometry === geometry)
        .filter((preset) => supportsDimensions(preset, width, height));
    const preset = rulePresets.find((candidate) => candidate.id === presetId) ?? rulePresets[0];
    if (!preset) {
        return [];
    }
    return uniqueCells(preset.build({ width, height, geometry, presetId: preset.id }));
}
