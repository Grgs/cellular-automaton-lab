import { renderThemeToggle } from "../controls/view-primitives.js";
import { THEME_STORAGE_KEY, currentTheme, toggleTheme } from "../theme.js";
import type { DomElements } from "../types/dom.js";

interface ShellThemeToggleOptions {
    root?: HTMLElement;
    storage?: Storage;
    media?: ((query: string) => MediaQueryList) | undefined;
}

/**
 * Owns the shared-header theme toggle so it is reachable from the wall too (the
 * Lab control panel no longer renders it). The sun/moon crossfade is CSS-driven
 * off `:root[data-theme]`, so this only keeps the button's aria state in step
 * with the theme -- including changes made elsewhere (a keyboard shortcut, a
 * settings reset) -- and, while the user has not made an explicit choice, keeps
 * following live OS colour-scheme changes.
 *
 * Returns a disposer.
 */
export function wireShellThemeToggle(
    elements: DomElements,
    {
        root = document.documentElement,
        storage = window.localStorage,
        media = typeof window !== "undefined" ? window.matchMedia?.bind(window) : undefined,
    }: ShellThemeToggleOptions = {},
): () => void {
    const button = elements.themeToggleBtn;
    if (!button) {
        return () => {};
    }
    const syncAria = (): void => renderThemeToggle(elements, currentTheme(root));
    syncAria();

    const onClick = (): void => {
        toggleTheme({ root, storage });
        syncAria();
    };
    button.addEventListener("click", onClick);

    // Reflect theme changes that originate elsewhere (keyboard shortcut, reset).
    const observer = new MutationObserver(syncAria);
    observer.observe(root, { attributes: true, attributeFilter: ["data-theme"] });

    // Track the OS scheme live, but only until the user picks a theme explicitly
    // (which writes storage and thereby wins from then on).
    const query = media ? media("(prefers-color-scheme: dark)") : null;
    const onOsChange = (event: MediaQueryListEvent): void => {
        if (storage.getItem(THEME_STORAGE_KEY) === null) {
            root.dataset.theme = event.matches ? "dark" : "light";
        }
    };
    query?.addEventListener?.("change", onOsChange);

    return () => {
        button.removeEventListener("click", onClick);
        observer.disconnect();
        query?.removeEventListener?.("change", onOsChange);
    };
}
