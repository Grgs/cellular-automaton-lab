import type { TopologyCell, TopologyIndex, TopologyPayload } from "./types/domain.js";

export function indexTopology(topology: TopologyPayload | null | undefined): TopologyIndex {
    const byId = new Map<string, TopologyCell & { index: number }>();
    topology?.cells?.forEach((cell, index) => {
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
