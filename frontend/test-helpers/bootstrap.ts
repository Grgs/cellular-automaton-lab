import type { BootstrappedFrontendDefaults, BootstrappedTopologyDefinition } from "../types/domain.js";

function geometryKeys(keys: Record<string, string>): Record<string, string> {
    return keys;
}

const DEFAULTS: BootstrappedFrontendDefaults = {
    simulation: {
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 30,
            height: 20,
            patch_depth: 0,
        },
        speed: 5,
        min_grid_size: 4,
        max_grid_size: 200,
        min_patch_depth: 0,
        max_patch_depth: 6,
        min_speed: 1,
        max_speed: 30,
    },
    ui: {
        cell_size: 12,
        min_cell_size: 8,
        max_cell_size: 24,
        storage_key: "cellular-automaton-lab-ui",
    },
    theme: {
        default: "light",
        storage_key: "cellular-automaton-theme",
    },
};

const TOPOLOGIES: ReadonlyArray<BootstrappedTopologyDefinition> = Object.freeze([
    {
        tiling_family: "square",
        label: "Square",
        picker_group: "Classic",
        picker_order: 1,
        sizing_mode: "grid",
        family: "regular",
        viewport_sync_mode: "backend-sync",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        geometry_keys: geometryKeys({ edge: "square" }),
        sizing_policy: { control: "cell_size", default: 12, min: 8, max: 24 },
    },
    {
        tiling_family: "hex",
        label: "Hex",
        picker_group: "Classic",
        picker_order: 2,
        sizing_mode: "grid",
        family: "regular",
        viewport_sync_mode: "backend-sync",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        geometry_keys: geometryKeys({ edge: "hex" }),
        sizing_policy: { control: "cell_size", default: 16, min: 10, max: 24 },
    },
    {
        tiling_family: "penrose-p3-rhombs",
        label: "Penrose P3 Rhombs",
        picker_group: "Aperiodic",
        picker_order: 30,
        sizing_mode: "patch_depth",
        family: "aperiodic",
        viewport_sync_mode: "backend-sync",
        supported_adjacency_modes: ["edge", "vertex"],
        default_adjacency_mode: "edge",
        geometry_keys: geometryKeys({
            edge: "penrose-p3-rhombs",
            vertex: "penrose-p3-rhombs-vertex",
        }),
        sizing_policy: { control: "patch_depth", default: 4, min: 0, max: 6 },
    },
]);

export function installFrontendGlobals(): void {
    window.APP_DEFAULTS = structuredClone(DEFAULTS);
    window.APP_TOPOLOGIES = TOPOLOGIES;
    window.APP_PERIODIC_FACE_TILINGS = [];
    window.__appReady = true;
}
