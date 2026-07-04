import { afterEach, describe, expect, it } from "vitest";

import { createFilmstripView, type FilmstripViewController } from "./compare-filmstrip-view.js";
import {
    createFilmstripTransport,
    type FilmstripTransportController,
    type IntervalScheduler,
} from "./compare-transport.js";
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

interface Harness {
    view: FilmstripViewController;
    transport: FilmstripTransportController;
    clock: ReturnType<typeof manualScheduler>;
}

/** Build a view wired to a real transport (both mounted so controls are queryable). */
function mountView(
    options: {
        loop?: boolean;
        onOpenFrame?: (tiling: TopologyFilmstrip, frameIndex: number) => void;
        onFocusChange?: (geometry: string | null) => void;
        previewTopology?: SimulationBackend["previewTopology"];
    } = {},
): Harness {
    const backend = stubBackend(options.previewTopology ?? (async () => squarePreview()));
    const clock = manualScheduler();
    const transport = createFilmstripTransport({ scheduler: clock.scheduler });
    const view = createFilmstripView({
        backend,
        transport,
        ...(options.loop === undefined ? {} : { loop: options.loop }),
        ...(options.onOpenFrame ? { onOpenFrame: options.onOpenFrame } : {}),
        ...(options.onFocusChange ? { onFocusChange: options.onFocusChange } : {}),
    });
    document.body.append(transport.element, view.element);
    return { view, transport, clock };
}

function twoBoardFilmstrip(): SeedFilmstripResult {
    return filmstrip(
        [tiling("square", [{ a: 1 }, { b: 1 }]), tiling("hex", [{ a: 1 }, { c: 1 }])],
        2,
    );
}

function boardFor(view: FilmstripViewController, geometry: string): HTMLElement {
    const board = [...view.element.querySelectorAll<HTMLElement>(".compare-filmstrip-board")].find(
        (node) => node.querySelector(".compare-filmstrip-label")?.textContent === geometry,
    );
    if (!board) {
        throw new Error(`missing board: ${geometry}`);
    }
    return board;
}

function liveCount(view: FilmstripViewController): number {
    return view.element.querySelectorAll(".compare-filmstrip-slot polygon.is-live").length;
}

function counterText(): string | null {
    return document.querySelector(".compare-filmstrip-counter")?.textContent ?? null;
}

function transportButton(title: string): HTMLButtonElement {
    const button = document.querySelector<HTMLButtonElement>(
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
        const { view } = mountView();

        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }, { c: 1 }, {}])], 3));

        expect(view.element.querySelectorAll(".compare-filmstrip-board")).toHaveLength(1);
        expect(liveCount(view)).toBe(2); // frame 0: a, b
        expect(counterText()).toBe("gen 0 / 2");
    });

    it("labels the transport and board list for assistive technology", async () => {
        const { view, transport } = mountView();

        await view.load(filmstrip([tiling("square", [{ a: 1 }])], 1));

        expect(view.element.getAttribute("role")).toBe("region");
        expect(view.element.getAttribute("aria-label")).toBe("Synchronized side-by-side filmstrip");
        expect(transport.element.getAttribute("role")).toBe("group");
        expect(transport.element.getAttribute("aria-label")).toBe("Filmstrip playback controls");
        expect(view.element.querySelector(".compare-filmstrip-boards")?.getAttribute("role")).toBe(
            "list",
        );
        expect(view.element.querySelector(".compare-filmstrip-board")?.getAttribute("role")).toBe(
            "listitem",
        );
        expect(
            transport.element
                .querySelector<HTMLButtonElement>('.compare-filmstrip-btn[title="Play / pause"]')
                ?.getAttribute("aria-label"),
        ).toBe("Play / pause");
    });

    it("advances every board in lockstep on each clock tick while playing", async () => {
        const { view, clock } = mountView();
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
        transportButton("Play / pause").click();
        expect(clock.active()).toBe(1);

        clock.tick(); // -> gen 1
        // square: c (1 live); hex: b,c,d (3 live) => 4 total
        expect(liveCount(view)).toBe(4);
        expect(counterText()).toBe("gen 1 / 2");

        clock.tick(); // -> gen 2 (last, all extinct)
        expect(liveCount(view)).toBe(0);
        // Non-looping: the next tick stops the clock at the end.
        clock.tick();
        expect(clock.active()).toBe(0);
    });

    it("loops back to the seed frame instead of stopping when loop is set", async () => {
        const { view, clock } = mountView({ loop: true });
        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }, { c: 1 }])], 2));

        transportButton("Play / pause").click();
        clock.tick(); // -> gen 1
        clock.tick(); // wraps -> gen 0
        expect(counterText()).toBe("gen 0 / 1");
        expect(clock.active()).toBe(1); // still playing
    });

    it("autoplays after load when the autoplay option is set", async () => {
        const { view, clock } = mountView({ loop: true });

        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }])], 2), {
            autoplay: true,
        });

        expect(clock.active()).toBe(1); // playing without a manual click
        expect(transportButton("Play / pause").textContent).toBe("⏸ Pause");
    });

    it("rests on the requested initial frame, paused, when given initialFrame", async () => {
        const { view, clock } = mountView();

        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }, { c: 1 }])], 3), {
            initialFrame: 2,
        });

        expect(clock.active()).toBe(0); // paused
        expect(counterText()).toBe("gen 2 / 2");
    });

    it("loops a sub-window back to loopStart instead of the seed", async () => {
        const { view, clock } = mountView({ loop: true });

        await view.load(
            filmstrip([tiling("square", [{ a: 1 }, { b: 1 }, { c: 1 }, { d: 1 }])], 4),
            { autoplay: true, initialFrame: 1, loopStart: 1 },
        );

        clock.tick(); // -> gen 2
        clock.tick(); // -> gen 3 (last)
        clock.tick(); // wraps to loopStart (gen 1), skipping the seed
        expect(counterText()).toBe("gen 1 / 3");
        expect(clock.active()).toBe(1); // still playing
    });

    it("supports manual step, seek and reset which pause playback", async () => {
        const { view, clock } = mountView();
        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }, { c: 1 }, { d: 1 }])], 3));

        transportButton("Play / pause").click();
        expect(clock.active()).toBe(1);
        transportButton("Step forward one generation").click();
        expect(clock.active()).toBe(0); // manual control pauses
        expect(liveCount(view)).toBe(1); // gen 1: c

        const scrubber = document.querySelector<HTMLInputElement>(".compare-filmstrip-scrubber");
        if (!scrubber) {
            throw new Error("missing scrubber");
        }
        scrubber.value = "2";
        scrubber.dispatchEvent(new Event("input"));
        expect(counterText()).toBe("gen 2 / 2");

        transportButton("Back to the seed").click();
        expect(counterText()).toBe("gen 0 / 2");
        expect(liveCount(view)).toBe(2);
    });

    it("opens the current generation for a board when requested", async () => {
        const opened: Array<{ geometry: string; frameIndex: number }> = [];
        const { view } = mountView({
            onOpenFrame: (tiling, frameIndex) => {
                opened.push({ geometry: tiling.geometry, frameIndex });
            },
        });
        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }, { c: 1 }])], 3));

        transportButton("Step forward one generation").click();
        const openButton = view.element.querySelector<HTMLButtonElement>(".compare-filmstrip-open");
        expect(openButton?.textContent).toBe("Open gen 1");
        openButton?.click();

        expect(opened).toEqual([{ geometry: "square", frameIndex: 1 }]);
    });

    it("omits open-generation actions when no callback is provided", async () => {
        const { view } = mountView();
        await view.load(filmstrip([tiling("square", [{ a: 1 }])], 1));

        expect(view.element.querySelector(".compare-filmstrip-open")).toBeNull();
    });

    it("re-times the running clock when the speed changes", async () => {
        const { view, clock } = mountView();
        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }, { c: 1 }])], 3));

        transportButton("Play / pause").click();
        expect(clock.active()).toBe(1);
        const speed = document.querySelector<HTMLSelectElement>(".compare-filmstrip-speed");
        if (!speed) {
            throw new Error("missing speed select");
        }
        speed.value = "2";
        speed.dispatchEvent(new Event("change"));
        expect(clock.active()).toBe(1); // exactly one interval, re-timed
    });

    it("disables playback for a single-frame filmstrip", async () => {
        const { view, clock } = mountView();
        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }])], 1));

        const play = transportButton("Play / pause");
        expect(play.disabled).toBe(true);
        play.click();
        expect(clock.active()).toBe(0);
    });

    it("shows a fallback when a board's geometry fails to load", async () => {
        const { view } = mountView({
            previewTopology: async () => {
                throw new Error("preview boom");
            },
        });
        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }])], 2));

        expect(view.element.querySelector(".compare-filmstrip-slot")?.textContent).toBe(
            "unavailable",
        );
    });

    it("stops the clock and detaches on dispose", async () => {
        const { view, clock } = mountView();
        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }, { c: 1 }])], 3));

        transportButton("Play / pause").click();
        expect(clock.active()).toBe(1);
        view.dispose();
        expect(clock.active()).toBe(0);
        expect(document.body.contains(view.element)).toBe(false);
    });

    it("re-clamps and rebuilds boards when a shorter filmstrip is loaded", async () => {
        const { view } = mountView();
        await view.load(filmstrip([tiling("square", [{ a: 1 }, { b: 1 }, { c: 1 }, { d: 1 }])], 4));
        const scrubber = document.querySelector<HTMLInputElement>(".compare-filmstrip-scrubber");
        scrubber!.value = "3";
        scrubber!.dispatchEvent(new Event("input"));
        expect(counterText()).toBe("gen 3 / 3");

        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }])], 1));
        expect(view.element.querySelectorAll(".compare-filmstrip-board")).toHaveLength(1);
        expect(counterText()).toBe("gen 0 / 0");
    });

    it("enlarges a focused board into speaker view and returns to the gallery", async () => {
        const focusEvents: Array<string | null> = [];
        const { view } = mountView({ onFocusChange: (geometry) => focusEvents.push(geometry) });
        await view.load(twoBoardFilmstrip());

        expect(view.element.classList.contains("compare-filmstrip--speaker")).toBe(false);

        view.element
            .querySelector<HTMLButtonElement>(
                '.compare-filmstrip-board .compare-filmstrip-focus[aria-label="Focus square"]',
            )
            ?.click();

        expect(view.element.classList.contains("compare-filmstrip--speaker")).toBe(true);
        expect(boardFor(view, "square").classList.contains("is-hero")).toBe(true);
        expect(boardFor(view, "hex").classList.contains("is-strip")).toBe(true);
        expect(focusEvents).toEqual(["square"]);

        // Clicking the hero's focus control (now "Back to the gallery") exits speaker view.
        boardFor(view, "square")
            .querySelector<HTMLButtonElement>(".compare-filmstrip-focus")
            ?.click();
        expect(view.element.classList.contains("compare-filmstrip--speaker")).toBe(false);
        expect(focusEvents).toEqual(["square", null]);
    });

    it("swaps focus when a strip board is clicked in speaker view", async () => {
        const { view } = mountView();
        await view.load(twoBoardFilmstrip());
        view.focus("square");
        expect(boardFor(view, "square").classList.contains("is-hero")).toBe(true);

        boardFor(view, "hex").click();
        expect(boardFor(view, "hex").classList.contains("is-hero")).toBe(true);
        expect(boardFor(view, "square").classList.contains("is-strip")).toBe(true);
    });

    it("ignores a focus request for an unknown geometry", async () => {
        const focusEvents: Array<string | null> = [];
        const { view } = mountView({ onFocusChange: (geometry) => focusEvents.push(geometry) });
        await view.load(twoBoardFilmstrip());

        view.focus("not-a-tiling");
        expect(view.element.classList.contains("compare-filmstrip--speaker")).toBe(false);
        expect(focusEvents).toEqual([]);
    });
});
