import type {
    BootstrappedFrontendDefaults,
    FrontendDefaults,
} from "./types/domain.js";

const FALLBACK_DEFAULTS: FrontendDefaults = Object.freeze({
    simulation: Object.freeze({
        topology_spec: Object.freeze({
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 30,
            height: 20,
            patch_depth: 4,
        }),
        speed: 7,
        rule: "conway",
        min_grid_size: 5,
        max_grid_size: 250,
        min_patch_depth: 0,
        max_patch_depth: 6,
        min_speed: 1,
        max_speed: 30,
    }),
    ui: Object.freeze({
        cell_size: 12,
        min_cell_size: 4,
        max_cell_size: 24,
        storage_key: "cellular-automaton-ui-session",
    }),
    theme: Object.freeze({
        default: "dark",
        storage_key: "cellular-automaton-theme",
    }),
}) as FrontendDefaults;

function appDefaults(): BootstrappedFrontendDefaults {
    return window.APP_DEFAULTS ?? {};
}

const bootstrappedDefaults = appDefaults();
const bootstrappedSimulation = bootstrappedDefaults.simulation ?? {};
const bootstrappedUi = bootstrappedDefaults.ui ?? {};
const bootstrappedTheme = bootstrappedDefaults.theme ?? {};

export const FRONTEND_DEFAULTS: FrontendDefaults = Object.freeze({
    simulation: Object.freeze({
        ...FALLBACK_DEFAULTS.simulation,
        ...bootstrappedSimulation,
        topology_spec: Object.freeze({
            ...FALLBACK_DEFAULTS.simulation.topology_spec,
            ...(bootstrappedSimulation.topology_spec ?? {}),
        }),
    }),
    ui: Object.freeze({
        ...FALLBACK_DEFAULTS.ui,
        ...bootstrappedUi,
    }),
    theme: Object.freeze({
        ...FALLBACK_DEFAULTS.theme,
        ...bootstrappedTheme,
    }),
}) as FrontendDefaults;
