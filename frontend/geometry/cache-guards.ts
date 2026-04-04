import type {
    GeometryCache,
    HexGeometryCache,
    PolygonGeometryCache,
    TriangleGeometryCache,
} from "../types/rendering.js";

export function asHexGeometryCache(cache: GeometryCache | null | undefined): HexGeometryCache | null {
    return cache !== null
        && cache !== undefined
        && cache.type === "hex"
        && Array.isArray(cache.cells)
        && !("strokePath" in cache)
        ? cache
        : null;
}

export function asTriangleGeometryCache(cache: GeometryCache | null | undefined): TriangleGeometryCache | null {
    return cache !== null
        && cache !== undefined
        && cache.type === "triangle"
        && Array.isArray(cache.cells)
        && "strokePath" in cache
        && !("cellsById" in cache)
        ? cache
        : null;
}

export function isPolygonGeometryCache(cache: GeometryCache | null | undefined): cache is PolygonGeometryCache {
    return cache !== null
        && cache !== undefined
        && "cellsById" in cache
        && "strokePath" in cache;
}

export function asPolygonGeometryCache(cache: GeometryCache | null | undefined): PolygonGeometryCache | null {
    return isPolygonGeometryCache(cache) ? cache : null;
}
