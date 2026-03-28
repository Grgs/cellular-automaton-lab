import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";

describe("pattern-io", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("parses valid patterns and builds stable filenames", async () => {
        const { buildPatternFilename, parsePatternText } = await import("./pattern-io.js");

        const parsed = parsePatternText(JSON.stringify({
            format: "cellular-automaton-lab-pattern",
            version: 5,
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                width: 8,
                height: 5,
                patch_depth: 0,
            },
            rule: "highlife",
            cells_by_id: {
                "c:1:1": 1,
                "c:2:1": 1,
            },
        }));

        expect(parsed.rule).toBe("highlife");
        expect(parsed.width).toBe(8);
        expect(parsed.cellsById).toEqual({
            "c:1:1": 1,
            "c:2:1": 1,
        });
        expect(buildPatternFilename({
            format: "cellular-automaton-lab-pattern",
            version: 5,
            topology_spec: parsed.topologySpec,
            rule: parsed.rule,
            cells_by_id: parsed.cellsById,
        })).toBe("pattern-highlife-square-edge-8x5.json");
    });

    it("rejects unsupported pattern formats", async () => {
        const { PatternValidationError, parsePatternText } = await import("./pattern-io.js");

        expect(() => parsePatternText(JSON.stringify({
            format: "unknown-format",
            version: 5,
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                width: 8,
                height: 5,
                patch_depth: 0,
            },
            rule: "conway",
            cells_by_id: {},
        }))).toThrow(PatternValidationError);
    });
});
