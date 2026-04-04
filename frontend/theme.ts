import { FRONTEND_DEFAULTS } from "./defaults.js";

export const THEME_STORAGE_KEY = FRONTEND_DEFAULTS.theme.storage_key;
export type ThemeName = "dark" | "light";

export const DEFAULT_THEME: ThemeName = FRONTEND_DEFAULTS.theme.default === "light"
    ? "light"
    : "dark";

export function isThemeName(value: string | null | undefined): value is ThemeName {
    return value === "dark" || value === "light";
}

export function resolveTheme(value: string | null | undefined): ThemeName {
    if (isThemeName(value)) {
        return value;
    }
    return DEFAULT_THEME;
}

export function currentTheme(root: HTMLElement = document.documentElement): ThemeName {
    return resolveTheme(root.dataset.theme);
}

export function nextTheme(theme: ThemeName): ThemeName {
    return theme === "dark" ? "light" : "dark";
}

export function applyTheme(theme: ThemeName, {
    root = document.documentElement,
    storage = window.localStorage,
}: {
    root?: HTMLElement;
    storage?: Storage;
} = {}): ThemeName {
    const nextTheme = resolveTheme(theme);
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
    const nextTheme = DEFAULT_THEME;
    root.dataset.theme = nextTheme;
    try {
        storage.removeItem(THEME_STORAGE_KEY);
    } catch (error) {
        void error;
    }
    return nextTheme;
}
