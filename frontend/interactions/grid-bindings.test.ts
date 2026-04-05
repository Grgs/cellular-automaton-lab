import { beforeEach, describe, expect, it, vi } from "vitest";

import { bindGridInteractions } from "./grid-bindings.js";

function createPointerEvent(
    type: string,
    {
        button = 0,
        buttons = 0,
        pointerId = 1,
        pointerType = "mouse",
    }: {
        button?: number;
        buttons?: number;
        pointerId?: number;
        pointerType?: string;
    } = {},
): PointerEvent {
    const event = new MouseEvent(type, {
        bubbles: true,
        cancelable: true,
        button,
        buttons,
    });
    Object.defineProperty(event, "pointerId", { value: pointerId });
    Object.defineProperty(event, "pointerType", { value: pointerType });
    return event as PointerEvent;
}

describe("interactions/grid-bindings", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    it("emits hover updates for idle desktop pointer movement", () => {
        const surface = document.createElement("div");
        document.body.append(surface);
        const cell = { id: "square:1:1", x: 1, y: 1 };
        const onHoverChange = vi.fn();
        const onPointerMove = vi.fn();

        bindGridInteractions({
            surfaceElement: surface,
            resolveCellFromEvent: () => cell,
            onPointerDown: vi.fn(),
            onPointerMove,
            onPointerUp: vi.fn(),
            onPointerCancel: vi.fn(),
            onClick: vi.fn(),
            onContextMenu: vi.fn(),
            onHoverChange,
        });

        surface.dispatchEvent(createPointerEvent("pointermove", { pointerType: "mouse" }));

        expect(onHoverChange).toHaveBeenCalledWith(cell);
        expect(onPointerMove).toHaveBeenCalledTimes(1);
    });

    it("clears hover when the pointer leaves the surface", () => {
        const surface = document.createElement("div");
        document.body.append(surface);
        const onHoverChange = vi.fn();

        bindGridInteractions({
            surfaceElement: surface,
            resolveCellFromEvent: () => null,
            onPointerDown: vi.fn(),
            onPointerMove: vi.fn(),
            onPointerUp: vi.fn(),
            onPointerCancel: vi.fn(),
            onClick: vi.fn(),
            onContextMenu: vi.fn(),
            onHoverChange,
        });

        surface.dispatchEvent(createPointerEvent("pointerleave"));

        expect(onHoverChange).toHaveBeenCalledWith(null);
    });

    it("does not emit hover updates for touch movement", () => {
        const surface = document.createElement("div");
        document.body.append(surface);
        const onHoverChange = vi.fn();

        bindGridInteractions({
            surfaceElement: surface,
            resolveCellFromEvent: () => ({ id: "square:1:1", x: 1, y: 1 }),
            onPointerDown: vi.fn(),
            onPointerMove: vi.fn(),
            onPointerUp: vi.fn(),
            onPointerCancel: vi.fn(),
            onClick: vi.fn(),
            onContextMenu: vi.fn(),
            onHoverChange,
        });

        surface.dispatchEvent(createPointerEvent("pointermove", { pointerType: "touch" }));

        expect(onHoverChange).not.toHaveBeenCalled();
    });

    it("suppresses the browser context menu and resolves the clicked cell", () => {
        const surface = document.createElement("div");
        document.body.append(surface);
        const cell = { id: "square:1:1", x: 1, y: 1 };
        const onContextMenu = vi.fn();

        bindGridInteractions({
            surfaceElement: surface,
            resolveCellFromEvent: () => cell,
            onPointerDown: vi.fn(),
            onPointerMove: vi.fn(),
            onPointerUp: vi.fn(),
            onPointerCancel: vi.fn(),
            onClick: vi.fn(),
            onContextMenu,
            onHoverChange: vi.fn(),
        });

        const event = new MouseEvent("contextmenu", { bubbles: true, cancelable: true });
        const preventDefaultSpy = vi.spyOn(event, "preventDefault");
        surface.dispatchEvent(event);

        expect(preventDefaultSpy).toHaveBeenCalledTimes(1);
        expect(onContextMenu).toHaveBeenCalledWith(cell);
    });

    it("reports empty-space context menu selections as null", () => {
        const surface = document.createElement("div");
        document.body.append(surface);
        const onContextMenu = vi.fn();

        bindGridInteractions({
            surfaceElement: surface,
            resolveCellFromEvent: () => null,
            onPointerDown: vi.fn(),
            onPointerMove: vi.fn(),
            onPointerUp: vi.fn(),
            onPointerCancel: vi.fn(),
            onClick: vi.fn(),
            onContextMenu,
            onHoverChange: vi.fn(),
        });

        surface.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true }));

        expect(onContextMenu).toHaveBeenCalledWith(null);
    });
});
