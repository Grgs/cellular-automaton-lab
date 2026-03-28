export type PlainObject = Record<string, unknown>;

export function isPlainObject(value: unknown): value is PlainObject {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function requirePlainObject(value: unknown, message: string): PlainObject {
    if (!isPlainObject(value)) {
        throw new Error(message);
    }
    return value;
}
