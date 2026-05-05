import {
    buildDrawerToggleState,
    buildOverlayVisibilityState,
    buildQuickStartHintState,
    resolveBlockingActivity,
    resolvePatternStatus,
} from "./shared.js";
import type { RuleDefinition } from "../types/domain.js";
import type { AppState } from "../types/state.js";
import type { DrawerShellViewModel } from "../types/ui.js";

export function buildDrawerShellViewModel({
    state,
    activeRule,
}: {
    state: AppState;
    activeRule: RuleDefinition | null;
}): DrawerShellViewModel {
    const overlayVisibility = buildOverlayVisibilityState(state);
    const { drawerToggleLabel, drawerToggleTitle } = buildDrawerToggleState(state);
    const blockingActivity = resolveBlockingActivity(state);
    const patternStatus = resolvePatternStatus(state);
    const quickStartHint = buildQuickStartHintState(state, activeRule);

    return {
        drawerVisible: overlayVisibility.drawerVisible,
        backdropVisible: overlayVisibility.backdropVisible,
        drawerToggleLabel,
        drawerToggleTitle,
        quickStartHintText: quickStartHint.quickStartHintText,
        quickStartHintVisible:
            quickStartHint.quickStartHintVisible && patternStatus.patternStatusText === "",
        ...blockingActivity,
        ...patternStatus,
    };
}
