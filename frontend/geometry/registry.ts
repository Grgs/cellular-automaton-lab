import { listTopologyDefinitions } from "../topology-catalog.js";
import { DEFAULT_GEOMETRY } from "./shared.js";
import { createAperiodicPrototileGeometryAdapter } from "./aperiodic-prototile-adapter.js";
import { hexGeometryAdapter } from "./hex-adapter.js";
import { createPeriodicMixedGeometryAdapter } from "./periodic-mixed-adapter.js";
import { squareGeometryAdapter } from "./square-adapter.js";
import { triangleGeometryAdapter } from "./triangle-adapter.js";
import type { GeometryAdapter } from "../types/rendering.js";

function adapterForRenderKind(renderKind: string, geometry: string): GeometryAdapter | null {
    if (renderKind === "polygon_periodic") {
        return createPeriodicMixedGeometryAdapter(geometry);
    }
    if (renderKind === "polygon_aperiodic") {
        return createAperiodicPrototileGeometryAdapter(geometry);
    }
    return null;
}

function bootstrappedGeometryAdapters(): Array<[string, GeometryAdapter]> {
    const adapters: Array<[string, GeometryAdapter]> = [
        [DEFAULT_GEOMETRY, squareGeometryAdapter],
        ["hex", hexGeometryAdapter],
        ["triangle", triangleGeometryAdapter],
    ];
    const seen = new Set<string>(adapters.map(([geometry]) => geometry));
    for (const definition of listTopologyDefinitions()) {
        for (const geometry of Object.values(definition.geometry_keys)) {
            if (seen.has(geometry)) {
                continue;
            }
            const adapter = adapterForRenderKind(definition.render_kind, geometry);
            if (!adapter) {
                continue;
            }
            seen.add(geometry);
            adapters.push([geometry, adapter]);
        }
    }
    return adapters;
}

const GEOMETRY_ADAPTERS = new Map<string, GeometryAdapter>(bootstrappedGeometryAdapters());

export function isSupportedGeometry(geometry: string | null | undefined): boolean {
    return typeof geometry === "string" && GEOMETRY_ADAPTERS.has(geometry);
}

export function normalizeGeometryKey(geometry: string | null | undefined): string {
    return typeof geometry === "string" && isSupportedGeometry(geometry) ? geometry : DEFAULT_GEOMETRY;
}

export function getGeometryAdapter(geometry = DEFAULT_GEOMETRY): GeometryAdapter {
    return GEOMETRY_ADAPTERS.get(normalizeGeometryKey(geometry)) || squareGeometryAdapter;
}

export function listGeometryAdapters(): GeometryAdapter[] {
    return Array.from(GEOMETRY_ADAPTERS.values());
}
