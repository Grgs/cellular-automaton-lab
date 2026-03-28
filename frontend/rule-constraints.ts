import type { ViewportDimensions } from "./types/controller.js";
import type { RuleDefinition } from "./types/domain.js";

export function ruleRequiresSquareDimensions(ruleOrName: RuleDefinition | string | null | undefined): boolean {
    void ruleOrName;
    return false;
}

export function normalizeRuleDimensions(
    ruleOrName: RuleDefinition | string | null | undefined,
    dimensions: Partial<ViewportDimensions> = {},
): ViewportDimensions {
    void ruleOrName;
    const width = Number(dimensions?.width);
    const height = Number(dimensions?.height);
    return {
        width: Number.isFinite(width) ? width : 0,
        height: Number.isFinite(height) ? height : 0,
    };
}
