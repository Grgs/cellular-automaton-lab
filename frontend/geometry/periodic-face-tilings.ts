import type { PeriodicFaceTilingDescriptor } from "../types/rendering.js";

function normalizeDescriptor(
    descriptor: PeriodicFaceTilingDescriptor,
): PeriodicFaceTilingDescriptor {
    return Object.freeze({
        geometry: descriptor.geometry,
        label: descriptor.label,
        metric_model: descriptor.metric_model,
        base_edge: descriptor.base_edge,
        unit_width: descriptor.unit_width,
        unit_height: descriptor.unit_height,
        min_dimension: descriptor.min_dimension,
        min_x: descriptor.min_x,
        min_y: descriptor.min_y,
        max_x: descriptor.max_x,
        max_y: descriptor.max_y,
        cell_count_per_unit: descriptor.cell_count_per_unit,
        row_offset_x: descriptor.row_offset_x,
    });
}

function bootstrappedPeriodicFaceTilings(): readonly PeriodicFaceTilingDescriptor[] {
    const bootstrapped = window.APP_PERIODIC_FACE_TILINGS;
    if (bootstrapped.length === 0) {
        throw new Error("Missing bootstrapped periodic-face descriptor catalog.");
    }

    return Object.freeze(bootstrapped.map((descriptor) => normalizeDescriptor(descriptor)));
}

export const PERIODIC_FACE_TILINGS = bootstrappedPeriodicFaceTilings();

const PERIODIC_FACE_TILING_BY_GEOMETRY = new Map(
    PERIODIC_FACE_TILINGS.map((descriptor) => [descriptor.geometry, descriptor]),
);

export function getPeriodicFaceTilingDescriptor(
    geometry: string,
): PeriodicFaceTilingDescriptor | null {
    return PERIODIC_FACE_TILING_BY_GEOMETRY.get(geometry) ?? null;
}

export function isPeriodicFaceTilingGeometry(geometry: string): boolean {
    return PERIODIC_FACE_TILING_BY_GEOMETRY.has(geometry);
}
