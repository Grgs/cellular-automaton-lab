import { describe, expect, it, vi } from "vitest";

import { createCompareOperationCoordinator } from "./compare-operation-coordinator.js";

describe("compare operation coordinator", () => {
    it("lets only the current ticket publish and settle the busy bracket", () => {
        const onBusyChange = vi.fn();
        const coordinator = createCompareOperationCoordinator({ onBusyChange });
        const first = coordinator.begin("analysis");
        const second = coordinator.begin("filmstrip");

        expect(coordinator.owns(first)).toBe(false);
        expect(coordinator.finish(first)).toBe(false);
        expect(coordinator.owns(second)).toBe(true);
        expect(coordinator.finish(second)).toBe(true);
        expect(onBusyChange.mock.calls).toEqual([[true], [true], [false]]);
    });

    it("invalidates a non-interruptible completion and settles once", () => {
        const onBusyChange = vi.fn();
        const coordinator = createCompareOperationCoordinator({ onBusyChange });
        const stale = coordinator.begin("filmstrip");

        expect(coordinator.invalidate()).toBe(true);
        expect(coordinator.owns(stale)).toBe(false);
        expect(coordinator.finish(stale)).toBe(false);
        expect(coordinator.invalidate()).toBe(false);
        expect(onBusyChange.mock.calls).toEqual([[true], [false]]);
    });

    it("cancels only the requested operation kind", () => {
        const onBusyChange = vi.fn();
        const coordinator = createCompareOperationCoordinator({ onBusyChange });
        const filmstrip = coordinator.begin("filmstrip");

        expect(coordinator.cancel("analysis")).toBe(false);
        expect(coordinator.owns(filmstrip)).toBe(true);
        expect(coordinator.cancel("filmstrip")).toBe(true);
        expect(coordinator.owns(filmstrip)).toBe(false);
        expect(onBusyChange.mock.calls).toEqual([[true], [false]]);
    });

    it("disposes the active bracket and rejects later ticket ownership", () => {
        const onBusyChange = vi.fn();
        const coordinator = createCompareOperationCoordinator({ onBusyChange });
        const active = coordinator.begin("analysis");

        coordinator.dispose();
        coordinator.dispose();
        const afterDispose = coordinator.begin("filmstrip");

        expect(coordinator.owns(active)).toBe(false);
        expect(coordinator.owns(afterDispose)).toBe(false);
        expect(onBusyChange.mock.calls).toEqual([[true], [false]]);
    });
});
