import { beforeEach, describe, expect, it, vi } from "vitest";

import {
    COMPARE_LAYOUT_DEFAULTS,
    COMPARE_LAYOUT_STORAGE_KEY,
    COMPARE_LAYOUT_RESET_EVENT,
    createCompareWorkspaceLayout,
} from "./compare-workspace-layout.js";

function memoryStorage(initial?: string): Storage {
    const values = new Map<string, string>();
    if (initial !== undefined) {
        values.set(COMPARE_LAYOUT_STORAGE_KEY, initial);
    }
    return {
        getItem: (key) => values.get(key) ?? null,
        setItem: (key, value) => void values.set(key, value),
        removeItem: (key) => void values.delete(key),
        clear: () => values.clear(),
        key: (index) => [...values.keys()][index] ?? null,
        get length() {
            return values.size;
        },
    };
}

function storedState(overrides: Record<string, unknown> = {}): string {
    return JSON.stringify({
        ...COMPARE_LAYOUT_DEFAULTS,
        ...overrides,
    });
}

function setViewport(width: number): void {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
}

function setupLayout({
    width = 1280,
    availableWidth = width,
    storage = memoryStorage(),
    resetEventTarget = new EventTarget(),
}: {
    width?: number;
    availableWidth?: number;
    storage?: Storage;
    resetEventTarget?: EventTarget;
} = {}) {
    setViewport(width);
    const setup = document.createElement("aside");
    const board = document.createElement("main");
    const inspector = document.createElement("aside");
    const dock = document.createElement("div");
    const setupToggle = document.createElement("button");
    const inspectorToggle = document.createElement("button");
    document.body.append(setupToggle, inspectorToggle);
    const layout = createCompareWorkspaceLayout({
        setup,
        boardWall: board,
        inspector,
        dock,
        setupToggle,
        inspectorToggle,
        storage,
        resetEventTarget,
    });
    document.body.append(layout.element);
    const grid = layout.element.querySelector<HTMLElement>(".compare-workspace-grid")!;
    if (availableWidth !== width) {
        vi.spyOn(grid, "getBoundingClientRect").mockReturnValue({
            width: availableWidth,
            height: 600,
            x: 0,
            y: 0,
            top: 0,
            right: availableWidth,
            bottom: 600,
            left: 0,
            toJSON: () => ({}),
        });
        window.dispatchEvent(new Event("resize"));
    }
    return {
        layout,
        setup,
        board,
        inspector,
        setupToggle,
        inspectorToggle,
        grid,
        storage,
        resetEventTarget,
    };
}

function key(target: HTMLElement, value: string, shiftKey = false): void {
    target.dispatchEvent(
        new KeyboardEvent("keydown", {
            key: value,
            shiftKey,
            bubbles: true,
            cancelable: true,
        }),
    );
}

function drag(
    target: HTMLElement,
    { from, to, pointerId = 7 }: { from: number; to: number; pointerId?: number },
): void {
    target.dispatchEvent(
        new PointerEvent("pointerdown", {
            button: 0,
            clientX: from,
            pointerId,
            bubbles: true,
            cancelable: true,
        }),
    );
    window.dispatchEvent(
        new PointerEvent("pointermove", {
            clientX: to,
            pointerId,
            bubbles: true,
            cancelable: true,
        }),
    );
    window.dispatchEvent(
        new PointerEvent("pointerup", {
            clientX: to,
            pointerId,
            bubbles: true,
        }),
    );
}

describe("compare workspace layout", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        setViewport(1280);
    });

    it("reuses supplied nodes while making narrow drawers exclusive and restoring focus", () => {
        const view = setupLayout({ width: 800 });

        view.setupToggle.focus();
        view.layout.openSetup();
        expect(view.layout.element.contains(view.setup)).toBe(true);
        expect(view.layout.element.contains(view.board)).toBe(true);
        expect(view.layout.element.contains(view.inspector)).toBe(true);
        expect(view.setup.parentElement?.className).toBe("compare-workspace-grid");
        expect(view.setupToggle.getAttribute("aria-expanded")).toBe("true");

        view.inspectorToggle.focus();
        view.layout.openInspector();
        expect(view.setup.classList.contains("is-open")).toBe(false);
        expect(view.inspector.classList.contains("is-open")).toBe(true);
        expect(view.layout.closeDrawer()).toBe(true);
        expect(document.activeElement).toBe(view.inspectorToggle);
        view.layout.dispose();
    });

    it("resizes both sides through realistic pointer sequences and persists on release", () => {
        const view = setupLayout();
        view.layout.openSetup();
        view.layout.openInspector();

        drag(view.layout.setupSeparator, { from: 250, to: 315 });
        expect(view.layout.getState().setupWidth).toBe(315);
        expect(view.layout.setupSeparator.getAttribute("aria-valuenow")).toBe("315");

        drag(view.layout.inspectorSeparator, { from: 1000, to: 940 });
        expect(view.layout.getState().inspectorWidth).toBe(330);
        expect(view.layout.inspectorSeparator.getAttribute("aria-valuenow")).toBe("330");
        expect(view.layout.element.classList.contains("is-resizing")).toBe(false);

        expect(JSON.parse(view.storage.getItem(COMPARE_LAYOUT_STORAGE_KEY)!)).toMatchObject({
            setupWidth: 315,
            inspectorWidth: 330,
            setupCollapsed: false,
            inspectorCollapsed: false,
        });
        view.layout.dispose();
    });

    it("uses correct keyboard direction, 10/40 steps, and Home/End for both sides", () => {
        const view = setupLayout();
        view.layout.openSetup();
        view.layout.openInspector();

        key(view.layout.setupSeparator, "ArrowRight");
        expect(view.layout.getState().setupWidth).toBe(260);
        key(view.layout.setupSeparator, "ArrowLeft", true);
        expect(view.layout.getState().setupWidth).toBe(220);
        key(view.layout.setupSeparator, "End");
        expect(view.layout.getState().setupWidth).toBe(420);
        key(view.layout.setupSeparator, "Home");
        expect(view.layout.getState().setupWidth).toBe(220);

        key(view.layout.inspectorSeparator, "ArrowLeft");
        expect(view.layout.getState().inspectorWidth).toBe(280);
        key(view.layout.inspectorSeparator, "ArrowRight", true);
        expect(view.layout.getState().inspectorWidth).toBe(240);
        key(view.layout.inspectorSeparator, "End");
        expect(view.layout.getState().inspectorWidth).toBe(440);
        key(view.layout.inspectorSeparator, "Home");
        expect(view.layout.getState().inspectorWidth).toBe(240);
        view.layout.dispose();
    });

    it("coordinates both widths against the actual workspace wall floor", () => {
        const view = setupLayout({ width: 1280, availableWidth: 960 });
        view.layout.openSetup();
        view.layout.openInspector();

        expect(view.layout.setupSeparator.getAttribute("role")).toBe("separator");
        expect(view.layout.setupSeparator.getAttribute("aria-orientation")).toBe("vertical");
        expect(view.layout.setupSeparator.getAttribute("aria-valuemin")).toBe("220");
        expect(view.layout.setupSeparator.getAttribute("aria-valuemax")).toBe("270");
        key(view.layout.setupSeparator, "End");
        expect(view.layout.getState().setupWidth).toBe(270);
        expect(view.layout.inspectorSeparator.getAttribute("aria-valuemax")).toBe("270");

        drag(view.layout.inspectorSeparator, { from: 700, to: 0 });
        expect(view.layout.getState().inspectorWidth).toBe(270);
        const state = view.layout.getState();
        expect(960 - state.setupWidth - state.inspectorWidth - 20).toBeGreaterThanOrEqual(400);
        view.layout.dispose();
    });

    it("persists widths and collapse states across controller recreation", () => {
        const storage = memoryStorage(
            storedState({
                setupWidth: 330,
                inspectorWidth: 360,
                setupCollapsed: false,
                inspectorCollapsed: false,
            }),
        );
        const first = setupLayout({ storage });
        key(first.layout.setupSeparator, "ArrowRight");
        first.inspectorToggle.focus();
        expect(first.layout.closeInspector()).toBe(true);
        first.layout.dispose();
        document.body.replaceChildren();

        const second = setupLayout({ storage });
        expect(second.layout.getState()).toEqual({
            setupWidth: 340,
            inspectorWidth: 360,
            setupCollapsed: false,
            inspectorCollapsed: true,
        });
        expect(second.setup.classList.contains("is-open")).toBe(true);
        expect(second.inspector.classList.contains("is-open")).toBe(false);
        expect(second.layout.setupSeparator.getAttribute("aria-valuenow")).toBe("340");
        expect(second.layout.inspectorSeparator.getAttribute("aria-hidden")).toBe("true");
        second.layout.dispose();
    });

    it("loads malformed and obsolete values defensively and normalizes storage", () => {
        const malformed = memoryStorage("{nope");
        const malformedView = setupLayout({ storage: malformed });
        expect(malformedView.layout.getState()).toEqual(COMPARE_LAYOUT_DEFAULTS);
        expect(JSON.parse(malformed.getItem(COMPARE_LAYOUT_STORAGE_KEY)!)).toEqual(
            COMPARE_LAYOUT_DEFAULTS,
        );
        malformedView.layout.dispose();
        document.body.replaceChildren();

        const obsolete = memoryStorage(
            JSON.stringify({
                setupWidth: 9999,
                inspectorWidth: -30,
                setupCollapsed: "no",
                inspectorCollapsed: false,
                removedProperty: 12,
            }),
        );
        const obsoleteView = setupLayout({ storage: obsolete });
        expect(obsoleteView.layout.getState()).toEqual({
            setupWidth: 420,
            inspectorWidth: 240,
            setupCollapsed: true,
            inspectorCollapsed: false,
        });
        expect(JSON.parse(obsolete.getItem(COMPARE_LAYOUT_STORAGE_KEY)!)).toEqual(
            obsoleteView.layout.getState(),
        );
        obsoleteView.layout.dispose();
    });

    it("resets defaults immediately, clears storage, and responds to the global reset event", () => {
        const storage = memoryStorage(
            storedState({
                setupWidth: 340,
                inspectorWidth: 380,
                setupCollapsed: false,
                inspectorCollapsed: false,
            }),
        );
        const resetEventTarget = new EventTarget();
        const view = setupLayout({ storage, resetEventTarget });
        resetEventTarget.dispatchEvent(new Event(COMPARE_LAYOUT_RESET_EVENT));

        expect(view.layout.getState()).toEqual(COMPARE_LAYOUT_DEFAULTS);
        expect(view.setup.classList.contains("is-open")).toBe(false);
        expect(view.inspector.classList.contains("is-open")).toBe(false);
        expect(storage.getItem(COMPARE_LAYOUT_STORAGE_KEY)).toBeNull();
        view.layout.dispose();
    });

    it("keeps desktop widths and collapse states untouched through narrow overlay use", () => {
        const storage = memoryStorage(
            storedState({
                setupWidth: 330,
                inspectorWidth: 350,
                setupCollapsed: false,
                inspectorCollapsed: false,
            }),
        );
        const view = setupLayout({ storage });
        const desktopSnapshot = storage.getItem(COMPARE_LAYOUT_STORAGE_KEY);

        setViewport(390);
        window.dispatchEvent(new Event("resize"));
        expect(view.layout.setupSeparator.getAttribute("aria-hidden")).toBe("true");
        expect(view.layout.inspectorSeparator.getAttribute("aria-hidden")).toBe("true");
        expect(view.setup.classList.contains("is-open")).toBe(false);
        expect(view.inspector.classList.contains("is-open")).toBe(false);

        view.layout.openSetup();
        view.layout.openInspector();
        view.layout.closeInspector();
        expect(storage.getItem(COMPARE_LAYOUT_STORAGE_KEY)).toBe(desktopSnapshot);
        expect(view.layout.getState()).toEqual({
            setupWidth: 330,
            inspectorWidth: 350,
            setupCollapsed: false,
            inspectorCollapsed: false,
        });

        setViewport(1280);
        window.dispatchEvent(new Event("resize"));
        expect(view.setup.classList.contains("is-open")).toBe(true);
        expect(view.inspector.classList.contains("is-open")).toBe(true);
        expect(view.layout.getState().setupWidth).toBe(330);
        expect(view.layout.getState().inspectorWidth).toBe(350);
        view.layout.dispose();
    });

    it("tolerates storage access failures", () => {
        const failingStorage = {
            getItem: vi.fn(() => {
                throw new Error("blocked");
            }),
            setItem: vi.fn(() => {
                throw new Error("blocked");
            }),
            removeItem: vi.fn(() => {
                throw new Error("blocked");
            }),
        } as unknown as Storage;
        const view = setupLayout({ storage: failingStorage });
        expect(view.layout.getState()).toEqual(COMPARE_LAYOUT_DEFAULTS);
        expect(() => {
            view.layout.openSetup();
            key(view.layout.setupSeparator, "ArrowRight");
            view.layout.reset();
        }).not.toThrow();
        view.layout.dispose();
    });
});
