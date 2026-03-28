import type { EditorTool } from "../editor-tools.js";

export type UiDisclosureId = "rule-notes-toggle";

export interface UiSessionState {
    cellSize: number;
    cellSizeByTilingFamily: Record<string, number>;
    editorTool: EditorTool;
    brushSize: number;
    drawerOpen: boolean | null;
    paintStatesByRule: Record<string, number>;
    patchDepthByTilingFamily: Record<string, number>;
    disclosures: Partial<Record<UiDisclosureId, boolean>>;
}

export interface UiSessionStorage {
    load(): UiSessionState;
    clear(): UiSessionState;
    getCellSizes(): Record<string, number>;
    getCellSize(tilingFamily?: string): number;
    setDefaultCellSize(cellSize: number): UiSessionState;
    setCellSizeForTilingFamily(tilingFamily: string, cellSize: number): UiSessionState;
    getEditorTool(): EditorTool;
    setEditorTool(editorTool: EditorTool): UiSessionState;
    getBrushSize(): number;
    setBrushSize(brushSize: number): UiSessionState;
    getDrawerOpen(): boolean | null;
    setDrawerOpen(drawerOpen: boolean): UiSessionState;
    getPaintState(ruleName: string | null): number | null;
    setPaintStateForRule(ruleName: string, paintState: number): UiSessionState;
    getPatchDepths(): Record<string, number>;
    getPatchDepth(tilingFamily: string | null | undefined): number | null;
    setPatchDepthForTilingFamily(tilingFamily: string, patchDepth: number): UiSessionState;
    getDisclosureStates(): Partial<Record<UiDisclosureId, boolean>>;
    setDisclosureState(id: UiDisclosureId, open: boolean): UiSessionState;
}

export interface MatchMediaResult {
    matches: boolean;
}
