import type { PeriodicFaceTilingDescriptor } from "../types/rendering.js";

function normalizeDescriptor(descriptor: Record<string, unknown>): PeriodicFaceTilingDescriptor {
    return Object.freeze({
        geometry: String(descriptor.geometry ?? ""),
        label: String(descriptor.label ?? descriptor.geometry ?? ""),
        metric_model: String(descriptor.metric_model ?? "pattern"),
        base_edge: Number(descriptor.base_edge) || 52,
        unit_width: Number(descriptor.unit_width) || 0,
        unit_height: Number(descriptor.unit_height) || 0,
        min_dimension: Number.isFinite(Number(descriptor.min_dimension))
            ? Number(descriptor.min_dimension)
            : 1,
        min_x: Number(descriptor.min_x) || 0,
        min_y: Number(descriptor.min_y) || 0,
        max_x: Number(descriptor.max_x) || 0,
        max_y: Number(descriptor.max_y) || 0,
        cell_count_per_unit: Number(descriptor.cell_count_per_unit) || 0,
        row_offset_x: Number(descriptor.row_offset_x) || 0,
    });
}

function bootstrappedPeriodicFaceTilings(): readonly PeriodicFaceTilingDescriptor[] {
    const bootstrapped = window.APP_PERIODIC_FACE_TILINGS;
    if (!Array.isArray(bootstrapped) || bootstrapped.length === 0) {
        throw new Error("Missing bootstrapped periodic-face descriptor catalog.");
    }

    return Object.freeze(
        bootstrapped
            .filter(
                (descriptor): descriptor is Record<string, unknown> => (
                    Boolean(descriptor)
                    && typeof descriptor === "object"
                    && "geometry" in descriptor
                ),
            )
            .map((descriptor) => normalizeDescriptor(descriptor)),
    );
}

export const PERIODIC_FACE_TILINGS = bootstrappedPeriodicFaceTilings();

const PERIODIC_FACE_TILING_BY_GEOMETRY = new Map(
    PERIODIC_FACE_TILINGS.map((descriptor) => [descriptor.geometry, descriptor]),
);

export function getPeriodicFaceTilingDescriptor(geometry: string): PeriodicFaceTilingDescriptor | null {
    return PERIODIC_FACE_TILING_BY_GEOMETRY.get(geometry) ?? null;
}

export function isPeriodicFaceTilingGeometry(geometry: string): boolean {
    return PERIODIC_FACE_TILING_BY_GEOMETRY.has(geometry);
}
