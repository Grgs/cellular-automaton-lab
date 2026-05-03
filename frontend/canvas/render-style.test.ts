import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";

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
const DELTOIDAL_HEXAGONAL_GEOMETRY = "deltoidal-hexagonal";
const TETRAKIS_SQUARE_GEOMETRY = "tetrakis-square";
const TRIAKIS_TRIANGULAR_GEOMETRY = "triakis-triangular";
const DELTOIDAL_TRIHEXAGONAL_GEOMETRY = "deltoidal-trihexagonal";
const PRISMATIC_PENTAGONAL_GEOMETRY = "prismatic-pentagonal";
const FLORET_PENTAGONAL_GEOMETRY = "floret-pentagonal";
const SNUB_SQUARE_DUAL_GEOMETRY = "snub-square-dual";

function installRenderStyleTestGlobals(): void {
    installFrontendGlobals();
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

    it("applies tone-driven dead fills to the Archimedean prototile kinds", async () => {
        // Each Archimedean family registers its prototile kinds in the
        // family-dead palette manifest. Primary kinds use cream (the family
        // base), the second kind uses tan, and three-kind families add clay
        // for the smallest shape. Kagome stays on the legacy deadAlt fallback
        // because its triangle-up/triangle-down kinds aren't yet in the
        // manifest's selector vocabulary.
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const colors = readCanvasColorsForTests();
        const expectations = [
            { geometry: ARCHIMEDEAN_488_GEOMETRY, kind: "octagon", expected: colors.toneCream },
            { geometry: ARCHIMEDEAN_488_GEOMETRY, kind: "square", expected: colors.toneTan },
            { geometry: ARCHIMEDEAN_31212_GEOMETRY, kind: "dodecagon", expected: colors.toneCream },
            { geometry: ARCHIMEDEAN_31212_GEOMETRY, kind: "triangle", expected: colors.toneTan },
            { geometry: ARCHIMEDEAN_3464_GEOMETRY, kind: "hexagon", expected: colors.toneCream },
            { geometry: ARCHIMEDEAN_3464_GEOMETRY, kind: "square", expected: colors.toneTan },
            { geometry: ARCHIMEDEAN_3464_GEOMETRY, kind: "triangle", expected: colors.toneClay },
            { geometry: ARCHIMEDEAN_4612_GEOMETRY, kind: "dodecagon", expected: colors.toneCream },
            { geometry: ARCHIMEDEAN_4612_GEOMETRY, kind: "hexagon", expected: colors.toneTan },
            { geometry: ARCHIMEDEAN_4612_GEOMETRY, kind: "square", expected: colors.toneClay },
            { geometry: ARCHIMEDEAN_33434_GEOMETRY, kind: "square", expected: colors.toneCream },
            { geometry: ARCHIMEDEAN_33434_GEOMETRY, kind: "triangle", expected: colors.toneTan },
            { geometry: ARCHIMEDEAN_33344_GEOMETRY, kind: "square", expected: colors.toneCream },
            { geometry: ARCHIMEDEAN_33344_GEOMETRY, kind: "triangle", expected: colors.toneTan },
            { geometry: ARCHIMEDEAN_33336_GEOMETRY, kind: "hexagon", expected: colors.toneCream },
            { geometry: ARCHIMEDEAN_33336_GEOMETRY, kind: "triangle", expected: colors.toneTan },
            { geometry: KAGOME_GEOMETRY, kind: "triangle-up", expected: "#d5bb8f" },
            { geometry: KAGOME_GEOMETRY, kind: "triangle-down", expected: "#d5bb8f" },
        ];

        expectations.forEach(({ geometry, kind, expected }) => {
            const cell = { id: `${kind}:0:0`, state: 0, kind };
            expect(resolveDeadCellColor(0, { geometry, cell })).toBe(expected);
            expect(resolveRenderedCellColor(0, colorLookup, colors, { geometry, cell })).toBe(expected);
        });
    });

    it("falls through to the default dead fill for geometries with no manifest entry", async () => {
        const { resolveDeadCellColor } = await import("./render-style.js");
        // Single-prototile lattices that do not yet register family variants
        // should fall through to the default dead color.
        const fallthroughGeometries = [
            CAIRO_GEOMETRY,
            TETRAKIS_SQUARE_GEOMETRY,
            TRIAKIS_TRIANGULAR_GEOMETRY,
            PRISMATIC_PENTAGONAL_GEOMETRY,
            FLORET_PENTAGONAL_GEOMETRY,
            SNUB_SQUARE_DUAL_GEOMETRY,
        ];
        fallthroughGeometries.forEach((geometry) => {
            expect(
                resolveDeadCellColor(0, {
                    geometry,
                    cell: { id: "p:0:0", state: 0, kind: "pentagon" },
                }),
            ).toBe("#f8f1e5");
        });
    });

    it("applies slot-based dead fills to Deltoidal Hexagonal kites", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const colors = readCanvasColorsForTests();
        const expectations = [
            { slot: "k0", expected: colors.toneTan },
            { slot: "k7", expected: colors.toneTan },
            { slot: "k1", expected: colors.toneStone },
            { slot: "k6", expected: colors.toneStone },
            { slot: "k2", expected: colors.toneClay },
            { slot: "k9", expected: colors.toneClay },
            { slot: "k3", expected: colors.toneLinen },
            { slot: "k8", expected: colors.toneLinen },
            { slot: "k4", expected: colors.toneSand },
            { slot: "k11", expected: colors.toneSand },
            { slot: "k5", expected: colors.toneFlax },
            { slot: "k10", expected: colors.toneFlax },
        ];

        expectations.forEach(({ slot, expected }) => {
            const cell = { id: `deltoidal-hexagonal:${slot}`, state: 0, kind: "kite", slot };
            expect(resolveDeadCellColor(0, { geometry: DELTOIDAL_HEXAGONAL_GEOMETRY, cell })).toBe(expected);
            expect(
                resolveRenderedCellColor(0, colorLookup, colors, { geometry: DELTOIDAL_HEXAGONAL_GEOMETRY, cell }),
            ).toBe(expected);
        });
    });

    it("applies slot-based dead fills to Deltoidal Trihexagonal kites", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const colors = readCanvasColorsForTests();
        const expectations = [
            { slot: "s5", expected: colors.toneLinen },
            { slot: "s10", expected: colors.toneLinen },
            { slot: "s3", expected: colors.toneSand },
            { slot: "s8", expected: colors.toneSand },
            { slot: "s2", expected: colors.toneFlax },
            { slot: "s9", expected: colors.toneFlax },
            { slot: "s4", expected: colors.toneTan },
            { slot: "s11", expected: colors.toneTan },
            { slot: "s0", expected: colors.toneStone },
            { slot: "s6", expected: colors.toneStone },
            { slot: "s1", expected: colors.toneClay },
            { slot: "s7", expected: colors.toneClay },
        ];

        expectations.forEach(({ slot, expected }) => {
            const cell = { id: `deltoidal-trihexagonal:${slot}`, state: 0, kind: "kite", slot };
            expect(resolveDeadCellColor(0, { geometry: DELTOIDAL_TRIHEXAGONAL_GEOMETRY, cell })).toBe(expected);
            expect(
                resolveRenderedCellColor(0, colorLookup, colors, { geometry: DELTOIDAL_TRIHEXAGONAL_GEOMETRY, cell }),
            ).toBe(expected);
        });
    });

    it("applies direction-based dead fills to Rhombille slots", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colorLookup = buildStateColorLookup();
        const colors = readCanvasColorsForTests();
        const expectations = [
            { slot: "s0", expected: colors.toneLinen },
            { slot: "s3", expected: colors.toneLinen },
            { slot: "s1", expected: colors.toneTan },
            { slot: "s4", expected: colors.toneTan },
            { slot: "s2", expected: colors.toneClay },
            { slot: "s5", expected: colors.toneClay },
        ];

        expectations.forEach(({ slot, expected }) => {
            const cell = { id: `rhombille:${slot}`, state: 0, kind: "rhombus", slot };
            expect(resolveDeadCellColor(0, { geometry: RHOMBILLE_GEOMETRY, cell })).toBe(expected);
            expect(resolveRenderedCellColor(0, colorLookup, colors, { geometry: RHOMBILLE_GEOMETRY, cell })).toBe(
                expected,
            );
        });
    });

    it("falls back to neutral dead fills when tile colors are disabled", async () => {
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colors = readCanvasColorsForTests();
        const colorLookup = buildStateColorLookup([], colors);
        const cell = { id: "rhombille:s1", state: 0, kind: "rhombus", slot: "s1" };

        expect(resolveDeadCellColor(0, { geometry: RHOMBILLE_GEOMETRY, cell, tileColorsEnabled: false })).toBe(
            colors.dead,
        );
        expect(
            resolveRenderedCellColor(0, colorLookup, colors, {
                geometry: RHOMBILLE_GEOMETRY,
                cell,
                tileColorsEnabled: false,
            }),
        ).toBe(colors.dead);
    });

    it("resolves registered family dead-state palettes from the shared registry", async () => {
        const {
            buildFamilyDeadPaletteTestCell,
            FAMILY_DEAD_PALETTE_REGISTRY,
            resolveDeadPaletteColorSpec,
        } = await import("./family-dead-palette-registry.js");
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colors = readCanvasColorsForTests();
        const colorLookup = buildStateColorLookup([], colors);

        FAMILY_DEAD_PALETTE_REGISTRY.forEach(({ geometry, variants }) => {
            variants.forEach((variant) => {
                const cell = buildFamilyDeadPaletteTestCell(variant);
                const expectedColor = resolveDeadPaletteColorSpec(variant.color, colors);
                expect(resolveDeadCellColor(0, { geometry, cell })).toBe(expectedColor);
                expect(resolveRenderedCellColor(0, colorLookup, colors, { geometry, cell })).toBe(expectedColor);
            });
        });
    });

    it("keeps registered family dead-state variants distinct from the live-state fill", async () => {
        const {
            buildFamilyDeadPaletteTestCell,
            FAMILY_DEAD_PALETTE_VARIANTS,
        } = await import("./family-dead-palette-registry.js");
        const {
            buildStateColorLookup,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colors = {
            line: "rgba(31, 36, 48, 0.16)",
            dead: "#fcfaf4",
            deadAlt: "#d1b57a",
            lineSoft: "rgba(31, 36, 48, 0.11)",
            lineStrong: "rgba(31, 36, 48, 0.21)",
            lineAperiodic: "rgba(31, 36, 48, 0.24)",
            live: "#131722",
            accent: "#bf5a36",
            accentStrong: "#8a3d20",
            toneCream: "#f8f1e5",
            toneLinen: "#ead6b6",
            toneSand: "#efe4d0",
            toneFlax: "#e1cdac",
            toneTan: "#e5c089",
            toneStone: "#d5bb8f",
            toneRose: "#dbc1b2",
            toneClay: "#c88d4b",
            toneShadow: "#b89a6e",
        };
        const colorLookup = buildStateColorLookup([], colors);

        FAMILY_DEAD_PALETTE_VARIANTS.forEach((variant) => {
            const cell = buildFamilyDeadPaletteTestCell(variant);
            expect(resolveRenderedCellColor(0, colorLookup, colors, { geometry: variant.geometry, cell })).not.toBe(
                colors.live,
            );
        });

        expect(
            resolveRenderedCellColor(
                1,
                colorLookup,
                colors,
                {
                    geometry: "shield",
                    cell: {
                        id: "shield:live",
                        state: 1,
                        kind: "shield-shield",
                        tile_family: "shield",
                    },
                },
            ),
        ).toBe(colors.live);
    });

    it("keeps registered family dead-state variants distinct within each geometry unless explicitly shared", async () => {
        const {
            FAMILY_DEAD_PALETTE_REGISTRY,
            resolveDeadPaletteColorSpec,
        } = await import("./family-dead-palette-registry.js");
        const colors = readCanvasColorsForTests();

        FAMILY_DEAD_PALETTE_REGISTRY.forEach(({ geometry, variants }) => {
            const colorLabels = new Map<string, string>();
            variants.forEach((variant) => {
                if (variant.allowSharedDeadColor) {
                    return;
                }
                const resolvedColor = resolveDeadPaletteColorSpec(variant.color, colors);
                const previousLabel = colorLabels.get(resolvedColor);
                expect(
                    previousLabel,
                    `${geometry} variant ${variant.label} collapsed onto ${previousLabel || "an earlier variant"}`,
                ).toBeUndefined();
                colorLabels.set(resolvedColor, variant.label);
            });
        });
    });

    it("applies token-backed family dead-state variants using runtime canvas colors", async () => {
        const {
            buildFamilyDeadPaletteTestCell,
            FAMILY_DEAD_PALETTE_VARIANTS,
            resolveDeadPaletteColorSpec,
        } = await import("./family-dead-palette-registry.js");
        const {
            buildStateColorLookup,
            resolveDeadCellColor,
            resolveRenderedCellColor,
        } = await import("./render-style.js");
        const colors = {
            line: "rgba(31, 36, 48, 0.16)",
            dead: "#f2ead9",
            deadAlt: "#cfab64",
            lineSoft: "rgba(31, 36, 48, 0.10)",
            lineStrong: "rgba(31, 36, 48, 0.20)",
            lineAperiodic: "rgba(31, 36, 48, 0.24)",
            live: "#1f2430",
            accent: "#d67a4c",
            accentStrong: "#f1a275",
            toneCream: "#f8f1e5",
            toneLinen: "#ead6b6",
            toneSand: "#efe4d0",
            toneFlax: "#e1cdac",
            toneTan: "#e5c089",
            toneStone: "#d5bb8f",
            toneRose: "#dbc1b2",
            toneClay: "#c88d4b",
            toneShadow: "#b89a6e",
        };
        const colorLookup = buildStateColorLookup([], colors);
        const tokenBackedVariants = FAMILY_DEAD_PALETTE_VARIANTS.filter((variant) => typeof variant.color !== "string");

        tokenBackedVariants.forEach((variant) => {
            const cell = buildFamilyDeadPaletteTestCell(variant);
            const expectedColor = resolveDeadPaletteColorSpec(variant.color, colors);
            expect(resolveDeadCellColor(0, { geometry: variant.geometry, cell }, colors)).toBe(expectedColor);
            expect(resolveRenderedCellColor(0, colorLookup, colors, { geometry: variant.geometry, cell })).toBe(
                expectedColor,
            );
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
            toneCream: "#f8f1e5",
            toneLinen: "#ead6b6",
            toneSand: "#efe4d0",
            toneFlax: "#e1cdac",
            toneTan: "#e5c089",
            toneStone: "#d5bb8f",
            toneRose: "#dbc1b2",
            toneClay: "#c88d4b",
            toneShadow: "#b89a6e",
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
        toneCream: "#f8f1e5",
        toneLinen: "#ead6b6",
        toneSand: "#efe4d0",
        toneFlax: "#e1cdac",
        toneTan: "#e5c089",
        toneStone: "#d5bb8f",
        toneRose: "#dbc1b2",
        toneClay: "#c88d4b",
        toneShadow: "#b89a6e",
    };
}
