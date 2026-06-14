import type { RuleDefinition } from "../types/domain.js";
import type { AppState } from "../types/state.js";
import type { DrawerRulePaletteViewModel, RuleSelectOption } from "../types/ui.js";
import { compatibleTilingFamiliesLabel, ruleSupportsTilingFamily } from "../rule-compatibility.js";

function lifeNotationAliases(...values: Array<string | null | undefined>): string[] {
    return values.flatMap((value) => {
        const matches = String(value ?? "").match(/\bB\d+\/S\d+\b/gi) ?? [];
        return matches.flatMap((match) => [match, match.replace(/[^a-z0-9]+/gi, "")]);
    });
}

function ruleIntentAliases(rule: RuleDefinition): string[] {
    const haystack = [
        rule.name,
        rule.display_name,
        rule.label,
        rule.description,
        ...(Array.isArray(rule.states) ? rule.states.map((cellState) => cellState.label) : []),
    ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
    const aliases: string[] = [
        "cellular automaton",
        "automata",
        ...lifeNotationAliases(rule.display_name, rule.label, rule.description, rule.name),
    ];
    if (haystack.includes("life")) {
        aliases.push("life like", "lifelike", "birth survival", "born survive");
    }
    if (haystack.includes("conway")) {
        aliases.push("game of life", "gol", "classic life", "glider");
    }
    if (haystack.includes("highlife")) {
        aliases.push("replicator", "replicators", "self replicating", "life variant");
    }
    if (haystack.includes("wireworld")) {
        aliases.push("wire", "wires", "circuit", "circuits", "logic", "electron", "signal");
    }
    if (haystack.includes("greenberg") || haystack.includes("hastings")) {
        aliases.push("excitable", "wave", "waves", "cyclic", "refractory", "oscillator");
    }
    if (haystack.includes("hex")) {
        aliases.push("hexagonal", "hexagon", "honeycomb");
    }
    if (haystack.includes("tri")) {
        aliases.push("triangular", "triangle");
    }
    if (haystack.includes("mixed")) {
        aliases.push("archimedean", "uniform tiling", "multi tile", "periodic mixed");
    }
    return aliases;
}

export function buildDrawerRulePaletteViewModel({
    state,
    paletteRule,
}: {
    state: AppState;
    paletteRule: RuleDefinition | null;
}): DrawerRulePaletteViewModel {
    const availableRules = Array.isArray(state.rules) ? state.rules : [];
    const tilingFamily = state.topologySpec?.tiling_family ?? null;
    const compatibleRules = availableRules.filter((rule) =>
        ruleSupportsTilingFamily(rule, tilingFamily),
    );
    const paletteRuleIsUnsupported =
        Boolean(paletteRule) && !ruleSupportsTilingFamily(paletteRule, tilingFamily);

    function buildRuleOption(rule: RuleDefinition, disabled = false): RuleSelectOption {
        const displayName = rule.display_name || rule.label || rule.name;
        const unsupportedText =
            disabled && tilingFamily
                ? `Unsupported on ${tilingFamily}; supports ${compatibleTilingFamiliesLabel(rule)}`
                : "";
        return {
            name: rule.name,
            displayName: disabled ? `${displayName} (unsupported on this tiling)` : displayName,
            description: [rule.description ?? "", unsupportedText].filter(Boolean).join(" "),
            searchText: [
                rule.name,
                rule.display_name,
                rule.label,
                rule.description,
                unsupportedText,
                ...(Array.isArray(rule.states)
                    ? rule.states.map((cellState) => cellState.label)
                    : []),
                ...ruleIntentAliases(rule),
            ]
                .filter(Boolean)
                .join(" "),
            ...(disabled ? { disabled: true } : {}),
        };
    }

    const ruleOptions = compatibleRules.map((rule) => buildRuleOption(rule));
    if (
        paletteRule &&
        paletteRuleIsUnsupported &&
        !ruleOptions.some((rule) => rule.name === paletteRule.name)
    ) {
        ruleOptions.unshift(buildRuleOption(paletteRule, true));
    }

    return {
        ruleSummaryText:
            paletteRule?.description ||
            "Select a rule to see its evolution notes and paint states.",
        ruleSelectValue: paletteRule ? paletteRule.name : "",
        ruleOptions,
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
