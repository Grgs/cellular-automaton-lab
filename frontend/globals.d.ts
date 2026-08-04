import type {
    BootstrappedAperiodicFamilyDefinition,
    BootstrappedFrontendDefaults,
    BootstrappedTopologyDefinition,
    CellStateUpdate,
    TopologyPayload,
} from "./types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";
import type { RenderDiagnosticsSnapshot } from "./types/rendering.js";
import type { LiveForkCapability } from "./types/controller.js";

export interface AppReadinessDiagnosticsSnapshot {
    appReady: boolean;
    blockingActivityVisible: boolean;
    blockingActivityKind: string | null;
    blockingActivityMessage: string;
    blockingActivityDetail: string;
    blockingActivityStartedAt: number | null;
    topologyRevision: string | null;
    topologyCellCount: number;
    patchDepth: number | null;
    renderCellSize: number | null;
    gridSizeText: string;
    generationText: string;
    statusText: string;
}

export interface AppDiagnosticsSnapshot {
    tilingFamily: string | null;
    patchDepth: number | null;
    topologyCellCount: number;
    width: number | null;
    height: number | null;
    topologyRevision: string | null;
    transformReport: RenderDiagnosticsSnapshot | null;
    diagnosticErrors: string[];
    readiness: AppReadinessDiagnosticsSnapshot;
}

export interface ReviewApi {
    getDiagnostics(): AppDiagnosticsSnapshot | null;
    applyTopology(topology: TopologyPayload): Promise<void>;
    applyCellStates(reviewCellStates: Record<string, number> | CellStateUpdate[]): Promise<void>;
    forceFullRender(): Promise<void>;
    resetState(): Promise<void>;
    sampleRenderedCellPixel(cellId: string): [number, number, number, number] | null;
}

declare global {
    interface Window {
        APP_DEFAULTS: BootstrappedFrontendDefaults;
        APP_TOPOLOGIES: ReadonlyArray<BootstrappedTopologyDefinition>;
        APP_PERIODIC_FACE_TILINGS: ReadonlyArray<PeriodicFaceTilingDescriptor>;
        APP_APERIODIC_FAMILIES: ReadonlyArray<BootstrappedAperiodicFamilyDefinition>;
        APP_SESSION_ID?: string;
        __appReady?: boolean;
        __standaloneStartupMs?: number;
        __standaloneStartupBudgetMs?: number;
        /** Standalone live-fork seam consumed only by the repo runtime profiler. */
        __sf?: Extract<LiveForkCapability, { kind: "supported" }>;
        __reviewApi?: ReviewApi | null;
    }
}

export {};
