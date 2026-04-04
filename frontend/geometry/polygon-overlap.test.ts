import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import { findPositiveAreaPolygonOverlaps } from "../test-helpers/polygon-overlap.js";
import type { BootstrappedTopologyDefinition, TopologyPayload } from "../types/domain.js";
import type { GeometryCache, PolygonGeometryCache } from "../types/rendering.js";

interface TopologyFixture {
    geometry: string;
    width: number;
    height: number;
    patchDepth: number | null;
    cellSize: number;
    topology: TopologyPayload;
}

const __dirname = dirname(fileURLToPath(import.meta.url));
const FIXTURE_DIR = resolve(__dirname, "../test-fixtures/topologies");

function topologyEntry(
    tilingFamily: string,
    renderKind: "polygon_aperiodic" | "polygon_periodic",
): BootstrappedTopologyDefinition {
    return {
        tiling_family: tilingFamily,
        label: tilingFamily,
        picker_group: renderKind === "polygon_aperiodic" ? "Aperiodic" : "Mixed",
        picker_order: 999,
        sizing_mode: renderKind === "polygon_aperiodic" ? "patch_depth" : "grid",
        family: renderKind === "polygon_aperiodic" ? "aperiodic" : "mixed",
        render_kind: renderKind,
        viewport_sync_mode: renderKind === "polygon_aperiodic" ? "presentation-only" : "backend-sync",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "life-b2-s23" },
        geometry_keys: { edge: tilingFamily },
        sizing_policy: {
            control: renderKind === "polygon_aperiodic" ? "patch_depth" : "cell_size",
            default: 3,
            min: 0,
            max: 12,
        },
    };
}

function loadFixture(filename: string): TopologyFixture {
    const raw = readFileSync(resolve(FIXTURE_DIR, filename), "utf-8");
    return JSON.parse(raw) as TopologyFixture;
}

function asPolygonGeometryCache(cache: GeometryCache | null): PolygonGeometryCache {
    if (!cache || !("cellsById" in cache) || !Array.isArray(cache.cells)) {
        throw new Error("Expected polygon geometry cache.");
    }
    return cache as PolygonGeometryCache;
}

describe("geometry/polygon-overlap", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installFrontendGlobals();
        window.APP_TOPOLOGIES = [
            ...window.APP_TOPOLOGIES,
            topologyEntry("archimedean-4-8-8", "polygon_periodic"),
            topologyEntry("chair", "polygon_aperiodic"),
            topologyEntry("hat-monotile", "polygon_aperiodic"),
            topologyEntry("shield", "polygon_aperiodic"),
            topologyEntry("pinwheel", "polygon_aperiodic"),
            topologyEntry("square-triangle", "polygon_aperiodic"),
        ];
    });

    async function overlapsForFixture(filename: string, maxResults?: number) {
        const { getGeometryAdapter } = await import("./registry.js");
        const fixture = loadFixture(filename);
        const topology = fixture.topology;
        const adapter = getGeometryAdapter(fixture.geometry);
        const width = fixture.width || topology.topology_spec.width || 0;
        const height = fixture.height || topology.topology_spec.height || 0;
        const metrics = adapter.buildMetrics({
            width,
            height,
            cellSize: fixture.cellSize,
            topology,
        });
        const cache = asPolygonGeometryCache(
            adapter.buildCache({
                width,
                height,
                cellSize: fixture.cellSize,
                metrics,
                topology,
                maxCachedCells: topology.cells.length,
            }),
        );
        return findPositiveAreaPolygonOverlaps(cache.cells, undefined, maxResults);
    }

    it("keeps representative polygon fixtures free of render-space overlap", async () => {
        for (const filename of [
            "archimedean-4-8-8-3x3.json",
            "chair-depth-3.json",
            "hat-monotile-depth-3.json",
            "square-triangle-depth-3.json",
            "shield-depth-3.json",
            "pinwheel-depth-3.json",
        ]) {
            const overlaps = await overlapsForFixture(filename);
            expect(overlaps, filename).toEqual([]);
        }
    }, 30_000);
});
