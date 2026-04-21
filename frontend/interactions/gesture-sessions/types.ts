import type { PaintableCell } from "../../types/editor.js";
import type { SimulationSnapshot } from "../../types/domain.js";
import type { InteractionEditPolicy } from "../edit-policy.js";

export type PointerDownIntent =
    | { kind: "ignore" }
    | { kind: "right-selection" }
    | { kind: "direct-paint" }
    | { kind: "running-brush" }
    | { kind: "blocked-advanced-tool" }
    | { kind: "blocked-editing" }
    | { kind: "fill-click" }
    | { kind: "editor-pointer" };

export interface PointerGestureSession {
    kind: "editor-pointer" | "legacy-drag" | "right-selection";
    handleMove(event: PointerEvent, cell: PaintableCell): void;
    handleUp(event: PointerEvent): boolean;
    cancel(event: PointerEvent): boolean;
}

export interface EditorGestureController {
    isPointerActive(): boolean;
    beginPointerSession(cell: PaintableCell, pointerId?: number | null): Promise<boolean>;
    handlePointerMove(cell: PaintableCell): void;
    handlePointerUp(): Promise<SimulationSnapshot | null>;
    cancelActivePreview(): Promise<void>;
    isClickSuppressed(): boolean;
    handleClick(cell: PaintableCell): Promise<{ handled: boolean }>;
}

export interface LegacyDragController {
    isActive(): boolean;
    begin(cell: PaintableCell, pointerId?: number | null, paintStateOverride?: number): void;
    update(cell: PaintableCell): void;
    end(): Promise<SimulationSnapshot | null>;
    cancel(): Promise<null>;
}

export interface GestureRouterOptions {
    surfaceElement: HTMLElement | null;
    editPolicy: InteractionEditPolicy;
    editorSession: EditorGestureController;
    legacyDrag: LegacyDragController;
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

export interface LegacyDragGestureSessionOptions {
    pointerId: number | null;
    legacyDrag: LegacyDragController;
    buttonMask: number;
    onCancel?: () => void;
}

export interface EditorPointerSessionOptions {
    pointerId: number | null;
    editorSession: EditorGestureController;
}

export interface RightSelectionGestureSessionOptions {
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
}
