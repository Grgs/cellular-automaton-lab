import { describe, expect, it, vi } from "vitest";

import { resolveShellRoute } from "./compare/compare-route.js";
import type { AppState } from "./types/state.js";

// The sync logic under test only branches on whether the payload has cells, so
// stub the payload builder and the validation error class -- their real forms
// pull in the whole topology catalog -- and drive the cell map off the state.
vi.mock("./pattern-io.js", () => ({
    buildPatternPayload: (state: { cells_by_id?: Record<string, number> }) => ({
        format: "cellular-automaton-lab-pattern",
        version: 5,
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 8,
            height: 8,
            patch_depth: 0,
        },
        rule: "conway",
        cells_by_id: state.cells_by_id ?? {},
    }),
}));
vi.mock("./parsers/pattern.js", () => ({
    PatternValidationError: class PatternValidationError extends Error {},
}));

const { syncShareLinkUrlFromState } = await import("./share-link-sync.js");

function sync(hash: string, cells: Record<string, number>) {
    const replaceState = vi.fn();
    syncShareLinkUrlFromState({ cells_by_id: cells } as unknown as AppState, {
        historyApi: { replaceState },
        locationApi: { hash, pathname: "/", search: "" },
    });
    return replaceState;
}

describe("syncShareLinkUrlFromState", () => {
    it("leaves a fresh empty Lab hash untouched instead of writing a share blob", () => {
        expect(sync("#/lab", {})).not.toHaveBeenCalled();
    });

    it("mirrors a painted board into a share slot beside the lab route", () => {
        const replaceState = sync("#/lab", { "c:0:0": 1 });
        expect(replaceState).toHaveBeenCalledTimes(1);
        const url = replaceState.mock.calls[0]![2] as string;
        expect(url).toContain("#share=");
        expect(url).toContain("/lab");
    });

    it.each([
        ["#share=v1.abc", "#/lab"],
        ["#/lab&share=v1.abc", "#/lab"],
        ["#share=v1.abc&run=v1.def", "#/lab&run=v1.def"],
        ["#/lab&share=v1.abc&run=v1.def", "#/lab&run=v1.def"],
    ])("keeps an emptied shared board on the Lab route for %s", (hash, expectedHash) => {
        const replaceState = sync(hash, {});
        expect(replaceState).toHaveBeenCalledTimes(1);
        const url = replaceState.mock.calls[0]![2] as string;
        expect(url).toBe(`/${expectedHash}`);
        expect(resolveShellRoute(expectedHash)).toBe("lab");
    });

    it("never mirrors while the hash addresses the wall", () => {
        expect(sync("#/compare", { "c:0:0": 1 })).not.toHaveBeenCalled();
        expect(sync("", { "c:0:0": 1 })).not.toHaveBeenCalled();
    });
});
