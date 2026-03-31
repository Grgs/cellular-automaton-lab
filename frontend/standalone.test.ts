import { afterEach, describe, expect, it, vi } from "vitest";

const bootstrapData = {
    app_defaults: {
        simulation: {
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 10,
                height: 6,
                patch_depth: 0,
            },
            speed: 5,
            rule: "conway",
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
    topology_catalog: [],
    periodic_face_tilings: [],
    server_meta: { app_name: "cellular-automaton-lab" },
    snapshot_version: 5,
};

afterEach(() => {
    vi.resetModules();
    vi.doUnmock("./bootstrap-data.js");
    vi.doUnmock("./standalone/worker-client.js");
    vi.doUnmock("./app-runtime.js");
});

describe("standalone startup", () => {
    it("renders a visible startup error when worker initialization fails", async () => {
        document.body.innerHTML = '<div id="app-startup-error" hidden></div>';
        vi.spyOn(console, "error").mockImplementation(() => {});

        vi.doMock("./bootstrap-data.js", () => ({
            fetchBootstrapData: vi.fn(async () => bootstrapData),
            installBootstrapData: vi.fn((payload) => payload),
        }));
        vi.doMock("./standalone/worker-client.js", () => ({
            createStandaloneEnvironment: vi.fn(async () => {
                throw new Error("worker initialization failed");
            }),
        }));
        vi.doMock("./app-runtime.js", () => ({
            disposeApp: vi.fn(),
            initApp: vi.fn(),
        }));

        await import("./standalone.js");
        await new Promise((resolve) => window.setTimeout(resolve, 0));

        const errorElement = document.getElementById("app-startup-error");
        expect(errorElement).not.toBeNull();
        expect(errorElement?.classList.contains("startup-error-visible")).toBe(true);
        expect(errorElement?.textContent).toContain("Standalone runtime failed to initialize");
        expect(errorElement?.textContent).toContain("worker initialization failed");
    });
});
