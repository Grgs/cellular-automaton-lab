import { describe, expect, it } from "vitest";

import {
    hashHasCompareRoute,
    hashHasLabRoute,
    hashWithCompareRoute,
    hashWithFocus,
    hashWithLabRoute,
    hashWithoutCompareRoute,
    hashWithoutFocus,
    hashWithoutLabRoute,
    readFocusFromHash,
    resolveShellRoute,
} from "./compare-route.js";

describe("hashHasCompareRoute", () => {
    it("detects the compare route in isolation and alongside other slots", () => {
        expect(hashHasCompareRoute("#/compare")).toBe(true);
        expect(hashHasCompareRoute("#/compare&share=v1.abc")).toBe(true);
        expect(hashHasCompareRoute("#share=v1.abc&/compare")).toBe(true);
    });

    it("is false for an empty, build, or share-only hash", () => {
        expect(hashHasCompareRoute("")).toBe(false);
        expect(hashHasCompareRoute("#")).toBe(false);
        expect(hashHasCompareRoute("#share=v1.abc")).toBe(false);
        // A different segment that merely contains the text is not a match.
        expect(hashHasCompareRoute("#/compареX")).toBe(false);
    });
});

describe("hashWithCompareRoute", () => {
    it("adds the route to an empty hash", () => {
        expect(hashWithCompareRoute("")).toBe("#/compare");
        expect(hashWithCompareRoute("#")).toBe("#/compare");
    });

    it("preserves other slots and is idempotent", () => {
        expect(hashWithCompareRoute("#share=v1.abc")).toBe("#/compare&share=v1.abc");
        expect(hashWithCompareRoute("#/compare&share=v1.abc")).toBe("#/compare&share=v1.abc");
        expect(hashWithCompareRoute("#/compare")).toBe("#/compare");
    });
});

describe("hashWithoutCompareRoute", () => {
    it("removes the route and is idempotent", () => {
        expect(hashWithoutCompareRoute("#/compare")).toBe("");
        expect(hashWithoutCompareRoute("#share=v1.abc")).toBe("#share=v1.abc");
        expect(hashWithoutCompareRoute("#/compare&share=v1.abc")).toBe("#share=v1.abc");
        expect(hashWithoutCompareRoute("#share=v1.abc&/compare")).toBe("#share=v1.abc");
    });
});

describe("lab route", () => {
    it("detects, adds and removes the /lab segment while preserving other slots", () => {
        expect(hashHasLabRoute("#/lab")).toBe(true);
        expect(hashHasLabRoute("#/lab&share=v1.abc")).toBe(true);
        expect(hashHasLabRoute("")).toBe(false);
        expect(hashHasLabRoute("#/compare")).toBe(false);

        expect(hashWithLabRoute("")).toBe("#/lab");
        expect(hashWithLabRoute("#share=v1.abc")).toBe("#/lab&share=v1.abc");
        expect(hashWithLabRoute("#/lab")).toBe("#/lab");

        expect(hashWithoutLabRoute("#/lab")).toBe("");
        expect(hashWithoutLabRoute("#/lab&share=v1.abc")).toBe("#share=v1.abc");
        expect(hashWithoutLabRoute("#share=v1.abc")).toBe("#share=v1.abc");
    });
});

describe("resolveShellRoute", () => {
    it("defaults to the wall for a bare or run-only hash", () => {
        expect(resolveShellRoute("")).toBe("wall");
        expect(resolveShellRoute("#")).toBe("wall");
        expect(resolveShellRoute("#run=v1.abc")).toBe("wall");
        expect(resolveShellRoute("#focus=square")).toBe("wall");
    });

    it("resolves the Lab for /lab and for bare share links", () => {
        expect(resolveShellRoute("#/lab")).toBe("lab");
        expect(resolveShellRoute("#/lab&run=v1.abc")).toBe("lab");
        expect(resolveShellRoute("#share=v1.abc")).toBe("lab");
        expect(resolveShellRoute("#/lab&share=v1.abc")).toBe("lab");
    });

    it("keeps the legacy /compare alias on the wall, even with a share slot", () => {
        expect(resolveShellRoute("#/compare")).toBe("wall");
        expect(resolveShellRoute("#/compare&run=v1.abc")).toBe("wall");
        expect(resolveShellRoute("#/compare&share=v1.abc")).toBe("wall");
    });
});

describe("focus slot", () => {
    it("reads the focused geometry, or null when absent", () => {
        expect(readFocusFromHash("#/compare&focus=penrose-p3-rhombs")).toBe("penrose-p3-rhombs");
        expect(readFocusFromHash("#/compare")).toBeNull();
        expect(readFocusFromHash("")).toBeNull();
        // Percent-encoded values decode back.
        expect(readFocusFromHash("#/compare&focus=a%2Fb")).toBe("a/b");
    });

    it("sets the focus slot, replacing any existing one and preserving other slots", () => {
        expect(hashWithFocus("#/compare", "square")).toBe("#/compare&focus=square");
        expect(hashWithFocus("#/compare&focus=hex", "square")).toBe("#/compare&focus=square");
        expect(hashWithFocus("#/compare&share=v1.abc", "square")).toBe(
            "#/compare&share=v1.abc&focus=square",
        );
    });

    it("removes the focus slot and is idempotent", () => {
        expect(hashWithoutFocus("#/compare&focus=square")).toBe("#/compare");
        expect(hashWithoutFocus("#/compare")).toBe("#/compare");
        expect(hashWithoutFocus("#focus=square")).toBe("");
    });
});
