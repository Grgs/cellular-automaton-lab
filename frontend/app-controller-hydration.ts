import { bindControls } from "./controls-bindings.js";
import { readShareBodyFromHash } from "./share-link.js";
import type { AppActionSet } from "./types/actions.js";
import type { AppControllerSync } from "./types/controller-app.js";
import type { UiSessionController } from "./types/controller-sync-session.js";
import type {
    AppView,
    InteractionController,
    ViewportController,
} from "./types/controller-view.js";
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
    // Capture any incoming share link before refreshState(), which mirrors the
    // freshly-fetched backend board into the hash via replaceState and would
    // otherwise clobber the link we are meant to load.
    const incomingShareHash =
        typeof window !== "undefined" && readShareBodyFromHash(window.location.hash)
            ? window.location.hash
            : null;

    await sync.loadRules();
    uiSessionController.restoreDisclosures();
    bindControls(elements, controlActions);
    appView.renderControlsPanel();
    await sync.refreshState();
    if (controlActions.applyShareLinkFromHash) {
        if (incomingShareHash !== null && typeof window !== "undefined") {
            window.history.replaceState(
                null,
                "",
                `${window.location.pathname}${window.location.search}${incomingShareHash}`,
            );
        }
        await controlActions.applyShareLinkFromHash();
    }
    interactions.bindGridInteractions();
    viewportController.install(elements.gridViewport);
}
