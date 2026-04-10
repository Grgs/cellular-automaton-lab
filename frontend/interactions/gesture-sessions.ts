import { EDITOR_TOOL_FILL } from "../editor-tools.js";
import type { PaintableCell } from "../types/editor.js";
import type { InteractionEditPolicy } from "./edit-policy.js";
import { FOLLOWUP_CLICK_SUPPRESSION_RESET_DELAY_MS } from "./constants.js";

export interface PointerGestureSession {
    pointerId: number | null;
    handleMove(event: PointerEvent, cell: PaintableCell): void;
    handleUp(event: PointerEvent): void;
    cancel(event: PointerEvent): void;
    isActive(): boolean;
}

interface GestureRouterOptions {
    surfaceElement: HTMLElement | null;
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
        cancel(): Promise<unknown>;
    };
    setHoveredCell: (cell: PaintableCell | null) => void;
    setSelectedCells: (cells: PaintableCell[]) => void;
    getSelectedCells: () => PaintableCell[];
    clearGestureOutline: () => void;
    openInspectorDrawer: () => void;
    renderControlPanel: () => void;
    paintCell: (cell: PaintableCell, stateValue?: number) => Promise<void>;
    resolveDirectGestureTargetState: (cell: PaintableCell) => number;
    setTimeoutFn: (callback: () => void, delay: number) => number;
}

export function identifyGestureCell(cell: PaintableCell): string {
    if (typeof cell.id === "string" && cell.id.length > 0) {
        return cell.id;
    }
    return `${cell.x ?? 0}:${cell.y ?? 0}`;
}

function cloneSelectedCells(cells: PaintableCell[]): Map<string, PaintableCell> {
    return new Map(
        cells
            .map((cell) => [identifyGestureCell(cell), { ...cell }])
            .filter((entry): entry is [string, PaintableCell] => typeof entry[0] === "string" && entry[0].length > 0),
    );
}

function setSurfacePointerCapture(surfaceElement: HTMLElement | null, pointerId: number | null): void {
    if (!surfaceElement || typeof surfaceElement.setPointerCapture !== "function" || pointerId === null) {
        return;
    }
    try {
        surfaceElement.setPointerCapture(pointerId);
    } catch {
        // Ignore unsupported pointer capture implementations.
    }
}

function releaseSurfacePointerCapture(surfaceElement: HTMLElement | null, pointerId: number | null): void {
    if (!surfaceElement || typeof surfaceElement.releasePointerCapture !== "function" || pointerId === null) {
        return;
    }
    try {
        surfaceElement.releasePointerCapture(pointerId);
    } catch {
        // Pointer capture may already be released.
    }
}

function createLegacyDragGestureSession({
    pointerId,
    legacyDrag,
    buttonMask,
    onCancel = () => {},
}: {
    pointerId: number | null;
    legacyDrag: GestureRouterOptions["legacyDrag"];
    buttonMask: number;
    onCancel?: () => void;
}): PointerGestureSession {
    return {
        pointerId,
        handleMove(event, cell) {
            if ((event.buttons & buttonMask) === 0) {
                return;
            }
            legacyDrag.update(cell);
        },
        handleUp() {
            void legacyDrag.end();
        },
        cancel() {
            onCancel();
            void legacyDrag.cancel();
        },
        isActive: () => legacyDrag.isActive(),
    };
}

function createEditorGestureSession({
    pointerId,
    editorSession,
}: {
    pointerId: number | null;
    editorSession: GestureRouterOptions["editorSession"];
}): PointerGestureSession {
    return {
        pointerId,
        handleMove(_event, cell) {
            if ((_event.buttons & 1) === 0) {
                return;
            }
            editorSession.handlePointerMove(cell);
        },
        handleUp() {
            void editorSession.handlePointerUp();
        },
        cancel() {
            void editorSession.cancelActivePreview();
        },
        isActive: () => editorSession.isPointerActive(),
    };
}

function createRightSelectionGestureSession({
    event,
    initialCell,
    surfaceElement,
    editPolicy,
    getSelectedCells,
    setSelectedCells,
    openInspectorDrawer,
    renderControlPanel,
    onSuppressContextMenu,
    onScheduleContextMenuReset,
    onClearContextMenuSuppression,
}: {
    event: PointerEvent;
    initialCell: PaintableCell;
    surfaceElement: HTMLElement | null;
    editPolicy: InteractionEditPolicy;
    getSelectedCells: () => PaintableCell[];
    setSelectedCells: (cells: PaintableCell[]) => void;
    openInspectorDrawer: () => void;
    renderControlPanel: () => void;
    onSuppressContextMenu: () => void;
    onScheduleContextMenuReset: () => void;
    onClearContextMenuSuppression: () => void;
}): PointerGestureSession {
    const pointerId = event.pointerId ?? null;
    const initialCells = cloneSelectedCells(getSelectedCells());
    const workingCells = new Map(initialCells);
    const initialCellKey = identifyGestureCell(initialCell);
    const mode: "select" | "deselect" = initialCells.has(initialCellKey) ? "deselect" : "select";

    function updateSelection(cell: PaintableCell): void {
        const cellKey = identifyGestureCell(cell);
        const hasCell = workingCells.has(cellKey);
        if (mode === "select") {
            if (hasCell) {
                return;
            }
            workingCells.set(cellKey, { ...cell });
        } else {
            if (!hasCell) {
                return;
            }
            workingCells.delete(cellKey);
        }
        const nextSelectedCells = Array.from(workingCells.values());
        setSelectedCells(nextSelectedCells);
        if (nextSelectedCells.length > 0) {
            openInspectorDrawer();
        }
        renderControlPanel();
    }

    editPolicy.prepareDirectGridInteraction(event);
    onSuppressContextMenu();
    setSurfacePointerCapture(surfaceElement, pointerId);
    updateSelection(initialCell);

    return {
        pointerId,
        handleMove(moveEvent, cell) {
            if (moveEvent.pointerId !== pointerId || (moveEvent.buttons & 2) === 0) {
                return;
            }
            updateSelection(cell);
        },
        handleUp(upEvent) {
            if (upEvent.pointerId !== pointerId) {
                return;
            }
            releaseSurfacePointerCapture(surfaceElement, pointerId);
            onScheduleContextMenuReset();
        },
        cancel(cancelEvent) {
            if (cancelEvent.pointerId !== pointerId) {
                return;
            }
            setSelectedCells(Array.from(initialCells.values()));
            releaseSurfacePointerCapture(surfaceElement, pointerId);
            onClearContextMenuSuppression();
            renderControlPanel();
        },
        isActive: () => true,
    };
}

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

    function beginPointerDown(event: PointerEvent, cell: PaintableCell): void {
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
        activeSession = createEditorGestureSession({
            pointerId: event.pointerId ?? null,
            editorSession,
        });
    }

    function handlePointerMove(event: PointerEvent, cell: PaintableCell): void {
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

    function handleHoverChange(cell: PaintableCell | null): void {
        if (isAnyPointerActive()) {
            setHoveredCell(null);
            return;
        }
        setHoveredCell(cell);
    }

    function handleContextMenu(cell: PaintableCell | null): void {
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

    function handleClick(event: MouseEvent, cell: PaintableCell): void {
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
