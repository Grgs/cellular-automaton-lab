/**
 * One policy for every wall entry point that can add a tiling.
 *
 * Six is the backend's payload/compute ceiling. Narrow screens and very small
 * devices use a lower ceiling so newly added boards remain legible and the
 * browser is not asked to render a six-board wall it is unlikely to handle
 * comfortably. Existing boards are never removed after a resize; the current
 * capacity only gates subsequent additions.
 */
export const WALL_HARD_TILING_LIMIT = 6;

/**
 * Fewest tilings a live wall can hold. A comparison needs at least two boards to
 * mean anything, so the wall refuses to drop below this floor -- both the play
 * gate and the per-board remove control enforce it.
 */
export const MIN_WALL_TILINGS = 2;

export interface WallCapacityEnvironment {
    viewportWidth?: number;
    hardwareConcurrency?: number;
}

export function wallTilingCapacity(environment: WallCapacityEnvironment = {}): number {
    const viewportWidth = environment.viewportWidth ?? globalThis.innerWidth ?? 1024;
    const hardwareConcurrency =
        environment.hardwareConcurrency ?? globalThis.navigator?.hardwareConcurrency ?? 4;
    const layoutLimit = viewportWidth <= 640 ? 4 : WALL_HARD_TILING_LIMIT;
    const computeLimit = hardwareConcurrency <= 2 ? 4 : WALL_HARD_TILING_LIMIT;
    return Math.min(WALL_HARD_TILING_LIMIT, layoutLimit, computeLimit);
}

export function wallCapacityMessage(limit: number): string {
    if (limit === WALL_HARD_TILING_LIMIT) {
        return `The wall supports up to ${limit} tilings at once.`;
    }
    return `This screen or device supports up to ${limit} tilings at once (maximum ${WALL_HARD_TILING_LIMIT}).`;
}
