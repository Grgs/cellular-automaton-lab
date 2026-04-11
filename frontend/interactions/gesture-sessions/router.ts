import { EDITOR_TOOL_FILL } from "../../editor-tools.js";
import { FOLLOWUP_CLICK_SUPPRESSION_RESET_DELAY_MS } from "../constants.js";
import { cloneSelectedCells, identifyGestureCell } from "./helpers.js";
import { createEditorPointerSession } from "./editor-pointer-session.js";
import { createLegacyDragGestureSession } from "./legacy-drag-session.js";
import { createRightSelectionGestureSession } from "./right-selection-session.js";
import type { GestureRouterOptions, PointerGestureSession } from "./types.js";

export function createPointerGestureRouter({
    surfaceElement,
    editPolicy,
    editorSession,
    legacyDrag,
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
        return Boolean(activeSession) || editorSession.isPointerActive() || legacyDrag.isActive();
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

    function beginPointerDown(event: PointerEvent, cell: Parameters<typeof resolveDirectGestureTargetState>[0]): void {
        setHoveredCell(null);
        clearGestureOutline();
        if (event.button === 2) {
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
            return;
        }
        if (event.button !== 0) {
            return;
        }

        const editModeActive = editPolicy.supportsEditorTools() && editPolicy.isEditArmed();
        if (!editModeActive) {
            editPolicy.prepareDirectGridInteraction(event);
            const targetState = resolveDirectGestureTargetState(cell);
            rememberDirectGesture(cell, targetState);
            legacyDrag.begin(cell, event.pointerId, targetState);
            activeSession = createLegacyDragGestureSession({
                pointerId: event.pointerId ?? null,
                legacyDrag,
                buttonMask: 1,
                onCancel: clearPendingDirectGesture,
            });
            return;
        }

        clearPendingDirectGesture();
        if (editPolicy.runningBrushEditingEnabled()) {
            void editPolicy.dismissEditingUi();
            event.preventDefault();
            legacyDrag.begin(cell, event.pointerId);
            activeSession = createLegacyDragGestureSession({
                pointerId: event.pointerId ?? null,
                legacyDrag,
                buttonMask: 1,
            });
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
        activeSession = createEditorPointerSession({
            pointerId: event.pointerId ?? null,
            editorSession,
        });
    }

    function handlePointerMove(event: PointerEvent, cell: Parameters<typeof resolveDirectGestureTargetState>[0]): void {
        activeSession?.handleMove(event, cell);
    }

    function handlePointerUp(event: PointerEvent): void {
        if (consumeNextClick && editPolicy.supportsEditorTools() && !editorSession.isPointerActive() && !legacyDrag.isActive()) {
            setTimeoutFn(() => {
                consumeNextClick = false;
            }, FOLLOWUP_CLICK_SUPPRESSION_RESET_DELAY_MS);
        }
        if (activeSession) {
            if (activeSession.pointerId !== null && event.pointerId !== activeSession.pointerId) {
                return;
            }
            activeSession.handleUp(event);
            clearActiveSession();
            return;
        }
        if (!editPolicy.supportsEditorTools()) {
            void legacyDrag.end();
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
            if (activeSession.pointerId !== null && event.pointerId !== activeSession.pointerId) {
                return;
            }
            activeSession.cancel(event);
            clearActiveSession();
            return;
        }
        if (legacyDrag.isActive()) {
            void legacyDrag.cancel();
            return;
        }
        if (!editPolicy.supportsEditorTools()) {
            void legacyDrag.end();
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
