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
});
