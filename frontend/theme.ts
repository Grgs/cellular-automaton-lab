import { FRONTEND_DEFAULTS } from "./defaults.js";

export const THEME_STORAGE_KEY = FRONTEND_DEFAULTS.theme.storage_key;
export type ThemeName = "dark" | "light";

export const DEFAULT_THEME: ThemeName =
    FRONTEND_DEFAULTS.theme.default === "light" ? "light" : "dark";

export type ThemeMediaResolver = (query: string) => Pick<MediaQueryList, "matches">;

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

export function preferredTheme(
    media: ThemeMediaResolver | undefined = typeof window !== "undefined" &&
    typeof window.matchMedia === "function"
        ? window.matchMedia.bind(window)
        : undefined,
): ThemeName {
    if (!media) {
        return DEFAULT_THEME;
    }
    try {
        if (media("(prefers-color-scheme: dark)").matches) {
            return "dark";
        }
        if (media("(prefers-color-scheme: light)").matches) {
            return "light";
        }
    } catch (error) {
        void error;
    }
    return DEFAULT_THEME;
}

export function applyTheme(
    theme: ThemeName,
    {
        root = document.documentElement,
        storage = window.localStorage,
    }: {
        root?: HTMLElement;
        storage?: Storage;
    } = {},
): ThemeName {
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
    media = typeof window !== "undefined" && typeof window.matchMedia === "function"
        ? window.matchMedia.bind(window)
        : undefined,
}: {
    root?: HTMLElement;
    storage?: Storage;
    media?: ThemeMediaResolver | undefined;
} = {}): ThemeName {
    const nextTheme = preferredTheme(media);
    root.dataset.theme = nextTheme;
    try {
        storage.removeItem(THEME_STORAGE_KEY);
    } catch (error) {
        void error;
    }
    return nextTheme;
}
