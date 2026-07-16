import type {
    PatternPayload,
    SeedComparisonResult,
    SeedFilmstripResult,
    TopologyComparisonResultPayload,
    TopologyFilmstrip,
} from "../types/domain.js";

export const PATTERN_FORMAT = "cellular-automaton-lab-pattern";
export const PATTERN_VERSION = 5;

export function buildComparisonStatePattern(
    comparison: SeedComparisonResult,
    result: TopologyComparisonResultPayload,
    phase: "begin" | "end",
): PatternPayload | null {
    const cells = phase === "begin" ? result.initial_cells_by_id : result.final_cells_by_id;
    if (!result.topology_spec || cells === undefined) return null;
    return {
        format: PATTERN_FORMAT,
        version: PATTERN_VERSION,
        topology_spec: result.topology_spec,
        rule: comparison.rule_name,
        cells_by_id: cells,
    };
}

export function buildFilmstripFramePattern(
    filmstrip: SeedFilmstripResult,
    tiling: TopologyFilmstrip,
    frameIndex: number,
): PatternPayload | null {
    const cells = tiling.frames[frameIndex];
    if (!tiling.topology_spec || cells === undefined) return null;
    return {
        format: PATTERN_FORMAT,
        version: PATTERN_VERSION,
        topology_spec: tiling.topology_spec,
        rule: filmstrip.rule_name,
        cells_by_id: cells,
    };
}
