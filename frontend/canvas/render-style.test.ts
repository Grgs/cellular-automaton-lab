import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type { BootstrappedTopologyDefinition } from "../types/domain.js";
import type { PeriodicFaceTilingDescriptor } from "../types/rendering.js";

const ARCHIMEDEAN_488_GEOMETRY = "archimedean-4-8-8";
const ARCHIMEDEAN_31212_GEOMETRY = "archimedean-3-12-12";
const ARCHIMEDEAN_3464_GEOMETRY = "archimedean-3-4-6-4";
const ARCHIMEDEAN_4612_GEOMETRY = "archimedean-4-6-12";
const ARCHIMEDEAN_33434_GEOMETRY = "archimedean-3-3-4-3-4";
const ARCHIMEDEAN_33344_GEOMETRY = "archimedean-3-3-3-4-4";
const ARCHIMEDEAN_33336_GEOMETRY = "archimedean-3-3-3-3-6";
const KAGOME_GEOMETRY = "trihexagonal-3-6-3-6";
const CAIRO_GEOMETRY = "cairo-pentagonal";
const RHOMBILLE_GEOMETRY = "rhombille";
const TETRAKIS_SQUARE_GEOMETRY = "tetrakis-square";
const TRIAKIS_TRIANGULAR_GEOMETRY = "triakis-triangular";
const DELTOIDAL_TRIHEXAGONAL_GEOMETRY = "deltoidal-trihexagonal";
const PRISMATIC_PENTAGONAL_GEOMETRY = "prismatic-pentagonal";
const FLORET_PENTAGONAL_GEOMETRY = "floret-pentagonal";
const SNUB_SQUARE_DUAL_GEOMETRY = "snub-square-dual";
const PERIODIC_GEOMETRIES = [
    ARCHIMEDEAN_488_GEOMETRY,
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    KAGOME_GEOMETRY,
    CAIRO_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    FLORET_PENTAGONAL_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
] as const;

function installRenderStyleTestGlobals(): void {
    installFrontendGlobals();
    const periodicTopologyEntries = PERIODIC_GEOMETRIES.map((geometry, index): BootstrappedTopologyDefinition => ({
        tiling_family: geometry,
        label: geometry,
        picker_group: "Periodic Mixed",
        picker_order: 100 + index,
        sizing_mode: "grid",
        family: "mixed",
        render_kind: "polygon_periodic",
        viewport_sync_mode: "backend-sync",
        supported_adjacency_modes: ["edge"],
        default_adjacency_mode: "edge",
        default_rules: { edge: "life-b2-s23" },
        geometry_keys: { edge: geometry },
        sizing_policy: { control: "cell_size", default: 12, min: 8, max: 20 },
    }));
    window.APP_TOPOLOGIES = [...window.APP_TOPOLOGIES, ...periodicTopologyEntries];
    window.APP_PERIODIC_FACE_TILINGS = PERIODIC_GEOMETRIES.map((geometry): PeriodicFaceTilingDescriptor => ({
        geometry,
        label: geometry,
        metric_model: "pattern",
        base_edge: 52,
        unit_width: 100,
        unit_height: 100,
        min_dimension: 1,
        min_x: 0,
        min_y: 0,
        max_x: 100,
        max_y: 100,
        cell_count_per_unit: 1,
        row_offset_x: 0,
    }));
}

function styleDeclaration(values: Record<string, string>): CSSStyleDeclaration {
    return {
        backgroundColor: values.backgroundColor ?? "",
        getPropertyValue: (name: string) => values[name] ?? "",
    } as CSSStyleDeclaration;
}

describe("canvas/render-style", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
        vi.resetModules();
        installRenderStyleTestGlobals();
    });

    it("uses alternate dead fills for the supported mixed tiling accent shapes", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const deadAltByGeometry = [
            { geometry: ARCHIMEDEAN_488_GEOMETRY, cell: { id: "s:0:0", state: 0, kind: "square" } },
            { geometry: ARCHIMEDEAN_31212_GEOMETRY, cell: { id: "t:0:0", state: 0, kind: "triangle" } },
            { geometry: ARCHIMEDEAN_4612_GEOMETRY, cell: { id: "s:0:0", state: 0, kind: "square" } },
            { geometry: KAGOME_GEOMETRY, cell: { id: "tu:0:0", state: 0, kind: "triangle-up" } },
        ];

        deadAltByGeometry.forEach(({ geometry, cell }) => {
            expect(resolveDeadCellColor(0, { geometry, cell })).toBe("#d5bb8f");
            expect(resolveRenderedCellColor(0, colorLookup, readCanvasColorsForTests(), { geometry, cell })).toBe("#d5bb8f");
        });
    });

    it("keeps unsupported or primary mixed tiling shapes on the default dead fill", async () => {
        const { resolveDeadCellColor } = await import("./render-style.js");
        expect(
            resolveDeadCellColor(0, {
                geometry: ARCHIMEDEAN_31212_GEOMETRY,
                cell: { id: "d:0:0", state: 0, kind: "dodecagon" },
            }),
        ).toBe("#f8f1e5");

        expect(
            resolveDeadCellColor(0, {
                geometry: ARCHIMEDEAN_4612_GEOMETRY,
                cell: { id: "h:0:0", state: 0, kind: "hexagon" },
            }),
        ).toBe("#f8f1e5");

        expect(
            resolveDeadCellColor(0, {
                geometry: ARCHIMEDEAN_4612_GEOMETRY,
                cell: { id: "d:0:0", state: 0, kind: "dodecagon" },
            }),
        ).toBe("#f8f1e5");

        expect(
            resolveDeadCellColor(0, {
                geometry: ARCHIMEDEAN_3464_GEOMETRY,
                cell: { id: "t:0:0", state: 0, kind: "triangle" },
            }),
        ).toBe("#f8f1e5");
    });

    it("uses a warm four-color dead palette for Tuebingen triangles based on kind and chirality", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const cases = [
            {
                cell: {
                    id: "tt:left",
                    state: 0,
                    kind: "tuebingen-thick",
                    tile_family: "tuebingen",
                    chirality_token: "left",
                },
                expectedColor: "#f8f1e5",
            },
            {
                cell: {
                    id: "tt:right",
                    state: 0,
                    kind: "tuebingen-thick",
                    tile_family: "tuebingen",
                    chirality_token: "right",
                },
                expectedColor: "#d5bb8f",
            },
            {
                cell: {
                    id: "tn:left",
                    state: 0,
                    kind: "tuebingen-thin",
                    tile_family: "tuebingen",
                    chirality_token: "left",
                },
                expectedColor: "#efe4d0",
            },
            {
                cell: {
                    id: "tn:right",
                    state: 0,
                    kind: "tuebingen-thin",
                    tile_family: "tuebingen",
                    chirality_token: "right",
                },
                expectedColor: "#e1cdac",
            },
        ];

        cases.forEach(({ cell, expectedColor }) => {
            expect(resolveDeadCellColor(0, { geometry: "tuebingen-triangle", cell })).toBe(expectedColor);
            expect(
                resolveRenderedCellColor(0, colorLookup, readCanvasColorsForTests(), {
                    geometry: "tuebingen-triangle",
                    cell,
                }),
            ).toBe(expectedColor);
        });
    });

    it("uses a warm four-color dead palette for chair tiles based on orientation", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const cases = [
            {
                cell: { id: "chair:o0", state: 0, kind: "chair", orientation_token: "0" },
                expectedColor: "#f8f1e5",
            },
            {
                cell: { id: "chair:o1", state: 0, kind: "chair", orientation_token: "1" },
                expectedColor: "#e5c089",
            },
            {
                cell: { id: "chair:o2", state: 0, kind: "chair", orientation_token: "2" },
                expectedColor: "#c88d4b",
            },
            {
                cell: { id: "chair:o3", state: 0, kind: "chair", orientation_token: "3" },
                expectedColor: "#dbc1b2",
            },
        ];

        cases.forEach(({ cell, expectedColor }) => {
            expect(resolveDeadCellColor(0, { geometry: "chair", cell })).toBe(expectedColor);
            expect(
                resolveRenderedCellColor(0, colorLookup, readCanvasColorsForTests(), {
                    geometry: "chair",
                    cell,
                }),
            ).toBe(expectedColor);
        });
    });

    it("uses differentiated dead-state colors for Robinson thick and thin triangles", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const cases = [
            {
                cell: { id: "rob:thick", state: 0, kind: "robinson-thick", tile_family: "robinson" },
                expectedColor: "#f8f1e5",
            },
            {
                cell: { id: "rob:thin", state: 0, kind: "robinson-thin", tile_family: "robinson" },
                expectedColor: "#d5bb8f",
            },
        ];

        cases.forEach(({ cell, expectedColor }) => {
            expect(resolveDeadCellColor(0, { geometry: "robinson-triangles", cell })).toBe(expectedColor);
            expect(
                resolveRenderedCellColor(0, colorLookup, readCanvasColorsForTests(), {
                    geometry: "robinson-triangles",
                    cell,
                }),
            ).toBe(expectedColor);
        });
    });

    it("uses chirality-based dead-state colors for hat monotiles", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const cases = [
            {
                cell: { id: "hat:left", state: 0, kind: "hat", tile_family: "hat", chirality_token: "left" },
                expectedColor: "#f8f1e5",
            },
            {
                cell: { id: "hat:right", state: 0, kind: "hat", tile_family: "hat", chirality_token: "right" },
                expectedColor: "#c88d4b",
            },
        ];

        cases.forEach(({ cell, expectedColor }) => {
            expect(resolveDeadCellColor(0, { geometry: "hat-monotile", cell })).toBe(expectedColor);
            expect(
                resolveRenderedCellColor(0, colorLookup, readCanvasColorsForTests(), {
                    geometry: "hat-monotile",
                    cell,
                }),
            ).toBe(expectedColor);
        });
    });

    it("uses warm metadata-based dead-state colors for dodecagonal square-triangle tiles", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const cases = [
            {
                cell: {
                    id: "st:square-blue",
                    state: 0,
                    kind: "dodecagonal-square-triangle-square",
                    tile_family: "dodecagonal-square-triangle",
                    chirality_token: "blue",
                },
                expectedColor: "#f8f1e5",
            },
            {
                cell: {
                    id: "st:square-yellow",
                    state: 0,
                    kind: "dodecagonal-square-triangle-square",
                    tile_family: "dodecagonal-square-triangle",
                    chirality_token: "yellow",
                },
                expectedColor: "#d5bb8f",
            },
            {
                cell: {
                    id: "st:triangle-red",
                    state: 0,
                    kind: "dodecagonal-square-triangle-triangle",
                    tile_family: "dodecagonal-square-triangle",
                    chirality_token: "red",
                },
                expectedColor: "#e1cdac",
            },
            {
                cell: {
                    id: "st:triangle-yellow",
                    state: 0,
                    kind: "dodecagonal-square-triangle-triangle",
                    tile_family: "dodecagonal-square-triangle",
                    chirality_token: "yellow",
                },
                expectedColor: "#c88d4b",
            },
        ];

        cases.forEach(({ cell, expectedColor }) => {
            expect(resolveDeadCellColor(0, { geometry: "dodecagonal-square-triangle", cell })).toBe(expectedColor);
            expect(
                resolveRenderedCellColor(0, colorLookup, readCanvasColorsForTests(), {
                    geometry: "dodecagonal-square-triangle",
                    cell,
                }),
            ).toBe(expectedColor);
        });
    });

    it("uses chirality-based dead-state colors for pinwheel triangles", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const cases = [
            {
                cell: {
                    id: "pin:left",
                    state: 0,
                    kind: "pinwheel-triangle",
                    tile_family: "pinwheel",
                    chirality_token: "left",
                },
                expectedColor: "#efe4d0",
            },
            {
                cell: {
                    id: "pin:right",
                    state: 0,
                    kind: "pinwheel-triangle",
                    tile_family: "pinwheel",
                    chirality_token: "right",
                },
                expectedColor: "#d5bb8f",
            },
        ];

        cases.forEach(({ cell, expectedColor }) => {
            expect(resolveDeadCellColor(0, { geometry: "pinwheel", cell })).toBe(expectedColor);
            expect(
                resolveRenderedCellColor(0, colorLookup, readCanvasColorsForTests(), {
                    geometry: "pinwheel",
                    cell,
                }),
            ).toBe(expectedColor);
        });
    });

    it("renders Shield public kinds with distinct dead-state accents", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const cases = [
            {
                cell: {
                    id: "shield:hex",
                    state: 0,
                    kind: "shield-shield",
                    tile_family: "shield",
                },
                expectedColor: "#1f2430",
            },
            {
                cell: {
                    id: "shield:square",
                    state: 0,
                    kind: "shield-square",
                    tile_family: "shield",
                },
                expectedColor: "#f8f1e5",
            },
            {
                cell: {
                    id: "shield:tri",
                    state: 0,
                    kind: "shield-triangle",
                    tile_family: "shield",
                },
                expectedColor: "#bf5a36",
            },
        ];

        cases.forEach(({ cell, expectedColor }) => {
            expect(resolveDeadCellColor(0, { geometry: "shield", cell })).toBe(expectedColor);
            expect(
                resolveRenderedCellColor(0, colorLookup, readCanvasColorsForTests(), {
                    geometry: "shield",
                    cell,
                }),
            ).toBe(expectedColor);
        });
    });

    it("reads canvas line tokens and applies them to the resolved render style", async () => {
        const { readCanvasColors, resolveCanvasRenderStyle } = await import("./render-style.js");
        const canvas = document.createElement("canvas");
        document.body.append(canvas);

        const colors = readCanvasColors(
            canvas,
            (node) => node === document.documentElement
                ? styleDeclaration({
                    "--cell-dead": "#fcfaf4",
                    "--cell-dead-alt": "#d1b57a",
                    "--cell-line-soft": "rgba(31, 36, 48, 0.11)",
                    "--cell-line-strong": "rgba(31, 36, 48, 0.21)",
                    "--cell-line-aperiodic": "rgba(31, 36, 48, 0.24)",
                    "--live": "#131722",
                    "--accent": "#bf5a36",
                    "--accent-dark": "#8a3d20",
                })
                : styleDeclaration({ backgroundColor: "rgba(255, 255, 255, 0.9)" }),
        );

        expect(colors.lineSoft).toBe("rgba(31, 36, 48, 0.11)");
        expect(colors.lineStrong).toBe("rgba(31, 36, 48, 0.21)");
        expect(colors.lineAperiodic).toBe("rgba(31, 36, 48, 0.24)");

        expect(resolveCanvasRenderStyle(6, "square", colors).lineColor).toBe("rgba(31, 36, 48, 0.11)");
        expect(resolveCanvasRenderStyle(12, "square", colors).lineColor).toBe("rgba(31, 36, 48, 0.21)");
        expect(resolveCanvasRenderStyle(12, "penrose-p3-rhombs", colors).aperiodicLineColor).toBe(
            "rgba(31, 36, 48, 0.24)",
        );
        expect(resolveCanvasRenderStyle(12, "square", colors).hoverTintColor).toBe("rgba(31, 36, 48, 0.21)");
        expect(resolveCanvasRenderStyle(12, "square", colors).hoverStrokeColor).toBe("#131722");
        expect(resolveCanvasRenderStyle(12, "square", colors).selectionTintColor).toBe("rgba(191, 90, 54, 0.16)");
        expect(resolveCanvasRenderStyle(12, "square", colors).selectionStrokeColor).toBe("#8a3d20");
        expect(resolveCanvasRenderStyle(12, "square", colors).gesturePaintStrokeColor).toBe("#8a3d20");
        expect(resolveCanvasRenderStyle(12, "square", colors).gestureEraseStrokeColor).toBe(
            "rgba(31, 36, 48, 0.24)",
        );
    });

    it("boosts hover contrast in dark theme while keeping the same token inputs", async () => {
        const { resolveCanvasRenderStyle } = await import("./render-style.js");
        const style = resolveCanvasRenderStyle(12, "square", {
            line: "rgba(231, 237, 248, 0.12)",
            dead: "#f8f1e5",
            deadAlt: "#d5bb8f",
            lineSoft: "rgba(231, 237, 248, 0.07)",
            lineStrong: "rgba(231, 237, 248, 0.14)",
            lineAperiodic: "rgba(7, 11, 17, 0.42)",
            live: "#f2f5ff",
            accent: "#d67a4c",
            accentStrong: "#f1a275",
        });

        expect(style.hoverTintColor).toBe("rgba(7, 11, 17, 0.18)");
        expect(style.hoverStrokeColor).toBe("rgba(7, 11, 17, 0.9)");
        expect(style.selectionTintColor).toBe("rgba(214, 122, 76, 0.18)");
        expect(style.selectionStrokeColor).toBe("#f1a275");
        expect(style.gesturePaintStrokeColor).toBe("#f1a275");
        expect(style.gestureEraseStrokeColor).toBe("rgba(7, 11, 17, 0.42)");
    });
});

function readCanvasColorsForTests() {
    return {
        line: "rgba(31, 36, 48, 0.16)",
        dead: "#f8f1e5",
        deadAlt: "#d5bb8f",
        lineSoft: "rgba(31, 36, 48, 0.10)",
        lineStrong: "rgba(31, 36, 48, 0.20)",
        lineAperiodic: "rgba(31, 36, 48, 0.24)",
        live: "#1f2430",
        accent: "#bf5a36",
        accentStrong: "#8a3d20",
    };
}
