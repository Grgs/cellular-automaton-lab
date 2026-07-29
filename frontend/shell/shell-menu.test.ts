import { afterEach, describe, expect, it, vi } from "vitest";

import { wireShellMenu } from "./shell-menu.js";
import { THEME_STORAGE_KEY } from "../theme.js";
import {
    COMPARE_LAYOUT_RESET_EVENT,
    COMPARE_LAYOUT_STORAGE_KEY,
} from "../compare/compare-workspace-layout.js";

function storage(): Storage {
    const values = new Map<string, string>();
    return {
        getItem: (key) => values.get(key) ?? null,
        setItem: (key, value) => void values.set(key, value),
        removeItem: (key) => void values.delete(key),
        clear: () => values.clear(),
        key: () => null,
        get length() {
            return values.size;
        },
    } as Storage;
}

function setup() {
    document.body.innerHTML = `
        <div id="shell-menu">
            <button id="shell-menu-toggle" aria-expanded="false">Menu</button>
            <div id="shell-menu-panel" hidden>
                <button id="shell-menu-compare" type="button">Compare</button>
                <button id="shell-menu-lab" type="button">Lab</button>
                <div id="shell-menu-lab-actions">
                    <button id="shell-menu-lab-export" type="button">Export Pattern</button>
                </div>
                <div id="shell-menu-compare-actions">
                    <button id="shell-menu-compare-wall" type="button">Choose Tilings…</button>
                    <button id="shell-menu-compare-rule" type="button">Change Rule…</button>
                    <button id="shell-menu-compare-saved" type="button">Saved</button>
                    <button id="shell-menu-compare-share" type="button">Copy Run Link</button>
                    <button id="shell-menu-compare-help" type="button">Help</button>
                </div>
                <button id="shell-preferences-btn" type="button">Preferences</button>
            </div>
        </div>
        <button id="outside" type="button">Outside</button>
        <button id="wall-view-btn" type="button">Compare</button>
        <button id="open-lab-btn" type="button">Lab</button>
        <button id="export-pattern-btn" type="button">Export</button>
        <dialog id="shell-preferences">
            <button id="shell-preferences-close" type="button">Close</button>
            <label><input name="shell-theme-preference" type="radio" value="light">Light</label>
            <label><input name="shell-theme-preference" type="radio" value="dark">Dark</label>
            <label><input name="shell-theme-preference" type="radio" value="system">System</label>
            <span id="shell-preferences-status"></span>
            <button id="shell-preferences-reset-compare-layout" type="button">
                Reset Compare layout
            </button>
            <span id="shell-preferences-compare-layout-status"></span>
        </dialog>
    `;
    const root = document.createElement("html");
    root.dataset.theme = "light";
    root.dataset.workspaceRoute = "lab";
    const stored = storage();
    const compareLayoutEventTarget = new EventTarget();
    const executeCompareMenuCommand = vi.fn();
    const media = () => ({ matches: true }) as MediaQueryList;
    const dispose = wireShellMenu({
        root,
        storage: stored,
        media,
        compareLayoutEventTarget,
        executeCompareMenuCommand,
    });
    return {
        dispose,
        root,
        stored,
        menu: document.querySelector<HTMLElement>("#shell-menu")!,
        menuButton: document.querySelector<HTMLButtonElement>("#shell-menu-toggle")!,
        menuPanel: document.querySelector<HTMLElement>("#shell-menu-panel")!,
        compare: document.querySelector<HTMLButtonElement>("#shell-menu-compare")!,
        lab: document.querySelector<HTMLButtonElement>("#shell-menu-lab")!,
        labActions: document.querySelector<HTMLElement>("#shell-menu-lab-actions")!,
        compareActions: document.querySelector<HTMLElement>("#shell-menu-compare-actions")!,
        labExport: document.querySelector<HTMLButtonElement>("#shell-menu-lab-export")!,
        exportTarget: document.querySelector<HTMLButtonElement>("#export-pattern-btn")!,
        compareWall: document.querySelector<HTMLButtonElement>("#shell-menu-compare-wall")!,
        executeCompareMenuCommand,
        preferences: document.querySelector<HTMLButtonElement>("#shell-preferences-btn")!,
        dialog: document.querySelector<HTMLDialogElement>("#shell-preferences")!,
        inputs: Array.from(
            document.querySelectorAll<HTMLInputElement>('input[name="shell-theme-preference"]'),
        ),
        status: document.querySelector<HTMLElement>("#shell-preferences-status")!,
        compareLayoutReset: document.querySelector<HTMLButtonElement>(
            "#shell-preferences-reset-compare-layout",
        )!,
        compareLayoutStatus: document.querySelector<HTMLElement>(
            "#shell-preferences-compare-layout-status",
        )!,
        compareLayoutEventTarget,
        wallTrigger: document.querySelector<HTMLButtonElement>("#wall-view-btn")!,
        labTrigger: document.querySelector<HTMLButtonElement>("#open-lab-btn")!,
        outside: document.querySelector<HTMLButtonElement>("#outside")!,
    };
}

describe("shell menu", () => {
    afterEach(() => document.body.replaceChildren());

    it("routes through the existing workspace triggers and closes the menu", () => {
        const view = setup();
        const compareListener = vi.fn();
        view.wallTrigger.addEventListener("click", compareListener);
        view.menuButton.click();
        view.compare.click();
        expect(compareListener).toHaveBeenCalledTimes(1);
        expect(view.menuPanel.hidden).toBe(true);

        const labListener = vi.fn();
        view.labTrigger.addEventListener("click", labListener);
        view.menuButton.click();
        view.lab.click();
        expect(labListener).toHaveBeenCalledTimes(1);
        view.dispose();
    });

    it("supports outside click and Escape with focus restoration", () => {
        const view = setup();
        view.menuButton.focus();
        view.menuButton.click();
        expect(view.menuButton.getAttribute("aria-expanded")).toBe("true");
        expect(view.menuPanel.hidden).toBe(false);

        view.outside.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));
        expect(view.menuPanel.hidden).toBe(true);

        view.menuButton.click();
        view.preferences.focus();
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        expect(view.menuPanel.hidden).toBe(true);
        expect(document.activeElement).toBe(view.menuButton);
        view.dispose();
    });

    it("shows contextual actions for only the active workspace", async () => {
        const view = setup();
        expect(view.labActions.hidden).toBe(false);
        expect(view.compareActions.hidden).toBe(true);

        view.root.dataset.workspaceRoute = "wall";
        await Promise.resolve();
        expect(view.labActions.hidden).toBe(true);
        expect(view.compareActions.hidden).toBe(false);
        view.dispose();
    });

    it("routes Lab commands through the existing controls", () => {
        const view = setup();
        const exportListener = vi.fn();
        view.exportTarget.addEventListener("click", exportListener);
        view.menuButton.click();
        view.labExport.click();
        expect(exportListener).toHaveBeenCalledTimes(1);
        expect(view.menuPanel.hidden).toBe(true);
        view.dispose();
    });

    it("dispatches semantic Compare commands and closes the menu", () => {
        const view = setup();
        view.root.dataset.workspaceRoute = "wall";
        view.menuButton.click();
        view.compareWall.click();
        expect(view.executeCompareMenuCommand).toHaveBeenLastCalledWith({
            type: "open-config",
            tab: "tilings",
        });
        expect(view.menuPanel.hidden).toBe(true);

        document.querySelector<HTMLButtonElement>("#shell-menu-compare-rule")?.click();
        expect(view.executeCompareMenuCommand).toHaveBeenLastCalledWith({
            type: "focus-rule",
        });
        document.querySelector<HTMLButtonElement>("#shell-menu-compare-saved")?.click();
        expect(view.executeCompareMenuCommand).toHaveBeenLastCalledWith({
            type: "open-config",
            tab: "saved",
        });
        document.querySelector<HTMLButtonElement>("#shell-menu-compare-help")?.click();
        expect(view.executeCompareMenuCommand).toHaveBeenLastCalledWith({
            type: "open-config",
            tab: "help",
        });
        document.querySelector<HTMLButtonElement>("#shell-menu-compare-share")?.click();
        expect(view.executeCompareMenuCommand).toHaveBeenLastCalledWith({
            type: "copy-run-link",
        });
        expect(view.executeCompareMenuCommand).toHaveBeenCalledTimes(5);
        view.dispose();
    });

    it("opens preferences and applies the three theme preferences", () => {
        const view = setup();
        view.menuButton.click();
        view.preferences.click();
        expect(view.dialog.open || view.dialog.hidden === false).toBe(true);
        expect(view.inputs.find((input) => input.value === "system")?.checked).toBe(true);

        const dark = view.inputs.find((input) => input.value === "dark")!;
        dark.click();
        expect(view.root.dataset.theme).toBe("dark");
        expect(view.stored.getItem(THEME_STORAGE_KEY)).toBe("dark");
        expect(view.status.textContent).toBe("Using dark mode.");

        const system = view.inputs.find((input) => input.value === "system")!;
        system.click();
        expect(view.root.dataset.theme).toBe("dark");
        expect(view.stored.getItem(THEME_STORAGE_KEY)).toBeNull();
        expect(view.status.textContent).toContain("Following system preference");
        view.dispose();
    });

    it("resets only the Compare layout preference and announces the immediate reset", () => {
        const view = setup();
        const resetListener = vi.fn();
        view.compareLayoutEventTarget.addEventListener(COMPARE_LAYOUT_RESET_EVENT, resetListener);
        view.stored.setItem(COMPARE_LAYOUT_STORAGE_KEY, '{"setupWidth":340}');
        view.stored.setItem("saved-runs", "keep");

        view.compareLayoutReset.click();

        expect(view.stored.getItem(COMPARE_LAYOUT_STORAGE_KEY)).toBeNull();
        expect(view.stored.getItem("saved-runs")).toBe("keep");
        expect(resetListener).toHaveBeenCalledTimes(1);
        expect(view.compareLayoutStatus.textContent).toBe("Compare layout reset.");
        view.dispose();
    });
});
