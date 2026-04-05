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
    setHoveredCell,
    setSelectedCell,
    getSelectedCell,
    paintCell,
    resolveDirectGestureTargetState,
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
        begin(cell: PaintableCell, pointerId?: number | null, paintStateOverride?: number): void;
        update(cell: PaintableCell): void;
        end(): Promise<unknown>;
    };
    setHoveredCell: (cell: PaintableCell | null) => void;
    setSelectedCell: (cell: PaintableCell | null) => void;
    getSelectedCell: () => PaintableCell | null;
    paintCell: (cell: PaintableCell, stateValue?: number) => Promise<void>;
    resolveDirectGestureTargetState: (cell: PaintableCell) => number;
    bindGridInteractionsFn?: ((options: GridInteractionBindings) => void) | undefined;
    setTimeoutFn?: ((callback: () => void, delay: number) => number) | undefined;
}): { bindGridInteractions(): void } {
    let consumeNextClick = false;
    let pendingDirectGestureTargetState: number | null = null;
    let pendingDirectGestureCellId: string | null = null;

    function identifyGestureCell(cell: PaintableCell): string {
        if (typeof cell.id === "string" && cell.id.length > 0) {
            return cell.id;
        }
        return `${cell.x ?? 0}:${cell.y ?? 0}`;
    }

    function rememberDirectGesture(cell: PaintableCell, targetState: number): void {
        pendingDirectGestureCellId = identifyGestureCell(cell);
        pendingDirectGestureTargetState = targetState;
    }

    function clearPendingDirectGesture(): void {
        pendingDirectGestureCellId = null;
        pendingDirectGestureTargetState = null;
    }

    function resolvePendingDirectGestureTargetState(cell: PaintableCell): number {
        if (
            pendingDirectGestureTargetState !== null
            && pendingDirectGestureCellId === identifyGestureCell(cell)
        ) {
            return pendingDirectGestureTargetState;
        }
        return resolveDirectGestureTargetState(cell);
    }

    return {
        bindGridInteractions() {
            bindGridInteractionsFn({
                surfaceElement,
                resolveCellFromEvent,
                onPointerDown(event: PointerEvent, cell: PaintableCell) {
                    setHoveredCell(null);
                    const editModeActive = editPolicy.supportsEditorTools() && editPolicy.isEditArmed();
                    if (!editModeActive) {
                        editPolicy.prepareDirectGridInteraction(event);
                        const targetState = resolveDirectGestureTargetState(cell);
                        rememberDirectGesture(cell, targetState);
                        legacyDrag.begin(cell, event.pointerId, targetState);
                        return;
                    }
                    clearPendingDirectGesture();
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
                    void editPolicy.dismissEditingUi();
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
                    clearPendingDirectGesture();
                    setHoveredCell(null);
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
                onHoverChange(cell) {
                    const hasActivePointer = editorSession.isPointerActive() || legacyDrag.isActive();
                    if (hasActivePointer) {
                        setHoveredCell(null);
                        return;
                    }
                    setHoveredCell(cell);
                },
                onContextMenu(cell) {
                    const selectedCell = getSelectedCell();
                    if (!cell) {
                        setSelectedCell(null);
                        return;
                    }
                    if (selectedCell?.id === cell.id) {
                        setSelectedCell(null);
                        return;
                    }
                    setSelectedCell(cell);
                },
                onClick(event: MouseEvent, cell: PaintableCell) {
                    if (editorSession.isClickSuppressed()) {
                        clearPendingDirectGesture();
                        event.preventDefault();
                        event.stopPropagation();
                        return;
                    }
                    if (consumeNextClick) {
                        consumeNextClick = false;
                        clearPendingDirectGesture();
                        event.preventDefault();
                        event.stopPropagation();
                        return;
                    }
                    const editModeActive = editPolicy.supportsEditorTools() && editPolicy.isEditArmed();
                    if (!editModeActive) {
                        event.preventDefault();
                        event.stopPropagation();
                        const targetState = resolvePendingDirectGestureTargetState(cell);
                        if (pendingDirectGestureTargetState === null) {
                            editPolicy.prepareDirectGridInteraction();
                        }
                        clearPendingDirectGesture();
                        void paintCell(cell, targetState);
                        return;
                    }
                    clearPendingDirectGesture();
                    if (editPolicy.runningAdvancedToolBlocked()) {
                        editPolicy.blockRunningAdvancedTool(event);
                        return;
                    }
                    if (editPolicy.editingBlockedByRun()) {
                        event.preventDefault();
                        event.stopPropagation();
                        void editPolicy.dismissEditingUi();
                        void paintCell(cell);
                        return;
                    }

                    void editPolicy.dismissEditingUi();
                    void editorSession.handleClick(cell);
                },
            });
        },
    };
}
