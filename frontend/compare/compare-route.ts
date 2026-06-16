/**
 * Hash-route helpers for the compare workspace.
 *
 * Compare mode is addressable as a `/compare` segment in the URL hash, e.g.
 * `#/compare`. The hash is the same `&`-separated slot space used by share links
 * (`#share=v1.…`), so the compare route coexists with a share fragment:
 * `#/compare&share=v1.…` is valid and both are honoured independently. Using the
 * hash (not the path) keeps this working in the standalone, server-less build.
 */

const COMPARE_ROUTE_SEGMENT = "/compare";

function splitHash(hash: string): string[] {
    const trimmed = hash.startsWith("#") ? hash.slice(1) : hash;
    if (!trimmed) {
        return [];
    }
    return trimmed.split("&").filter((segment) => segment.length > 0);
}

function joinHash(segments: string[]): string {
    return segments.length > 0 ? `#${segments.join("&")}` : "";
}

/** True when the hash addresses the compare workspace. */
export function hashHasCompareRoute(hash: string): boolean {
    return splitHash(hash).includes(COMPARE_ROUTE_SEGMENT);
}

/** Add the compare route to a hash, preserving any other slots (idempotent). */
export function hashWithCompareRoute(hash: string): string {
    const segments = splitHash(hash);
    if (segments.includes(COMPARE_ROUTE_SEGMENT)) {
        return joinHash(segments);
    }
    return joinHash([COMPARE_ROUTE_SEGMENT, ...segments]);
}

/** Remove the compare route from a hash, preserving any other slots (idempotent). */
export function hashWithoutCompareRoute(hash: string): string {
    return joinHash(splitHash(hash).filter((segment) => segment !== COMPARE_ROUTE_SEGMENT));
}
