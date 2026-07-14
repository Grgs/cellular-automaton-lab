import { afterEach, describe, expect, it, vi } from "vitest";

import { request } from "./api.js";

function stubFetch(response: Response): void {
    vi.stubGlobal(
        "fetch",
        vi.fn(() => Promise.resolve(response)),
    );
}

describe("request", () => {
    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("returns the parsed body on success", async () => {
        stubFetch(new Response(JSON.stringify({ ok: true }), { status: 200 }));

        await expect(request<{ ok: boolean }>("/api/state")).resolves.toEqual({ ok: true });
    });

    it("surfaces the server's error detail so callers can classify failures", async () => {
        stubFetch(
            new Response(
                JSON.stringify({ error: "Topology has 60984 cells; preview limit is 10000." }),
                { status: 400 },
            ),
        );

        await expect(request("/api/topology/preview")).rejects.toThrow(
            "Request failed: 400 — Topology has 60984 cells; preview limit is 10000.",
        );
    });

    it("falls back to the status code when the error body is not JSON", async () => {
        stubFetch(new Response("<html>boom</html>", { status: 502 }));

        await expect(request("/api/state")).rejects.toThrow("Request failed: 502");
    });
});
