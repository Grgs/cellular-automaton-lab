import { buildCenteredAsciiSeed, buildCenteredBinaryRleSeed } from "./core.js";
import { squareCellCenter, squareGridCenter, squareMaxRadius } from "./geometry.js";
import { buildVortexSeed } from "./vortex.js";
import { buildWireworldDiodeDemo, buildWireworldSignalLoop } from "./wireworld.js";
import type { PresetBuildContext, PresetRegistry } from "../types/presets.js";

const SQUARE_GEOMETRY = "square";

const HIGHLIFE_REPLICATOR_ROWS = Object.freeze([
    ".OO",
    ".O.",
    "O..",
    "O..",
    "OOO",
]);

const HIGHLIFE_REPLICATOR_PREDECESSOR_RLE = "b3o$o$o$o!";
const HIGHLIFE_REPLICATOR_OSCILLATOR_RLE = "2o33b$2o10bo22b$11b2o22b$10bobo22b$9b3o23b$35b$15b3o17b$14bobo18b$14b2o19b$14bo20b$35b$35b$35b$35b$35b$35b$35b$33b2o$33b2o!";
const HIGHLIFE_BOMBER_PREDECESSOR_RLE = "b3o6b$o9b$o9b$o8bo$9bo$9bo!";

function buildHighlifeReplicator(width: number, height: number) {
    return buildCenteredAsciiSeed(width, height, HIGHLIFE_REPLICATOR_ROWS, { O: 1 });
}

function buildHighlifeReplicatorPredecessor(width: number, height: number) {
    return buildCenteredBinaryRleSeed(width, height, HIGHLIFE_REPLICATOR_PREDECESSOR_RLE);
}

function buildHighlifeReplicatorOscillator(width: number, height: number) {
    return buildCenteredBinaryRleSeed(width, height, HIGHLIFE_REPLICATOR_OSCILLATOR_RLE);
}

function buildHighlifeBomberPredecessor(width: number, height: number) {
    return buildCenteredBinaryRleSeed(width, height, HIGHLIFE_BOMBER_PREDECESSOR_RLE);
}

export const SQUARE_PRESET_REGISTRY: PresetRegistry = Object.freeze({
    conway: Object.freeze([
        {
            id: "r-pentomino",
            label: "R-pentomino",
            description: "A tiny classic seed with long, chaotic growth.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 5,
            minHeight: 5,
            build: ({ width, height }: PresetBuildContext) => buildCenteredAsciiSeed(width, height, [
                ".OO",
                "OO.",
                ".O.",
            ], {
                O: 1,
            }),
        },
    ]),
    highlife: Object.freeze([
        {
            id: "replicator",
            label: "Replicator",
            description: "The canonical HighLife seed that self-copies over time.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 7,
            minHeight: 7,
            build: ({ width, height }: PresetBuildContext) => buildHighlifeReplicator(width, height),
        },
        {
            id: "replicator-predecessor",
            label: "Replicator Predecessor",
            description: "A tiny four-row seed that quickly blossoms into the classic replicator family.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 5,
            minHeight: 5,
            build: ({ width, height }: PresetBuildContext) => buildHighlifeReplicatorPredecessor(width, height),
        },
        {
            id: "replicator-oscillator",
            label: "Replicator Oscillator",
            description: "A large period-96 HighLife oscillator built from interacting replicator fronts.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 35,
            minHeight: 19,
            build: ({ width, height }: PresetBuildContext) => buildHighlifeReplicatorOscillator(width, height),
        },
        {
            id: "bomber-predecessor",
            label: "Bomber Predecessor",
            description: "A small replicator-and-blinker precursor that turns into HighLife's classic bomber spaceship.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 10,
            minHeight: 6,
            build: ({ width, height }: PresetBuildContext) => buildHighlifeBomberPredecessor(width, height),
        },
    ]),
    wireworld: Object.freeze([
        {
            id: "signal-loop",
            label: "Signal Loop",
            description: "A broad conductor loop with a live pulse already in motion.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 12,
            minHeight: 9,
            build: ({ width, height }: PresetBuildContext) => buildWireworldSignalLoop(width, height),
        },
        {
            id: "diode-demo",
            label: "Diode Demo",
            description: "A larger directional gate seeded with an incoming pulse.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 15,
            minHeight: 11,
            build: ({ width, height }: PresetBuildContext) => buildWireworldDiodeDemo(width, height),
        },
    ]),
    whirlpool: Object.freeze([
        {
            id: "anchored-source-vortex",
            label: "Anchored Source Vortex",
            description: "A broken clockwise arm fed by two sources and pinned by a short refractory crescent.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 12,
            minHeight: 12,
            build: ({ width, height }: PresetBuildContext) => buildVortexSeed({
                width,
                height,
                getGridCenter: squareGridCenter,
                getMaxRadius: squareMaxRadius,
                getCellCenter: squareCellCenter,
                arms: [{
                    angleOrigin: -0.64,
                    twist: 1.58,
                    normalizedRadii: [0.20, 0.26, 0.32, 0.39, 0.46, 0.53],
                    angularOffsets: [-1.08, -0.82, -0.55, -0.28, -0.02, 0.22, 0.49, 0.78],
                    gapRanges: [[0.0, 0.34]],
                }],
                arcs: [{
                    state: 3,
                    angleOrigin: -0.64,
                    normalizedRadii: [0.22, 0.26, 0.30],
                    angularOffsets: [0.52, 0.76, 0.98],
                }],
                sources: [
                    { angleOrigin: -0.64, normalizedRadius: 0.28, angularOffset: 0.14 },
                    { angleOrigin: -0.64, normalizedRadius: 0.52, angularOffset: 0.62 },
                ],
            }),
        },
        {
            id: "dual-source-vortex",
            label: "Dual Source Vortex",
            description: "Two offset source anchors feed a dominant clockwise arm with a wider outer curl.",
            supportedGeometry: SQUARE_GEOMETRY,
            minWidth: 16,
            minHeight: 16,
            build: ({ width, height }: PresetBuildContext) => buildVortexSeed({
                width,
                height,
                getGridCenter: squareGridCenter,
                getMaxRadius: squareMaxRadius,
                getCellCenter: squareCellCenter,
                arms: [
                    {
                        angleOrigin: -0.58,
                        twist: 1.54,
                        normalizedRadii: [0.20, 0.27, 0.34, 0.41, 0.49, 0.57],
                        angularOffsets: [-1.06, -0.78, -0.50, -0.22, 0.04, 0.31, 0.59, 0.88],
                        gapRanges: [[0.08, 0.42]],
                    },
                ],
                arcs: [{
                    state: 3,
                    angleOrigin: -0.58,
                    normalizedRadii: [0.24, 0.29],
                    angularOffsets: [0.56, 0.82, 1.05],
                }],
                sources: [
                    { angleOrigin: -0.58, normalizedRadius: 0.31, angularOffset: 0.08 },
                    { angleOrigin: 1.68, normalizedRadius: 0.43, angularOffset: 0.0 },
                ],
            }),
        },
    ]),
});
