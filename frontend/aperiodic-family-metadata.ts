export const PENROSE_GEOMETRY = "penrose-p3-rhombs";
export const PENROSE_VERTEX_GEOMETRY = "penrose-p3-rhombs-vertex";
export const PENROSE_P2_GEOMETRY = "penrose-p2-kite-dart";
export const AMMANN_BEENKER_GEOMETRY = "ammann-beenker";
export const SPECTRE_GEOMETRY = "spectre";
export const TAYLOR_SOCOLAR_GEOMETRY = "taylor-socolar";
export const SPHINX_GEOMETRY = "sphinx";
export const HAT_MONOTILE_GEOMETRY = "hat-monotile";
export const CHAIR_GEOMETRY = "chair";
export const ROBINSON_TRIANGLES_GEOMETRY = "robinson-triangles";
export const TUEBINGEN_TRIANGLE_GEOMETRY = "tuebingen-triangle";
export const DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY = "dodecagonal-square-triangle";
export const SHIELD_GEOMETRY = "shield";
export const PINWHEEL_GEOMETRY = "pinwheel";

export const THICK_RHOMB_KIND = "thick-rhomb";
export const THIN_RHOMB_KIND = "thin-rhomb";
export const KITE_KIND = "kite";
export const DART_KIND = "dart";
export const AMMANN_RHOMB_KIND = "rhomb";
export const AMMANN_SQUARE_KIND = "square";
export const SPECTRE_KIND = "spectre";
export const TAYLOR_HALF_HEX_KIND = "taylor-half-hex";
export const SPHINX_KIND = "sphinx";
export const HAT_KIND = "hat";
export const HAT_TILE_FAMILY = "hat";
export const CHAIR_KIND = "chair";
export const ROBINSON_THICK_KIND = "robinson-thick";
export const ROBINSON_THIN_KIND = "robinson-thin";
export const ROBINSON_TILE_FAMILY = "robinson";
export const TUEBINGEN_THICK_KIND = "tuebingen-thick";
export const TUEBINGEN_THIN_KIND = "tuebingen-thin";
export const TUEBINGEN_TILE_FAMILY = "tuebingen";
export const DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND = "dodecagonal-square-triangle-square";
export const DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND = "dodecagonal-square-triangle-triangle";
export const DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY = DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY;
export const SHIELD_SHIELD_KIND = "shield-shield";
export const SHIELD_SQUARE_KIND = "shield-square";
export const SHIELD_TRIANGLE_KIND = "shield-triangle";
export const SHIELD_TILE_FAMILY = "shield";
export const PINWHEEL_TRIANGLE_KIND = "pinwheel-triangle";
export const PINWHEEL_TILE_FAMILY = "pinwheel";

type AperiodicFamilyMetadata = Readonly<{
    label: string;
    experimental: boolean;
    publicCellKinds: readonly string[];
}>;

export const APERIODIC_FAMILY_METADATA = Object.freeze({
    "penrose-p3-rhombs": {
        label: "Penrose P3 Rhombs",
        experimental: false,
        publicCellKinds: ["thick-rhomb", "thin-rhomb"],
    },
    "penrose-p2-kite-dart": {
        label: "Penrose P2 Kite-Dart",
        experimental: false,
        publicCellKinds: ["kite", "dart"],
    },
    "ammann-beenker": {
        label: "Ammann-Beenker",
        experimental: false,
        publicCellKinds: ["rhomb", "square"],
    },
    "spectre": {
        label: "Spectre",
        experimental: false,
        publicCellKinds: ["spectre"],
    },
    "hat-monotile": {
        label: "Hat",
        experimental: false,
        publicCellKinds: ["hat"],
    },
    "taylor-socolar": {
        label: "Taylor-Socolar",
        experimental: false,
        publicCellKinds: ["taylor-half-hex"],
    },
    "sphinx": {
        label: "Sphinx",
        experimental: false,
        publicCellKinds: ["sphinx"],
    },
    "chair": {
        label: "Chair",
        experimental: false,
        publicCellKinds: ["chair"],
    },
    "robinson-triangles": {
        label: "Robinson Triangles",
        experimental: false,
        publicCellKinds: ["robinson-thick", "robinson-thin"],
    },
    "tuebingen-triangle": {
        label: "Tuebingen Triangle",
        experimental: false,
        publicCellKinds: ["tuebingen-thick", "tuebingen-thin"],
    },
    "dodecagonal-square-triangle": {
        label: "Dodecagonal Square-Triangle",
        experimental: true,
        publicCellKinds: [
            "dodecagonal-square-triangle-square",
            "dodecagonal-square-triangle-triangle",
        ],
    },
    "shield": {
        label: "Shield",
        experimental: true,
        publicCellKinds: ["shield-shield", "shield-square", "shield-triangle"],
    },
    "pinwheel": {
        label: "Pinwheel",
        experimental: true,
        publicCellKinds: ["pinwheel-triangle"],
    },
} as const satisfies Record<string, AperiodicFamilyMetadata>);
