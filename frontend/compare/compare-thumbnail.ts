import type { TopologyPreview, TopologyPreviewCell } from "../types/domain.js";

const SVG_NS = "http://www.w3.org/2000/svg";

export interface ThumbnailBounds {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
}

export interface ThumbnailOptions {
    /** Max rendered dimension in px; the other axis scales to preserve aspect ratio. */
    size?: number;
    deadFill?: string;
    stroke?: string;
    /** Fill for a live cell given its (non-zero) state. */
    liveColor?: (state: number) => string;
    label?: string;
}

const DEFAULTS = {
    size: 132,
    deadFill: "var(--cell-dead, #fdf8ef)",
    stroke: "var(--cell-line-soft, rgba(31,36,48,0.1))",
    liveColor: () => "var(--live, #1f2430)",
};

/** Bounding box over every cell vertex (geometry units). */
export function computeBounds(cells: readonly TopologyPreviewCell[]): ThumbnailBounds {
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    for (const cell of cells) {
        for (const vertex of cell.vertices) {
            minX = Math.min(minX, vertex.x);
            minY = Math.min(minY, vertex.y);
            maxX = Math.max(maxX, vertex.x);
            maxY = Math.max(maxY, vertex.y);
        }
    }
    if (!Number.isFinite(minX)) {
        return { minX: 0, minY: 0, maxX: 1, maxY: 1 };
    }
    return { minX, minY, maxX, maxY };
}

/** Rendered px dimensions for a bounds box, capped at `size` on the longer axis. */
export function fitDimensions(
    bounds: ThumbnailBounds,
    size: number,
): { width: number; height: number } {
    const w = Math.max(bounds.maxX - bounds.minX, 1e-6);
    const h = Math.max(bounds.maxY - bounds.minY, 1e-6);
    if (w >= h) {
        return { width: size, height: Math.max(1, Math.round((size * h) / w)) };
    }
    return { width: Math.max(1, Math.round((size * w) / h)), height: size };
}

function svgElement<K extends keyof SVGElementTagNameMap>(
    tag: K,
    attributes: Record<string, string>,
): SVGElementTagNameMap[K] {
    const element = document.createElementNS(SVG_NS, tag);
    for (const [name, value] of Object.entries(attributes)) {
        element.setAttribute(name, value);
    }
    return element;
}

/**
 * Render a tiling's board (one polygon per cell) as an SVG, colouring live
 * cells from `cellsById`. The board geometry already matches the app's screen
 * orientation (y increases downward), so vertices map straight onto the viewBox.
 */
export function buildBoardThumbnailSvg(
    preview: TopologyPreview,
    cellsById: Record<string, number>,
    options: ThumbnailOptions = {},
): SVGSVGElement {
    const size = options.size ?? DEFAULTS.size;
    const deadFill = options.deadFill ?? DEFAULTS.deadFill;
    const stroke = options.stroke ?? DEFAULTS.stroke;
    const liveColor = options.liveColor ?? DEFAULTS.liveColor;

    const bounds = computeBounds(preview.cells);
    const { width, height } = fitDimensions(bounds, size);
    const svg = svgElement("svg", {
        viewBox: `${bounds.minX} ${bounds.minY} ${Math.max(bounds.maxX - bounds.minX, 1e-6)} ${Math.max(bounds.maxY - bounds.minY, 1e-6)}`,
        width: String(width),
        height: String(height),
        class: "compare-thumb",
        role: "img",
        "aria-label": options.label ?? "Board preview",
    });

    for (const cell of preview.cells) {
        if (cell.vertices.length < 3) {
            continue;
        }
        const state = cellsById[cell.id] ?? 0;
        const polygon = svgElement("polygon", {
            points: cell.vertices.map((vertex) => `${vertex.x},${vertex.y}`).join(" "),
            fill: state !== 0 ? liveColor(state) : deadFill,
            stroke,
            "stroke-width": "0.02",
        });
        if (state !== 0) {
            polygon.classList.add("is-live");
        }
        svg.append(polygon);
    }
    return svg;
}
