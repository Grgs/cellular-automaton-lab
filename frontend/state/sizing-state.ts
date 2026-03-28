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

function normalizeCellSizeByTilingFamily(value: unknown): Record<string, number> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return {};
    }
    return Object.fromEntries(
        Object.entries(value)
            .filter(([tilingFamily]) => typeof tilingFamily === "string" && tilingFamily.length > 0)
            .map(([tilingFamily, cellSize]) => [
                tilingFamily,
                normalizeCellSizeForTilingFamily(tilingFamily, cellSize),
            ])
            .filter(([, cellSize]) => Number.isInteger(cellSize)),
    );
}

function normalizePatchDepthByTilingFamily(value: unknown): Record<string, number> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return {};
    }
    return Object.fromEntries(
        Object.entries(value)
            .filter(([tilingFamily]) => typeof tilingFamily === "string" && tilingFamily.length > 0)
            .map(([tilingFamily, patchDepth]) => [
                tilingFamily,
                normalizePatchDepthForTilingFamily(tilingFamily, patchDepth),
            ])
            .filter(([, patchDepth]) => Number.isInteger(patchDepth)),
    );
}

export function sizingPolicyForTilingFamily(tilingFamily: string | null | undefined): Readonly<SizingPolicy> {
    return getTopologySizingPolicy(tilingFamily);
}

export function defaultCellSizeForTilingFamily(tilingFamily: string | null | undefined): number {
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "cell_size"
        ? policy.default
        : DEFAULT_CELL_SIZE;
}

export function minCellSizeForTilingFamily(tilingFamily: string | null | undefined): number {
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "cell_size"
        ? policy.min
        : MIN_CELL_SIZE;
}

export function maxCellSizeForTilingFamily(tilingFamily: string | null | undefined): number {
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "cell_size"
        ? policy.max
        : MAX_CELL_SIZE;
}

export function normalizeCellSize(value: unknown): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return DEFAULT_CELL_SIZE;
    }
    return Math.min(MAX_CELL_SIZE, Math.max(MIN_CELL_SIZE, Math.round(parsed)));
}

export function normalizeCellSizeForTilingFamily(
    tilingFamily: string | null | undefined,
    value: unknown,
): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return defaultCellSizeForTilingFamily(tilingFamily);
    }
    return Math.min(
        maxCellSizeForTilingFamily(tilingFamily),
        Math.max(minCellSizeForTilingFamily(tilingFamily), Math.round(parsed)),
    );
}

export function normalizeRenderCellSize(value: unknown): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return DEFAULT_CELL_SIZE;
    }
    return Math.min(MAX_RENDER_CELL_SIZE, Math.max(MIN_RENDER_CELL_SIZE, parsed));
}

export function normalizePatchDepth(value: unknown): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return DEFAULT_PATCH_DEPTH;
    }
    return Math.min(MAX_PATCH_DEPTH, Math.max(MIN_PATCH_DEPTH, Math.round(parsed)));
}

export function maxPatchDepthForTilingFamily(tilingFamily: string | null | undefined): number {
    const policy = sizingPolicyForTilingFamily(tilingFamily);
    return policy.control === "patch_depth"
        ? policy.max
        : MAX_PATCH_DEPTH;
}

export function minPatchDepthForTilingFamily(tilingFamily: string | null | undefined): number {
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
    value: unknown,
): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return defaultPatchDepthForTilingFamily(tilingFamily);
    }
    return Math.min(
        maxPatchDepthForTilingFamily(tilingFamily),
        Math.max(minPatchDepthForTilingFamily(tilingFamily), Math.round(parsed)),
    );
}

export function setPatchDepth(
    state: AppState,
    patchDepth: unknown,
    tilingFamily: string | null | undefined = state.topologySpec.tiling_family,
): void {
    state.patchDepth = normalizePatchDepthForTilingFamily(tilingFamily, patchDepth);
    state.topologySpec = {
        ...state.topologySpec,
        patch_depth: state.patchDepth,
    };
}

export function setPendingPatchDepth(state: AppState, patchDepth: unknown): void {
    if (patchDepth === null || patchDepth === undefined || patchDepth === "") {
        state.pendingPatchDepth = null;
        return;
    }
    state.pendingPatchDepth = normalizePatchDepthForTilingFamily(state.topologySpec.tiling_family, patchDepth);
}

export function clearPendingPatchDepth(state: AppState): void {
    state.pendingPatchDepth = null;
}

export function setPatchDepthMemoryMap(state: AppState, patchDepthByTilingFamily: unknown): void {
    state.patchDepthByTilingFamily = normalizePatchDepthByTilingFamily(patchDepthByTilingFamily);
}

export function setCellSizeMemoryMap(state: AppState, cellSizeByTilingFamily: unknown): void {
    state.cellSizeByTilingFamily = normalizeCellSizeByTilingFamily(cellSizeByTilingFamily);
}

export function rememberCellSizeForTilingFamily(
    state: AppState,
    tilingFamily: string | null | undefined,
    cellSize: unknown,
): void {
    if (!tilingFamily) {
        return;
    }
    state.cellSizeByTilingFamily = {
        ...normalizeCellSizeByTilingFamily(state.cellSizeByTilingFamily),
        [String(tilingFamily)]: normalizeCellSizeForTilingFamily(tilingFamily, cellSize),
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
    );
}

export function rememberPatchDepthForTilingFamily(
    state: AppState,
    tilingFamily: string | null | undefined,
    patchDepth: unknown,
): void {
    if (!tilingFamily) {
        return;
    }
    state.patchDepthByTilingFamily = {
        ...normalizePatchDepthByTilingFamily(state.patchDepthByTilingFamily),
        [String(tilingFamily)]: normalizePatchDepthForTilingFamily(tilingFamily, patchDepth),
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
        state.patchDepthByTilingFamily[String(tilingFamily)] ?? DEFAULT_PATCH_DEPTH,
    );
}

export function setCellSize(
    state: AppState,
    cellSize: unknown,
    tilingFamily: string | null | undefined = state.topologySpec.tiling_family,
): void {
    state.cellSize = normalizeCellSizeForTilingFamily(tilingFamily, cellSize);
}

export function setRenderCellSize(state: AppState, cellSize: unknown): void {
    state.renderCellSize = normalizeRenderCellSize(cellSize);
}
