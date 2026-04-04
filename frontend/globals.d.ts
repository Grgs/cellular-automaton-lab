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
    }
}

export {};
