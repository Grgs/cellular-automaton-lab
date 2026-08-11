import { resolveTopologyVariantKey } from "./topology-catalog.js";
import type {
    CartesianSeedCell,
    CellStateUpdate,
    TopologyIndex,
    TopologyPayload,
} from "./types/domain.js";
import { findTopologyCellById } from "./topology-index.js";
export { findTopologyCellById, indexTopology } from "./topology-index.js";

export const ARCHIMEDEAN_488_GEOMETRY = "archimedean-4-8-8";
export const ARCHIMEDEAN_31212_GEOMETRY = "archimedean-3-12-12";
export const ARCHIMEDEAN_3464_GEOMETRY = "archimedean-3-4-6-4";
export const ARCHIMEDEAN_4612_GEOMETRY = "archimedean-4-6-12";
export const ARCHIMEDEAN_33434_GEOMETRY = "archimedean-3-3-4-3-4";
export const ARCHIMEDEAN_33344_GEOMETRY = "archimedean-3-3-3-4-4";
export const ARCHIMEDEAN_33336_GEOMETRY = "archimedean-3-3-3-3-6";
export const KAGOME_GEOMETRY = "trihexagonal-3-6-3-6";
export const CAIRO_GEOMETRY = "cairo-pentagonal";
export const RHOMBILLE_GEOMETRY = "rhombille";
export const DELTOIDAL_HEXAGONAL_GEOMETRY = "deltoidal-hexagonal";
export const TETRAKIS_SQUARE_GEOMETRY = "tetrakis-square";
export const TRIAKIS_TRIANGULAR_GEOMETRY = "triakis-triangular";
export const DELTOIDAL_TRIHEXAGONAL_GEOMETRY = "deltoidal-trihexagonal";
export const PRISMATIC_PENTAGONAL_GEOMETRY = "prismatic-pentagonal";
export const FLORET_PENTAGONAL_GEOMETRY = "floret-pentagonal";
export const SNUB_SQUARE_DUAL_GEOMETRY = "snub-square-dual";
export const TYPE_7_PENTAGONAL_GEOMETRY = "type-7-pentagonal";
export function topologyVariantKey(topology: TopologyPayload | null | undefined): string {
    const topologySpec = topology?.topology_spec;
    if (!topologySpec || typeof topologySpec !== "object") {
        return "square";
    }
    return resolveTopologyVariantKey(topologySpec.tiling_family, topologySpec.adjacency_mode);
}

export function topologyWidth(topology: TopologyPayload | null | undefined): number {
    return Number(topology?.topology_spec?.width) || 0;
}

export function topologyHeight(topology: TopologyPayload | null | undefined): number {
    return Number(topology?.topology_spec?.height) || 0;
}

export function isRegularGeometry(geometry: string): boolean {
    return geometry === "square" || geometry === "hex" || geometry === "triangle";
}

export function regularCellId(x: number, y: number): string {
    return `c:${x}:${y}`;
}

export function parseRegularCellId(
    cellId: string | null | undefined,
): { x: number; y: number } | null {
    const match = /^c:(-?\d+):(-?\d+)$/.exec(String(cellId || ""));
    if (!match) {
        return null;
    }
    return {
        x: Number(match[1]),
        y: Number(match[2]),
    };
}

export function topologyCellStatesById(
    topology: TopologyPayload | null | undefined,
    cellStates: number[] | null | undefined,
): Record<string, number> {
    const byId: Record<string, number> = {};
    if (!topology || !Array.isArray(topology.cells) || !Array.isArray(cellStates)) {
        return byId;
    }
    topology.cells.forEach((cell, index) => {
        const state = Number(cellStates[index] ?? 0);
        if (state !== 0) {
            byId[cell.id] = state;
        }
    });
    return byId;
}

export function presetCellsToTopologyUpdates(
    topologyIndex: TopologyIndex | null | undefined,
    cells: Array<CartesianSeedCell | CellStateUpdate>,
): CellStateUpdate[] {
    return cells.flatMap((cell) => {
        if ("id" in cell && typeof cell.id === "string") {
            return [{ id: cell.id, state: cell.state }];
        }
        if (
            !("x" in cell) ||
            !("y" in cell) ||
            !Number.isFinite(cell.x) ||
            !Number.isFinite(cell.y)
        ) {
            return [];
        }
        const resolved = findTopologyCellById(topologyIndex, regularCellId(cell.x, cell.y));
        return resolved ? [{ id: resolved.id, state: cell.state }] : [];
    });
}
