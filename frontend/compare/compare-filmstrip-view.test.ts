import { afterEach, describe, expect, it, vi } from "vitest";

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
    TopologyOption,
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
        canAddBoard?: () => boolean;
        addBoardDisabledReason?: () => string;
        isTilingAvailable?: (geometry: string) => boolean;
        onAddBoard?: (geometry: string) => void;
        onFocusChange?: (geometry: string | null) => void;
        onRemoveBoard?: (geometry: string) => void;
        onReplaceBoard?: (previousGeometry: string, nextGeometry: string) => void;
        previewTopology?: SimulationBackend["previewTopology"];
        tilingOptions?: readonly TopologyOption[];
    } = {},
): Harness {
    const backend = stubBackend(options.previewTopology ?? (async () => squarePreview()));
    const clock = manualScheduler();
    const transport = createFilmstripTransport({ scheduler: clock.scheduler });
    const view = createFilmstripView({
        backend,
        transport,
        ...(options.loop === undefined ? {} : { loop: options.loop }),
        ...(options.canAddBoard ? { canAddBoard: options.canAddBoard } : {}),
        ...(options.addBoardDisabledReason
            ? { addBoardDisabledReason: options.addBoardDisabledReason }
            : {}),
        ...(options.isTilingAvailable ? { isTilingAvailable: options.isTilingAvailable } : {}),
        ...(options.onAddBoard ? { onAddBoard: options.onAddBoard } : {}),
        ...(options.onFocusChange ? { onFocusChange: options.onFocusChange } : {}),
        ...(options.onRemoveBoard ? { onRemoveBoard: options.onRemoveBoard } : {}),
        ...(options.onReplaceBoard ? { onReplaceBoard: options.onReplaceBoard } : {}),
        ...(options.tilingOptions ? { tilingOptions: options.tilingOptions } : {}),
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

function pickerOption(value: string, label: string): TopologyOption {
    return {
        value,
        label,
        group: "Test tilings",
        order: 0,
        family: "regular",
        previewKey: value,
        renderKind: "square",
        sizingMode: "grid",
        searchAliases: [],
    };
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
        expect(view.element.querySelector<HTMLElement>(".compare-filmstrip-board")?.tabIndex).toBe(
            0,
        );
        expect(
            view.element
                .querySelector<HTMLElement>(".compare-filmstrip-board")
                ?.getAttribute("aria-label"),
        ).toBe("square: focus this board");
        expect(
            transport.element
                .querySelector<HTMLButtonElement>('.compare-filmstrip-btn[title="Play / pause"]')
                ?.getAttribute("aria-label"),
        ).toBe("Play / pause");
    });

    it("labels boards with the friendly catalog label, geometry key as fallback", async () => {
        const { view } = mountView();

        await view.load(
            filmstrip(
                [
                    { ...tiling("penrose-p3-rhombs", [{ a: 1 }]), label: "Penrose P3 Rhombs" },
                    tiling("hex", [{ a: 1 }]),
                ],
                1,
            ),
        );

        const labels = [...view.element.querySelectorAll(".compare-filmstrip-label")].map(
            (node) => node.textContent,
        );
        expect(labels).toEqual(["Penrose P3 Rhombs", "hex"]);
        expect(
            view.element
                .querySelector<HTMLElement>(".compare-filmstrip-board")
                ?.getAttribute("aria-label"),
        ).toBe("Penrose P3 Rhombs: focus this board");
    });

    it("keeps remove discoverable and disables it at the two-board minimum", async () => {
        const removed: string[] = [];
        const { view } = mountView({ onRemoveBoard: (geometry) => removed.push(geometry) });

        await view.load(
            filmstrip(
                [
                    tiling("square", [{ a: 1 }]),
                    tiling("hex", [{ a: 1 }]),
                    tiling("tri", [{ a: 1 }]),
                ],
                1,
            ),
        );
        const removeButtons = view.element.querySelectorAll<HTMLButtonElement>(
            ".compare-filmstrip-remove",
        );
        expect(removeButtons).toHaveLength(3);
        expect([...removeButtons].every((button) => !button.disabled)).toBe(true);

        view.element
            .querySelector<HTMLButtonElement>(".compare-filmstrip-remove")
            ?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        expect(removed).toEqual(["square"]);
        // The × is a button, so the board click handler ignored it (no zoom).
        expect(view.element.querySelector(".compare-filmstrip-board.is-hero")).toBeNull();

        // At the backend's two-board minimum the affordance stays discoverable
        // and explains why it cannot remove another board.
        await view.load(twoBoardFilmstrip());
        const minimumButtons = view.element.querySelectorAll<HTMLButtonElement>(
            ".compare-filmstrip-remove",
        );
        expect(minimumButtons).toHaveLength(2);
        expect([...minimumButtons].every((button) => button.disabled)).toBe(true);
        expect(minimumButtons[0]?.title).toBe("Keep at least two tilings on the wall");
    });

    it("opens a searchable in-wall picker and adds an available tiling", async () => {
        const added: string[] = [];
        const { view } = mountView({
            onAddBoard: (geometry) => added.push(geometry),
            tilingOptions: [
                pickerOption("square", "Square"),
                pickerOption("hex", "Hexagonal"),
                pickerOption("tri", "Triangular"),
            ],
        });

        await view.load(twoBoardFilmstrip());

        const addButton = view.element.querySelector<HTMLButtonElement>(".compare-filmstrip-add");
        expect(addButton?.disabled).toBe(false);
        expect(view.element.querySelectorAll(".compare-filmstrip-board")).toHaveLength(2);
        addButton?.click();

        const search = view.element.querySelector<HTMLInputElement>(
            ".compare-board-tiling-picker-search",
        );
        expect(document.activeElement).toBe(search);
        expect(
            [...view.element.querySelectorAll<HTMLButtonElement>(".compare-board-tiling-choice")]
                .filter((choice) => choice.disabled)
                .map((choice) => choice.textContent),
        ).toEqual(["SquareTest tilings", "HexagonalTest tilings"]);

        search!.value = "tri";
        search?.dispatchEvent(new Event("input", { bubbles: true }));
        const choices = view.element.querySelectorAll<HTMLButtonElement>(
            ".compare-board-tiling-choice",
        );
        expect(choices).toHaveLength(1);
        expect(choices[0]?.textContent).toContain("Triangular");
        choices[0]?.click();
        expect(added).toEqual(["tri"]);
        expect(view.element.querySelector(".compare-board-tiling-picker")).toBeNull();

        const { view: plainView } = mountView();
        await plainView.load(twoBoardFilmstrip());
        expect(plainView.element.querySelector(".compare-filmstrip-add")).toBeNull();
    });

    it("disables in-wall adding with a visible capacity explanation", async () => {
        let hasCapacity = false;
        const { view } = mountView({
            onAddBoard: vi.fn(),
            canAddBoard: () => hasCapacity,
            addBoardDisabledReason: () => "This screen supports up to 4 tilings at once.",
            tilingOptions: [
                pickerOption("square", "Square"),
                pickerOption("hex", "Hexagonal"),
                pickerOption("tri", "Triangular"),
            ],
        });
        await view.load(twoBoardFilmstrip());

        const addButton = view.element.querySelector<HTMLButtonElement>(".compare-filmstrip-add");
        expect(addButton?.disabled).toBe(true);
        expect(addButton?.title).toContain("up to 4 tilings");

        hasCapacity = true;
        view.refreshAddControl();
        expect(
            view.element.querySelector<HTMLButtonElement>(".compare-filmstrip-add")?.disabled,
        ).toBe(false);
    });

    it("keeps add, replace, and remove truthful while a wall rebuild is busy", async () => {
        const added: string[] = [];
        const removed: string[] = [];
        const replaced: Array<[string, string]> = [];
        const { view } = mountView({
            onAddBoard: (geometry) => added.push(geometry),
            onRemoveBoard: (geometry) => removed.push(geometry),
            onReplaceBoard: (previousGeometry, nextGeometry) =>
                replaced.push([previousGeometry, nextGeometry]),
            tilingOptions: [
                pickerOption("square", "Square"),
                pickerOption("hex", "Hexagonal"),
                pickerOption("tri", "Triangular"),
                pickerOption("penrose", "Penrose"),
            ],
        });
        await view.load(
            filmstrip(
                [
                    tiling("square", [{ a: 1 }]),
                    tiling("hex", [{ a: 1 }]),
                    tiling("tri", [{ a: 1 }]),
                ],
                1,
            ),
        );

        view.setManagementBusy(true);

        const addButton = view.element.querySelector<HTMLButtonElement>(".compare-filmstrip-add");
        const labels = view.element.querySelectorAll<HTMLButtonElement>(".compare-filmstrip-label");
        const removeButtons = view.element.querySelectorAll<HTMLButtonElement>(
            ".compare-filmstrip-remove",
        );
        expect(addButton?.disabled).toBe(true);
        expect(addButton?.title).toBe("Wait for the wall update to finish");
        expect([...labels].every((button) => button.disabled)).toBe(true);
        expect([...removeButtons].every((button) => button.disabled)).toBe(true);
        expect([...removeButtons].every((button) => button.title.includes("Wait"))).toBe(true);
        addButton?.click();
        labels[0]?.click();
        removeButtons[0]?.click();
        expect(added).toEqual([]);
        expect(replaced).toEqual([]);
        expect(removed).toEqual([]);

        view.setManagementBusy(false);

        expect(
            view.element.querySelector<HTMLButtonElement>(".compare-filmstrip-add")?.disabled,
        ).toBe(false);
        expect([...labels].every((button) => !button.disabled)).toBe(true);
        expect([...removeButtons].every((button) => !button.disabled)).toBe(true);
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

    it("shows board chrome (name and live count) and no per-tile fork button", async () => {
        const { view } = mountView();
        await view.load(filmstrip([tiling("square", [{ a: 1, b: 1 }, { c: 1 }])], 2));

        const board = boardFor(view, "square");
        const chrome = board.querySelector(".compare-filmstrip-board-chrome");
        expect(chrome).not.toBeNull();
        expect(chrome?.querySelector(".compare-filmstrip-label")?.textContent).toBe("square");
        expect(board.querySelector(".compare-filmstrip-count")?.textContent).toBe("2 live");
        // Forking now lives in speaker view, not on every gallery tile.
        expect(view.element.querySelector(".compare-filmstrip-open")).toBeNull();
        expect(board.querySelector(".compare-filmstrip-label")?.getAttribute("aria-label")).toBe(
            "Replace square",
        );
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

    it("preserves matching board DOM and previews when requested", async () => {
        const previewTopology = vi.fn(async () => squarePreview());
        const { view } = mountView({ previewTopology });
        await view.load(twoBoardFilmstrip());
        const squareBoard = boardFor(view, "square");
        const hexBoard = boardFor(view, "hex");
        expect(previewTopology).toHaveBeenCalledTimes(2);

        await view.load(
            filmstrip([tiling("square", [{ b: 1 }]), tiling("hex", [{ c: 1, d: 1 }])], 1),
            { preserveBoards: true },
        );

        expect(boardFor(view, "square")).toBe(squareBoard);
        expect(boardFor(view, "hex")).toBe(hexBoard);
        expect(previewTopology).toHaveBeenCalledTimes(2);
        expect(
            boardFor(view, "square").querySelector(".compare-filmstrip-count")?.textContent,
        ).toBe("1 live");
        expect(boardFor(view, "hex").querySelector(".compare-filmstrip-count")?.textContent).toBe(
            "2 live",
        );
    });

    it("enlarges a clicked board into speaker view and returns to the gallery", async () => {
        const focusEvents: Array<string | null> = [];
        const { view } = mountView({ onFocusChange: (geometry) => focusEvents.push(geometry) });
        await view.load(twoBoardFilmstrip());

        expect(view.element.classList.contains("compare-filmstrip--speaker")).toBe(false);
        expect(view.element.querySelector(".compare-filmstrip-focus")).toBeNull();

        boardFor(view, "square").click();

        expect(view.element.classList.contains("compare-filmstrip--speaker")).toBe(true);
        expect(boardFor(view, "square").classList.contains("is-hero")).toBe(true);
        expect(boardFor(view, "hex").classList.contains("is-strip")).toBe(true);
        expect(boardFor(view, "square").getAttribute("aria-label")).toBe(
            "square: back to the wall",
        );
        expect(focusEvents).toEqual(["square"]);

        // Clicking the hero exits speaker view.
        boardFor(view, "square").click();
        expect(view.element.classList.contains("compare-filmstrip--speaker")).toBe(false);
        expect(focusEvents).toEqual(["square", null]);
    });

    it("focuses a board from the keyboard", async () => {
        const focusEvents: Array<string | null> = [];
        const { view } = mountView({ onFocusChange: (geometry) => focusEvents.push(geometry) });
        await view.load(twoBoardFilmstrip());

        boardFor(view, "hex").dispatchEvent(
            new KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
        );

        expect(view.element.classList.contains("compare-filmstrip--speaker")).toBe(true);
        expect(boardFor(view, "hex").classList.contains("is-hero")).toBe(true);
        expect(focusEvents).toEqual(["hex"]);
    });

    it("parks the hero toolbelt on the focused board and detaches it in the gallery", async () => {
        const { view } = mountView();
        await view.load(twoBoardFilmstrip());
        const toolbelt = document.createElement("div");
        toolbelt.className = "compare-hero-toolbelt";
        view.setHeroToolbelt(toolbelt);

        // Gallery: the toolbelt is not mounted on any board.
        expect(toolbelt.isConnected).toBe(false);

        view.focus("square");
        expect(boardFor(view, "square").contains(toolbelt)).toBe(true);

        // Swapping the hero moves the toolbelt to the new hero.
        view.focus("hex");
        expect(boardFor(view, "hex").contains(toolbelt)).toBe(true);
        expect(boardFor(view, "square").contains(toolbelt)).toBe(false);

        // Back to the gallery detaches it.
        view.focus(null);
        expect(toolbelt.isConnected).toBe(false);
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

    it("keeps focus when a live fork overlay is clicked (paints must not unfocus)", async () => {
        const focusEvents: Array<string | null> = [];
        const { view } = mountView({ onFocusChange: (geometry) => focusEvents.push(geometry) });
        await view.load(twoBoardFilmstrip());
        view.focus("square");
        expect(focusEvents).toEqual(["square"]);

        const pane = document.createElement("div");
        pane.className = "compare-focus-pane";
        const canvas = document.createElement("canvas");
        pane.append(canvas);
        expect(view.setBoardOverlay("square", pane)).toBe(true);

        // Painting the forked board bubbles a click from inside the slot;
        // the board must stay the focused hero.
        canvas.click();
        expect(view.element.classList.contains("compare-filmstrip--speaker")).toBe(true);
        expect(boardFor(view, "square").classList.contains("is-hero")).toBe(true);
        expect(focusEvents).toEqual(["square"]);

        // Clicking the hero cell outside the pane still returns to the wall.
        boardFor(view, "square").click();
        expect(focusEvents).toEqual(["square", null]);

        // In the gallery the fork keeps rendering as a compact tile; clicking
        // it (the click lands inside the pane) must focus the board again
        // rather than being swallowed.
        canvas.click();
        expect(boardFor(view, "square").classList.contains("is-hero")).toBe(true);
        expect(focusEvents).toEqual(["square", null, "square"]);

        // Once the overlay is cleared, hero slot clicks toggle focus again.
        expect(view.setBoardOverlay("square", null)).toBe(true);
        boardFor(view, "square").querySelector<HTMLElement>(".compare-filmstrip-slot")!.click();
        expect(focusEvents).toEqual(["square", null, "square", null]);
    });
});
