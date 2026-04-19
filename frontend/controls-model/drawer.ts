import { buildDrawerInspectorViewModel } from "./drawer-inspector.js";
import { buildDrawerPatternViewModel } from "./drawer-patterns.js";
import { buildDrawerRulePaletteViewModel } from "./drawer-rule-palette.js";
import { buildDrawerShellViewModel } from "./drawer-shell.js";
import { buildDrawerTopologyViewModel } from "./drawer-topology.js";
import type { ResolvedPresetSelection } from "../types/domain.js";
import type {
    ControlsModelRuleContext,
    DrawerViewModel,
    SelectionInspectorSource,
} from "../types/ui.js";

export function buildDrawerViewModel({
    state,
    syncState,
    activeRule,
    paletteRule,
    presetSelection,
    selectionInspectorSource,
}: ControlsModelRuleContext & {
    presetSelection: ResolvedPresetSelection;
    selectionInspectorSource: SelectionInspectorSource;
}): DrawerViewModel {
    return {
        ...buildDrawerShellViewModel({
            state,
            activeRule,
        }),
        ...buildDrawerInspectorViewModel({
            state,
            activeRule,
            selectionInspectorSource,
        }),
        ...buildDrawerTopologyViewModel({
            state,
            syncState,
        }),
        ...buildDrawerRulePaletteViewModel({
            state,
            paletteRule,
        }),
        ...buildDrawerPatternViewModel({
            state,
            activeRule,
            paletteRule,
            presetSelection,
        }),
    };
}
