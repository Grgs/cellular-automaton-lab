import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type { CompareRunConfig } from "./compare-run-link.js";

function runConfig(overrides: Partial<CompareRunConfig> = {}): CompareRunConfig {
    return {
        seed: "01100 11000 01000",
        rule: "conway",
        traversal: "bfs",
        grid_size: 16,
        frames: 50,
        geometries: ["square", "hex"],
        ...overrides,
    };
}

describe("compare-run-link", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("round-trips a compare run config through the URL hash", async () => {
        const { encodeCompareRunFragment, decodeCompareRunFragment } =
            await import("./compare-run-link.js");
        const fragment = encodeCompareRunFragment(runConfig({ pattern: "glider" }));

        expect(fragment.startsWith("run=v1.")).toBe(true);
        expect(decodeCompareRunFragment(`#/compare&${fragment}`)).toEqual({
            seed: "01100 11000 01000",
            rule: "conway",
            traversal: "bfs",
            grid_size: 16,
            frames: 50,
            geometries: ["square", "hex"],
            pattern: "glider",
        });
    });

    it("returns null when no run slot is present", async () => {
        const { decodeCompareRunFragment } = await import("./compare-run-link.js");

        expect(decodeCompareRunFragment("")).toBeNull();
        expect(decodeCompareRunFragment("#/compare")).toBeNull();
        expect(decodeCompareRunFragment("#share=v1.abc")).toBeNull();
    });

    it("rejects invalid payloads", async () => {
        const { CompareRunLinkDecodeError, decodeCompareRunFragment, encodeCompareRunFragment } =
            await import("./compare-run-link.js");

        expect(() => decodeCompareRunFragment("#/compare&run=v1.@@@@")).toThrow(
            CompareRunLinkDecodeError,
        );
        const badFragment = encodeCompareRunFragment(
            runConfig({ geometries: [] }) as CompareRunConfig,
        );
        expect(() => decodeCompareRunFragment(`#/compare&${badFragment}`)).toThrow(
            CompareRunLinkDecodeError,
        );
    });

    it("builds a run URL without disturbing other hash slots", async () => {
        const { buildCompareRunUrl } = await import("./compare-run-link.js");
        const url = buildCompareRunUrl(
            runConfig(),
            "http://localhost/?x=1#share=v1.board&theme=dark",
        );

        expect(url).toContain("http://localhost/?x=1#/compare&run=v1.");
        expect(url).toContain("share=v1.board");
        expect(url).toContain("theme=dark");
    });

    it("adds and removes the compare route slot independently", async () => {
        const { addCompareRouteToHash, hashHasCompareRoute, removeCompareRouteFromHash } =
            await import("./compare-run-link.js");

        expect(addCompareRouteToHash("#share=v1.board")).toBe("#/compare&share=v1.board");
        expect(hashHasCompareRoute("#/compare&share=v1.board")).toBe(true);
        expect(removeCompareRouteFromHash("#/compare&run=v1.abc")).toBe("#run=v1.abc");
    });
});
