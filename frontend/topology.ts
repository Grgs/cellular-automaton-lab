import {
    resolveTopologyVariantKey,
} from "./topology-catalog.js";
import {
    AMMANN_BEENKER_GEOMETRY,
    CHAIR_KIND,
    CHAIR_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
    HAT_KIND,
    HAT_MONOTILE_GEOMETRY,
    HAT_TILE_FAMILY,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PINWHEEL_GEOMETRY,
    PINWHEEL_TILE_FAMILY,
    PINWHEEL_TRIANGLE_KIND,
    ROBINSON_THICK_KIND,
    ROBINSON_THIN_KIND,
    ROBINSON_TILE_FAMILY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SHIELD_SHIELD_KIND,
    SHIELD_SQUARE_KIND,
    SHIELD_TILE_FAMILY,
    SHIELD_TRIANGLE_KIND,
    SPECTRE_GEOMETRY,
    SPHINX_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TUEBINGEN_THICK_KIND,
    TUEBINGEN_THIN_KIND,
    TUEBINGEN_TILE_FAMILY,
    TUEBINGEN_TRIANGLE_GEOMETRY,
} from "./aperiodic-family-metadata.js";
export {
    AMMANN_BEENKER_GEOMETRY,
    CHAIR_KIND,
    CHAIR_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
    HAT_KIND,
    HAT_MONOTILE_GEOMETRY,
    HAT_TILE_FAMILY,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PINWHEEL_GEOMETRY,
    PINWHEEL_TILE_FAMILY,
    PINWHEEL_TRIANGLE_KIND,
    ROBINSON_THICK_KIND,
    ROBINSON_THIN_KIND,
    ROBINSON_TILE_FAMILY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SHIELD_SHIELD_KIND,
    SHIELD_SQUARE_KIND,
    SHIELD_TILE_FAMILY,
    SHIELD_TRIANGLE_KIND,
    SPECTRE_GEOMETRY,
    SPHINX_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TUEBINGEN_THICK_KIND,
    TUEBINGEN_THIN_KIND,
    TUEBINGEN_TILE_FAMILY,
    TUEBINGEN_TRIANGLE_GEOMETRY,
};
import type {
    CartesianSeedCell,
    CellStateUpdate,
    TopologyCell,
    TopologyIndex,
    TopologyPayload,
} from "./types/domain.js";

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
export const PENROSE_GEOMETRIES = Object.freeze([PENROSE_GEOMETRY, PENROSE_VERTEX_GEOMETRY]);
export const PERIODIC_MIXED_GEOMETRIES = Object.freeze([
    ARCHIMEDEAN_488_GEOMETRY,
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    KAGOME_GEOMETRY,
    CAIRO_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    DELTOIDAL_HEXAGONAL_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    FLORET_PENTAGONAL_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
]);

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

export function isPenroseGeometry(geometry: string): boolean {
    return geometry === PENROSE_GEOMETRY || geometry === PENROSE_VERTEX_GEOMETRY;
}

export function regularCellId(x: number, y: number): string {
    return `c:${x}:${y}`;
}

export function parseRegularCellId(cellId: string | null | undefined): { x: number; y: number } | null {
    const match = /^c:(-?\d+):(-?\d+)$/.exec(String(cellId || ""));
    if (!match) {
        return null;
    }
    return {
        x: Number(match[1]),
        y: Number(match[2]),
    };
}

export function indexTopology(topology: TopologyPayload | null | undefined): TopologyIndex {
    const byId = new Map<string, TopologyCell & { index: number }>();

    if (!topology || !Array.isArray(topology.cells)) {
        return { byId };
    }

    topology.cells.forEach((cell, index) => {
        byId.set(cell.id, { ...cell, index });
    });

    return { byId };
}

export function findTopologyCellById(
    topologyIndex: TopologyIndex | null | undefined,
    cellId: string,
): (TopologyCell & { index: number }) | null {
    return topologyIndex?.byId?.get(cellId) ?? null;
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
        if (!("x" in cell) || !("y" in cell) || !Number.isFinite(cell.x) || !Number.isFinite(cell.y)) {
            return [];
        }
        const resolved = findTopologyCellById(topologyIndex, regularCellId(cell.x, cell.y));
        return resolved ? [{ id: resolved.id, state: cell.state }] : [];
    });
}
