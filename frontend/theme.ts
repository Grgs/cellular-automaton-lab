import { FRONTEND_DEFAULTS } from "./defaults.js";

export const THEME_STORAGE_KEY = FRONTEND_DEFAULTS.theme.storage_key;
export const DEFAULT_THEME = FRONTEND_DEFAULTS.theme.default;

type ThemeName = "dark" | "light";

export function normalizeTheme(value: unknown): ThemeName {
    if (value === "dark" || value === "light") {
        return value;
    }
    return DEFAULT_THEME === "dark" ? "dark" : "light";
}

export function currentTheme(root: HTMLElement = document.documentElement): ThemeName {
    return normalizeTheme(root.dataset.theme);
}

export function nextTheme(theme: unknown): ThemeName {
    return normalizeTheme(theme) === "dark" ? "light" : "dark";
}

export function applyTheme(theme: unknown, {
    root = document.documentElement,
    storage = window.localStorage,
}: {
    root?: HTMLElement;
    storage?: Storage;
} = {}): ThemeName {
    const nextTheme = normalizeTheme(theme);
    root.dataset.theme = nextTheme;

    try {
        storage.setItem(THEME_STORAGE_KEY, nextTheme);
    } catch (error) {
        void error;
    }

    return nextTheme;
}

export function toggleTheme({
    root = document.documentElement,
    storage = window.localStorage,
}: {
    root?: HTMLElement;
    storage?: Storage;
} = {}): ThemeName {
    return applyTheme(nextTheme(currentTheme(root)), { root, storage });
}

export function resetThemeToDefault({
    root = document.documentElement,
    storage = window.localStorage,
}: {
    root?: HTMLElement;
    storage?: Storage;
} = {}): ThemeName {
    const nextTheme = normalizeTheme(DEFAULT_THEME);
    root.dataset.theme = nextTheme;
    try {
        storage.removeItem(THEME_STORAGE_KEY);
    } catch (error) {
        void error;
    }
    return nextTheme;
}
