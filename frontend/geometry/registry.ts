import {
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_488_GEOMETRY,
    CAIRO_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    FLORET_PENTAGONAL_GEOMETRY,
    KAGOME_GEOMETRY,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
    AMMANN_BEENKER_GEOMETRY,
} from "../topology.js";
import { DEFAULT_GEOMETRY } from "./shared.js";
import { createAperiodicPrototileGeometryAdapter } from "./aperiodic-prototile-adapter.js";
import { hexGeometryAdapter } from "./hex-adapter.js";
import { createPeriodicMixedGeometryAdapter } from "./periodic-mixed-adapter.js";
import { squareGeometryAdapter } from "./square-adapter.js";
import { triangleGeometryAdapter } from "./triangle-adapter.js";
import type { GeometryAdapter } from "../types/rendering.js";

const periodicMixedGeometryAdapters: GeometryAdapter[] = [
    createPeriodicMixedGeometryAdapter(ARCHIMEDEAN_488_GEOMETRY),
    createPeriodicMixedGeometryAdapter(ARCHIMEDEAN_31212_GEOMETRY),
    createPeriodicMixedGeometryAdapter(ARCHIMEDEAN_3464_GEOMETRY),
    createPeriodicMixedGeometryAdapter(ARCHIMEDEAN_4612_GEOMETRY),
    createPeriodicMixedGeometryAdapter(ARCHIMEDEAN_33434_GEOMETRY),
    createPeriodicMixedGeometryAdapter(ARCHIMEDEAN_33344_GEOMETRY),
    createPeriodicMixedGeometryAdapter(ARCHIMEDEAN_33336_GEOMETRY),
    createPeriodicMixedGeometryAdapter(KAGOME_GEOMETRY),
    createPeriodicMixedGeometryAdapter(CAIRO_GEOMETRY),
    createPeriodicMixedGeometryAdapter(RHOMBILLE_GEOMETRY),
    createPeriodicMixedGeometryAdapter(DELTOIDAL_TRIHEXAGONAL_GEOMETRY),
    createPeriodicMixedGeometryAdapter(TETRAKIS_SQUARE_GEOMETRY),
    createPeriodicMixedGeometryAdapter(TRIAKIS_TRIANGULAR_GEOMETRY),
    createPeriodicMixedGeometryAdapter(PRISMATIC_PENTAGONAL_GEOMETRY),
    createPeriodicMixedGeometryAdapter(FLORET_PENTAGONAL_GEOMETRY),
    createPeriodicMixedGeometryAdapter(SNUB_SQUARE_DUAL_GEOMETRY),
];

const aperiodicGeometryAdapters: GeometryAdapter[] = [
    createAperiodicPrototileGeometryAdapter(PENROSE_GEOMETRY),
    createAperiodicPrototileGeometryAdapter(PENROSE_VERTEX_GEOMETRY),
    createAperiodicPrototileGeometryAdapter(PENROSE_P2_GEOMETRY),
    createAperiodicPrototileGeometryAdapter(AMMANN_BEENKER_GEOMETRY),
];

const GEOMETRY_ADAPTER_ENTRIES: Array<[string, GeometryAdapter]> = [
    [DEFAULT_GEOMETRY, squareGeometryAdapter],
    ["hex", hexGeometryAdapter],
    ["triangle", triangleGeometryAdapter],
    ...periodicMixedGeometryAdapters.map((adapter): [string, GeometryAdapter] => [adapter.geometry, adapter]),
    ...aperiodicGeometryAdapters.map((adapter): [string, GeometryAdapter] => [adapter.geometry, adapter]),
];

const GEOMETRY_ADAPTERS = new Map<string, GeometryAdapter>(GEOMETRY_ADAPTER_ENTRIES);

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
