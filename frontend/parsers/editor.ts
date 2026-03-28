import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
    clampBrushSize,
    resolveEditorTool,
} from "../editor-tools.js";
import type { EditorTool } from "../editor-tools.js";

export function parseEditorTool(value: unknown): EditorTool {
    return typeof value === "string"
        ? resolveEditorTool(value)
        : DEFAULT_EDITOR_TOOL;
}

export function parseBrushSize(value: unknown): number {
    const parsed = Number(value);
    return Number.isFinite(parsed)
        ? clampBrushSize(parsed)
        : DEFAULT_BRUSH_SIZE;
}
