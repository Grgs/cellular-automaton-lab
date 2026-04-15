import type {
    BootstrappedFrontendDefaults,
    BootstrappedTopologyDefinition,
} from "./types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "./types/rendering.js";

declare global {
    interface Window {
        APP_DEFAULTS: BootstrappedFrontendDefaults;
        APP_TOPOLOGIES: ReadonlyArray<BootstrappedTopologyDefinition>;
        APP_PERIODIC_FACE_TILINGS: ReadonlyArray<PeriodicFaceTilingDescriptor>;
        __appReady?: boolean;
        __appDiagnostics?: ((() => {
            tilingFamily: string | null;
            patchDepth: number | null;
            topologyCellCount: number;
            width: number | null;
            height: number | null;
            topologyRevision: string | null;
        } | null) | null);
    }
}

export {};
