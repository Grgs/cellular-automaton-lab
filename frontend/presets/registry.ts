import { HEX_PRESET_REGISTRY } from "./catalog-hex.js";
import { SQUARE_PRESET_REGISTRY } from "./catalog-square.js";
import type { PresetDefinition, PresetRegistry } from "../types/presets.js";

function mergePresetRegistries(...registries: readonly PresetRegistry[]): PresetRegistry {
    const merged: Record<string, PresetDefinition[]> = {};
    registries.forEach((registry) => {
        Object.entries(registry).forEach(([ruleName, presets]) => {
            merged[ruleName] = [...(merged[ruleName] ?? []), ...presets];
        });
    });
    return Object.freeze(
        Object.fromEntries(
            Object.entries(merged).map(([ruleName, presets]) => [ruleName, Object.freeze(presets)]),
        ),
    );
}

const PRESET_REGISTRY = mergePresetRegistries(
    SQUARE_PRESET_REGISTRY,
    HEX_PRESET_REGISTRY,
);

const PRESET_RULE_ALIASES = Object.freeze<Record<string, string>>({
    hexwhirlpool: "whirlpool",
});

export function listRulePresets(ruleName: string): readonly PresetDefinition[] {
    const resolvedRuleName = PRESET_RULE_ALIASES[ruleName] ?? ruleName;
    return PRESET_REGISTRY[resolvedRuleName] ?? [];
}
