import { POLYGON_PREVIEW_DATA } from "./tiling-preview-data.js";
import type { TopologyOption } from "../types/domain.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const PREVIEW_VIEW_BOX = "0 0 120 72";

type Point = readonly [number, number];

const PREVIEW_FILL_CLASSES = [
    "tiling-preview-fill-a",
    "tiling-preview-fill-b",
    "tiling-preview-fill-c",
    "tiling-preview-fill-d",
] as const;

function svgElement<TElement extends SVGElement>(tagName: string): TElement {
    return document.createElementNS(SVG_NS, tagName) as TElement;
}

function formatPoint(value: number): string {
    return Number(value.toFixed(3)).toString();
}

function pointsAttribute(points: readonly Point[]): string {
    return points.map(([x, y]) => `${formatPoint(x)},${formatPoint(y)}`).join(" ");
}

function previewFill(index: number): string {
    return PREVIEW_FILL_CLASSES[index % PREVIEW_FILL_CLASSES.length] ?? PREVIEW_FILL_CLASSES[0];
}

function addPolygon(svg: SVGSVGElement, points: readonly Point[], fillIndex = 0): void {
    const polygon = svgElement<SVGPolygonElement>("polygon");
    polygon.setAttribute("points", pointsAttribute(points));
    polygon.setAttribute("class", `tiling-preview-shape ${previewFill(fillIndex)}`);
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
    addPolygon(svg, [[x, y], [x + width, y], [x + width, y + height], [x, y + height]], fillIndex);
}

function regularPolygonPoints(
    sides: number,
    centerX: number,
    centerY: number,
    radius: number,
    rotation = -Math.PI / 2,
): Point[] {
    return Array.from({ length: sides }, (_, index) => {
        const angle = rotation + ((Math.PI * 2 * index) / sides);
        return [
            centerX + (Math.cos(angle) * radius),
            centerY + (Math.sin(angle) * radius),
        ] as const;
    });
}

function addSquarePreview(svg: SVGSVGElement): void {
    for (let row = 0; row < 4; row += 1) {
        for (let column = 0; column < 6; column += 1) {
            addRect(svg, 8 + (column * 18), 6 + (row * 16), 17, 15, row + column);
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
                    20 + (column * 27) + ((row % 2) * 13.5),
                    16 + (row * 20),
                    12,
                    Math.PI / 6,
                ),
                row + column,
            );
        }
    }
}

function addTrianglePreview(svg: SVGSVGElement): void {
    const side = 17;
    const height = (Math.sqrt(3) * side) / 2;
    for (let row = 0; row < 4; row += 1) {
        for (let column = 0; column < 7; column += 1) {
            const x = 2 + (column * side);
            const y = 5 + (row * height);
            addPolygon(svg, [[x, y + height], [x + (side / 2), y], [x + side, y + height]], row + column);
            addPolygon(
                svg,
                [[x + (side / 2), y], [x + side + (side / 2), y], [x + side, y + height]],
                row + column + 1,
            );
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
        const fillIndex = Number(polygonPayload.slice(0, separatorIndex));
        const points = polygonPayload
            .slice(separatorIndex + 1)
            .split(" ")
            .map(parsePolygonPreviewPoint)
            .filter((point): point is Point => point !== null);
        if (points.length < 3) {
            return;
        }
        addPolygon(svg, points, Number.isFinite(fillIndex) ? fillIndex : 0);
        rendered = true;
    });
    return rendered;
}

function addPreviewGeometry(svg: SVGSVGElement, option: TopologyOption): void {
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
    if (addPolygonDataPreview(svg, POLYGON_PREVIEW_DATA[option.previewKey] ?? "")) {
        return;
    }
    addSquarePreview(svg);
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
    addPreviewGeometry(svg, option);
    return svg;
}
