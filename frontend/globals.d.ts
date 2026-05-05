import type {
    BootstrappedAperiodicFamilyDefinition,
    BootstrappedFrontendDefaults,
    BootstrappedTopologyDefinition,
    CellStateUpdate,
    TopologyPayload,
} from "./types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";
import type { RenderDiagnosticsSnapshot } from "./types/rendering.js";

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
    resetState(): Promise<void>;
    sampleRenderedCellPixel(cellId: string): [number, number, number, number] | null;
}

declare global {
    interface Window {
        APP_DEFAULTS: BootstrappedFrontendDefaults;
        APP_TOPOLOGIES: ReadonlyArray<BootstrappedTopologyDefinition>;
        APP_PERIODIC_FACE_TILINGS: ReadonlyArray<PeriodicFaceTilingDescriptor>;
        APP_APERIODIC_FAMILIES: ReadonlyArray<BootstrappedAperiodicFamilyDefinition>;
        __appReady?: boolean;
        __reviewApi?: ReviewApi | null;
    }
}

export {};
