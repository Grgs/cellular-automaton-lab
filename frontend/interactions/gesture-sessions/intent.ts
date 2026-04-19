import { EDITOR_TOOL_FILL } from "../../editor-tools.js";
import type { InteractionEditPolicy } from "../edit-policy.js";
import type { PointerDownIntent } from "./types.js";

export function resolvePointerDownIntent(
    event: PointerEvent,
    editPolicy: InteractionEditPolicy,
): PointerDownIntent {
    if (event.button === 2) {
        return { kind: "right-selection" };
    }
    if (event.button !== 0) {
        return { kind: "ignore" };
    }

    const editModeActive = editPolicy.supportsEditorTools() && editPolicy.isEditArmed();
    if (!editModeActive) {
        return { kind: "direct-paint" };
    }
    if (editPolicy.runningBrushEditingEnabled()) {
        return { kind: "running-brush" };
    }
    if (editPolicy.runningAdvancedToolBlocked()) {
        return { kind: "blocked-advanced-tool" };
    }
    if (editPolicy.supportsEditorTools() && editPolicy.editingBlockedByRun()) {
        return { kind: "blocked-editing" };
    }
    if (editPolicy.currentTool() === EDITOR_TOOL_FILL) {
        return { kind: "fill-click" };
    }
    return { kind: "editor-pointer" };
}
