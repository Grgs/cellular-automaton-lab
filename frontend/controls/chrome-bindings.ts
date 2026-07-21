import { bindButtonControl } from "./binding-primitives.js";
import { eventTargetElement, isInteractiveChromeClick } from "./shell-clicks.js";
import type { AppActionSet } from "../types/actions.js";
import type { DomElements } from "../types/dom.js";

export function bindChromeControls(elements: DomElements, actions: AppActionSet): void {
    // The theme toggle lives in the shared shell header (reachable from the wall
    // too) and is wired by the shell, not the Lab control panel.
    bindButtonControl(elements.drawerToggleBtn, actions.toggleDrawer);

    if (elements.drawerBackdrop && actions.closeDrawer) {
        elements.drawerBackdrop.addEventListener("click", () => {
            void actions.closeDrawer();
        });
    }

    if (elements.labDock && actions.handleTopBarEmptyClick) {
        elements.labDock.addEventListener("click", (event) => {
            if (isInteractiveChromeClick(event, elements.labDock)) {
                return;
            }
            void actions.handleTopBarEmptyClick();
        });
    }

    if (elements.controlDrawer && actions.handleInspectorEmptyClick) {
        const controlDrawer = elements.controlDrawer;
        controlDrawer.addEventListener("click", (event) => {
            if (
                controlDrawer.dataset.open !== "true" ||
                controlDrawer.getAttribute("aria-hidden") === "true"
            ) {
                return;
            }
            if (isInteractiveChromeClick(event, controlDrawer)) {
                return;
            }
            void actions.handleInspectorEmptyClick();
        });
    }

    if (elements.grid && actions.enterEditMode) {
        elements.grid.addEventListener("pointerdown", () => {
            actions.enterEditMode();
        });
    }

    if (elements.mainStage && actions.handleWorkspaceEmptyClick) {
        const mainStage = elements.mainStage;
        mainStage.addEventListener("click", (event) => {
            const target = eventTargetElement(event);
            if (!target || !mainStage.contains(target)) {
                return;
            }
            if (elements.controlDrawer?.contains(target)) {
                return;
            }
            if (elements.grid?.contains?.(target) || target === elements.grid) {
                return;
            }
            if (isInteractiveChromeClick(event, mainStage)) {
                return;
            }
            void actions.handleWorkspaceEmptyClick();
        });
    }
}
