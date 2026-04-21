import { bindGridInteractions as bindGridInteractionsToSurface } from "./grid-bindings.js";
import { createPointerGestureRouter } from "./gesture-sessions.js";
import type { InteractionEditPolicy } from "./edit-policy.js";
import type { SimulationSnapshot } from "../types/domain.js";
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
    openInspectorDrawer,
    renderControlPanel,
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
        handlePointerUp(): Promise<SimulationSnapshot | null>;
        cancelActivePreview(): Promise<void>;
        isClickSuppressed(): boolean;
        handleClick(cell: PaintableCell): Promise<{ handled: boolean }>;
    };
    legacyDrag: {
        isActive(): boolean;
        begin(cell: PaintableCell, pointerId?: number | null, paintStateOverride?: number): void;
        update(cell: PaintableCell): void;
        end(): Promise<SimulationSnapshot | null>;
        cancel(): Promise<null>;
    };
    setHoveredCell: (cell: PaintableCell | null) => void;
    setSelectedCells: (cells: PaintableCell[]) => void;
    getSelectedCells: () => PaintableCell[];
    clearGestureOutline: () => void;
    openInspectorDrawer: () => void;
    renderControlPanel: () => void;
    paintCell: (cell: PaintableCell, stateValue?: number) => Promise<void>;
    resolveDirectGestureTargetState: (cell: PaintableCell) => number;
    bindGridInteractionsFn?: ((options: GridInteractionBindings) => void) | undefined;
    setTimeoutFn?: ((callback: () => void, delay: number) => number) | undefined;
}): { bindGridInteractions(): void } {
    const gestureRouter = createPointerGestureRouter({
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
    });

    return {
        bindGridInteractions() {
            bindGridInteractionsFn({
                surfaceElement,
                resolveCellFromEvent,
                onPointerDown(event: PointerEvent, cell: PaintableCell) {
                    gestureRouter.beginPointerDown(event, cell);
                },
                onPointerMove(event: PointerEvent, cell: PaintableCell) {
                    gestureRouter.handlePointerMove(event, cell);
                },
                onPointerUp(event: PointerEvent) {
                    gestureRouter.handlePointerUp(event);
                },
                onPointerCancel(event: PointerEvent) {
                    gestureRouter.handlePointerCancel(event);
                },
                onHoverChange(cell) {
                    gestureRouter.handleHoverChange(cell);
                },
                onContextMenu(cell) {
                    gestureRouter.handleContextMenu(cell);
                },
                onClick(event: MouseEvent, cell: PaintableCell) {
                    gestureRouter.handleClick(event, cell);
                },
            });
        },
    };
}
