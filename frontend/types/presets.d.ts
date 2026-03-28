import type { CartesianSeedCell, PresetBuildContext, PresetMetadata } from "./domain.js";

export type { PresetBuildContext } from "./domain.js";

export interface PresetDefinition extends PresetMetadata {
    supportedGeometry: string;
    minWidth: number;
    minHeight: number;
    build(context: PresetBuildContext): CartesianSeedCell[];
}

export type PresetRegistry = Readonly<Record<string, readonly PresetDefinition[]>>;

export interface PolarSourceSpec {
    normalizedRadius: number;
    angleOrigin?: number;
    angularOffset?: number;
    state?: number;
}

export interface PolarArcSpec {
    normalizedRadii?: readonly number[];
    angularOffsets?: readonly number[];
    angleOrigin?: number;
    state?: number;
}

export interface PolarArmSpec {
    normalizedRadii?: readonly number[];
    angularOffsets?: readonly number[];
    angleOrigin?: number;
    twist?: number;
    gapRanges?: ReadonlyArray<readonly [number, number]>;
}

export interface VortexSeedOptions {
    width: number;
    height: number;
    getGridCenter: (width: number, height: number) => { x: number; y: number };
    getMaxRadius: (width: number, height: number) => number;
    getCellCenter: (x: number, y: number) => { x: number; y: number };
    arms: readonly PolarArmSpec[];
    sources?: readonly PolarSourceSpec[];
    arcs?: readonly PolarArcSpec[];
    trailingPhaseCutoff?: number;
    refractoryPhaseCutoff?: number;
}
