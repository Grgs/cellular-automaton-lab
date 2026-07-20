import { beforeEach, describe, expect, it } from "vitest";

import { wireShellThemeToggle } from "./shell-theme.js";
import { THEME_STORAGE_KEY } from "../theme.js";
import type { DomElements } from "../types/dom.js";

function fakeStorage(): Storage {
    const map = new Map<string, string>();
    return {
        getItem: (key) => map.get(key) ?? null,
        setItem: (key, value) => void map.set(key, value),
        removeItem: (key) => void map.delete(key),
        clear: () => map.clear(),
        key: () => null,
        get length() {
            return map.size;
        },
    } as Storage;
}

/** Minimal MediaQueryList whose `matches` can be flipped and broadcast. */
function fakeMedia(initialMatches: boolean) {
    const target = new EventTarget();
    const mql = {
        matches: initialMatches,
        media: "(prefers-color-scheme: dark)",
        addEventListener: (type: string, listener: EventListener) =>
            target.addEventListener(type, listener),
        removeEventListener: (type: string, listener: EventListener) =>
            target.removeEventListener(type, listener),
    } as unknown as MediaQueryList;
    const emit = (matches: boolean) => {
        (mql as { matches: boolean }).matches = matches;
        target.dispatchEvent(Object.assign(new Event("change"), { matches }));
    };
    return { media: () => mql, emit };
}

function setup(rootTheme?: string) {
    const button = document.createElement("button");
    const root = document.createElement("div");
    if (rootTheme) {
        root.dataset.theme = rootTheme;
    }
    const elements = { themeToggleBtn: button } as unknown as DomElements;
    const storage = fakeStorage();
    const mediaCtl = fakeMedia(true);
    const dispose = wireShellThemeToggle(elements, {
        root,
        storage,
        media: mediaCtl.media,
    });
    return { button, root, storage, mediaCtl, dispose };
}

describe("wireShellThemeToggle", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    it("toggles the theme, persists it, and keeps the button's aria in step", () => {
        const { button, root, storage } = setup("dark");
        expect(button.getAttribute("aria-label")).toBe("Switch to light mode");
        expect(button.getAttribute("aria-pressed")).toBe("true");

        button.click();
        expect(root.dataset.theme).toBe("light");
        expect(storage.getItem(THEME_STORAGE_KEY)).toBe("light");
        expect(button.getAttribute("aria-label")).toBe("Switch to dark mode");
        expect(button.getAttribute("aria-pressed")).toBe("false");
    });

    it("follows OS scheme changes only while no explicit choice is stored", () => {
        const { root, storage, mediaCtl } = setup("dark");

        // Unstored: an OS switch to light is followed.
        mediaCtl.emit(false);
        expect(root.dataset.theme).toBe("light");

        // An explicit choice wins from then on.
        storage.setItem(THEME_STORAGE_KEY, "light");
        mediaCtl.emit(true);
        expect(root.dataset.theme).toBe("light");
    });

    it("syncs the button's aria when the theme changes elsewhere", () => {
        const { button, root } = setup("dark");
        root.dataset.theme = "light";
        // The MutationObserver is async; flush a microtask/macrotask.
        return new Promise<void>((resolve) => {
            setTimeout(() => {
                expect(button.getAttribute("aria-label")).toBe("Switch to dark mode");
                resolve();
            }, 0);
        });
    });

    it("stops responding after dispose", () => {
        const { button, root, dispose } = setup("dark");
        dispose();
        button.click();
        expect(root.dataset.theme).toBe("dark");
    });
});
