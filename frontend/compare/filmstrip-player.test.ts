import { describe, expect, it, vi } from "vitest";

import { FilmstripPlayer } from "./filmstrip-player.js";

describe("FilmstripPlayer", () => {
    it("starts paused on the first frame", () => {
        const player = new FilmstripPlayer(10);
        expect(player.index).toBe(0);
        expect(player.playing).toBe(false);
        expect(player.frameCount).toBe(10);
        expect(player.atEnd).toBe(false);
    });

    it("advances one frame per tick only while playing", () => {
        const player = new FilmstripPlayer(4);
        player.advance();
        expect(player.index).toBe(0); // paused: no movement

        player.play();
        player.advance();
        player.advance();
        expect(player.index).toBe(2);
    });

    it("stops on the last frame when not looping", () => {
        const player = new FilmstripPlayer(3);
        player.play();
        player.advance(); // 1
        player.advance(); // 2 (last)
        expect(player.index).toBe(2);
        expect(player.atEnd).toBe(true);
        player.advance(); // stays, stops
        expect(player.index).toBe(2);
        expect(player.playing).toBe(false);
    });

    it("wraps to the start when looping", () => {
        const player = new FilmstripPlayer(3, { loop: true });
        player.play();
        player.advance(); // 1
        player.advance(); // 2
        player.advance(); // wraps to 0, still playing
        expect(player.index).toBe(0);
        expect(player.playing).toBe(true);
    });

    it("wraps to loopStart instead of frame 0 when a sub-window loop is set", () => {
        const player = new FilmstripPlayer(5, { loop: true, loopStart: 2 });
        player.seek(4);
        player.play();
        player.advance(); // at last frame -> wraps to loopStart
        expect(player.index).toBe(2);
        expect(player.playing).toBe(true);
    });

    it("replays from the start when played after reaching the end", () => {
        const player = new FilmstripPlayer(3);
        player.seek(2);
        expect(player.atEnd).toBe(true);
        player.play();
        expect(player.index).toBe(0);
        expect(player.playing).toBe(true);
    });

    it("clamps step and seek to the valid range and pauses", () => {
        const player = new FilmstripPlayer(5);
        player.play();
        player.step(2);
        expect(player.index).toBe(2);
        expect(player.playing).toBe(false); // manual control pauses

        player.step(-10);
        expect(player.index).toBe(0);
        player.seek(99);
        expect(player.index).toBe(4);
    });

    it("does not play a single-frame (or empty) filmstrip", () => {
        const single = new FilmstripPlayer(1);
        single.play();
        expect(single.playing).toBe(false);

        const empty = new FilmstripPlayer(0);
        empty.play();
        empty.advance();
        expect(empty.index).toBe(0);
        expect(empty.playing).toBe(false);
    });

    it("re-clamps and stops when a new filmstrip length is loaded", () => {
        const player = new FilmstripPlayer(10);
        player.seek(8);
        player.play();
        expect(player.playing).toBe(true);

        player.setFrameCount(4);
        expect(player.frameCount).toBe(4);
        expect(player.index).toBe(3); // re-clamped into the new range
        expect(player.playing).toBe(false);
    });

    it("notifies subscribers on state changes and unsubscribes cleanly", () => {
        const player = new FilmstripPlayer(5);
        const listener = vi.fn();
        const unsubscribe = player.subscribe(listener);

        player.play();
        player.advance();
        expect(listener).toHaveBeenCalled();
        expect(listener.mock.calls.at(-1)?.[0]).toMatchObject({ index: 1, playing: true });

        listener.mockClear();
        unsubscribe();
        player.advance();
        expect(listener).not.toHaveBeenCalled();
    });
});
