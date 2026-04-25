import {
    DEFAULT_CELL_SIZE,
    DEFAULT_PATCH_DEPTH,
    MAX_CELL_SIZE,
    MAX_PATCH_DEPTH,
    MAX_RENDER_CELL_SIZE,
    MIN_CELL_SIZE,
    MIN_PATCH_DEPTH,
    MIN_RENDER_CELL_SIZE,
} from "./constants.js";
import { getTopologySizingPolicy } from "../topology-catalog.js";
import type { SizingPolicy } from "../types/domain.js";
import type { AppState } from "../types/state.js";

function normalizeSizingRecord(
    value: Record<string, number>,
    normalizeEntry: (tilingFamily: string, rawValue: number) => number,
): Record<string, number> {
    return Object.fromEntries(
        Object.entries(value)
            .filter(([tilingFamily]) => typeof tilingFamily === "string" && tilingFamily.length > 0)
            .map(([tilingFamily, rawValue]) => [tilingFamily, normalizeEntry(tilingFamily, rawValue)])
            .filter(([, normalizedValue]) => Number.isInteger(normalizedValue)),
    );
}

export function sizingPolicyForTilingFamily(tilingFamily: string | null | undefined): Readonly<SizingPolicy> {
    return getTopologySizingPolicy(tilingFamily);
}

export const MIN_UNSAFE_CELL_SIZE = 1;
export const MAX_UNSAFE_CELL_SIZE = Math.floor(MAX_RENDER_CELL_SIZE);
export const MIN_UNSAFE_PATCH_DEPTH = MIN_PATCH_DEPTH;
export const MAX_UNSAFE_PATCH_DEPTH = 12;
const PATCH_DEPTH_UNSAFE_OVERRIDE_BLOCKLIST = new Set(["dodecagonal-square-triangle"]);

function unsafeSizingEnabled(options: { unsafe?: boolean } = {}): boolean {
    return Boolean(options.unsafe);
}

function safePatchDepthMaxForTilingFamily(tilingFamily: string | null | undefined): number {
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "patch_depth"
        ? policy.max
        : MAX_PATCH_DEPTH;
}

function normalizeInteger(value: number, minimum: number, maximum: number): number {
    const parsed = Number(value);
    return Math.min(maximum, Math.max(minimum, Math.round(parsed)));
}

export function defaultCellSizeForTilingFamily(tilingFamily: string | null | undefined): number {
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "cell_size"
        ? policy.default
        : DEFAULT_CELL_SIZE;
}

export function minCellSizeForTilingFamily(
    tilingFamily: string | null | undefined,
    options: { unsafe?: boolean } = {},
): number {
    if (unsafeSizingEnabled(options)) {
        return MIN_UNSAFE_CELL_SIZE;
    }
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "cell_size"
        ? policy.min
        : MIN_CELL_SIZE;
}

export function maxCellSizeForTilingFamily(
    tilingFamily: string | null | undefined,
    options: { unsafe?: boolean } = {},
): number {
    if (unsafeSizingEnabled(options)) {
        return MAX_UNSAFE_CELL_SIZE;
    }
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "cell_size"
        ? policy.max
        : MAX_CELL_SIZE;
}

export function normalizeCellSize(value: number): number {
    const parsed = Number(value);
    return Math.min(MAX_CELL_SIZE, Math.max(MIN_CELL_SIZE, Math.round(parsed)));
}

export function normalizeCellSizeForTilingFamily(
    tilingFamily: string | null | undefined,
    value: number,
    options: { unsafe?: boolean } = {},
): number {
    return normalizeInteger(
        value,
        minCellSizeForTilingFamily(tilingFamily, options),
        maxCellSizeForTilingFamily(tilingFamily, options),
    );
}

export function normalizeRenderCellSize(value: number): number {
    const parsed = Number(value);
    return Math.min(MAX_RENDER_CELL_SIZE, Math.max(MIN_RENDER_CELL_SIZE, parsed));
}

export function normalizePatchDepth(value: number): number {
    const parsed = Number(value);
    return Math.min(MAX_PATCH_DEPTH, Math.max(MIN_PATCH_DEPTH, Math.round(parsed)));
}

export function maxPatchDepthForTilingFamily(
    tilingFamily: string | null | undefined,
    options: { unsafe?: boolean } = {},
): number {
    if (tilingFamily && PATCH_DEPTH_UNSAFE_OVERRIDE_BLOCKLIST.has(tilingFamily)) {
        return safePatchDepthMaxForTilingFamily(tilingFamily);
    }
    if (unsafeSizingEnabled(options)) {
        return Math.max(MAX_UNSAFE_PATCH_DEPTH, safePatchDepthMaxForTilingFamily(tilingFamily));
    }
    return safePatchDepthMaxForTilingFamily(tilingFamily);
}

export function minPatchDepthForTilingFamily(
    tilingFamily: string | null | undefined,
    options: { unsafe?: boolean } = {},
): number {
    if (unsafeSizingEnabled(options)) {
        return MIN_UNSAFE_PATCH_DEPTH;
    }
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "patch_depth"
        ? policy.min
        : MIN_PATCH_DEPTH;
}

export function defaultPatchDepthForTilingFamily(tilingFamily: string | null | undefined): number {
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "patch_depth"
        ? policy.default
        : DEFAULT_PATCH_DEPTH;
}

export function normalizePatchDepthForTilingFamily(
    tilingFamily: string | null | undefined,
    value: number,
    options: { unsafe?: boolean } = {},
): number {
    return normalizeInteger(
        value,
        minPatchDepthForTilingFamily(tilingFamily, options),
        maxPatchDepthForTilingFamily(tilingFamily, options),
    );
}

export function buildTopologySpecRequest<TTopologySpec extends object>(
    topologySpec: TTopologySpec,
    unsafe = false,
): TTopologySpec & { unsafe_size_override?: boolean } {
    return unsafe
        ? { ...topologySpec, unsafe_size_override: true }
        : { ...topologySpec };
}

export function setPatchDepth(
    state: AppState,
    patchDepth: number,
    tilingFamily: string | null | undefined = state.topologySpec.tiling_family,
    {
        preserveOutOfRange = false,
    }: {
        preserveOutOfRange?: boolean;
    } = {},
): void {
    state.patchDepth = preserveOutOfRange
        ? normalizeInteger(
            patchDepth,
            MIN_UNSAFE_PATCH_DEPTH,
            maxPatchDepthForTilingFamily(tilingFamily, { unsafe: true }),
        )
        : normalizePatchDepthForTilingFamily(tilingFamily, patchDepth, { unsafe: state.unsafeSizingEnabled });
    state.topologySpec = {
        ...state.topologySpec,
        patch_depth: state.patchDepth,
    };
}

export function setPendingPatchDepth(state: AppState, patchDepth: number | null): void {
    if (patchDepth === null) {
        state.pendingPatchDepth = null;
        return;
    }
    state.pendingPatchDepth = normalizePatchDepthForTilingFamily(
        state.topologySpec.tiling_family,
        patchDepth,
        { unsafe: state.unsafeSizingEnabled },
    );
}

export function clearPendingPatchDepth(state: AppState): void {
    state.pendingPatchDepth = null;
}

export function setPatchDepthMemoryMap(state: AppState, patchDepthByTilingFamily: Record<string, number>): void {
    state.patchDepthByTilingFamily = normalizeSizingRecord(
        patchDepthByTilingFamily,
        (tilingFamily, rawValue) => normalizePatchDepthForTilingFamily(
            tilingFamily,
            rawValue,
            { unsafe: state.unsafeSizingEnabled },
        ),
    );
}

export function setCellSizeMemoryMap(state: AppState, cellSizeByTilingFamily: Record<string, number>): void {
    state.cellSizeByTilingFamily = normalizeSizingRecord(
        cellSizeByTilingFamily,
        (tilingFamily, rawValue) => normalizeCellSizeForTilingFamily(
            tilingFamily,
            rawValue,
            { unsafe: state.unsafeSizingEnabled },
        ),
    );
}

export function rememberCellSizeForTilingFamily(
    state: AppState,
    tilingFamily: string | null | undefined,
    cellSize: number,
): void {
    if (!tilingFamily) {
        return;
    }
    state.cellSizeByTilingFamily = {
        ...normalizeSizingRecord(
            state.cellSizeByTilingFamily,
            (candidateTilingFamily, rawValue) => normalizeCellSizeForTilingFamily(
                candidateTilingFamily,
                rawValue,
                { unsafe: state.unsafeSizingEnabled },
            ),
        ),
        [String(tilingFamily)]: normalizeCellSizeForTilingFamily(
            tilingFamily,
            cellSize,
            { unsafe: state.unsafeSizingEnabled },
        ),
    };
}

export function rememberedCellSizeForTilingFamily(
    state: AppState,
    tilingFamily: string | null | undefined,
): number {
    if (!tilingFamily) {
        return DEFAULT_CELL_SIZE;
    }
    return normalizeCellSizeForTilingFamily(
        tilingFamily,
        state.cellSizeByTilingFamily[String(tilingFamily)] ?? defaultCellSizeForTilingFamily(tilingFamily),
        { unsafe: state.unsafeSizingEnabled },
    );
}

export function rememberPatchDepthForTilingFamily(
    state: AppState,
    tilingFamily: string | null | undefined,
    patchDepth: number,
): void {
    if (!tilingFamily) {
        return;
    }
    state.patchDepthByTilingFamily = {
        ...normalizeSizingRecord(
            state.patchDepthByTilingFamily,
            (candidateTilingFamily, rawValue) => normalizePatchDepthForTilingFamily(
                candidateTilingFamily,
                rawValue,
                { unsafe: state.unsafeSizingEnabled },
            ),
        ),
        [String(tilingFamily)]: normalizePatchDepthForTilingFamily(
            tilingFamily,
            patchDepth,
            { unsafe: state.unsafeSizingEnabled },
        ),
    };
}

export function rememberedPatchDepthForTilingFamily(
    state: AppState,
    tilingFamily: string | null | undefined,
): number {
    if (!tilingFamily) {
        return DEFAULT_PATCH_DEPTH;
    }
    return normalizePatchDepthForTilingFamily(
        tilingFamily,
        state.patchDepthByTilingFamily[String(tilingFamily)] ?? defaultPatchDepthForTilingFamily(tilingFamily),
        { unsafe: state.unsafeSizingEnabled },
    );
}

export function setCellSize(
    state: AppState,
    cellSize: number,
    tilingFamily: string | null | undefined = state.topologySpec.tiling_family,
): void {
    state.cellSize = normalizeCellSizeForTilingFamily(
        tilingFamily,
        cellSize,
        { unsafe: state.unsafeSizingEnabled },
    );
}

export function setRenderCellSize(state: AppState, cellSize: number): void {
    state.renderCellSize = normalizeRenderCellSize(cellSize);
}
