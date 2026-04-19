import { describeAperiodicFamilyStatus } from "../aperiodic-family-registry.js";
import { getTopologyDefinition } from "../topology-catalog.js";
import { buildSelectionInspectorViewModel } from "./selection-inspector.js";
import type { RuleDefinition } from "../types/domain.js";
import type { AppState } from "../types/state.js";
import type {
    DrawerInspectorViewModel,
    SelectionInspectorSource,
} from "../types/ui.js";

export function buildDrawerInspectorViewModel({
    state,
    activeRule,
    selectionInspectorSource,
}: {
    state: AppState;
    activeRule: RuleDefinition | null;
    selectionInspectorSource: SelectionInspectorSource;
}): DrawerInspectorViewModel {
    const tilingFamily = state.topologySpec?.tiling_family || "square";
    const topologyDefinition = getTopologyDefinition(tilingFamily);
    const topologyStatus = describeAperiodicFamilyStatus(tilingFamily);

    return {
        inspectorTilingText: topologyDefinition?.label || tilingFamily,
        inspectorRuleText: activeRule?.display_name || activeRule?.label || "Choose a rule",
        topologyStatusVisible: topologyStatus !== null,
        topologyStatusLabel: topologyStatus?.label || "",
        topologyStatusDetail: topologyStatus?.detail || "",
        topologyStatusTone: topologyStatus?.tone || "info",
        selectionInspector: buildSelectionInspectorViewModel({
            selectedCells: selectionInspectorSource.selectedCells,
            topologyIndex: state.topologyIndex,
            cellStates: state.cellStates,
            activeRule,
        }),
    };
}
