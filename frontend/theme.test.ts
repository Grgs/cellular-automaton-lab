import { describe, expect, it } from "vitest";

import { DEFAULT_THEME, preferredTheme } from "./theme.js";

describe("theme preference", () => {
    it("uses the current light OS preference when dark does not match", () => {
        const media = (query: string) => ({ matches: query.includes("light") });

        expect(preferredTheme(media)).toBe("light");
    });

    it("uses the configured default when no OS preference is available", () => {
        const media = () => ({ matches: false });

        expect(preferredTheme(media)).toBe(DEFAULT_THEME);
    });
});
