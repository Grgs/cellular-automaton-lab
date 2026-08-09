import { isPlainObject } from "../runtime-validation.js";
import {
    normalizeCellSizeForTilingFamily,
    normalizePatchDepthForTilingFamily,
} from "../state/sizing-state.js";

function parseNumberRecord(
    value: unknown,
    normalizeEntry: (key: string, rawValue: unknown) => number,
): Record<string, number> {
    if (!isPlainObject(value)) {
        return {};
    }

    return Object.fromEntries(
        Object.entries(value)
            .filter(([key]) => typeof key === "string" && key.length > 0)
            .map(([key, rawValue]) => [key, normalizeEntry(key, rawValue)])
            .filter(([, normalizedValue]) => Number.isInteger(normalizedValue)),
    );
}

export function parseCellSizeByTilingFamily(
    value: unknown,
    { unsafe = false }: { unsafe?: boolean } = {},
): Record<string, number> {
    return parseNumberRecord(value, (tilingFamily, rawValue) =>
        normalizeCellSizeForTilingFamily(tilingFamily, Number(rawValue), { unsafe }),
    );
}

export function parsePatchDepthByTilingFamily(
    value: unknown,
    { unsafe = false }: { unsafe?: boolean } = {},
): Record<string, number> {
    return parseNumberRecord(value, (tilingFamily, rawValue) =>
        normalizePatchDepthForTilingFamily(tilingFamily, Number(rawValue), { unsafe }),
    );
}
