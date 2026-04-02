import { hasPatternCells } from "../state/overlay-state.js";
import type { ResetControlBody } from "../types/controller.js";
import type { CellStateUpdate, ParsedPattern } from "../types/domain.js";
import type { AppState } from "../types/state.js";

export function shouldConfirmPatternImport(state: AppState): boolean {
    return Number(state.generation) > 0 || hasPatternCells(state);
}

export function buildPatternImportResetRequest(
    parsedPattern: ParsedPattern,
    speed: number,
): ResetControlBody {
    return {
        topology_spec: {
            ...parsedPattern.topologySpec,
            width: parsedPattern.width,
            height: parsedPattern.height,
            patch_depth: parsedPattern.patchDepth,
        },
        speed,
        rule: parsedPattern.rule,
        randomize: false,
    };
}

export function normalizeImportedCellUpdates(parsedPattern: ParsedPattern): CellStateUpdate[] {
    return Object.entries(parsedPattern.cellsById).map(([id, state]) => ({
        id,
        state,
    }));
}
