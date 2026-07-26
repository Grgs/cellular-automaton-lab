import { describe, expect, it } from "vitest";

import {
    applyThemePreference,
    DEFAULT_THEME,
    preferredTheme,
    readThemePreference,
    THEME_STORAGE_KEY,
} from "./theme.js";

function memoryStorage(initial: Record<string, string> = {}): Storage {
    const values = new Map(Object.entries(initial));
    return {
        getItem: (key) => values.get(key) ?? null,
        setItem: (key, value) => void values.set(key, value),
        removeItem: (key) => void values.delete(key),
        clear: () => values.clear(),
        key: (index) => Array.from(values.keys())[index] ?? null,
        get length() {
            return values.size;
        },
    } as Storage;
}

describe("theme preference", () => {
    it("uses the current light OS preference when dark does not match", () => {
        const media = (query: string) => ({ matches: query.includes("light") });

        expect(preferredTheme(media)).toBe("light");
    });

    it("uses the configured default when no OS preference is available", () => {
        const media = () => ({ matches: false });

        expect(preferredTheme(media)).toBe(DEFAULT_THEME);
    });

    it("reads existing stored light and dark values as explicit preferences", () => {
        expect(
            readThemePreference({
                storage: memoryStorage({ [THEME_STORAGE_KEY]: "light" }),
            }),
        ).toBe("light");
        expect(
            readThemePreference({
                storage: memoryStorage({ [THEME_STORAGE_KEY]: "dark" }),
            }),
        ).toBe("dark");
    });

    it("represents system preference by removing explicit storage", () => {
        const root = document.createElement("html");
        const storage = memoryStorage({ [THEME_STORAGE_KEY]: "dark" });
        const media = (query: string) => ({ matches: query.includes("light") });

        expect(applyThemePreference("system", { root, storage, media })).toBe("light");
        expect(root.dataset.theme).toBe("light");
        expect(storage.getItem(THEME_STORAGE_KEY)).toBeNull();
        expect(readThemePreference({ storage })).toBe("system");
    });

    it("stores explicit preferences and applies them immediately", () => {
        const root = document.createElement("html");
        const storage = memoryStorage();

        expect(applyThemePreference("dark", { root, storage })).toBe("dark");
        expect(root.dataset.theme).toBe("dark");
        expect(storage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    });
});
