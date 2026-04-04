import { DEFAULT_THEME, resolveTheme } from "../theme.js";
import type { ThemeName } from "../theme.js";

export function parseTheme(value: unknown): ThemeName {
    return typeof value === "string"
        ? resolveTheme(value)
        : DEFAULT_THEME;
}
