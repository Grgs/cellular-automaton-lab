import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "./test-helpers/bootstrap.js";
import type { PatternPayload } from "./types/domain.js";

function buildPayload(overrides: Partial<PatternPayload> = {}): PatternPayload {
    return {
        format: "cellular-automaton-lab-pattern",
        version: 5,
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "cell_size",
            width: 8,
            height: 5,
            patch_depth: 0,
        },
        rule: "conway",
        cells_by_id: {
            "c:1:1": 1,
            "c:2:1": 1,
        },
        ...overrides,
    };
}

describe("share-link", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("round-trips a pattern payload through the URL hash", async () => {
        const { encodeShareFragment, decodeShareFragment } = await import("./share-link.js");
        const payload = buildPayload();
        const fragment = encodeShareFragment(payload);
        expect(fragment.startsWith("share=v1.")).toBe(true);
        const parsed = decodeShareFragment(`#${fragment}`);
        expect(parsed).not.toBeNull();
        expect(parsed?.rule).toBe("conway");
        expect(parsed?.cellsById).toEqual({ "c:1:1": 1, "c:2:1": 1 });
        expect(parsed?.topologySpec.tiling_family).toBe("square");
    });

    it("round-trips an empty board", async () => {
        const { encodeShareFragment, decodeShareFragment } = await import("./share-link.js");
        const payload = buildPayload({ cells_by_id: {} });
        const fragment = encodeShareFragment(payload);
        const parsed = decodeShareFragment(`#${fragment}`);
        expect(parsed?.cellsById).toEqual({});
    });

    it("returns null for hashes without a share slot", async () => {
        const { decodeShareFragment } = await import("./share-link.js");
        expect(decodeShareFragment("")).toBeNull();
        expect(decodeShareFragment("#")).toBeNull();
        expect(decodeShareFragment("#foo=bar")).toBeNull();
    });

    it("rejects invalid base64 payloads", async () => {
        const { decodeShareFragment, ShareLinkDecodeError } = await import("./share-link.js");
        expect(() => decodeShareFragment("#share=v1.@@@@")).toThrow(ShareLinkDecodeError);
    });

    it("wraps pattern validation errors as ShareLinkDecodeError", async () => {
        const { encodeShareFragment, decodeShareFragment, ShareLinkDecodeError } = await import(
            "./share-link.js"
        );
        const corruptedPayload = buildPayload();
        // Encode a pattern with an unsupported rule field type, then ensure decode
        // surfaces a ShareLinkDecodeError rather than a raw PatternValidationError.
        const badPayload = { ...corruptedPayload, rule: "" };
        const fragment = encodeShareFragment(badPayload as PatternPayload);
        expect(() => decodeShareFragment(`#${fragment}`)).toThrow(ShareLinkDecodeError);
    });

    it("preserves unrelated hash slots when building a share URL", async () => {
        const { buildShareUrl } = await import("./share-link.js");
        const url = buildShareUrl(buildPayload(), "http://localhost/#theme=dark");
        expect(url.includes("share=v1.")).toBe(true);
        expect(url.includes("theme=dark")).toBe(true);
    });

    it("clears the share slot without disturbing other hash slots", async () => {
        const { clearShareFragment } = await import("./share-link.js");
        expect(clearShareFragment("#share=v1.abc&theme=dark")).toBe("#theme=dark");
        expect(clearShareFragment("#share=v1.abc")).toBe("");
        expect(clearShareFragment("")).toBe("");
    });

    it("handles multi-byte unicode in cell ids without corruption", async () => {
        const { encodeShareFragment, decodeShareFragment } = await import("./share-link.js");
        const payload = buildPayload({
            cells_by_id: { "c:π:1": 1, "c:漢:2": 2 },
        });
        const fragment = encodeShareFragment(payload);
        const parsed = decodeShareFragment(`#${fragment}`);
        expect(parsed?.cellsById).toEqual({ "c:π:1": 1, "c:漢:2": 2 });
    });
});
