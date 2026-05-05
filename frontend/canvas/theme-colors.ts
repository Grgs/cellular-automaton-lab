import type { CanvasColors } from "../types/rendering.js";

export const DEFAULT_COLORS: CanvasColors = {
    line: "rgba(31, 36, 48, 0.16)",
    dead: "#f8f1e5",
    deadAlt: "#d5bb8f",
    lineSoft: "rgba(31, 36, 48, 0.07)",
    lineStrong: "rgba(31, 36, 48, 0.14)",
    lineAperiodic: "rgba(31, 36, 48, 0.18)",
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

export function readCanvasColors(
    canvas: HTMLElement,
    getComputedStyleFn: (node: Element) => CSSStyleDeclaration,
): CanvasColors {
    const rootStyle = getComputedStyleFn(document.documentElement);
    const canvasStyle = getComputedStyleFn(canvas);
    const dead =
        rootStyle.getPropertyValue("--cell-dead").trim() ||
        rootStyle.getPropertyValue("--dead").trim() ||
        DEFAULT_COLORS.dead;
    return {
        line:
            rootStyle.getPropertyValue("--line").trim() ||
            canvasStyle.backgroundColor ||
            DEFAULT_COLORS.line,
        dead,
        deadAlt:
            rootStyle.getPropertyValue("--cell-dead-alt").trim() || dead || DEFAULT_COLORS.deadAlt,
        lineSoft:
            rootStyle.getPropertyValue("--cell-line-soft").trim() ||
            rootStyle.getPropertyValue("--line").trim() ||
            canvasStyle.backgroundColor ||
            DEFAULT_COLORS.lineSoft,
        lineStrong:
            rootStyle.getPropertyValue("--cell-line-strong").trim() ||
            rootStyle.getPropertyValue("--line").trim() ||
            canvasStyle.backgroundColor ||
            DEFAULT_COLORS.lineStrong,
        lineAperiodic:
            rootStyle.getPropertyValue("--cell-line-aperiodic").trim() ||
            rootStyle.getPropertyValue("--cell-line-strong").trim() ||
            rootStyle.getPropertyValue("--line").trim() ||
            canvasStyle.backgroundColor ||
            DEFAULT_COLORS.lineAperiodic,
        live: rootStyle.getPropertyValue("--live").trim() || DEFAULT_COLORS.live,
        accent: rootStyle.getPropertyValue("--accent").trim() || DEFAULT_COLORS.accent,
        accentStrong:
            rootStyle.getPropertyValue("--accent-dark").trim() ||
            rootStyle.getPropertyValue("--accent").trim() ||
            DEFAULT_COLORS.accentStrong,
        toneCream: rootStyle.getPropertyValue("--tone-cream").trim() || DEFAULT_COLORS.toneCream,
        toneLinen: rootStyle.getPropertyValue("--tone-linen").trim() || DEFAULT_COLORS.toneLinen,
        toneSand: rootStyle.getPropertyValue("--tone-sand").trim() || DEFAULT_COLORS.toneSand,
        toneFlax: rootStyle.getPropertyValue("--tone-flax").trim() || DEFAULT_COLORS.toneFlax,
        toneTan: rootStyle.getPropertyValue("--tone-tan").trim() || DEFAULT_COLORS.toneTan,
        toneStone: rootStyle.getPropertyValue("--tone-stone").trim() || DEFAULT_COLORS.toneStone,
        toneRose: rootStyle.getPropertyValue("--tone-rose").trim() || DEFAULT_COLORS.toneRose,
        toneClay: rootStyle.getPropertyValue("--tone-clay").trim() || DEFAULT_COLORS.toneClay,
        toneShadow: rootStyle.getPropertyValue("--tone-shadow").trim() || DEFAULT_COLORS.toneShadow,
    };
}

export function parseColorChannels(
    color: string,
): { r: number; g: number; b: number; a: number } | null {
    const normalized = color.trim().toLowerCase();
    const hexMatch = normalized.match(/^#([0-9a-f]{3,8})$/i);
    if (hexMatch) {
        const hex = hexMatch[1] ?? "";
        if (hex.length === 3 || hex.length === 4) {
            const chars = hex.split("");
            const r = chars[0] ?? "0";
            const g = chars[1] ?? "0";
            const b = chars[2] ?? "0";
            const a = chars[3] ?? "f";
            return {
                r: Number.parseInt(r + r, 16),
                g: Number.parseInt(g + g, 16),
                b: Number.parseInt(b + b, 16),
                a: Number.parseInt(a + a, 16) / 255,
            };
        }
        if (hex.length === 6 || hex.length === 8) {
            return {
                r: Number.parseInt(hex.slice(0, 2), 16),
                g: Number.parseInt(hex.slice(2, 4), 16),
                b: Number.parseInt(hex.slice(4, 6), 16),
                a: hex.length === 8 ? Number.parseInt(hex.slice(6, 8), 16) / 255 : 1,
            };
        }
        return null;
    }

    const rgbMatch = normalized.match(/^rgba?\(([^)]+)\)$/);
    if (!rgbMatch) {
        return null;
    }
    const rgbBody = rgbMatch[1] ?? "";
    const parts = rgbBody.split(",").map((part) => part.trim());
    if (parts.length < 3) {
        return null;
    }
    const red = parts[0];
    const green = parts[1];
    const blue = parts[2];
    if (!red || !green || !blue) {
        return null;
    }
    return {
        r: Number.parseFloat(red),
        g: Number.parseFloat(green),
        b: Number.parseFloat(blue),
        a: parts.length >= 4 && parts[3] ? Number.parseFloat(parts[3]) : 1,
    };
}

export function relativeLuminance({ r, g, b }: { r: number; g: number; b: number }): number {
    const toLinear = (channel: number) => {
        const srgb = channel / 255;
        return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
    };
    return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
}

export function withAlpha(color: string, alpha: number): string {
    const parsed = parseColorChannels(color);
    if (!parsed) {
        return color;
    }
    return `rgba(${parsed.r}, ${parsed.g}, ${parsed.b}, ${alpha})`;
}
