import { describe, expect, it, vi } from "vitest";

import { createCompareWorkspaceStore } from "./compare-workspace-store.js";
import { shallowEqual, subscribeSelector } from "./compare-workspace-subscriptions.js";

function makeStore() {
    return createCompareWorkspaceStore({
        seed: "1",
        rule: "conway",
        traversal: "bfs",
        grid_size: 16,
        frames: 50,
        geometries: ["square", "hex"],
    });
}

describe("shallowEqual", () => {
    it("compares primitives, arrays, and flat records one level deep", () => {
        expect(shallowEqual(1, 1)).toBe(true);
        expect(shallowEqual("a", "b")).toBe(false);
        expect(shallowEqual(null, null)).toBe(true);
        expect(shallowEqual(["a", "b"], ["a", "b"])).toBe(true);
        expect(shallowEqual(["a", "b"], ["a", "c"])).toBe(false);
        expect(shallowEqual(["a"], ["a", "b"])).toBe(false);
        expect(shallowEqual({ x: 1, y: 2 }, { x: 1, y: 2 })).toBe(true);
        expect(shallowEqual({ x: 1 }, { x: 2 })).toBe(false);
        // One level only: nested different references are not equal.
        expect(shallowEqual({ x: { a: 1 } }, { x: { a: 1 } })).toBe(false);
    });
});

describe("subscribeSelector", () => {
    it("fires only when the selected slice changes", () => {
        const store = makeStore();
        const listener = vi.fn();
        subscribeSelector(store, (state) => state.selectedBoard, listener);

        // An update that leaves the slice unchanged does not fire.
        store.update((state) => ({ ...state, focusedBoard: "hex" }));
        expect(listener).not.toHaveBeenCalled();

        store.update((state) => ({ ...state, selectedBoard: "square" }));
        expect(listener).toHaveBeenCalledExactlyOnceWith("square", null);
    });

    it("does not fire on frame-index churn when the selector omits it", () => {
        const store = makeStore();
        const summaryListener = vi.fn();
        const explainerListener = vi.fn();
        // Summary-style selector: operation + results, no playback.
        subscribeSelector(
            store,
            (state) => [state.operation.status, state.results.filmstrip],
            summaryListener,
        );
        // Explainer-style selector: includes the frame index.
        subscribeSelector(store, (state) => state.playback.frameIndex, explainerListener);

        // Simulate playback advancing the shared clock.
        for (let frame = 1; frame <= 30; frame += 1) {
            store.update((state) => ({
                ...state,
                playback: { ...state.playback, frameIndex: frame },
            }));
        }

        expect(summaryListener).not.toHaveBeenCalled();
        expect(explainerListener).toHaveBeenCalledTimes(30);
        expect(explainerListener).toHaveBeenLastCalledWith(30, 29);
    });

    it("treats recreated-but-equal array slices as unchanged", () => {
        const store = makeStore();
        const listener = vi.fn();
        // forkedBoards is a fresh frozen array on every update; element-equal
        // slices must not fire.
        subscribeSelector(store, (state) => state.forkedBoards, listener);

        store.update((state) => ({ ...state, selectedBoard: "hex" }));
        expect(listener).not.toHaveBeenCalled();

        store.update((state) => ({ ...state, forkedBoards: ["hex"] }));
        expect(listener).toHaveBeenCalledOnce();
    });

    it("stops firing after the returned handle unsubscribes", () => {
        const store = makeStore();
        const listener = vi.fn();
        const unsubscribe = subscribeSelector(store, (state) => state.selectedBoard, listener);

        store.update((state) => ({ ...state, selectedBoard: "square" }));
        expect(listener).toHaveBeenCalledOnce();

        unsubscribe();
        store.update((state) => ({ ...state, selectedBoard: "hex" }));
        expect(listener).toHaveBeenCalledOnce();
    });
});
