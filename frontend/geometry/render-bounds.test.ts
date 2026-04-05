import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
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

interface Bounds {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
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

function boundsWidth(bounds: Bounds): number {
    return bounds.maxX - bounds.minX;
}

function boundsHeight(bounds: Bounds): number {
    return bounds.maxY - bounds.minY;
}

function boundsAspectRatio(bounds: Bounds): number {
    const width = boundsWidth(bounds);
    const height = boundsHeight(bounds);
    return Math.max(width, height) / Math.max(1e-9, Math.min(width, height));
}

function topologyBounds(fixture: TopologyFixture): Bounds {
    const vertices = fixture.topology.cells.flatMap((cell) => cell.vertices ?? []);
    return {
        minX: Math.min(...vertices.map((vertex) => vertex.x)),
        maxX: Math.max(...vertices.map((vertex) => vertex.x)),
        minY: Math.min(...vertices.map((vertex) => vertex.y)),
        maxY: Math.max(...vertices.map((vertex) => vertex.y)),
    };
}

async function renderedBoundsForFixture(filename: string): Promise<Bounds> {
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
    const vertices = cache.cells.flatMap((cell) => cell.vertices);
    return {
        minX: Math.min(...vertices.map((vertex) => vertex.x)),
        maxX: Math.max(...vertices.map((vertex) => vertex.x)),
        minY: Math.min(...vertices.map((vertex) => vertex.y)),
        maxY: Math.max(...vertices.map((vertex) => vertex.y)),
    };
}

async function renderedMetricsAndBoundsForFixture(
    filename: string,
): Promise<{ bounds: Bounds; cssWidth: number; cssHeight: number }> {
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
    const vertices = cache.cells.flatMap((cell) => cell.vertices);
    return {
        bounds: {
            minX: Math.min(...vertices.map((vertex) => vertex.x)),
            maxX: Math.max(...vertices.map((vertex) => vertex.x)),
            minY: Math.min(...vertices.map((vertex) => vertex.y)),
            maxY: Math.max(...vertices.map((vertex) => vertex.y)),
        },
        cssWidth: metrics.cssWidth,
        cssHeight: metrics.cssHeight,
    };
}

describe("geometry/render-bounds", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installFrontendGlobals();
        window.APP_TOPOLOGIES = [
            ...window.APP_TOPOLOGIES,
            topologyEntry("archimedean-4-8-8", "polygon_periodic"),
            topologyEntry("chair", "polygon_aperiodic"),
            topologyEntry("hat-monotile", "polygon_aperiodic"),
            topologyEntry("robinson-triangles", "polygon_aperiodic"),
            topologyEntry("shield", "polygon_aperiodic"),
            topologyEntry("pinwheel", "polygon_aperiodic"),
            topologyEntry("square-triangle", "polygon_aperiodic"),
            topologyEntry("tuebingen-triangle", "polygon_aperiodic"),
        ];
    });

    it("keeps representative polygon fixtures non-degenerate in render space", async () => {
        for (const filename of [
            "archimedean-4-8-8-3x3.json",
            "chair-depth-3.json",
            "hat-monotile-depth-3.json",
            "robinson-triangles-depth-3.json",
            "square-triangle-depth-3.json",
            "shield-depth-3.json",
            "pinwheel-depth-3.json",
            "tuebingen-triangle-depth-3.json",
        ]) {
            const fixture = loadFixture(filename);
            const sourceBounds = topologyBounds(fixture);
            const renderedBounds = await renderedBoundsForFixture(filename);
            expect(boundsWidth(renderedBounds), filename).toBeGreaterThan(1);
            expect(boundsHeight(renderedBounds), filename).toBeGreaterThan(1);
            expect(boundsAspectRatio(renderedBounds), filename).toBeCloseTo(
                boundsAspectRatio(sourceBounds),
                2,
            );
        }
    }, 30_000);

    it("frames chair tightly enough that the rendered patch occupies most of the canvas box", async () => {
        const rendered = await renderedMetricsAndBoundsForFixture("chair-depth-3.json");
        expect(boundsWidth(rendered.bounds) / rendered.cssWidth).toBeGreaterThan(0.8);
        expect(boundsHeight(rendered.bounds) / rendered.cssHeight).toBeGreaterThan(0.8);
    });

    it("frames Robinson and Tuebingen representative fixtures tightly enough for visual inspection", async () => {
        for (const filename of [
            "robinson-triangles-depth-3.json",
            "tuebingen-triangle-depth-3.json",
        ]) {
            const rendered = await renderedMetricsAndBoundsForFixture(filename);
            expect(boundsWidth(rendered.bounds) / rendered.cssWidth, filename).toBeGreaterThan(0.8);
            expect(boundsHeight(rendered.bounds) / rendered.cssHeight, filename).toBeGreaterThan(0.8);
        }
    });

    it("frames promoted-experimental candidate fixtures tightly enough for browser-visible review", async () => {
        for (const filename of [
            "square-triangle-depth-3.json",
            "shield-depth-3.json",
            "pinwheel-depth-3.json",
        ]) {
            const rendered = await renderedMetricsAndBoundsForFixture(filename);
            expect(boundsWidth(rendered.bounds) / rendered.cssWidth, filename).toBeGreaterThan(0.75);
            expect(boundsHeight(rendered.bounds) / rendered.cssHeight, filename).toBeGreaterThan(0.75);
        }
    });
});
