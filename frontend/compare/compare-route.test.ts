import { describe, expect, it } from "vitest";

import {
    hashHasCompareRoute,
    hashWithCompareRoute,
    hashWithoutCompareRoute,
    hashWithFocus,
    hashWithoutFocus,
    readFocusFromHash,
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
