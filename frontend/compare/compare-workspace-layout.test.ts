import { beforeEach, describe, expect, it } from "vitest";

import { createCompareWorkspaceLayout } from "./compare-workspace-layout.js";

describe("compare workspace layout", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        Object.defineProperty(window, "innerWidth", { configurable: true, value: 800 });
    });

    it("reuses supplied nodes while making drawers exclusive and restoring focus", () => {
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
        });
        document.body.append(layout.element);

        setupToggle.focus();
        layout.openSetup();
        expect(layout.element.contains(setup)).toBe(true);
        expect(layout.element.contains(board)).toBe(true);
        expect(layout.element.contains(inspector)).toBe(true);
        expect(setup.parentElement?.className).toBe("compare-workspace-grid");
        expect(setupToggle.getAttribute("aria-expanded")).toBe("true");

        inspectorToggle.focus();
        layout.openInspector();
        expect(setup.classList.contains("is-open")).toBe(false);
        expect(inspector.classList.contains("is-open")).toBe(true);
        expect(layout.closeDrawer()).toBe(true);
        expect(document.activeElement).toBe(inspectorToggle);
    });
});
