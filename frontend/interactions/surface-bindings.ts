import {
    EDITOR_TOOL_FILL,
} from "../editor-tools.js";
import { FOLLOWUP_CLICK_SUPPRESSION_RESET_DELAY_MS } from "./constants.js";
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
    setSelectedCells,
    getSelectedCells,
    clearGestureOutline,
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
        cancel(): Promise<null>;
    };
    setHoveredCell: (cell: PaintableCell | null) => void;
    setSelectedCells: (cells: PaintableCell[]) => void;
    getSelectedCells: () => PaintableCell[];
    clearGestureOutline: () => void;
    paintCell: (cell: PaintableCell, stateValue?: number) => Promise<void>;
    resolveDirectGestureTargetState: (cell: PaintableCell) => number;
    bindGridInteractionsFn?: ((options: GridInteractionBindings) => void) | undefined;
    setTimeoutFn?: ((callback: () => void, delay: number) => number) | undefined;
}): { bindGridInteractions(): void } {
    let consumeNextClick = false;
    let pendingDirectGestureTargetState: number | null = null;
    let pendingDirectGestureCellId: string | null = null;
    let selectionPointerId: number | null = null;
    let selectionGestureMode: "select" | "deselect" | null = null;
    let selectionGestureInitialCells = new Map<string, PaintableCell>();
    let selectionGestureWorkingCells = new Map<string, PaintableCell>();
    let suppressNextContextMenu = false;

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

    function cloneSelectedCells(cells: PaintableCell[]): Map<string, PaintableCell> {
        return new Map(
            cells
                .map((cell) => [identifyGestureCell(cell), { ...cell }])
                .filter((entry): entry is [string, PaintableCell] => typeof entry[0] === "string" && entry[0].length > 0),
        );
    }

    function setSurfacePointerCapture(pointerId: number | null): void {
        if (!surfaceElement || typeof surfaceElement.setPointerCapture !== "function" || pointerId === null) {
            return;
        }
        try {
            surfaceElement.setPointerCapture(pointerId);
        } catch {
            // Ignore unsupported pointer capture implementations.
        }
    }

    function releaseSurfacePointerCapture(pointerId: number | null): void {
        if (!surfaceElement || typeof surfaceElement.releasePointerCapture !== "function" || pointerId === null) {
            return;
        }
        try {
            surfaceElement.releasePointerCapture(pointerId);
        } catch {
            // Pointer capture may already be released.
        }
    }

    function clearSelectionGestureState(): void {
        selectionPointerId = null;
        selectionGestureMode = null;
        selectionGestureInitialCells = new Map();
        selectionGestureWorkingCells = new Map();
    }

    function updateSelectionGesture(cell: PaintableCell): void {
        if (selectionGestureMode === null) {
            return;
        }
        const cellKey = identifyGestureCell(cell);
        const hasCell = selectionGestureWorkingCells.has(cellKey);
        if (selectionGestureMode === "select") {
            if (hasCell) {
                return;
            }
            selectionGestureWorkingCells.set(cellKey, { ...cell });
        } else {
            if (!hasCell) {
                return;
            }
            selectionGestureWorkingCells.delete(cellKey);
        }
        setSelectedCells(Array.from(selectionGestureWorkingCells.values()));
    }

    function beginSelectionGesture(event: PointerEvent, cell: PaintableCell): void {
        editPolicy.prepareDirectGridInteraction(event);
        const currentSelectedCells = cloneSelectedCells(getSelectedCells());
        const cellKey = identifyGestureCell(cell);
        selectionPointerId = event.pointerId ?? null;
        selectionGestureMode = currentSelectedCells.has(cellKey) ? "deselect" : "select";
        selectionGestureInitialCells = new Map(currentSelectedCells);
        selectionGestureWorkingCells = new Map(currentSelectedCells);
        suppressNextContextMenu = true;
        setSurfacePointerCapture(selectionPointerId);
        updateSelectionGesture(cell);
    }

    function endSelectionGesture(): void {
        releaseSurfacePointerCapture(selectionPointerId);
        clearSelectionGestureState();
        if (suppressNextContextMenu) {
            setTimeoutFn(() => {
                suppressNextContextMenu = false;
            }, FOLLOWUP_CLICK_SUPPRESSION_RESET_DELAY_MS);
        }
    }

    function cancelSelectionGesture(): void {
        setSelectedCells(Array.from(selectionGestureInitialCells.values()));
        releaseSurfacePointerCapture(selectionPointerId);
        clearSelectionGestureState();
        suppressNextContextMenu = false;
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
                    clearGestureOutline();
                    if (event.button === 2) {
                        beginSelectionGesture(event, cell);
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
                    if (selectionPointerId !== null) {
                        if (event.pointerId !== selectionPointerId || (event.buttons & 2) === 0) {
                            return;
                        }
                        updateSelectionGesture(cell);
                        return;
                    }
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
                onPointerUp(event: PointerEvent) {
                    if (selectionPointerId !== null && event.pointerId === selectionPointerId) {
                        endSelectionGesture();
                        return;
                    }
                    if (consumeNextClick && editPolicy.supportsEditorTools() && !editorSession.isPointerActive() && !legacyDrag.isActive()) {
                        setTimeoutFn(() => {
                            consumeNextClick = false;
                        }, FOLLOWUP_CLICK_SUPPRESSION_RESET_DELAY_MS);
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
                    clearGestureOutline();
                    if (selectionPointerId !== null) {
                        cancelSelectionGesture();
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
                },
                onHoverChange(cell) {
                    const hasActivePointer = selectionPointerId !== null || editorSession.isPointerActive() || legacyDrag.isActive();
                    if (hasActivePointer) {
                        setHoveredCell(null);
                        return;
                    }
                    setHoveredCell(cell);
                },
                onContextMenu(cell) {
                    if (suppressNextContextMenu) {
                        suppressNextContextMenu = false;
                        return;
                    }
                    if (!cell) {
                        setSelectedCells([]);
                        return;
                    }
                    const selectedCells = cloneSelectedCells(getSelectedCells());
                    const cellKey = identifyGestureCell(cell);
                    if (selectedCells.has(cellKey)) {
                        selectedCells.delete(cellKey);
                        setSelectedCells(Array.from(selectedCells.values()));
                        return;
                    }
                    selectedCells.set(cellKey, { ...cell });
                    setSelectedCells(Array.from(selectedCells.values()));
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
