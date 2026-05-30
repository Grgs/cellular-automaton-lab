import type { SeedComparisonResult, TopologyComparisonResultPayload } from "../types/domain.js";

const SVG_NS = "http://www.w3.org/2000/svg";

export const FAMILY_COLORS: Readonly<Record<string, string>> = {
    regular: "#bf5a36",
    mixed: "#2f6f4f",
    periodic: "#2f6f4f",
    aperiodic: "#3a5a9f",
};

export function familyColor(family: string): string {
    return FAMILY_COLORS[family] ?? "#6d756f";
}

export interface ClassificationStyle {
    label: string;
    color: string;
}

export function classificationStyle(classification: string): ClassificationStyle {
    if (classification === "extinct") {
        return { label: "Extinct", color: "#9aa0a6" };
    }
    if (classification === "still-life") {
        return { label: "Still life", color: "#2f6f4f" };
    }
    if (classification.startsWith("oscillator-p")) {
        return {
            label: `Oscillator (p${classification.slice("oscillator-p".length)})`,
            color: "#3a5a9f",
        };
    }
    if (classification === "unsettled") {
        return { label: "Unsettled", color: "#bf5a36" };
    }
    if (classification === "error") {
        return { label: "Error", color: "#b02a37" };
    }
    return { label: classification, color: "#6d756f" };
}

/** Population trace normalised to the seed's initial live count (live(t)/live(0)). */
export function normalizedSeries(result: TopologyComparisonResultPayload): number[] {
    const base = result.population[0] ?? 0;
    if (base <= 0) {
        return result.population.map(() => 0);
    }
    return result.population.map((value) => value / base);
}

export interface PlotDimensions {
    width: number;
    height: number;
    padding: number;
}

export interface PlotSeries {
    geometry: string;
    family: string;
    points: Array<[number, number]>;
}

export interface PhasePortraitModel {
    series: PlotSeries[];
    xMax: number;
    yMax: number;
}

/**
 * Map each tiling's normalised population trace into SVG pixel coordinates.
 * Pure (no DOM) so the layout maths can be unit-tested directly.
 */
export function buildPhasePortraitModel(
    comparison: SeedComparisonResult,
    dims: PlotDimensions,
): PhasePortraitModel {
    const plotted = comparison.results.filter((result) => result.classification !== "error");
    const xMax = Math.max(1, comparison.steps);
    const yMax = Math.max(
        1,
        ...plotted.map((result) => {
            const series = normalizedSeries(result);
            return series.length ? Math.max(...series) : 0;
        }),
    );
    const plotWidth = dims.width - dims.padding * 2;
    const plotHeight = dims.height - dims.padding * 2;

    const series = plotted.map((result) => {
        const values = normalizedSeries(result);
        const points = values.map((value, index): [number, number] => {
            const x = dims.padding + (index / xMax) * plotWidth;
            const y = dims.padding + plotHeight - (value / yMax) * plotHeight;
            return [x, y];
        });
        return { geometry: result.geometry, family: result.family, points };
    });

    return { series, xMax, yMax };
}

export function pointsAttribute(points: Array<[number, number]>): string {
    return points.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(" ");
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

/** Build the phase-portrait SVG: one line per tiling, coloured by family. */
export function buildPhasePortraitSvg(
    comparison: SeedComparisonResult,
    dims: PlotDimensions = { width: 640, height: 320, padding: 32 },
): SVGSVGElement {
    const model = buildPhasePortraitModel(comparison, dims);
    const svg = svgElement("svg", {
        viewBox: `0 0 ${dims.width} ${dims.height}`,
        class: "compare-portrait",
        role: "img",
        "aria-label": "Normalised population over time, one line per tiling.",
        preserveAspectRatio: "none",
    });

    const plotWidth = dims.width - dims.padding * 2;
    const plotHeight = dims.height - dims.padding * 2;
    const baselineY = dims.padding + plotHeight - (1 / model.yMax) * plotHeight;

    svg.append(
        svgElement("rect", {
            x: String(dims.padding),
            y: String(dims.padding),
            width: String(plotWidth),
            height: String(plotHeight),
            class: "compare-portrait__frame",
        }),
    );
    // Reference line at live(t)/live(0) = 1 (initial population).
    svg.append(
        svgElement("line", {
            x1: String(dims.padding),
            y1: baselineY.toFixed(2),
            x2: String(dims.padding + plotWidth),
            y2: baselineY.toFixed(2),
            class: "compare-portrait__baseline",
        }),
    );

    for (const series of model.series) {
        if (series.points.length < 2) {
            const single = series.points[0];
            if (single) {
                const dot = svgElement("circle", {
                    cx: single[0].toFixed(2),
                    cy: single[1].toFixed(2),
                    r: "2.5",
                    fill: familyColor(series.family),
                    "data-geometry": series.geometry,
                });
                dot.classList.add("compare-portrait__point");
                svg.append(dot);
            }
            continue;
        }
        const line = svgElement("polyline", {
            points: pointsAttribute(series.points),
            fill: "none",
            stroke: familyColor(series.family),
            "data-geometry": series.geometry,
        });
        line.classList.add("compare-portrait__line");
        svg.append(line);
    }

    return svg;
}

export interface ComparePanelCallbacks {
    onRowHover?: (geometry: string | null) => void;
}

/** Build the classification grid: rows = tilings, coloured by end-state class. */
export function buildClassificationGrid(
    comparison: SeedComparisonResult,
    callbacks: ComparePanelCallbacks = {},
): HTMLTableElement {
    const rows = [...comparison.results].sort(
        (a, b) => a.family.localeCompare(b.family) || a.geometry.localeCompare(b.geometry),
    );

    const table = document.createElement("table");
    table.className = "compare-grid";

    const head = document.createElement("thead");
    head.innerHTML =
        "<tr><th>Tiling</th><th>Family</th><th>Cells</th><th>live₀→liveₙ</th>" +
        "<th>norm</th><th>End state</th></tr>";
    table.append(head);

    const body = document.createElement("tbody");
    for (const result of rows) {
        const style = classificationStyle(result.classification);
        const row = document.createElement("tr");
        row.dataset.geometry = result.geometry;
        if (callbacks.onRowHover) {
            row.addEventListener("mouseenter", () => callbacks.onRowHover?.(result.geometry));
            row.addEventListener("mouseleave", () => callbacks.onRowHover?.(null));
        }

        const note = result.note ? ` · ${result.note}` : "";
        row.innerHTML =
            `<td class="compare-grid__name">${escapeHtml(result.geometry)}</td>` +
            `<td>${escapeHtml(result.family)}</td>` +
            `<td>${result.cell_count}</td>` +
            `<td>${result.initial_population} → ${result.final_population}</td>` +
            `<td>${result.normalized_population.toFixed(2)}</td>` +
            `<td><span class="compare-chip" style="--chip:${style.color}">` +
            `${escapeHtml(style.label)}</span>${escapeHtml(note)}</td>`;
        body.append(row);
    }
    table.append(body);
    return table;
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}
