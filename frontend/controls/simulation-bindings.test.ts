import { describe, expect, it, vi } from "vitest";

import { bindSimulationControls } from "./simulation-bindings.js";
import { populateRules } from "./view-options.js";
import type { AppActionSet } from "../types/actions.js";
import type { DomElements } from "../types/dom.js";
import type { RuleSelectOption } from "../types/ui.js";

const RULES: RuleSelectOption[] = [
    {
        name: "conway",
        displayName: "Conway Life",
        description: "Classic binary survival rule.",
        searchText: "conway Conway Life classic binary survival dead live",
    },
    {
        name: "wireworld",
        displayName: "WireWorld",
        description: "Signal circuits with conductor wires.",
        searchText: "wireworld WireWorld signal circuits conductor electron head tail",
    },
];

describe("controls/simulation-bindings", () => {
    it("refreshes rule filter input without changing the selected rule", () => {
        const elements = {
            ruleSelect: document.createElement("select"),
            ruleSearchInput: document.createElement("input"),
            ruleSearchStatus: document.createElement("span"),
        } as Partial<DomElements> as DomElements;
        const actions = {
            changeRule: vi.fn(),
        } as Partial<AppActionSet> as AppActionSet;

        populateRules(elements, RULES, "conway");
        bindSimulationControls(elements, actions);

        elements.ruleSearchInput!.value = "wire";
        elements.ruleSearchInput!.dispatchEvent(new Event("input"));

        expect(Array.from(elements.ruleSelect!.options).map((option) => option.value)).toEqual([
            "conway",
            "wireworld",
        ]);
        expect(elements.ruleSelect?.value).toBe("conway");
        expect(actions.changeRule).not.toHaveBeenCalled();
    });
});
