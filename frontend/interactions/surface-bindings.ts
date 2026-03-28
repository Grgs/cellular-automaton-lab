import {
    EDITOR_TOOL_FILL,
} from "../editor-tools.js";
import { bindGridInteractions as bindGridInteractionsToSurface } from "./grid-bindings.js";
import type { InteractionEditPolicy } from "./edit-policy.js";
import type { PaintableCell, GridInteractionBindings } from "../types/editor.js";

export function createInteractionSurfaceBindings({
    surfaceElement,
    resolveCellFromEvent,
    editPolicy,
    editorSession,
    legacyDrag,
    paintCell,
    bindGridInteractionsFn = bindGridInteractionsToSurface,
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
}: {
    surfaceElement: HTMLElement | null;
    resolveCellFromEvent: (event: PointerEvent | MouseEvent) => PaintableCell | null;
    editPolicy: InteractionEditPolicy;
    editorSession: {
        isPointerActive(): boolean;
        beginPointerSession(cell: PaintableCell, pointerId?: number | null): Promise<boolean>;
        handlePointerMove(cell: PaintableCell): void;
        handlePointerUp(): Promise<unknown>;
        cancelActivePreview(): Promise<void>;
        isClickSuppressed(): boolean;
        handleClick(cell: PaintableCell): Promise<{ handled: boolean }>;
    };
    legacyDrag: {
        isActive(): boolean;
        begin(cell: PaintableCell, pointerId?: number | null): void;
        update(cell: PaintableCell): void;
        end(): Promise<unknown>;
    };
    paintCell: (cell: PaintableCell) => Promise<void>;
    bindGridInteractionsFn?: ((options: GridInteractionBindings) => void) | undefined;
    setTimeoutFn?: ((callback: () => void, delay: number) => number) | undefined;
}): { bindGridInteractions(): void } {
    let consumeNextClick = false;

    return {
        bindGridInteractions() {
            bindGridInteractionsFn({
                surfaceElement,
                resolveCellFromEvent,
                onPointerDown(event: PointerEvent, cell: PaintableCell) {
                    if (editPolicy.runningBrushEditingEnabled()) {
                        void editPolicy.dismissEditingUi();
                        event.preventDefault();
                        legacyDrag.begin(cell, event.pointerId);
                        return;
                    }
                    if (editPolicy.runningAdvancedToolBlocked()) {
                        editPolicy.blockRunningAdvancedTool(event);
                        consumeNextClick = true;
                        return;
                    }
                    if (editPolicy.supportsEditorTools() && editPolicy.editingBlockedByRun()) {
                        return;
                    }
                    if (editPolicy.supportsEditorTools() && !editPolicy.isEditArmed()) {
                        consumeNextClick = editPolicy.armEditingFromGrid(event, {
                            suppressFollowupClick: true,
                        }).consumeNextClick;
                        return;
                    }
                    void editPolicy.dismissEditingUi();
                    if (!editPolicy.supportsEditorTools()) {
                        event.preventDefault();
                        legacyDrag.begin(cell, event.pointerId);
                        return;
                    }

                    if (editPolicy.currentTool() === EDITOR_TOOL_FILL) {
                        return;
                    }

                    event.preventDefault();
                    void editorSession.beginPointerSession(cell, event.pointerId);
                },
                onPointerMove(event: PointerEvent, cell: PaintableCell) {
                    const hasActivePointer = editorSession.isPointerActive() || legacyDrag.isActive();
                    if (!hasActivePointer || (event.buttons & 1) === 0) {
                        return;
                    }

                    if (legacyDrag.isActive()) {
                        legacyDrag.update(cell);
                        return;
                    }

                    editorSession.handlePointerMove(cell);
                },
                onPointerUp() {
                    if (consumeNextClick && editPolicy.supportsEditorTools() && !editorSession.isPointerActive() && !legacyDrag.isActive()) {
                        setTimeoutFn(() => {
                            consumeNextClick = false;
                        }, 0);
                    }
                    if (legacyDrag.isActive()) {
                        void legacyDrag.end();
                        return;
                    }
                    if (!editPolicy.supportsEditorTools()) {
                        void legacyDrag.end();
                        return;
                    }

                    void editorSession.handlePointerUp();
                },
                onPointerCancel() {
                    consumeNextClick = false;
                    if (legacyDrag.isActive()) {
                        void legacyDrag.end();
                        return;
                    }
                    if (!editPolicy.supportsEditorTools()) {
                        void legacyDrag.end();
                        return;
                    }

                    void editorSession.cancelActivePreview();
                },
                onClick(event: MouseEvent, cell: PaintableCell) {
                    if (editorSession.isClickSuppressed()) {
                        event.preventDefault();
                        event.stopPropagation();
                        return;
                    }
                    if (consumeNextClick) {
                        consumeNextClick = false;
                        event.preventDefault();
                        event.stopPropagation();
                        return;
                    }
                    if (editPolicy.runningAdvancedToolBlocked()) {
                        editPolicy.blockRunningAdvancedTool(event);
                        return;
                    }
                    if (editPolicy.supportsEditorTools() && editPolicy.editingBlockedByRun()) {
                        event.preventDefault();
                        event.stopPropagation();
                        void editPolicy.dismissEditingUi();
                        void paintCell(cell);
                        return;
                    }
                    if (editPolicy.supportsEditorTools() && !editPolicy.isEditArmed()) {
                        consumeNextClick = editPolicy.armEditingFromGrid(event).consumeNextClick;
                        return;
                    }

                    void editPolicy.dismissEditingUi();
                    if (!editPolicy.supportsEditorTools()) {
                        void paintCell(cell);
                        return;
                    }

                    void editorSession.handleClick(cell);
                },
            });
        },
    };
}
