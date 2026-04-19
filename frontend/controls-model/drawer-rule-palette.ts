import type { RuleDefinition } from "../types/domain.js";
import type { AppState } from "../types/state.js";
import type { DrawerRulePaletteViewModel } from "../types/ui.js";

export function buildDrawerRulePaletteViewModel({
    state,
    paletteRule,
}: {
    state: AppState;
    paletteRule: RuleDefinition | null;
}): DrawerRulePaletteViewModel {
    const availableRules = Array.isArray(state.rules) ? state.rules : [];

    return {
        ruleSummaryText: paletteRule?.description || "Select a rule to see its evolution notes and paint states.",
        ruleSelectValue: paletteRule ? paletteRule.name : "",
        ruleOptions: availableRules.map((rule) => ({
            name: rule.name,
            displayName: rule.display_name || rule.label || rule.name,
        })),
        ruleDescription: paletteRule?.description ?? "",
        paletteStates: Array.isArray(paletteRule?.states)
            ? paletteRule.states
                .filter((cellState) => cellState.paintable)
                .map((cellState) => ({
                    value: cellState.value,
                    label: cellState.label ?? `State ${cellState.value}`,
                    color: cellState.color ?? "",
                }))
            : [],
        selectedPaintState: state.selectedPaintState,
    };
}
