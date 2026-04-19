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
