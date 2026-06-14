import type { RuleDefinition } from "./types/domain.js";

export function ruleSupportsTilingFamily(
    rule: RuleDefinition | null | undefined,
    tilingFamily: string | null | undefined,
): boolean {
    if (!rule || !tilingFamily) {
        return true;
    }
    const compatibleFamilies = rule.compatible_tiling_families;
    return compatibleFamilies === null || compatibleFamilies.includes(tilingFamily);
}

export function compatibleTilingFamiliesLabel(rule: RuleDefinition): string {
    return rule.compatible_tiling_families?.join(", ") ?? "all tilings";
}
