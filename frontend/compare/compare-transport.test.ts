import { afterEach, describe, expect, it } from "vitest";

import {
    createFilmstripTransport,
    type FilmstripTransportController,
    type IntervalScheduler,
} from "./compare-transport.js";
import { FilmstripPlayer } from "./filmstrip-player.js";

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

function control(transport: FilmstripTransportController, title: string): HTMLButtonElement {
    const button = transport.element.querySelector<HTMLButtonElement>(
        `.compare-filmstrip-btn[title="${title}"]`,
    );
    if (!button) {
        throw new Error(`missing control: ${title}`);
    }
    return button;
}

function counterText(transport: FilmstripTransportController): string | null {
    return transport.element.querySelector(".compare-filmstrip-counter")?.textContent ?? null;
}

describe("createFilmstripTransport", () => {
    afterEach(() => {
        document.body.innerHTML = "";
    });

    it("renders a disabled idle bar before any player is attached", () => {
        const clock = manualScheduler();
        const transport = createFilmstripTransport({ scheduler: clock.scheduler });

        expect(control(transport, "Play / pause").disabled).toBe(true);
        expect(control(transport, "Step forward one generation").disabled).toBe(true);
        expect(
            transport.element.querySelector<HTMLInputElement>(".compare-filmstrip-scrubber")
                ?.disabled,
        ).toBe(true);
        expect(counterText(transport)).toBe("—");
    });

    it("primes and enables the controls when a multi-frame player attaches", () => {
        const clock = manualScheduler();
        const transport = createFilmstripTransport({ scheduler: clock.scheduler });

        transport.attach(new FilmstripPlayer(3));

        expect(control(transport, "Play / pause").disabled).toBe(false);
        expect(counterText(transport)).toBe("gen 0 / 2");
    });

    it("drives the shared clock from the play control", () => {
        const clock = manualScheduler();
        const transport = createFilmstripTransport({ scheduler: clock.scheduler });
        transport.attach(new FilmstripPlayer(3));

        expect(clock.active()).toBe(0);
        control(transport, "Play / pause").click();
        expect(clock.active()).toBe(1);
        clock.tick(); // -> gen 1
        expect(counterText(transport)).toBe("gen 1 / 2");

        control(transport, "Play / pause").click(); // pause
        expect(clock.active()).toBe(0);
    });

    it("keeps the play control disabled for a single-frame player", () => {
        const clock = manualScheduler();
        const transport = createFilmstripTransport({ scheduler: clock.scheduler });
        transport.attach(new FilmstripPlayer(1));

        const play = control(transport, "Play / pause");
        expect(play.disabled).toBe(true);
        play.click();
        expect(clock.active()).toBe(0);
    });

    it("re-times a running clock when the speed is set", () => {
        const clock = manualScheduler();
        const transport = createFilmstripTransport({ scheduler: clock.scheduler });
        transport.attach(new FilmstripPlayer(4));

        control(transport, "Play / pause").click();
        expect(clock.active()).toBe(1);
        transport.setSpeed(2);
        expect(clock.active()).toBe(1); // still exactly one interval, re-timed
        expect(
            transport.element.querySelector<HTMLSelectElement>(".compare-filmstrip-speed")?.value,
        ).toBe("2");
    });

    it("stops the clock and returns to idle on detach", () => {
        const clock = manualScheduler();
        const transport = createFilmstripTransport({ scheduler: clock.scheduler });
        transport.attach(new FilmstripPlayer(3));
        control(transport, "Play / pause").click();
        expect(clock.active()).toBe(1);

        transport.detach();

        expect(clock.active()).toBe(0);
        expect(control(transport, "Play / pause").disabled).toBe(true);
        expect(counterText(transport)).toBe("—");
    });

    it("pauses playback without detaching the active player", () => {
        const clock = manualScheduler();
        const transport = createFilmstripTransport({ scheduler: clock.scheduler });
        transport.attach(new FilmstripPlayer(3));
        control(transport, "Play / pause").click();
        expect(clock.active()).toBe(1);

        transport.pause();

        expect(clock.active()).toBe(0);
        expect(control(transport, "Play / pause").disabled).toBe(false);
        expect(control(transport, "Play / pause").textContent).toBe("▶ Play");
        expect(counterText(transport)).toBe("gen 0 / 2");
    });

    it("drives the attached player through toggle and step (keyboard idioms)", () => {
        const clock = manualScheduler();
        const transport = createFilmstripTransport({ scheduler: clock.scheduler });
        transport.attach(new FilmstripPlayer(3));

        transport.step(1);
        expect(counterText(transport)).toBe("gen 1 / 2");
        transport.toggle();
        expect(clock.active()).toBe(1); // playing
        transport.toggle();
        expect(clock.active()).toBe(0); // paused
    });
});
