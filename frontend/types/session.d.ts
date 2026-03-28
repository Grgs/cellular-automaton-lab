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
    setCellSize(tilingFamilyOrCellSize: string | number, cellSize?: number): UiSessionState | void;
    getEditorTool(): EditorTool;
    setEditorTool(editorTool: EditorTool): void;
    getBrushSize(): number;
    setBrushSize(brushSize: number): void;
    getDrawerOpen(): boolean | null;
    setDrawerOpen(drawerOpen: boolean): void;
    getPaintState(ruleName: string | null): number | null;
    setPaintState(ruleName: string | null, paintState: number): void;
    getPatchDepths(): Record<string, number>;
    getPatchDepth(tilingFamily: string | null | undefined): number | null;
    setPatchDepth(tilingFamily: string | null | undefined, patchDepth: number): void;
    getDisclosureStates(): Partial<Record<UiDisclosureId, boolean>>;
    setDisclosureState(id: UiDisclosureId, open: boolean): void;
}

export interface MatchMediaResult {
    matches: boolean;
}
