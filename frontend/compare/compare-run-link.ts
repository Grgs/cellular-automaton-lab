/**
 * Shareable URL state for compare workspace run configurations.
 *
 * The hash format is:
 *
 *     #/compare&run=v1.<base64url(JSON.stringify(CompareRunConfig))>
 *
 * This intentionally mirrors the board `share=` slot model while keeping the
 * compare workspace route as its own hash segment.
 */

export const COMPARE_ROUTE_SLOT = "/compare";
export const COMPARE_RUN_HASH_KEY = "run";
export const COMPARE_RUN_VERSION_TAG = "v1";

const RUN_HASH_PREFIX = `${COMPARE_RUN_HASH_KEY}=`;
const RUN_BODY_PREFIX = `${COMPARE_RUN_VERSION_TAG}.`;

export interface CompareRunConfig {
    seed: string;
    rule: string;
    traversal: string;
    grid_size: number;
    frames: number;
    geometries: readonly string[];
    pattern?: string;
}

interface HashSlot {
    tagWithEquals: string;
    body: string;
    raw: string;
}

export class CompareRunLinkDecodeError extends Error {}

function base64UrlEncode(value: string): string {
    const utf8Bytes = new TextEncoder().encode(value);
    let binary = "";
    for (const byte of utf8Bytes) {
        binary += String.fromCharCode(byte);
    }
    return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlDecode(value: string): string {
    const padded = value
        .replace(/-/g, "+")
        .replace(/_/g, "/")
        .padEnd(value.length + ((4 - (value.length % 4)) % 4), "=");
    let binary: string;
    try {
        binary = atob(padded);
    } catch {
        throw new CompareRunLinkDecodeError("Run link payload is not valid base64.");
    }
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
        bytes[index] = binary.charCodeAt(index);
    }
    return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
}

function splitHashIntoSlots(hash: string): HashSlot[] {
    const trimmed = hash.startsWith("#") ? hash.slice(1) : hash;
    if (!trimmed) {
        return [];
    }
    return trimmed
        .split("&")
        .filter((segment) => segment.length > 0)
        .map((segment) => {
            const eqIndex = segment.indexOf("=");
            if (eqIndex === -1) {
                return { tagWithEquals: segment, body: "", raw: segment };
            }
            return {
                tagWithEquals: segment.slice(0, eqIndex + 1),
                body: segment.slice(eqIndex + 1),
                raw: segment,
            };
        });
}

function joinSlots(slots: readonly string[]): string {
    return slots.length > 0 ? `#${slots.join("&")}` : "";
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validateNonEmptyString(value: unknown, field: string): string {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new CompareRunLinkDecodeError(`Run link is invalid: ${field} is required.`);
    }
    return value;
}

function validateInteger(value: unknown, field: string, low: number, high: number): number {
    if (typeof value !== "number" || !Number.isInteger(value) || value < low || value > high) {
        throw new CompareRunLinkDecodeError(
            `Run link is invalid: ${field} must be an integer from ${low} to ${high}.`,
        );
    }
    return value;
}

function validateGeometries(value: unknown): readonly string[] {
    if (!Array.isArray(value) || value.length === 0) {
        throw new CompareRunLinkDecodeError(
            "Run link is invalid: at least one tiling is required.",
        );
    }
    const geometries: string[] = [];
    const seen = new Set<string>();
    for (const item of value) {
        if (typeof item !== "string" || item.trim().length === 0) {
            throw new CompareRunLinkDecodeError(
                "Run link is invalid: tilings must be non-empty strings.",
            );
        }
        if (!seen.has(item)) {
            seen.add(item);
            geometries.push(item);
        }
    }
    return geometries;
}

function validateConfig(value: unknown): CompareRunConfig {
    if (!isRecord(value)) {
        throw new CompareRunLinkDecodeError("Run link payload is not an object.");
    }
    const config: CompareRunConfig = {
        seed: typeof value.seed === "string" ? value.seed : "",
        rule: validateNonEmptyString(value.rule, "rule"),
        traversal: validateNonEmptyString(value.traversal, "traversal"),
        grid_size: validateInteger(value.grid_size, "grid_size", 2, 64),
        frames: validateInteger(value.frames, "frames", 1, 500),
        geometries: validateGeometries(value.geometries),
    };
    if (value.pattern !== undefined) {
        config.pattern = validateNonEmptyString(value.pattern, "pattern");
    }
    return config;
}

export function encodeCompareRunFragment(config: CompareRunConfig): string {
    return `${RUN_HASH_PREFIX}${RUN_BODY_PREFIX}${base64UrlEncode(JSON.stringify(config))}`;
}

export function readCompareRunBodyFromHash(hash: string): string | null {
    for (const slot of splitHashIntoSlots(hash)) {
        if (slot.tagWithEquals === RUN_HASH_PREFIX && slot.body.startsWith(RUN_BODY_PREFIX)) {
            return slot.body.slice(RUN_BODY_PREFIX.length);
        }
    }
    return null;
}

export function decodeCompareRunFragment(hash: string): CompareRunConfig | null {
    const body = readCompareRunBodyFromHash(hash);
    if (!body) {
        return null;
    }
    let parsed: unknown;
    try {
        parsed = JSON.parse(base64UrlDecode(body));
    } catch (error) {
        if (error instanceof CompareRunLinkDecodeError) {
            throw error;
        }
        throw new CompareRunLinkDecodeError("Run link payload is not valid JSON.");
    }
    return validateConfig(parsed);
}

export function buildCompareRunUrl(config: CompareRunConfig, currentUrl: string): string {
    const hashIndex = currentUrl.indexOf("#");
    const baseUrl = hashIndex === -1 ? currentUrl : currentUrl.slice(0, hashIndex);
    const existingHash = hashIndex === -1 ? "" : currentUrl.slice(hashIndex + 1);
    const slots = splitHashIntoSlots(existingHash)
        .filter((slot) => slot.raw !== COMPARE_ROUTE_SLOT && slot.tagWithEquals !== RUN_HASH_PREFIX)
        .map((slot) => slot.raw);
    const merged = [COMPARE_ROUTE_SLOT, encodeCompareRunFragment(config), ...slots];
    return `${baseUrl}${joinSlots(merged)}`;
}
