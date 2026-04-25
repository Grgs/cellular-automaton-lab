import { FOLLOWUP_CLICK_SUPPRESSION_RESET_DELAY_MS } from "../constants.js";
import { cloneSelectedCells, identifyGestureCell } from "./helpers.js";
import { createEditorPointerSession } from "./editor-pointer-session.js";
import { resolvePointerDownIntent } from "./intent.js";
import { createPaintDragGestureSession } from "./paint-drag-session.js";
import { createRightSelectionGestureSession } from "./right-selection-session.js";
import type { GestureRouterOptions, PointerGestureSession } from "./types.js";

export function createPointerGestureRouter({
    surfaceElement,
    editPolicy,
    editorSession,
    paintDrag,
    setHoveredCell,
    setSelectedCells,
    getSelectedCells,
    clearGestureOutline,
    openInspectorDrawer,
    renderControlPanel,
    paintCell,
    resolveDirectGestureTargetState,
    setTimeoutFn,
}: GestureRouterOptions) {
    let activeSession: PointerGestureSession | null = null;
    let consumeNextClick = false;
    let pendingDirectGestureTargetState: number | null = null;
    let pendingDirectGestureCellId: string | null = null;
    let suppressNextContextMenu = false;

    function rememberDirectGesture(cell: Parameters<typeof resolveDirectGestureTargetState>[0], targetState: number): void {
        pendingDirectGestureCellId = identifyGestureCell(cell);
        pendingDirectGestureTargetState = targetState;
    }

    function clearPendingDirectGesture(): void {
        pendingDirectGestureCellId = null;
        pendingDirectGestureTargetState = null;
    }

    function resolvePendingDirectGestureTargetState(cell: Parameters<typeof resolveDirectGestureTargetState>[0]): number {
        if (
            pendingDirectGestureTargetState !== null
            && pendingDirectGestureCellId === identifyGestureCell(cell)
        ) {
            return pendingDirectGestureTargetState;
        }
        return resolveDirectGestureTargetState(cell);
    }

    function isAnyPointerActive(): boolean {
        return Boolean(activeSession) || editorSession.isPointerActive() || paintDrag.isActive();
    }

    function clearActiveSession(): void {
        activeSession = null;
    }

    function scheduleContextMenuReset(): void {
        if (!suppressNextContextMenu) {
            return;
        }
        setTimeoutFn(() => {
            suppressNextContextMenu = false;
        }, FOLLOWUP_CLICK_SUPPRESSION_RESET_DELAY_MS);
    }

    function beginRightSelectionSession(
        event: PointerEvent,
        cell: Parameters<typeof resolveDirectGestureTargetState>[0],
    ): void {
        activeSession = createRightSelectionGestureSession({
            event,
            initialCell: cell,
            surfaceElement,
            editPolicy,
            getSelectedCells,
            setSelectedCells,
            openInspectorDrawer,
            renderControlPanel,
            onSuppressContextMenu: () => {
                suppressNextContextMenu = true;
            },
            onScheduleContextMenuReset: scheduleContextMenuReset,
            onClearContextMenuSuppression: () => {
                suppressNextContextMenu = false;
            },
        });
    }

    function beginDirectPaintSession(
        event: PointerEvent,
        cell: Parameters<typeof resolveDirectGestureTargetState>[0],
    ): void {
        editPolicy.prepareDirectGridInteraction(event);
        const targetState = resolveDirectGestureTargetState(cell);
        rememberDirectGesture(cell, targetState);
        paintDrag.begin(cell, event.pointerId, targetState);
        activeSession = createPaintDragGestureSession({
            pointerId: event.pointerId ?? null,
            paintDrag,
            buttonMask: 1,
            onCancel: clearPendingDirectGesture,
        });
    }

    function beginRunningBrushSession(
        event: PointerEvent,
        cell: Parameters<typeof resolveDirectGestureTargetState>[0],
    ): void {
        clearPendingDirectGesture();
        void editPolicy.dismissEditingUi();
        event.preventDefault();
        paintDrag.begin(cell, event.pointerId);
        activeSession = createPaintDragGestureSession({
            pointerId: event.pointerId ?? null,
            paintDrag,
            buttonMask: 1,
        });
    }

    function beginEditorPointerSession(
        event: PointerEvent,
        cell: Parameters<typeof resolveDirectGestureTargetState>[0],
    ): void {
        clearPendingDirectGesture();
        void editPolicy.dismissEditingUi();
        event.preventDefault();
        void editorSession.beginPointerSession(cell, event.pointerId);
        activeSession = createEditorPointerSession({
            pointerId: event.pointerId ?? null,
            editorSession,
        });
    }

    function beginPointerDown(event: PointerEvent, cell: Parameters<typeof resolveDirectGestureTargetState>[0]): void {
        setHoveredCell(null);
        clearGestureOutline();
        switch (resolvePointerDownIntent(event, editPolicy).kind) {
            case "right-selection":
                beginRightSelectionSession(event, cell);
                return;
            case "ignore":
                return;
            case "direct-paint":
                beginDirectPaintSession(event, cell);
                return;
            case "running-brush":
                beginRunningBrushSession(event, cell);
                return;
            case "blocked-advanced-tool":
                clearPendingDirectGesture();
                editPolicy.blockRunningAdvancedTool(event);
                consumeNextClick = true;
                return;
            case "blocked-editing":
                clearPendingDirectGesture();
                return;
            case "fill-click":
                clearPendingDirectGesture();
                void editPolicy.dismissEditingUi();
                return;
            case "editor-pointer":
                beginEditorPointerSession(event, cell);
                return;
        }
    }

    function handlePointerMove(event: PointerEvent, cell: Parameters<typeof resolveDirectGestureTargetState>[0]): void {
        activeSession?.handleMove(event, cell);
    }

    function handlePointerUp(event: PointerEvent): void {
        if (consumeNextClick && editPolicy.supportsEditorTools() && !editorSession.isPointerActive() && !paintDrag.isActive()) {
            setTimeoutFn(() => {
                consumeNextClick = false;
            }, FOLLOWUP_CLICK_SUPPRESSION_RESET_DELAY_MS);
        }
        if (activeSession) {
            if (activeSession.handleUp(event)) {
                clearActiveSession();
            }
            return;
        }
        if (!editPolicy.supportsEditorTools()) {
            void paintDrag.end();
            return;
        }

        void editorSession.handlePointerUp();
    }

    function handlePointerCancel(event: PointerEvent): void {
        consumeNextClick = false;
        clearPendingDirectGesture();
        setHoveredCell(null);
        clearGestureOutline();
        if (activeSession) {
            if (activeSession.cancel(event)) {
                clearActiveSession();
            }
            return;
        }
        if (paintDrag.isActive()) {
            void paintDrag.cancel();
            return;
        }
        if (!editPolicy.supportsEditorTools()) {
            void paintDrag.end();
            return;
        }

        void editorSession.cancelActivePreview();
    }

    function handleHoverChange(cell: Parameters<typeof setHoveredCell>[0]): void {
        if (isAnyPointerActive()) {
            setHoveredCell(null);
            return;
        }
        setHoveredCell(cell);
    }

    function handleContextMenu(cell: Parameters<typeof setHoveredCell>[0]): void {
        if (suppressNextContextMenu) {
            suppressNextContextMenu = false;
            return;
        }
        if (!cell) {
            setSelectedCells([]);
            renderControlPanel();
            return;
        }
        const selectedCells = cloneSelectedCells(getSelectedCells());
        const cellKey = identifyGestureCell(cell);
        if (selectedCells.has(cellKey)) {
            selectedCells.delete(cellKey);
            setSelectedCells(Array.from(selectedCells.values()));
            renderControlPanel();
            return;
        }
        selectedCells.set(cellKey, { ...cell });
        setSelectedCells(Array.from(selectedCells.values()));
        openInspectorDrawer();
        renderControlPanel();
    }

    function handleClick(event: MouseEvent, cell: Parameters<typeof resolveDirectGestureTargetState>[0]): void {
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
    }

    return {
        beginPointerDown,
        handlePointerMove,
        handlePointerUp,
        handlePointerCancel,
        handleHoverChange,
        handleContextMenu,
        handleClick,
        isActive: isAnyPointerActive,
    };
}
