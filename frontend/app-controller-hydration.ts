import { bindControls } from "./controls-bindings.js";
import type { AppActionSet } from "./types/actions.js";
import type { AppControllerSync } from "./types/controller-app.js";
import type { UiSessionController } from "./types/controller-sync-session.js";
import type { AppView, InteractionController, ViewportController } from "./types/controller-view.js";
import type { DomElements } from "./types/dom.js";

export async function hydrateAppController({
    elements,
    appView,
    sync,
    uiSessionController,
    interactions,
    viewportController,
    controlActions,
}: {
    elements: DomElements;
    appView: AppView;
    sync: AppControllerSync;
    uiSessionController: UiSessionController;
    interactions: InteractionController;
    viewportController: ViewportController;
    controlActions: AppActionSet;
}): Promise<void> {
    await sync.loadRules();
    uiSessionController.restoreDisclosures();
    bindControls(elements, controlActions);
    appView.renderControlsPanel();
    await sync.refreshState();
    if (controlActions.applyShareLinkFromHash) {
        await controlActions.applyShareLinkFromHash();
    }
    interactions.bindGridInteractions();
    viewportController.install(elements.gridViewport);
}
