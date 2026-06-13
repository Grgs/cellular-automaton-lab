import { describe, expect, it } from "vitest";

import { getOrCreateServerSessionId } from "./session-id.js";

class MemoryStorage implements Pick<Storage, "getItem" | "setItem"> {
    private readonly values = new Map<string, string>();

    getItem(key: string): string | null {
        return this.values.get(key) ?? null;
    }

    setItem(key: string, value: string): void {
        this.values.set(key, value);
    }
}

describe("server session ids", () => {
    it("reuses a valid stored session id", () => {
        const storage = new MemoryStorage();
        storage.setItem("cellular-automaton-lab.session-id", "s-existing");

        expect(getOrCreateServerSessionId({ storage })).toBe("s-existing");
    });

    it("replaces malformed stored values", () => {
        const storage = new MemoryStorage();
        storage.setItem("cellular-automaton-lab.session-id", "../bad");

        const sessionId = getOrCreateServerSessionId({ storage });

        expect(sessionId).toMatch(/^s-[A-Za-z0-9_-]+/);
        expect(storage.getItem("cellular-automaton-lab.session-id")).toBe(sessionId);
    });
});
