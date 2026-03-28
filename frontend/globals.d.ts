import type {
    BootstrappedFrontendDefaults,
    BootstrappedTopologyDefinition,
} from "./types/domain.js";

declare global {
    interface Window {
        APP_DEFAULTS?: BootstrappedFrontendDefaults;
        APP_TOPOLOGIES?: ReadonlyArray<BootstrappedTopologyDefinition>;
        APP_PERIODIC_FACE_TILINGS?: unknown;
        __appReady?: boolean;
    }
}

export {};
