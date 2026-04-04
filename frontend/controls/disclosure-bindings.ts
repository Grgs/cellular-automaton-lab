import { bindControlShortcuts } from "../controls-shortcuts.js";
import { DISCLOSURE_IDS } from "../ui-session.js";
import type { AppActionSet } from "../types/actions.js";
import type { DomElements } from "../types/dom.js";
import type { UiDisclosureId } from "../types/session.js";

export function bindDisclosureAndShortcutControls(elements: DomElements, actions: AppActionSet): void {
    if (actions.setDisclosureState) {
        DISCLOSURE_IDS.forEach((id) => {
            const disclosure = elements[id];
            if (!disclosure) {
                return;
            }
            disclosure.addEventListener("toggle", () => {
                actions.setDisclosureState(id as UiDisclosureId, disclosure.open);
            });
        });
    }

    bindControlShortcuts(actions);
}
