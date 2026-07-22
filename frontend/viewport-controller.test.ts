import { describe, expect, it, vi } from "vitest";

import { createViewportController } from "./viewport-controller.js";

describe("viewport controller", () => {
    it("resizes topology for window changes without observing internal viewport layout", () => {
        const listeners: { windowResize?: () => void } = {};
        let desiredDimensions = { width: 10, height: 10 };
        const sendControl = vi.fn(async () => null);
        const setTimeoutFn = vi.fn((callback: () => void) => {
            callback();
            return 1;
        });
        const controller = createViewportController({
            getCurrentDimensions: () => ({ width: 10, height: 10 }),
            getViewportDimensions: () => desiredDimensions,
            collectConfig: () => ({ speed: 7, rule: "conway" }),
            applyPreview: vi.fn(),
            sendControl,
            sameDimensions: (left, right) =>
                Boolean(right && left.width === right.width && left.height === right.height),
            setTimeoutFn,
            clearTimeoutFn: vi.fn(),
            addWindowResizeListener: (listener) => {
                listeners.windowResize = listener;
                return vi.fn();
            },
        });

        controller.install(document.createElement("div"));
        expect(sendControl).not.toHaveBeenCalled();

        desiredDimensions = { width: 12, height: 8 };
        listeners.windowResize?.();
        expect(sendControl).toHaveBeenCalledWith(
            "/api/config",
            { topology_spec: { width: 12, height: 8 } },
            expect.any(Object),
        );
    });

    it("refits presentation-only layout changes after the active pointer settles", () => {
        const listeners: { presentationResize?: ResizeObserverCallback } = {};
        const scheduledCallbacks: Array<() => void> = [];
        const renderPresentation = vi.fn();
        const sendControl = vi.fn(async () => null);
        const resizeObserver = {
            observe: vi.fn(),
            disconnect: vi.fn(),
        } as unknown as ResizeObserver;
        let pointerActive = true;
        let viewportWidth = 900;
        const viewport = document.createElement("div");
        Object.defineProperties(viewport, {
            clientWidth: { configurable: true, get: () => viewportWidth },
            clientHeight: { configurable: true, value: 600 },
        });
        const controller = createViewportController({
            getCurrentDimensions: () => ({ width: 10, height: 10 }),
            getViewportDimensions: () => ({ width: 10, height: 10 }),
            collectConfig: () => ({ speed: 7, rule: "conway" }),
            applyPreview: vi.fn(),
            renderPresentation,
            isPointerGestureActive: () => pointerActive,
            sendControl,
            sameDimensions: (left, right) =>
                Boolean(right && left.width === right.width && left.height === right.height),
            setTimeoutFn: (callback) => {
                scheduledCallbacks.push(callback);
                return scheduledCallbacks.length;
            },
            clearTimeoutFn: vi.fn(),
            createResizeObserver: (callback) => {
                listeners.presentationResize = callback;
                return resizeObserver;
            },
            addWindowResizeListener: () => vi.fn(),
        });

        controller.install(viewport);
        viewportWidth = 640;
        listeners.presentationResize?.([], resizeObserver);
        expect(scheduledCallbacks).toHaveLength(1);

        scheduledCallbacks.shift()?.();
        expect(renderPresentation).not.toHaveBeenCalled();
        expect(scheduledCallbacks).toHaveLength(1);

        pointerActive = false;
        scheduledCallbacks.shift()?.();
        expect(renderPresentation).toHaveBeenCalledTimes(1);
        expect(sendControl).not.toHaveBeenCalled();

        controller.dispose();
        expect(resizeObserver.disconnect).toHaveBeenCalledTimes(1);
    });
});
