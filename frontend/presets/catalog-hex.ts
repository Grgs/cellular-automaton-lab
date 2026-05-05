import { buildCenteredBinaryRleSeed, inBounds, uniqueCells } from "./core.js";
import {
    hexCellsAtDistance,
    oddRNeighbors,
    pointyHexCellCenter,
    pointyHexGridCenter,
    pointyHexMaxRadius,
} from "./geometry.js";
import { buildVortexSeed } from "./vortex.js";
import type { CartesianSeedCell } from "../types/domain.js";
import type { CoordinateCell } from "../types/editor.js";
import type { PresetBuildContext, PresetRegistry } from "../types/presets.js";

const HEX_GEOMETRY = "hex";

const HEXLIFE_OSCILLATOR_SAMPLE_RLE = "5bo$6bo$5b4o$4b3ob3o$3b3o4b3o$2b3o7b3obo$4o10b3o$2bo13bo$2b2o12b2o$3bo13bo$3b2o12b2o$4bo13bo$4b2o12b2o$5bo13bo$5b2o4bo2bo4b2o$6bo6bo6bo$6b3o10b4o$6bob3o3bo3b3o$10b3o4b3o$12b3ob3o$14b4o$16bo$17bo!";
const HEXLIFE_NESTED_P9_RLE = "10b2o$9b5o$8b3o2b3o$8b2o5b2o8b2o$9bo6bo7b5o$2b2o5b2o5b2o5b3o2b3o$b5o4bo6bo5b2o5b2o$3o2b3o2b2o5b2o5bo6bo$2o5b2o2b3o2b3o5b2o5b2o$bo6bo4b5o7bo6bo$b2o5b2o5b2o8b2o5b2o$2bo6bo6bo7b5o2b3o$2b2o5b2o4b4o4b3o2b5o$3b3o2b5ob3ob3ob3o5b2o$5b5o2b4o4b4o$7b2o5bo7bo$14b10o$15bo7bo$15b10o3b2o$16bo7bo2b5o$8b2o5b4o4b6o2b3o$7b5o2b3ob3ob3ob2o5b2o$6b3o2b5o4b4o3bo6bo$6b2o5b2o7bo4b2o5b2o$7bo6bo7b2o4bo6bo$7b2o5b2o7bo4b2o5b2o$8bo6bo7b2o4b3o2b3o$8b2o5b2o5b5o4b5o$9b3o2b3o4b3o2b3o4b2o$11b5o5b2o5b2o$13b2o7bo6bo$22b2o5b2o$23bo6bo$23b2o5b2o$24b3o2b3o$26b5o$28b2o!";
const HEXLIFE_ORTHOGONAL_SPACESHIP_RLE = "5b2o$4bo2b2o$3bo$bobo3bo2bo$obo$b4obo5bo$bo3b4o$bo10b2o$bo2bob2o4bo2$5bo$5bo$5bo!";

function centerCell(width: number, height: number): { x: number; y: number } {
    return {
        x: Math.floor((width - 1) / 2),
        y: Math.floor((height - 1) / 2),
    };
}

function buildHexBloomCells(centerX: number, centerY: number): CoordinateCell[] {
    const firstRing = oddRNeighbors(centerX, centerY);
    const east = firstRing[2];
    const southEast = firstRing[3];
    if (!east || !southEast) {
        return firstRing;
    }
    const outerEast = oddRNeighbors(east.x, east.y)[2];
    const outerSouthEast = oddRNeighbors(southEast.x, southEast.y)[3];

    return [
        ...firstRing,
        ...(outerEast ? [outerEast] : []),
        ...(outerSouthEast ? [outerSouthEast] : []),
    ];
}

function buildHexLifeHoneycombBloom(width: number, height: number): CartesianSeedCell[] {
    const center = centerCell(width, height);
    return uniqueCells(
        buildHexBloomCells(center.x, center.y)
            .filter((cell) => inBounds(cell.x, cell.y, width, height))
            .map((cell) => ({ ...cell, state: 1 }))
    );
}

function buildHexLifeRingCurrent(width: number, height: number): CartesianSeedCell[] {
    const center = centerCell(width, height);
    const firstRing = oddRNeighbors(center.x, center.y);
    const secondRing = hexCellsAtDistance(center.x, center.y, 2);
    const eastSecond = secondRing.reduce<CoordinateCell | null>((best, cell) => {
        if (!best || cell.x > best.x || (cell.x === best.x && cell.y < best.y)) {
            return cell;
        }
        return best;
    }, null);
    const thirdRingAccent = eastSecond ? oddRNeighbors(eastSecond.x, eastSecond.y)[2] : null;

    const cells = [
        ...firstRing,
        ...secondRing.filter((_, index) => index % 2 === 0),
        ...(thirdRingAccent ? [thirdRingAccent] : []),
    ];

    return uniqueCells(
        cells
            .filter((cell) => inBounds(cell.x, cell.y, width, height))
            .map((cell) => ({ ...cell, state: 1 }))
    );
}

function buildHexLifeTriBloom(width: number, height: number): CartesianSeedCell[] {
    const center = centerCell(width, height);
    const east = oddRNeighbors(center.x, center.y)[2];
    const west = oddRNeighbors(center.x, center.y)[5];
    if (!east || !west) {
        return [];
    }
    const east2 = oddRNeighbors(east.x, east.y)[2];
    const west2 = oddRNeighbors(west.x, west.y)[5];
    if (!east2 || !west2) {
        return [];
    }

    const cells = [
        ...buildHexBloomCells(center.x, center.y),
        ...buildHexBloomCells(east2.x, east2.y),
        ...buildHexBloomCells(west2.x, west2.y),
    ];

    return uniqueCells(
        cells
            .filter((cell) => inBounds(cell.x, cell.y, width, height))
            .map((cell) => ({ ...cell, state: 1 }))
    );
}

function buildHexLifeOscillatorSample(width: number, height: number): CartesianSeedCell[] {
    return buildCenteredBinaryRleSeed(width, height, HEXLIFE_OSCILLATOR_SAMPLE_RLE);
}

function buildHexLifeNestedP9(width: number, height: number): CartesianSeedCell[] {
    return buildCenteredBinaryRleSeed(width, height, HEXLIFE_NESTED_P9_RLE);
}

function buildHexLifeOrthogonalSpaceship(width: number, height: number): CartesianSeedCell[] {
    return buildCenteredBinaryRleSeed(width, height, HEXLIFE_ORTHOGONAL_SPACESHIP_RLE);
}

export const HEX_PRESET_REGISTRY: PresetRegistry = Object.freeze({
    hexlife: Object.freeze([
        {
            id: "honeycomb-bloom",
            label: "Honeycomb Bloom",
            description: "A centered hex rosette with a slight asymmetry to encourage outward bloom.",
            supportedGeometry: HEX_GEOMETRY,
            minWidth: 9,
            minHeight: 9,
            build: ({ width, height }: PresetBuildContext) => buildHexLifeHoneycombBloom(width, height),
        },
        {
            id: "ring-current",
            label: "Ring Current",
            description: "An alternating double ring that pushes a wave around the first two hex shells.",
            supportedGeometry: HEX_GEOMETRY,
            minWidth: 11,
            minHeight: 9,
            build: ({ width, height }: PresetBuildContext) => buildHexLifeRingCurrent(width, height),
        },
        {
            id: "tri-bloom",
            label: "Tri Bloom",
            description: "Three nearby rosettes that force an immediate asymmetric collision field.",
            supportedGeometry: HEX_GEOMETRY,
            minWidth: 13,
            minHeight: 9,
            build: ({ width, height }: PresetBuildContext) => buildHexLifeTriBloom(width, height),
        },
        {
            id: "oscillator-sample",
            label: "Oscillator Sample",
            description: "A larger B2/S34H oscillator sample that shows structured hex-periodic motion.",
            supportedGeometry: HEX_GEOMETRY,
            minWidth: 23,
            minHeight: 23,
            build: ({ width, height }: PresetBuildContext) => buildHexLifeOscillatorSample(width, height),
        },
        {
            id: "orthogonal-runner",
            label: "Orthogonal Runner",
            description: "A sourced B2/S34H c/6 spaceship sample that travels across the hex lattice.",
            supportedGeometry: HEX_GEOMETRY,
            minWidth: 14,
            minHeight: 13,
            build: ({ width, height }: PresetBuildContext) => buildHexLifeOrthogonalSpaceship(width, height),
        },
        {
            id: "nested-resonator",
            label: "Nested Resonator",
            description: "A larger p9-in-p3 hex oscillator with a dense layered core and outer ring.",
            supportedGeometry: HEX_GEOMETRY,
            minWidth: 37,
            minHeight: 37,
            build: ({ width, height }: PresetBuildContext) => buildHexLifeNestedP9(width, height),
        },
    ]),
    whirlpool: Object.freeze([
        {
            id: "anchored-source-vortex",
            label: "Anchored Source Vortex",
            description: "A compact broken arm with a clockwise source pair near the eye and a short guard crescent.",
            supportedGeometry: HEX_GEOMETRY,
            minWidth: 10,
            minHeight: 10,
            build: ({ width, height }: PresetBuildContext) => buildVortexSeed({
                width,
                height,
                getGridCenter: pointyHexGridCenter,
                getMaxRadius: pointyHexMaxRadius,
                getCellCenter: pointyHexCellCenter,
                arms: [{
                    angleOrigin: -0.54,
                    twist: 1.92,
                    normalizedRadii: [0.24, 0.30, 0.35, 0.41, 0.47],
                    angularOffsets: [-1.02, -0.78, -0.49, -0.18, 0.12, 0.42, 0.74],
                    gapRanges: [[0.0, 0.28]],
                }],
                arcs: [{
                    state: 3,
                    angleOrigin: -0.54,
                    normalizedRadii: [0.18, 0.23, 0.28],
                    angularOffsets: [0.54, 0.80],
                }],
                sources: [
                    { angleOrigin: -0.54, normalizedRadius: 0.22, angularOffset: 0.12 },
                    { angleOrigin: -0.54, normalizedRadius: 0.31, angularOffset: 0.36 },
                ],
            }),
        },
        {
            id: "triple-source-rotor",
            label: "Triple Source Rotor",
            description: "Three sparse source anchors and one broken arm maintain a longer-lived hex rotor.",
            supportedGeometry: HEX_GEOMETRY,
            minWidth: 14,
            minHeight: 12,
            build: ({ width, height }: PresetBuildContext) => buildVortexSeed({
                width,
                height,
                getGridCenter: pointyHexGridCenter,
                getMaxRadius: pointyHexMaxRadius,
                getCellCenter: pointyHexCellCenter,
                arms: [{
                    angleOrigin: -0.44,
                    twist: 1.98,
                    normalizedRadii: [0.24, 0.30, 0.36, 0.42],
                    angularOffsets: [-0.96, -0.67, -0.37, -0.06, 0.26, 0.58],
                    gapRanges: [[0.04, 0.34]],
                }],
                arcs: [{
                    state: 3,
                    angleOrigin: -0.44,
                    normalizedRadii: [0.26, 0.31],
                    angularOffsets: [0.68, 0.94, 1.20],
                }],
                sources: [
                    { angleOrigin: -0.44, normalizedRadius: 0.26, angularOffset: 0.14 },
                    { angleOrigin: 1.72, normalizedRadius: 0.34, angularOffset: 0.0 },
                    { angleOrigin: -2.42, normalizedRadius: 0.42, angularOffset: 0.0 },
                ],
            }),
        },
    ]),
});
