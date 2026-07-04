/**
 * Hash-route helpers for the app's two destinations.
 *
 * The URL hash is an `&`-separated slot space shared with run links
 * (`run=v1.…`) and board share links (`share=v1.…`). Two route segments live in
 * it: `/lab` addresses the single-board editor, and the legacy `/compare`
 * segment is kept as a parsed-forever alias for the wall (it is never emitted
 * for new links). A bare hash is the wall — the comparison is the landing
 * experience. Using the hash (not the path) keeps all of this working in the
 * standalone, server-less build.
 */

const COMPARE_ROUTE_SEGMENT = "/compare";
const LAB_ROUTE_SEGMENT = "/lab";
const FOCUS_SLOT_PREFIX = "focus=";
const SHARE_SLOT_PREFIX = "share=";

/** The two top-level destinations the hash can resolve to. */
export type ShellRoute = "wall" | "lab";

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

/** The focused board's geometry key, when the hash addresses speaker view. */
export function readFocusFromHash(hash: string): string | null {
    const segment = splitHash(hash).find((slot) => slot.startsWith(FOCUS_SLOT_PREFIX));
    if (!segment) {
        return null;
    }
    const value = segment.slice(FOCUS_SLOT_PREFIX.length);
    try {
        return decodeURIComponent(value) || null;
    } catch {
        return value || null;
    }
}

/** Set the focused geometry slot, replacing any existing one (preserves other slots). */
export function hashWithFocus(hash: string, geometry: string): string {
    const segments = splitHash(hash).filter((slot) => !slot.startsWith(FOCUS_SLOT_PREFIX));
    segments.push(`${FOCUS_SLOT_PREFIX}${encodeURIComponent(geometry)}`);
    return joinHash(segments);
}

/** Remove the focus slot, returning to gallery view (idempotent). */
export function hashWithoutFocus(hash: string): string {
    return joinHash(splitHash(hash).filter((slot) => !slot.startsWith(FOCUS_SLOT_PREFIX)));
}

/** True when the hash addresses the Lab (the single-board editor). */
export function hashHasLabRoute(hash: string): boolean {
    return splitHash(hash).includes(LAB_ROUTE_SEGMENT);
}

/** Add the Lab route to a hash, preserving any other slots (idempotent). */
export function hashWithLabRoute(hash: string): string {
    const segments = splitHash(hash);
    if (segments.includes(LAB_ROUTE_SEGMENT)) {
        return joinHash(segments);
    }
    return joinHash([LAB_ROUTE_SEGMENT, ...segments]);
}

/** Remove the Lab route from a hash, preserving any other slots (idempotent). */
export function hashWithoutLabRoute(hash: string): string {
    return joinHash(splitHash(hash).filter((segment) => segment !== LAB_ROUTE_SEGMENT));
}

/**
 * Resolve which destination a hash addresses. The wall is the default: the Lab
 * is only addressed explicitly (`/lab`) or by a board share link (`share=…`)
 * that is not wrapped in the legacy `/compare` alias — a shared board is an
 * editor artefact, so bare share links keep landing in the editor.
 */
export function resolveShellRoute(hash: string): ShellRoute {
    const segments = splitHash(hash);
    if (segments.includes(LAB_ROUTE_SEGMENT)) {
        return "lab";
    }
    if (segments.includes(COMPARE_ROUTE_SEGMENT)) {
        return "wall";
    }
    if (segments.some((segment) => segment.startsWith(SHARE_SLOT_PREFIX))) {
        return "lab";
    }
    return "wall";
}
