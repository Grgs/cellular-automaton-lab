import { afterEach, describe, expect, it, vi } from "vitest";

import { wireShellMenu } from "./shell-menu.js";
import { THEME_STORAGE_KEY } from "../theme.js";

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
        <details id="shell-menu"><summary>Menu</summary>
            <button id="shell-menu-compare" type="button">Compare</button>
            <button id="shell-menu-lab" type="button">Lab</button>
            <button id="shell-preferences-btn" type="button">Preferences</button>
        </details>
        <button id="wall-view-btn" type="button">Compare</button>
        <button id="open-lab-btn" type="button">Lab</button>
        <dialog id="shell-preferences">
            <button id="shell-preferences-close" type="button">Close</button>
            <button id="shell-preferences-theme-btn" type="button"></button>
            <button id="shell-preferences-system-btn" type="button">System</button>
            <span id="shell-preferences-status"></span>
        </dialog>
    `;
    const root = document.createElement("html");
    root.dataset.theme = "light";
    const stored = storage();
    const media = () => ({ matches: true }) as MediaQueryList;
    const dispose = wireShellMenu({
        root,
        storage: stored,
        media,
    });
    return {
        dispose,
        root,
        stored,
        menu: document.querySelector<HTMLDetailsElement>("#shell-menu")!,
        compare: document.querySelector<HTMLButtonElement>("#shell-menu-compare")!,
        lab: document.querySelector<HTMLButtonElement>("#shell-menu-lab")!,
        preferences: document.querySelector<HTMLButtonElement>("#shell-preferences-btn")!,
        dialog: document.querySelector<HTMLDialogElement>("#shell-preferences")!,
        theme: document.querySelector<HTMLButtonElement>("#shell-preferences-theme-btn")!,
        system: document.querySelector<HTMLButtonElement>("#shell-preferences-system-btn")!,
        status: document.querySelector<HTMLElement>("#shell-preferences-status")!,
        wallTrigger: document.querySelector<HTMLButtonElement>("#wall-view-btn")!,
        labTrigger: document.querySelector<HTMLButtonElement>("#open-lab-btn")!,
    };
}

describe("shell menu", () => {
    afterEach(() => document.body.replaceChildren());

    it("routes through the existing workspace triggers and closes the menu", () => {
        const view = setup();
        const compareListener = vi.fn();
        view.wallTrigger.addEventListener("click", compareListener);
        view.menu.open = true;
        view.compare.click();
        expect(compareListener).toHaveBeenCalledTimes(1);
        expect(view.menu.open).toBe(false);
        // The native button click is observable through a listener on the trigger.
        const labListener = vi.fn();
        view.labTrigger.addEventListener("click", labListener);
        view.menu.open = true;
        view.lab.click();
        expect(labListener).toHaveBeenCalledTimes(1);
        view.dispose();
    });

    it("opens preferences and changes or resets the persisted theme", () => {
        const view = setup();
        view.preferences.click();
        expect(view.dialog.open || view.dialog.hidden === false).toBe(true);
        expect(view.theme.textContent).toBe("Use dark mode");
        view.theme.click();
        expect(view.root.dataset.theme).toBe("dark");
        expect(view.stored.getItem(THEME_STORAGE_KEY)).toBe("dark");
        expect(view.status.textContent).toBe("Currently using dark mode.");
        view.system.click();
        expect(view.root.dataset.theme).toBe("dark");
        expect(view.stored.getItem(THEME_STORAGE_KEY)).toBeNull();
        view.dispose();
    });
});
