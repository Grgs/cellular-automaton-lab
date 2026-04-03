import type { SimulationMutationOptions } from "./controller-runtime.js";
import type { BlockingActivityConfig, MutationRunnerOptions } from "./controller-runtime.js";
import type { ConfigSyncBody, EmptyControlCommandPath, ResetControlBody } from "./controller-api.js";
import type { CellIdentifier, CellStateDefinition, SimulationSnapshot } from "./domain.js";
import type { PreviewPaintCells } from "./editor.js";
import type { TopologyRenderPayload } from "./state.js";

export interface ViewportDimensions {
    width: number;
    height: number;
}

export interface ViewportSyncOptions {
    includeConfig?: boolean;
    force?: boolean;
    preview?: boolean;
    previewApplied?: boolean;
    delay?: number;
    body?: ConfigSyncBody;
    desiredDimensions?: ViewportDimensions;
    blockingActivity?: BlockingActivityConfig | null;
}

export interface AppView {
    renderAll(): void;
    renderGrid(): void;
    renderControlsPanel(): void;
    viewportDimensionsFor(geometry?: string, ruleName?: string | null, cellSizeOverride?: number): ViewportDimensions;
    applyViewportPreview(dimensions: ViewportDimensions): void;
}

export interface InteractionController {
    bindGridInteractions(): void;
    toggleCell?(cell: CellIdentifier): Promise<void>;
    sendControl(path: EmptyControlCommandPath, options?: SimulationMutationOptions): Promise<SimulationSnapshot | null>;
    sendControl(
        path: "/api/control/reset",
        body: ResetControlBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    sendControl(
        path: "/api/config",
        body: ConfigSyncBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    runSerialized<T>(task: () => Promise<T>, options?: MutationRunnerOptions): Promise<T>;
    undo?(): Promise<SimulationSnapshot | null>;
    redo?(): Promise<SimulationSnapshot | null>;
    cancelActivePreview?(): Promise<void>;
}

export interface ViewportController {
    sync(options?: ViewportSyncOptions): Promise<boolean>;
    schedule(options?: ViewportSyncOptions): boolean;
    flush(options?: ViewportSyncOptions): Promise<boolean>;
    suppressAutoSync(durationMs?: number): void;
    install(viewportElement: HTMLElement | null): void;
    dispose(): void;
}

export interface GridView {
    render?(
        payload: TopologyRenderPayload,
        cellSize: number,
        stateDefinitions: CellStateDefinition[],
        geometry: string,
    ): void;
    getCellFromPointerEvent?(event: Event): CellIdentifier | null;
    setPreviewCells(cells: PreviewPaintCells): void;
    clearPreview(): void;
}

export interface ViewportControllerDependencies {
    getCurrentDimensions(): ViewportDimensions;
    getViewportDimensions(geometry?: string, ruleName?: string | null, cellSize?: number): ViewportDimensions;
    collectConfig(): { speed: number; rule: string };
    unsafeSizeOverrideEnabled?(): boolean;
    applyPreview(dimensions: ViewportDimensions): void;
    sendControl(
        path: "/api/config",
        body: ConfigSyncBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    sameDimensions(left: ViewportDimensions, right: ViewportDimensions | null | undefined): boolean;
}
