import { regularCellId } from "../topology.js";
import { describeTopologySpec } from "../topology-catalog.js";
import type { TopologyPayload, TopologySpec } from "../types/domain.js";

export function buildRegularPreviewTopology(
    geometry: string,
    topologySpec: Partial<TopologySpec> = {},
): TopologyPayload | null {
    if (!["square", "hex", "triangle"].includes(String(geometry))) {
        return null;
    }

    const width = Number(topologySpec?.width) || 0;
    const height = Number(topologySpec?.height) || 0;
    const cells: TopologyPayload["cells"] = [];
    for (let y = 0; y < height; y += 1) {
        for (let x = 0; x < width; x += 1) {
            cells.push({
                id: regularCellId(x, y),
                kind: "cell",
                neighbors: [],
            });
        }
    }

    return {
        topology_revision: `preview:${geometry}:${width}x${height}`,
        topology_spec: describeTopologySpec({
            ...topologySpec,
            width,
            height,
        }),
        cells,
    };
}
