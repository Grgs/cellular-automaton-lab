import { describe, expect, it } from "vitest";

import { resolvePointerDownIntent } from "./intent.js";
import type { EditorTool } from "../../editor-tools.js";

function pointerEvent(button: number): PointerEvent {
    return { button } as PointerEvent;
}

function editPolicy({
    supportsEditorTools = true,
    isEditArmed = false,
    runningBrushEditingEnabled = false,
    runningAdvancedToolBlocked = false,
    editingBlockedByRun = false,
    currentTool = "brush",
}: {
    supportsEditorTools?: boolean;
    isEditArmed?: boolean;
    runningBrushEditingEnabled?: boolean;
    runningAdvancedToolBlocked?: boolean;
    editingBlockedByRun?: boolean;
    currentTool?: EditorTool;
}) {
    return {
        supportsEditorTools: () => supportsEditorTools,
        isEditArmed: () => isEditArmed,
        runningBrushEditingEnabled: () => runningBrushEditingEnabled,
        runningAdvancedToolBlocked: () => runningAdvancedToolBlocked,
        editingBlockedByRun: () => editingBlockedByRun,
        currentTool: () => currentTool,
        prepareDirectGridInteraction: () => {},
        armEditingFromGrid: () => ({ consumeNextClick: false }),
        blockRunningAdvancedTool: () => {},
        dismissEditingUi: () => Promise.resolve(false),
    };
}

describe("interactions/gesture-sessions/intent", () => {
    it("classifies right-button pointer down as a selection gesture", () => {
        expect(resolvePointerDownIntent(pointerEvent(2), editPolicy({})).kind).toBe("right-selection");
    });

    it("ignores unsupported pointer buttons", () => {
        expect(resolvePointerDownIntent(pointerEvent(1), editPolicy({})).kind).toBe("ignore");
    });

    it("treats unarmed left pointer down as direct paint", () => {
        expect(resolvePointerDownIntent(pointerEvent(0), editPolicy({ isEditArmed: false })).kind).toBe("direct-paint");
    });

    it("keeps running armed brush gestures on the legacy paint path", () => {
        expect(
            resolvePointerDownIntent(
                pointerEvent(0),
                editPolicy({ isEditArmed: true, runningBrushEditingEnabled: true }),
            ).kind,
        ).toBe("running-brush");
    });

    it("classifies blocked advanced tools before run-blocked editing", () => {
        expect(
            resolvePointerDownIntent(
                pointerEvent(0),
                editPolicy({
                    isEditArmed: true,
                    runningAdvancedToolBlocked: true,
                    editingBlockedByRun: true,
                    currentTool: "line",
                }),
            ).kind,
        ).toBe("blocked-advanced-tool");
    });

    it("treats armed fill as a click-only gesture", () => {
        expect(
            resolvePointerDownIntent(
                pointerEvent(0),
                editPolicy({ isEditArmed: true, currentTool: "fill" }),
            ).kind,
        ).toBe("fill-click");
    });

    it("falls back to editor pointer sessions for armed line and rectangle tools", () => {
        expect(
            resolvePointerDownIntent(
                pointerEvent(0),
                editPolicy({ isEditArmed: true, currentTool: "line" }),
            ).kind,
        ).toBe("editor-pointer");
    });
});
