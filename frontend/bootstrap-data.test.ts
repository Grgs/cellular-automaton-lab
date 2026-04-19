import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("bootstrap-data", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.restoreAllMocks();
    });

    it("installs bootstrap data into window globals", async () => {
        const { installBootstrapData } = await import("./bootstrap-data.js");

        const payload = installBootstrapData({
            app_defaults: {
                simulation: {
                    topology_spec: {
                        tiling_family: "hex",
                        adjacency_mode: "edge",
                        sizing_mode: "grid",
                        width: 12,
                        height: 8,
                        patch_depth: 0,
                    },
                    speed: 5,
                    rule: "hexlife",
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
                    storage_key: "ui-key",
                },
                theme: {
                    default: "light",
                    storage_key: "theme-key",
                },
            },
            topology_catalog: [
                {
                    tiling_family: "hex",
                    label: "Hex",
                    picker_group: "Classic",
                    picker_order: 2,
                    sizing_mode: "grid",
                    family: "regular",
                    render_kind: "regular_grid",
                    viewport_sync_mode: "backend-sync",
                    supported_adjacency_modes: ["edge"],
                    default_adjacency_mode: "edge",
                    default_rules: { edge: "hexlife" },
                    geometry_keys: { edge: "hex" },
                    sizing_policy: { control: "cell_size", default: 12, min: 8, max: 24 },
                },
            ],
            periodic_face_tilings: [],
            aperiodic_families: [
                {
                    tiling_family: "penrose-p3-rhombs",
                    label: "Penrose P3 Rhombs",
                    experimental: false,
                    implementation_status: "true_substitution",
                    promotion_blocker: null,
                    public_cell_kinds: ["thick-rhomb", "thin-rhomb"],
                },
            ],
            server_meta: { app_name: "cellular-automaton-lab" },
            snapshot_version: 5,
        });

        expect(payload.app_defaults.simulation.rule).toBe("hexlife");
        expect(window.APP_DEFAULTS.simulation.rule).toBe("hexlife");
        expect(window.APP_TOPOLOGIES[0]?.tiling_family).toBe("hex");
        expect(window.APP_APERIODIC_FAMILIES[0]?.tiling_family).toBe("penrose-p3-rhombs");
    });

    it("loads bootstrap data over fetch", async () => {
        const { fetchBootstrapData } = await import("./bootstrap-data.js");
        vi.stubGlobal(
            "fetch",
            vi.fn(async () => ({
                ok: true,
                json: async () => ({
                    app_defaults: window.APP_DEFAULTS,
                    topology_catalog: window.APP_TOPOLOGIES,
                    periodic_face_tilings: window.APP_PERIODIC_FACE_TILINGS,
                    aperiodic_families: window.APP_APERIODIC_FAMILIES,
                    server_meta: { app_name: "cellular-automaton-lab" },
                    snapshot_version: 5,
                }),
            })),
        );

        const payload = await fetchBootstrapData("/api/bootstrap");

        expect(payload.server_meta.app_name).toBe("cellular-automaton-lab");
        expect(payload.snapshot_version).toBe(5);
        expect(payload.topology_catalog.length).toBeGreaterThan(0);
        expect(payload.aperiodic_families.length).toBeGreaterThan(0);
        expect(payload.aperiodic_families[0]?.implementation_status).toBeTruthy();
    });
});
