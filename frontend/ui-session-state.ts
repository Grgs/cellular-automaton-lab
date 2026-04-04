import { DEFAULT_CELL_SIZE } from "./state/constants.js";
import { defaultCellSizeForTilingFamily } from "./state/sizing-state.js";
import { DEFAULT_BRUSH_SIZE, DEFAULT_EDITOR_TOOL } from "./editor-tools.js";
import type { UiSessionState } from "./types/session.js";

export function createEmptyUiSession(defaultTilingFamily: string): UiSessionState {
    return {
        cellSize: defaultCellSizeForTilingFamily(defaultTilingFamily) || DEFAULT_CELL_SIZE,
        cellSizeByTilingFamily: {},
        unsafeSizingEnabled: false,
        editorTool: DEFAULT_EDITOR_TOOL,
        brushSize: DEFAULT_BRUSH_SIZE,
        drawerOpen: null,
        paintStatesByRule: {},
        patchDepthByTilingFamily: {},
        disclosures: {},
    };
}

export function cloneUiSession(session: UiSessionState): UiSessionState {
    return {
        cellSize: session.cellSize,
        cellSizeByTilingFamily: { ...session.cellSizeByTilingFamily },
        unsafeSizingEnabled: Boolean(session.unsafeSizingEnabled),
        editorTool: session.editorTool,
        brushSize: session.brushSize,
        drawerOpen: session.drawerOpen,
        paintStatesByRule: { ...session.paintStatesByRule },
        patchDepthByTilingFamily: { ...session.patchDepthByTilingFamily },
        disclosures: { ...session.disclosures },
    };
}
