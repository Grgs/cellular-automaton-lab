import type { BootstrappedFrontendDefaults, FrontendDefaults } from "./types/domain.js";
import defaultConfig from "../config/defaults.json";

const FALLBACK_DEFAULTS = defaultConfig as FrontendDefaults;

function cloneDefaults(defaults: FrontendDefaults): FrontendDefaults {
    return Object.freeze({
        simulation: Object.freeze({
            ...defaults.simulation,
            topology_spec: Object.freeze({
                ...defaults.simulation.topology_spec,
            }),
        }),
        ui: Object.freeze({
            ...defaults.ui,
        }),
        theme: Object.freeze({
            ...defaults.theme,
        }),
    }) as FrontendDefaults;
}

function appDefaults(): BootstrappedFrontendDefaults {
    return window.APP_DEFAULTS ?? FALLBACK_DEFAULTS;
}

export const FRONTEND_DEFAULTS: FrontendDefaults = cloneDefaults(appDefaults());
