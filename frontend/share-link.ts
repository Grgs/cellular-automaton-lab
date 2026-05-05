/**
 * Shareable URL state for board configurations.
 *
 * The hash format is:
 *
 *     #share=v1.<base64url(JSON.stringify(PatternPayload))>
 *
 * The encoded payload is the same `PatternPayload` shape used by the
 * Import/Export Pattern flow (`format`, `version`, `topology_spec`, `rule`,
 * `cells_by_id`). Reusing that schema means the share-link parser delegates to
 * the existing well-tested `parsePatternText` and any future evolution of the
 * pattern format only needs to bump the version once.
 *
 * Future versions can switch to a compressed binary representation under a
 * different prefix (e.g. `v2.`) without breaking links emitted by v1.
 */

import { parsePatternText, PatternValidationError } from "./parsers/pattern.js";
import type { ParsedPattern, PatternPayload } from "./types/domain.js";

export const SHARE_HASH_KEY = "share";
export const SHARE_VERSION_TAG = "v1";

const SHARE_HASH_PREFIX = `${SHARE_HASH_KEY}=`;
const SHARE_BODY_PREFIX = `${SHARE_VERSION_TAG}.`;

export class ShareLinkDecodeError extends Error {}

function base64UrlEncode(value: string): string {
    // btoa requires a binary string; encode UTF-8 first so multi-byte chars survive.
    const utf8Bytes = new TextEncoder().encode(value);
    let binary = "";
    for (const byte of utf8Bytes) {
        binary += String.fromCharCode(byte);
    }
    const base64 = btoa(binary);
    return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
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
        throw new ShareLinkDecodeError("Share link payload is not valid base64.");
    }
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
        bytes[index] = binary.charCodeAt(index);
    }
    return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
}

export function encodeShareFragment(payload: PatternPayload): string {
    const json = JSON.stringify(payload);
    return `${SHARE_HASH_PREFIX}${SHARE_BODY_PREFIX}${base64UrlEncode(json)}`;
}

interface ShareHashSlot {
    tagWithEquals: string;
    body: string;
    raw: string;
}

function splitHashIntoSlots(hash: string): ShareHashSlot[] {
    const trimmed = hash.startsWith("#") ? hash.slice(1) : hash;
    if (!trimmed) {
        return [];
    }
    return trimmed.split("&").map((segment) => {
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

export function readShareBodyFromHash(hash: string): string | null {
    const slots = splitHashIntoSlots(hash);
    for (const slot of slots) {
        if (slot.tagWithEquals === SHARE_HASH_PREFIX && slot.body.startsWith(SHARE_BODY_PREFIX)) {
            return slot.body.slice(SHARE_BODY_PREFIX.length);
        }
    }
    return null;
}

export function decodeShareFragment(hash: string): ParsedPattern | null {
    const body = readShareBodyFromHash(hash);
    if (!body) {
        return null;
    }
    let json: string;
    try {
        json = base64UrlDecode(body);
    } catch (error) {
        if (error instanceof ShareLinkDecodeError) {
            throw error;
        }
        throw new ShareLinkDecodeError("Failed to decode share link payload.");
    }
    try {
        return parsePatternText(json);
    } catch (error) {
        if (error instanceof PatternValidationError) {
            throw new ShareLinkDecodeError(`Share link is invalid: ${error.message}`);
        }
        throw error;
    }
}

export function buildShareUrl(payload: PatternPayload, currentUrl: string): string {
    // currentUrl may be passed as-is from window.location.href.
    // Replace the hash portion with the new share fragment, preserving any
    // unrelated existing hash segments.
    const hashIndex = currentUrl.indexOf("#");
    const baseUrl = hashIndex === -1 ? currentUrl : currentUrl.slice(0, hashIndex);
    const existingHash = hashIndex === -1 ? "" : currentUrl.slice(hashIndex + 1);
    const newFragment = encodeShareFragment(payload);
    const otherSlots = splitHashIntoSlots(existingHash).filter(
        (slot) => slot.tagWithEquals !== SHARE_HASH_PREFIX,
    );
    const merged = otherSlots.length > 0
        ? [newFragment, ...otherSlots.map((slot) => slot.raw)].join("&")
        : newFragment;
    return `${baseUrl}#${merged}`;
}

export function buildHashFragmentForReplaceState(
    payload: PatternPayload,
    currentHash: string,
): string {
    const newFragment = encodeShareFragment(payload);
    const otherSlots = splitHashIntoSlots(currentHash).filter(
        (slot) => slot.tagWithEquals !== SHARE_HASH_PREFIX,
    );
    return otherSlots.length > 0
        ? `#${[newFragment, ...otherSlots.map((slot) => slot.raw)].join("&")}`
        : `#${newFragment}`;
}

export function clearShareFragment(currentHash: string): string {
    const otherSlots = splitHashIntoSlots(currentHash).filter(
        (slot) => slot.tagWithEquals !== SHARE_HASH_PREFIX,
    );
    return otherSlots.length > 0 ? `#${otherSlots.map((slot) => slot.raw).join("&")}` : "";
}
