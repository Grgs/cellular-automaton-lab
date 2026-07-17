import {
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_FILL,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
    type EditorTool,
} from "../editor-tools.js";
import type { GridView } from "../types/controller-view.js";
import type { PaintableCell, PreviewPaintCell } from "../types/editor.js";

export interface PaneEditGesture {
    tool: EditorTool;
    pointerId: number | null;
    startCell: PaintableCell;
    currentCell: PaintableCell;
    previewCells: Map<string, PreviewPaintCell>;
    moved: boolean;
}

interface PaneGestureControllerOptions {
    canvas: HTMLCanvasElement;
    gridView: GridView;
    getTool: () => EditorTool;
    buildToolCells: (
        tool: EditorTool,
        startCell: PaintableCell,
        endCell: PaintableCell | null,
    ) => PreviewPaintCell[];
    previewCells: (cells: PreviewPaintCell[]) => void;
    clearPreview: () => void;
    commitCells: (cells: PreviewPaintCell[]) => Promise<void>;
    onError: (error: unknown) => void;
}

export interface PaneGestureController {
    dispose(): void;
}

export function createPaneGestureController(
    options: PaneGestureControllerOptions,
): PaneGestureController {
    const {
        canvas,
        gridView,
        getTool,
        buildToolCells,
        previewCells,
        clearPreview,
        commitCells,
        onError,
    } = options;
    const controller = new AbortController();
    const { signal } = controller;
    let activeGesture: PaneEditGesture | null = null;
    let suppressFollowupClick = false;

    function suppressNextClick(): void {
        suppressFollowupClick = true;
        window.setTimeout(() => {
            suppressFollowupClick = false;
        }, 0);
    }

    canvas.addEventListener(
        "pointerdown",
        (event) => {
            const cell = gridView.getCellFromPointerEvent?.(event) ?? null;
            if (!cell) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            const paintableCell = cell as PaintableCell;
            const selectedTool = getTool();
            if (selectedTool === EDITOR_TOOL_FILL) {
                const cells = buildToolCells(EDITOR_TOOL_FILL, paintableCell, paintableCell);
                previewCells(cells);
                suppressNextClick();
                void commitCells(cells)
                    .then(() => clearPreview())
                    .catch(onError);
                return;
            }
            const tool =
                selectedTool === EDITOR_TOOL_LINE || selectedTool === EDITOR_TOOL_RECTANGLE
                    ? selectedTool
                    : EDITOR_TOOL_BRUSH;
            const cells = buildToolCells(tool, paintableCell, paintableCell);
            activeGesture = {
                tool,
                pointerId: event.pointerId ?? null,
                startCell: paintableCell,
                currentCell: paintableCell,
                previewCells: new Map(cells.map((previewCell) => [previewCell.id, previewCell])),
                moved: false,
            };
            previewCells(cells);
            canvas.setPointerCapture?.(event.pointerId);
        },
        { signal },
    );
    canvas.addEventListener(
        "pointermove",
        (event) => {
            if (!activeGesture) {
                return;
            }
            const cell = gridView.getCellFromPointerEvent?.(event) ?? null;
            if (!cell) {
                return;
            }
            event.preventDefault();
            const paintableCell = cell as PaintableCell;
            if (activeGesture.currentCell.id === paintableCell.id) {
                return;
            }
            activeGesture.moved = true;
            const cells =
                activeGesture.tool === EDITOR_TOOL_BRUSH
                    ? buildToolCells(EDITOR_TOOL_LINE, activeGesture.currentCell, paintableCell)
                    : buildToolCells(activeGesture.tool, activeGesture.startCell, paintableCell);
            if (activeGesture.tool === EDITOR_TOOL_BRUSH) {
                cells.forEach((previewCell) =>
                    activeGesture?.previewCells.set(previewCell.id, previewCell),
                );
            } else {
                activeGesture.previewCells = new Map(
                    cells.map((previewCell) => [previewCell.id, previewCell]),
                );
            }
            activeGesture.currentCell = paintableCell;
            previewCells(Array.from(activeGesture.previewCells.values()));
        },
        { signal },
    );
    canvas.addEventListener(
        "pointerup",
        (event) => {
            if (!activeGesture) {
                return;
            }
            event.preventDefault();
            canvas.releasePointerCapture?.(event.pointerId);
            const cells = Array.from(activeGesture.previewCells.values());
            activeGesture = null;
            suppressNextClick();
            void commitCells(cells)
                .then(() => clearPreview())
                .catch(onError);
        },
        { signal },
    );
    canvas.addEventListener(
        "click",
        (event) => {
            if (suppressFollowupClick || activeGesture) {
                return;
            }
            const cell = gridView.getCellFromPointerEvent?.(event) ?? null;
            if (!cell) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            const paintableCell = cell as PaintableCell;
            const tool = getTool() === EDITOR_TOOL_FILL ? EDITOR_TOOL_FILL : EDITOR_TOOL_BRUSH;
            const cells = buildToolCells(tool, paintableCell, paintableCell);
            previewCells(cells);
            void commitCells(cells)
                .then(() => clearPreview())
                .catch(onError);
        },
        { signal },
    );
    canvas.addEventListener(
        "pointercancel",
        () => {
            if (!activeGesture) {
                return;
            }
            activeGesture = null;
            clearPreview();
        },
        { signal },
    );

    return {
        dispose(): void {
            controller.abort();
            activeGesture = null;
            clearPreview();
        },
    };
}
