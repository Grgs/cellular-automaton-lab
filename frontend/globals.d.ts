import type {
    BootstrappedFrontendDefaults,
    BootstrappedTopologyDefinition,
    TopologyPayload,
} from "./types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";
import type { RenderDiagnosticsSnapshot } from "./types/rendering.js";

interface AppReadinessDiagnosticsSnapshot {
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

interface AppDiagnosticsSnapshot {
    tilingFamily: string | null;
    patchDepth: number | null;
    topologyCellCount: number;
    width: number | null;
    height: number | null;
    topologyRevision: string | null;
    transformReport: RenderDiagnosticsSnapshot | null;
    readiness: AppReadinessDiagnosticsSnapshot;
}

declare global {
    interface Window {
        APP_DEFAULTS: BootstrappedFrontendDefaults;
        APP_TOPOLOGIES: ReadonlyArray<BootstrappedTopologyDefinition>;
        APP_PERIODIC_FACE_TILINGS: ReadonlyArray<PeriodicFaceTilingDescriptor>;
        __appReady?: boolean;
        __appDiagnostics?: ((() => AppDiagnosticsSnapshot | null) | null);
        __applyReviewTopology?: (((topology: TopologyPayload) => Promise<void>) | null);
        __resolveRenderedCellCenter?: (((cellId: string) => Promise<{ x: number; y: number } | null>) | null);
    }
}

export {};
