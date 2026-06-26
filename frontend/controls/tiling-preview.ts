import type { TopologyOption } from "../types/domain.js";

// The polygon thumbnail strings are bulky (one entry per tiling family, and the
// aperiodic rhombic families are especially large). They are only needed once the
// tiling picker renders, never at initial page load, so the data module is loaded
// lazily via dynamic import. This keeps it in its own async chunk instead of the
// runtime bundle, so adding a tiling no longer grows app-runtime-*.js.
type PolygonPreviewData = Readonly<Record<string, string>>;

let polygonPreviewData: PolygonPreviewData | null = null;
let polygonPreviewDataPromise: Promise<PolygonPreviewData> | null = null;
const pendingPreviewThumbnails = new Set<{ svg: SVGSVGElement; option: TopologyOption }>();

export function ensureTilingPreviewData(): Promise<PolygonPreviewData> {
    if (polygonPreviewData) {
        return Promise.resolve(polygonPreviewData);
    }
    if (!polygonPreviewDataPromise) {
        polygonPreviewDataPromise = import("./tiling-preview-data.js")
            .then((module) => {
                polygonPreviewData = module.POLYGON_PREVIEW_DATA;
                flushPendingPreviewThumbnails();
                return polygonPreviewData;
            })
            .catch((error: unknown) => {
                polygonPreviewDataPromise = null;
                throw error;
            });
    }
    return polygonPreviewDataPromise;
}

function flushPendingPreviewThumbnails(): void {
    const pending = Array.from(pendingPreviewThumbnails);
    pendingPreviewThumbnails.clear();
    pending.forEach(({ svg, option }) => {
        while (svg.firstChild) {
            svg.removeChild(svg.firstChild);
        }
        renderPreviewGeometry(svg, option);
    });
}

const SVG_NS = "http://www.w3.org/2000/svg";
const PREVIEW_VIEW_BOX = "0 0 120 72";

type Point = readonly [number, number];

const PREVIEW_FILL_CLASSES = [
    "tiling-preview-fill-a",
    "tiling-preview-fill-b",
    "tiling-preview-fill-c",
    "tiling-preview-fill-d",
] as const;

const PREVIEW_FILL_TOKEN_CSS: Readonly<Record<string, string>> = {
    dead: "var(--cell-dead, var(--dead, #f8f1e5))",
    deadAlt: "var(--cell-dead-alt, #d5bb8f)",
    accent: "var(--accent, #bf5a36)",
    accentStrong: "var(--accent-dark, var(--accent, #8a3d20))",
    toneCream: "var(--tone-cream, #f8f1e5)",
    toneLinen: "var(--tone-linen, #ead6b6)",
    toneSand: "var(--tone-sand, #efe4d0)",
    toneFlax: "var(--tone-flax, #e1cdac)",
    toneTan: "var(--tone-tan, #e5c089)",
    toneStone: "var(--tone-stone, #d5bb8f)",
    toneRose: "var(--tone-rose, #dbc1b2)",
    toneClay: "var(--tone-clay, #c88d4b)",
    toneShadow: "var(--tone-shadow, #b89a6e)",
};

function svgElement<TElement extends SVGElement>(tagName: string): TElement {
    return document.createElementNS(SVG_NS, tagName) as TElement;
}

function formatPoint(value: number): string {
    return Number(value.toFixed(3)).toString();
}

function pointsAttribute(points: readonly Point[]): string {
    return points.map(([x, y]) => `${formatPoint(x)},${formatPoint(y)}`).join(" ");
}

function previewFillClass(index: number): string {
    return PREVIEW_FILL_CLASSES[index % PREVIEW_FILL_CLASSES.length] ?? PREVIEW_FILL_CLASSES[0];
}

function addPolygon(
    svg: SVGSVGElement,
    points: readonly Point[],
    fill: string | number = "0",
): void {
    const polygon = svgElement<SVGPolygonElement>("polygon");
    polygon.setAttribute("points", pointsAttribute(points));
    polygon.classList.add("tiling-preview-shape");
    const numericFillIndex = Number(fill);
    if (Number.isInteger(numericFillIndex) && numericFillIndex >= 0) {
        polygon.classList.add(previewFillClass(numericFillIndex));
    } else {
        const fillToken = String(fill);
        polygon.setAttribute("data-fill-token", fillToken);
        polygon.setAttribute("fill", PREVIEW_FILL_TOKEN_CSS[fillToken] ?? fillToken);
    }
    svg.appendChild(polygon);
}

function addRect(
    svg: SVGSVGElement,
    x: number,
    y: number,
    width: number,
    height: number,
    fillIndex = 0,
): void {
    addPolygon(
        svg,
        [
            [x, y],
            [x + width, y],
            [x + width, y + height],
            [x, y + height],
        ],
        fillIndex,
    );
}

function regularPolygonPoints(
    sides: number,
    centerX: number,
    centerY: number,
    radius: number,
    rotation = -Math.PI / 2,
): Point[] {
    return Array.from({ length: sides }, (_, index) => {
        const angle = rotation + (Math.PI * 2 * index) / sides;
        return [centerX + Math.cos(angle) * radius, centerY + Math.sin(angle) * radius] as const;
    });
}

function addSquarePreview(svg: SVGSVGElement): void {
    for (let row = 0; row < 4; row += 1) {
        for (let column = 0; column < 6; column += 1) {
            addRect(svg, 8 + column * 18, 6 + row * 16, 17, 15);
        }
    }
}

function addHexPreview(svg: SVGSVGElement): void {
    for (let row = 0; row < 3; row += 1) {
        for (let column = 0; column < 4; column += 1) {
            addPolygon(
                svg,
                regularPolygonPoints(
                    6,
                    20 + column * 27 + (row % 2) * 13.5,
                    16 + row * 20,
                    12,
                    Math.PI / 6,
                ),
            );
        }
    }
}

function addTrianglePreview(svg: SVGSVGElement): void {
    const side = 17;
    const height = (Math.sqrt(3) * side) / 2;
    for (let row = 0; row < 4; row += 1) {
        for (let column = 0; column < 7; column += 1) {
            const x = 2 + column * side;
            const y = 5 + row * height;
            addPolygon(svg, [
                [x, y + height],
                [x + side / 2, y],
                [x + side, y + height],
            ]);
            addPolygon(svg, [
                [x + side / 2, y],
                [x + side + side / 2, y],
                [x + side, y + height],
            ]);
        }
    }
}

function parsePolygonPreviewPoint(pointPayload: string): Point | null {
    const [rawX, rawY] = pointPayload.split(",");
    const x = Number(rawX);
    const y = Number(rawY);
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
        return null;
    }
    return [x, y];
}

function addPolygonDataPreview(svg: SVGSVGElement, payload: string): boolean {
    if (!payload) {
        return false;
    }
    let rendered = false;
    payload.split(";").forEach((polygonPayload) => {
        const separatorIndex = polygonPayload.indexOf(":");
        if (separatorIndex < 0) {
            return;
        }
        const fill = polygonPayload.slice(0, separatorIndex).trim();
        const points = polygonPayload
            .slice(separatorIndex + 1)
            .split(" ")
            .map(parsePolygonPreviewPoint)
            .filter((point): point is Point => point !== null);
        if (points.length < 3) {
            return;
        }
        addPolygon(svg, points, fill || "0");
        rendered = true;
    });
    return rendered;
}

function renderPreviewGeometry(svg: SVGSVGElement, option: TopologyOption): void {
    if (option.previewKey === "square") {
        addSquarePreview(svg);
        return;
    }
    if (option.previewKey === "hex") {
        addHexPreview(svg);
        return;
    }
    if (option.previewKey === "triangle") {
        addTrianglePreview(svg);
        return;
    }
    const payload = polygonPreviewData?.[option.previewKey] ?? "";
    if (payload && addPolygonDataPreview(svg, payload)) {
        return;
    }
    // Show a generic square placeholder until the lazily-loaded polygon data
    // arrives, then re-render this thumbnail in place. Once the data has loaded,
    // a missing key just keeps the square fallback (matching prior behaviour).
    addSquarePreview(svg);
    if (!polygonPreviewData) {
        pendingPreviewThumbnails.add({ svg, option });
        void ensureTilingPreviewData().catch(() => {
            // Keep the fallback thumbnail visible. A later picker render or
            // explicit ensureTilingPreviewData() call will retry the chunk load.
        });
    }
}

export function createTilingPreviewThumbnail(
    option: TopologyOption,
    className = "tiling-preview-svg",
): SVGSVGElement {
    const svg = svgElement<SVGSVGElement>("svg");
    svg.setAttribute("viewBox", PREVIEW_VIEW_BOX);
    svg.setAttribute("focusable", "false");
    svg.setAttribute("aria-hidden", "true");
    svg.classList.add("tiling-preview-svg");
    if (className !== "tiling-preview-svg") {
        svg.classList.add(className);
    }
    renderPreviewGeometry(svg, option);
    return svg;
}
