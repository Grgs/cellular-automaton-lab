const SESSION_STORAGE_KEY = "cellular-automaton-lab.session-id";
const SESSION_ID_PATTERN = /^[A-Za-z0-9_-]{1,80}$/;

function randomSessionId(): string {
    const cryptoRef = globalThis.crypto;
    if (typeof cryptoRef?.randomUUID === "function") {
        return `s-${cryptoRef.randomUUID()}`;
    }
    const values = new Uint32Array(4);
    cryptoRef?.getRandomValues?.(values);
    const entropy = Array.from(values, (value) => value.toString(36)).join("-");
    return `s-${Date.now().toString(36)}-${entropy || Math.random().toString(36).slice(2)}`;
}

export function getOrCreateServerSessionId({
    storage = typeof window !== "undefined" ? window.localStorage : null,
}: {
    storage?: Pick<Storage, "getItem" | "setItem"> | null;
} = {}): string {
    try {
        const existing = storage?.getItem(SESSION_STORAGE_KEY);
        if (existing && SESSION_ID_PATTERN.test(existing)) {
            return existing;
        }
        const nextSessionId = randomSessionId();
        storage?.setItem(SESSION_STORAGE_KEY, nextSessionId);
        return nextSessionId;
    } catch {
        return randomSessionId();
    }
}
