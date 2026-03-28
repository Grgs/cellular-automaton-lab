export const EDITOR_TOOL_BRUSH = "brush";
export const EDITOR_TOOL_LINE = "line";
export const EDITOR_TOOL_RECTANGLE = "rectangle";
export const EDITOR_TOOL_FILL = "fill";

export type EditorTool =
    | typeof EDITOR_TOOL_BRUSH
    | typeof EDITOR_TOOL_LINE
    | typeof EDITOR_TOOL_RECTANGLE
    | typeof EDITOR_TOOL_FILL;

export const EDITOR_TOOLS = Object.freeze([
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
    EDITOR_TOOL_FILL,
]) as readonly EditorTool[];

export const DEFAULT_EDITOR_TOOL = EDITOR_TOOL_BRUSH;
export const DEFAULT_BRUSH_SIZE = 1;
export const MIN_BRUSH_SIZE = 1;
export const MAX_BRUSH_SIZE = 3;
export const MAX_EDITOR_HISTORY = 50;
export const EDITOR_SHORTCUT_HINT = "Shortcuts: B brush, L line, R rectangle, F fill, 1-3 brush size.";

export function normalizeEditorTool(tool: unknown): EditorTool {
    return typeof tool === "string" && EDITOR_TOOLS.includes(tool as EditorTool)
        ? (tool as EditorTool)
        : DEFAULT_EDITOR_TOOL;
}

export function normalizeBrushSize(value: unknown): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return DEFAULT_BRUSH_SIZE;
    }
    return Math.min(MAX_BRUSH_SIZE, Math.max(MIN_BRUSH_SIZE, Math.round(parsed)));
}

export function brushRadiusForSize(brushSize: unknown): number {
    return normalizeBrushSize(brushSize) - 1;
}
