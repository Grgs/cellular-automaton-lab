import { afterEach, describe, expect, it } from "vitest";

import { createFilmstripView, type IntervalScheduler } from "./compare-filmstrip-view.js";
import type { SimulationBackend } from "../types/controller.js";
import type {
    SeedFilmstripResult,
    SimulationSnapshot,
    TopologyFilmstrip,
    TopologyPreview,
    TopologySpec,
} from "../types/domain.js";

function topologySpec(): TopologySpec {
    return {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 2,
        height: 2,
        patch_depth: 0,
    };
}

/** A 2×2 square board whose cell ids (a..d) match the filmstrip frame keys. */
function squarePreview(): TopologyPreview {
    const ids = ["a", "b", "c", "d"];
    return {
        topology_revision: "t",
        topology_spec: topologySpec(),
        cells: ids.map((id, index) => ({
            id,
            kind: "square",
            center: { x: (index % 2) + 0.5, y: Math.floor(index / 2) + 0.5 },
            vertices: [
                { x: index % 2, y: Math.floor(index / 2) },
                { x: (index % 2) + 1, y: Math.floor(index / 2) },
                { x: (index % 2) + 1, y: Math.floor(index / 2) + 1 },
                { x: index % 2, y: Math.floor(index / 2) + 1 },
            ],
        })),
    };
}

function tiling(geometry: string, frames: Record<string, number>[]): TopologyFilmstrip {
    return {
        geometry,
        tiling_family: "square",
        family: "regular",
        cell_count: 4,
        topology: {} as TopologyFilmstrip["topology"],
        topology_spec: topologySpec(),
        frames,
        extinction_step: null,
        period: null,
        note: null,
    };
}

function filmstrip(tilings: TopologyFilmstrip[], frameCount: number): SeedFilmstripResult {
    return {
        rule_name: "conway",
        seed: "1100",
        traversal: "bfs",
        frame_count: frameCount,
        grid_size: 2,
        tilings,
    };
}

function manualScheduler(): {
    scheduler: IntervalScheduler;
    tick(): void;
    active(): number;
} {
    const handlers = new Map<number, () => void>();
    let nextId = 1;
    return {
        scheduler: {
            setInterval(handler: () => void): number {
                const id = nextId++;
                handlers.set(id, handler);
                return id;
            },
            clearInterval(id: number): void {
                handlers.delete(id);
            },
        },
        tick(): void {
            for (const handler of [...handlers.values()]) {
                handler();
            }
        },
        active(): number {
            return handlers.size;
        },
    };
}

function stubBackend(previewTopology: SimulationBackend["previewTopology"]): SimulationBackend {
    const snapshot = {} as SimulationSnapshot;
    return {
        getState: async () => snapshot,
        getRules: async () => ({ rules: [] }),
        dispose: () => {},
        postControl: async () => snapshot,
        toggleCell: async () => snapshot,
        setCell: async () => snapshot,
        setCells: async () => snapshot,
        compareSeed: async () => ({
            rule_name: "conway",
            seed: "",
            seed_bits: 0,
            traversal: "bfs",
            steps: 1,
            grid_size: 16,
            degenerate: false,
            results: [],
        }),
        requestFilmstrip: async () => filmstrip([tiling("square", [{}])], 1),
        previewTopology,
    };
}

function liveCount(view: { element: HTMLElement }): number {
    return view.element.querySelectorAll(".compare-filmstrip-slot polygon.is-live").length;
}

function transportButton(view: { element: HTMLElement }, title: string): HTMLButtonElement {
    const button = view.element.querySelector<HTMLButtonElement>(
        `.compare-filmstrip-btn[title="${title}"]`,
    );
    if (!button) {
        throw new Error(`missing transport button: ${title}`);
    }
    return button;
}

describe("createFilmstripView", () => {
    afterEach(() => {
        document.body.innerHTML = "";
    });

    it("renders one board per tiling showing the seed frame", async () => {
        const backend = stubBackend(async () => squarePreview());
        const clock = manualScheduler();
        const view = createFilmstripView({ backend, scheduler: clock.scheduler });
        document.body.append(view.element);

        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }, { c: 1 }, {}])], 3));

        expect(view.element.querySelectorAll(".compare-filmstrip-board")).toHaveLength(1);
        expect(liveCount(view)).toBe(2); // frame 0: a, b
        expect(view.element.querySelector(".compare-filmstrip-counter")?.textContent).toBe(
            "gen 0 / 2",
        );
    });

    it("advances every board in lockstep on each clock tick while playing", async () => {
        const backend = stubBackend(async () => squarePreview());
        const clock = manualScheduler();
        const view = createFilmstripView({ backend, scheduler: clock.scheduler });
        document.body.append(view.element);
        await view.load(
            filmstrip(
                [
                    tiling("square", [{ a: 1, b: 1 }, { c: 1 }, {}]),
                    tiling("hex", [{ a: 1 }, { b: 1, c: 1, d: 1 }, {}]),
                ],
                3,
            ),
        );

        expect(clock.active()).toBe(0); // starts paused
        transportButton(view, "Play / pause").click();
        expect(clock.active()).toBe(1);

        clock.tick(); // -> gen 1
        // square: c (1 live); hex: b,c,d (3 live) => 4 total
        expect(liveCount(view)).toBe(4);
        expect(view.element.querySelector(".compare-filmstrip-counter")?.textContent).toBe(
            "gen 1 / 2",
        );

        clock.tick(); // -> gen 2 (last, all extinct)
        expect(liveCount(view)).toBe(0);
        // Non-looping: the next tick stops the clock at the end.
        clock.tick();
        expect(clock.active()).toBe(0);
    });

    it("loops back to the seed frame instead of stopping when loop is set", async () => {
        const backend = stubBackend(async () => squarePreview());
        const clock = manualScheduler();
        const view = createFilmstripView({ backend, scheduler: clock.scheduler, loop: true });
        document.body.append(view.element);
        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }, { c: 1 }])], 2));

        transportButton(view, "Play / pause").click();
        clock.tick(); // -> gen 1
        clock.tick(); // wraps -> gen 0
        expect(view.element.querySelector(".compare-filmstrip-counter")?.textContent).toBe(
            "gen 0 / 1",
        );
        expect(clock.active()).toBe(1); // still playing
    });

    it("supports manual step, seek and reset which pause playback", async () => {
        const backend = stubBackend(async () => squarePreview());
        const clock = manualScheduler();
        const view = createFilmstripView({ backend, scheduler: clock.scheduler });
        document.body.append(view.element);
        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }, { c: 1 }, { d: 1 }])], 3));

        transportButton(view, "Play / pause").click();
        expect(clock.active()).toBe(1);
        transportButton(view, "Step forward one generation").click();
        expect(clock.active()).toBe(0); // manual control pauses
        expect(liveCount(view)).toBe(1); // gen 1: c

        const scrubber = view.element.querySelector<HTMLInputElement>(
            ".compare-filmstrip-scrubber",
        );
        if (!scrubber) {
            throw new Error("missing scrubber");
        }
        scrubber.value = "2";
        scrubber.dispatchEvent(new Event("input"));
        expect(view.element.querySelector(".compare-filmstrip-counter")?.textContent).toBe(
            "gen 2 / 2",
        );

        transportButton(view, "Back to the seed").click();
        expect(view.element.querySelector(".compare-filmstrip-counter")?.textContent).toBe(
            "gen 0 / 2",
        );
        expect(liveCount(view)).toBe(2);
    });

    it("re-times the running clock when the speed changes", async () => {
        const backend = stubBackend(async () => squarePreview());
        const clock = manualScheduler();
        const view = createFilmstripView({ backend, scheduler: clock.scheduler });
        document.body.append(view.element);
        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }, { c: 1 }])], 3));

        transportButton(view, "Play / pause").click();
        expect(clock.active()).toBe(1);
        const speed = view.element.querySelector<HTMLSelectElement>(".compare-filmstrip-speed");
        if (!speed) {
            throw new Error("missing speed select");
        }
        speed.value = "2";
        speed.dispatchEvent(new Event("change"));
        expect(clock.active()).toBe(1); // exactly one interval, re-timed
    });

    it("disables playback for a single-frame filmstrip", async () => {
        const backend = stubBackend(async () => squarePreview());
        const clock = manualScheduler();
        const view = createFilmstripView({ backend, scheduler: clock.scheduler });
        document.body.append(view.element);
        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }])], 1));

        const play = transportButton(view, "Play / pause");
        expect(play.disabled).toBe(true);
        play.click();
        expect(clock.active()).toBe(0);
    });

    it("shows a fallback when a board's geometry fails to load", async () => {
        const backend = stubBackend(async () => {
            throw new Error("preview boom");
        });
        const clock = manualScheduler();
        const view = createFilmstripView({ backend, scheduler: clock.scheduler });
        document.body.append(view.element);
        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }])], 2));

        expect(view.element.querySelector(".compare-filmstrip-slot")?.textContent).toBe(
            "unavailable",
        );
    });

    it("stops the clock and detaches on dispose", async () => {
        const backend = stubBackend(async () => squarePreview());
        const clock = manualScheduler();
        const view = createFilmstripView({ backend, scheduler: clock.scheduler });
        document.body.append(view.element);
        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }, { c: 1 }])], 3));

        transportButton(view, "Play / pause").click();
        expect(clock.active()).toBe(1);
        view.dispose();
        expect(clock.active()).toBe(0);
        expect(document.body.contains(view.element)).toBe(false);
    });

    it("re-clamps and rebuilds boards when a shorter filmstrip is loaded", async () => {
        const backend = stubBackend(async () => squarePreview());
        const clock = manualScheduler();
        const view = createFilmstripView({ backend, scheduler: clock.scheduler });
        document.body.append(view.element);
        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }, { c: 1 }, { d: 1 }])], 4));
        const scrubber = view.element.querySelector<HTMLInputElement>(
            ".compare-filmstrip-scrubber",
        );
        scrubber!.value = "3";
        scrubber!.dispatchEvent(new Event("input"));
        expect(view.element.querySelector(".compare-filmstrip-counter")?.textContent).toBe(
            "gen 3 / 3",
        );

        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }])], 1));
        expect(view.element.querySelectorAll(".compare-filmstrip-board")).toHaveLength(1);
        expect(view.element.querySelector(".compare-filmstrip-counter")?.textContent).toBe(
            "gen 0 / 0",
        );
    });
});
