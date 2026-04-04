import type { CartesianSeedCell } from "../types/domain.js";
import type { PolarArcSpec, PolarSourceSpec, VortexSeedOptions } from "../types/presets.js";

const DEFAULT_VORTEX_RADII = Object.freeze([0.22, 0.27, 0.33, 0.39, 0.46, 0.53]);
const DEFAULT_VORTEX_ANGLES = Object.freeze([-0.98, -0.78, -0.52, -0.24, 0.08, 0.34, 0.63, 0.92]);
const SOURCE_STATE = 4;
const REFRACTORY_STATE = 3;

function wrapAngle(angle: number): number {
    let wrappedAngle = angle;
    while (wrappedAngle <= -Math.PI) {
        wrappedAngle += 2 * Math.PI;
    }
    while (wrappedAngle > Math.PI) {
        wrappedAngle -= 2 * Math.PI;
    }
    return wrappedAngle;
}

function findNearestUntakenCell(
    width: number,
    height: number,
    getCellCenter: VortexSeedOptions["getCellCenter"],
    takenCells: Set<string>,
    targetX: number,
    targetY: number,
): { x: number; y: number; center: { x: number; y: number }; distanceSquared: number } | null {
    let nearestCell: { x: number; y: number; center: { x: number; y: number }; distanceSquared: number } | null = null;

    for (let y = 0; y < height; y += 1) {
        for (let x = 0; x < width; x += 1) {
            const key = `${x}:${y}`;
            if (takenCells.has(key)) {
                continue;
            }

            const center = getCellCenter(x, y);
            const distanceSquared = ((center.x - targetX) ** 2) + ((center.y - targetY) ** 2);
            if (!nearestCell || distanceSquared < nearestCell.distanceSquared) {
                nearestCell = { x, y, center, distanceSquared };
            }
        }
    }

    return nearestCell;
}

function offsetIsInsideAnyRange(offset: number, ranges: ReadonlyArray<readonly [number, number]> = []): boolean {
    return ranges.some(([minOffset, maxOffset]) => offset >= minOffset && offset <= maxOffset);
}

function resolvedAngleOrigin(spec: { angleOrigin?: number }, fallback = -0.58): number {
    return spec.angleOrigin ?? fallback;
}

function placePolarSample({
    width,
    height,
    gridCenter,
    maxRadius,
    getCellCenter,
    takenCells,
    normalizedRadius,
    angleOrigin = 0,
    angularOffset = 0,
    state,
}: {
    width: number;
    height: number;
    gridCenter: { x: number; y: number };
    maxRadius: number;
    getCellCenter: VortexSeedOptions["getCellCenter"];
    takenCells: Set<string>;
    normalizedRadius: number;
    angleOrigin?: number;
    angularOffset?: number;
    state: number;
}): CartesianSeedCell | null {
    const angle = angleOrigin + angularOffset;
    const targetX = gridCenter.x + (Math.cos(angle) * maxRadius * normalizedRadius);
    const targetY = gridCenter.y + (Math.sin(angle) * maxRadius * normalizedRadius);
    const nearestCell = findNearestUntakenCell(
        width,
        height,
        getCellCenter,
        takenCells,
        targetX,
        targetY,
    );

    if (!nearestCell) {
        return null;
    }

    takenCells.add(`${nearestCell.x}:${nearestCell.y}`);
    return { x: nearestCell.x, y: nearestCell.y, state };
}

function placePolarArc({
    width,
    height,
    gridCenter,
    maxRadius,
    getCellCenter,
    takenCells,
    arc,
    defaultState = REFRACTORY_STATE,
}: {
    width: number;
    height: number;
    gridCenter: { x: number; y: number };
    maxRadius: number;
    getCellCenter: VortexSeedOptions["getCellCenter"];
    takenCells: Set<string>;
    arc: PolarArcSpec;
    defaultState?: number;
}): CartesianSeedCell[] {
    const cells: CartesianSeedCell[] = [];
    const radialSamples = arc.normalizedRadii ?? [];
    const angularOffsets = arc.angularOffsets ?? [];
    const angleOrigin = resolvedAngleOrigin(arc, 0);

    radialSamples.forEach((normalizedRadius) => {
        angularOffsets.forEach((angularOffset) => {
            const cell = placePolarSample({
                width,
                height,
                gridCenter,
                maxRadius,
                getCellCenter,
                takenCells,
                normalizedRadius,
                angleOrigin,
                angularOffset,
                state: arc.state ?? defaultState,
            });
            if (cell) {
                cells.push(cell);
            }
        });
    });

    return cells;
}

export function buildVortexSeed({
    width,
    height,
    getGridCenter,
    getMaxRadius,
    getCellCenter,
    arms,
    sources = [],
    arcs = [],
    trailingPhaseCutoff = 0.0,
    refractoryPhaseCutoff = -0.32,
}: VortexSeedOptions): CartesianSeedCell[] {
    const gridCenter = getGridCenter(width, height);
    const maxRadius = getMaxRadius(width, height);
    const cells: CartesianSeedCell[] = [];
    const takenCells = new Set<string>();

    arms.forEach((arm) => {
        const radialSamples = arm.normalizedRadii ?? DEFAULT_VORTEX_RADII;
        const angularOffsets = (arm.angularOffsets ?? DEFAULT_VORTEX_ANGLES)
            .filter((angularOffset) => !offsetIsInsideAnyRange(angularOffset, arm.gapRanges ?? []));
        const angleOrigin = resolvedAngleOrigin(arm);
        const twist = arm.twist ?? 1.6;

        radialSamples.forEach((normalizedRadius) => {
            angularOffsets.forEach((angularOffset) => {
                const angle = angleOrigin + angularOffset;
                const targetX = gridCenter.x + (Math.cos(angle) * maxRadius * normalizedRadius);
                const targetY = gridCenter.y + (Math.sin(angle) * maxRadius * normalizedRadius);
                const nearestCell = findNearestUntakenCell(
                    width,
                    height,
                    getCellCenter,
                    takenCells,
                    targetX,
                    targetY,
                );

                if (!nearestCell) {
                    return;
                }

                const key = `${nearestCell.x}:${nearestCell.y}`;
                takenCells.add(key);

                const dx = nearestCell.center.x - gridCenter.x;
                const dy = nearestCell.center.y - gridCenter.y;
                const actualAngle = Math.atan2(dy, dx);
                const actualRadius = Math.hypot(dx, dy) / maxRadius;
                const phase = wrapAngle(actualAngle - angleOrigin) + (twist * actualRadius);

                let state = 1;
                if (phase < refractoryPhaseCutoff) {
                    state = 3;
                } else if (phase < trailingPhaseCutoff) {
                    state = 2;
                }

                cells.push({ x: nearestCell.x, y: nearestCell.y, state });
            });
        });
    });

    arcs.forEach((arc) => {
        cells.push(...placePolarArc({
            width,
            height,
            gridCenter,
            maxRadius,
            getCellCenter,
            takenCells,
            arc,
        }));
    });

    sources.forEach((source) => {
        const cell = placePolarSample({
            width,
            height,
            gridCenter,
            maxRadius,
            getCellCenter,
            takenCells,
            normalizedRadius: source.normalizedRadius,
            angleOrigin: resolvedAngleOrigin(source, 0),
            angularOffset: source.angularOffset ?? 0,
            state: source.state ?? SOURCE_STATE,
        });
        if (cell) {
            cells.push(cell);
        }
    });

    return cells;
}
