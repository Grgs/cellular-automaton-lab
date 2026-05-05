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
    aperiodic_families: [],
    server_meta: { app_name: "cellular-automaton-lab" },
    snapshot_version: 5,
};

function deferred<T>(): {
    promise: Promise<T>;
    resolve: (value: T) => void;
    reject: (reason?: unknown) => void;
} {
    let resolvePromise!: (value: T) => void;
    let rejectPromise!: (reason?: unknown) => void;
    const promise = new Promise<T>((resolve, reject) => {
        resolvePromise = resolve;
        rejectPromise = reject;
    });
    return {
        promise,
        resolve: resolvePromise,
        reject: rejectPromise,
    };
}

function installStandaloneShell(): void {
    document.body.innerHTML = `
        <main id="app-frame" class="app-frame">
            <div id="grid-viewport" class="grid-viewport">
                <div id="standalone-startup-overlay" class="standalone-startup-status" aria-hidden="false">
                    <div class="standalone-startup-status-card">
                        <div class="blocking-activity-spinner standalone-startup-spinner" aria-hidden="true"></div>
                        <div class="standalone-startup-copy">
                            <strong id="standalone-startup-message" class="blocking-activity-message">Loading app data</strong>
                            <span id="standalone-startup-detail" class="blocking-activity-detail">
                                Reading bundled defaults and topology catalog.
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </main>
        <div id="app-startup-error" hidden></div>
    `;
}

function appFrame(): HTMLElement {
    const element = document.getElementById("app-frame");
    if (!(element instanceof HTMLElement)) {
        throw new Error("app frame not found");
    }
    return element;
}

function startupOverlay(): HTMLElement {
    const overlay = document.getElementById("standalone-startup-overlay");
    if (!(overlay instanceof HTMLElement)) {
        throw new Error("standalone startup overlay not found");
    }
    return overlay;
}

function gridViewport(): HTMLElement {
    const viewport = document.getElementById("grid-viewport");
    if (!(viewport instanceof HTMLElement)) {
        throw new Error("grid viewport not found");
    }
    return viewport;
}

function startupMessage(): HTMLElement {
    const element = document.getElementById("standalone-startup-message");
    if (!(element instanceof HTMLElement)) {
        throw new Error("standalone startup message not found");
    }
    return element;
}

function startupDetail(): HTMLElement {
    const element = document.getElementById("standalone-startup-detail");
    if (!(element instanceof HTMLElement)) {
        throw new Error("standalone startup detail not found");
    }
    return element;
}

async function flushAsyncStartup(): Promise<void> {
    await Promise.resolve();
    await Promise.resolve();
    await new Promise((resolve) => window.setTimeout(resolve, 0));
}

afterEach(() => {
    vi.resetModules();
    vi.restoreAllMocks();
    vi.doUnmock("./bootstrap-data.js");
    vi.doUnmock("./standalone/worker-client.js");
    vi.doUnmock("./app-runtime.js");
});

describe("standalone startup", () => {
    it("shows staged overlay progress and hides the overlay after first render", async () => {
        installStandaloneShell();

        const bootstrapDeferred = deferred<typeof bootstrapData>();
        const environmentDeferred = deferred<{
            backend: object;
            bootstrapData: typeof bootstrapData;
        }>();
        const initDeferred = deferred<void>();

        vi.doMock("./bootstrap-data.js", () => ({
            fetchBootstrapData: vi.fn(() => bootstrapDeferred.promise),
            installBootstrapData: vi.fn((payload) => payload),
        }));
        vi.doMock("./standalone/worker-client.js", () => ({
            createStandaloneEnvironment: vi.fn(() => environmentDeferred.promise),
        }));
        vi.doMock("./app-runtime.js", () => ({
            disposeApp: vi.fn(),
            initApp: vi.fn(() => initDeferred.promise),
        }));

        await import("./standalone.js");
        await flushAsyncStartup();

        expect(startupOverlay().hidden).toBe(false);
        expect(startupOverlay().getAttribute("aria-hidden")).toBe("false");
        expect(startupMessage().textContent).toBe("Loading app data");
        expect(startupDetail().textContent?.trim()).toBe(
            "Reading bundled defaults and topology catalog.",
        );
        expect(startupOverlay().parentElement).toBe(gridViewport());
        expect(appFrame().classList.contains("standalone-startup-pending")).toBe(true);
        expect(appFrame().getAttribute("aria-busy")).toBe("true");
        expect(appFrame().hasAttribute("inert")).toBe(true);

        bootstrapDeferred.resolve(bootstrapData);
        await flushAsyncStartup();

        expect(startupMessage().textContent).toBe("Starting Python runtime");
        expect(startupDetail().textContent?.trim()).toBe(
            "Loading Pyodide, bundled Python sources, and the first board.",
        );

        environmentDeferred.resolve({ backend: {}, bootstrapData });
        await flushAsyncStartup();
        expect(startupMessage().textContent).toBe("Starting Python runtime");
        expect(startupDetail().textContent?.trim()).toBe(
            "Loading Pyodide, bundled Python sources, and the first board.",
        );

        initDeferred.resolve();
        await flushAsyncStartup();

        expect(startupOverlay().hidden).toBe(true);
        expect(startupOverlay().getAttribute("aria-hidden")).toBe("true");
        expect(startupOverlay().classList.contains("is-error")).toBe(false);
        expect(appFrame().classList.contains("standalone-startup-pending")).toBe(false);
        expect(appFrame().getAttribute("aria-busy")).toBe("false");
        expect(appFrame().hasAttribute("inert")).toBe(false);
    });

    it("keeps the overlay visible in error mode and surfaces the startup failure", async () => {
        installStandaloneShell();
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
        await flushAsyncStartup();

        expect(startupOverlay().hidden).toBe(false);
        expect(startupOverlay().getAttribute("aria-hidden")).toBe("false");
        expect(startupOverlay().classList.contains("is-error")).toBe(true);
        expect(startupMessage().textContent).toBe("Standalone runtime failed to initialize");
        expect(startupDetail().textContent).toContain("worker initialization failed");
        expect(appFrame().classList.contains("standalone-startup-pending")).toBe(true);
        expect(appFrame().getAttribute("aria-busy")).toBe("true");
        expect(appFrame().hasAttribute("inert")).toBe(true);

        const errorElement = document.getElementById("app-startup-error");
        expect(errorElement).not.toBeNull();
        expect(errorElement?.classList.contains("startup-error-visible")).toBe(true);
        expect(errorElement?.textContent).toContain("Standalone runtime failed to initialize");
        expect(errorElement?.textContent).toContain("worker initialization failed");
    });
});
