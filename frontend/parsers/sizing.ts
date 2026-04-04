import { isPlainObject } from "../runtime-validation.js";
import {
    defaultCellSizeForTilingFamily,
    defaultPatchDepthForTilingFamily,
    normalizeCellSize,
    normalizeCellSizeForTilingFamily,
    normalizePatchDepth,
    normalizePatchDepthForTilingFamily,
    normalizeRenderCellSize,
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

export function parseCellSize(value: unknown): number {
    const parsed = Number(value);
    return Number.isFinite(parsed)
        ? normalizeCellSize(parsed)
        : normalizeCellSize(defaultCellSizeForTilingFamily(null));
}

export function parseRenderCellSize(value: unknown): number {
    const parsed = Number(value);
    return Number.isFinite(parsed)
        ? normalizeRenderCellSize(parsed)
        : normalizeRenderCellSize(defaultCellSizeForTilingFamily(null));
}

export function parsePatchDepth(value: unknown): number {
    const parsed = Number(value);
    return Number.isFinite(parsed)
        ? normalizePatchDepth(parsed)
        : normalizePatchDepth(defaultPatchDepthForTilingFamily(null));
}

export function parseCellSizeByTilingFamily(
    value: unknown,
    { unsafe = false }: { unsafe?: boolean } = {},
): Record<string, number> {
    return parseNumberRecord(
        value,
        (tilingFamily, rawValue) => normalizeCellSizeForTilingFamily(
            tilingFamily,
            Number(rawValue),
            { unsafe },
        ),
    );
}

export function parsePatchDepthByTilingFamily(
    value: unknown,
    { unsafe = false }: { unsafe?: boolean } = {},
): Record<string, number> {
    return parseNumberRecord(
        value,
        (tilingFamily, rawValue) => normalizePatchDepthForTilingFamily(
            tilingFamily,
            Number(rawValue),
            { unsafe },
        ),
    );
}
