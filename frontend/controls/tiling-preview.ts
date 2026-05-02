import type { TopologyOption } from "../types/domain.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const PREVIEW_VIEW_BOX = "0 0 120 72";

type Point = readonly [number, number];
type PreviewBuilder = (svg: SVGSVGElement) => void;

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

function appendShape(svg: SVGSVGElement, shape: SVGElement, fillClass: string): void {
    shape.setAttribute("class", `tiling-preview-shape ${fillClass}`);
    svg.appendChild(shape);
}

function addPolygon(svg: SVGSVGElement, points: readonly Point[], fillClass = "tiling-preview-fill-a"): void {
    const polygon = svgElement<SVGPolygonElement>("polygon");
    polygon.setAttribute("points", pointsAttribute(points));
    appendShape(svg, polygon, fillClass);
}

function addRect(
    svg: SVGSVGElement,
    x: number,
    y: number,
    width: number,
    height: number,
    fillClass = "tiling-preview-fill-a",
): void {
    const rect = svgElement<SVGRectElement>("rect");
    rect.setAttribute("x", formatPoint(x));
    rect.setAttribute("y", formatPoint(y));
    rect.setAttribute("width", formatPoint(width));
    rect.setAttribute("height", formatPoint(height));
    appendShape(svg, rect, fillClass);
}

function addLine(svg: SVGSVGElement, from: Point, to: Point): void {
    const line = svgElement<SVGLineElement>("line");
    line.setAttribute("class", "tiling-preview-line");
    line.setAttribute("x1", formatPoint(from[0]));
    line.setAttribute("y1", formatPoint(from[1]));
    line.setAttribute("x2", formatPoint(to[0]));
    line.setAttribute("y2", formatPoint(to[1]));
    svg.appendChild(line);
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

function addRegularPolygon(
    svg: SVGSVGElement,
    sides: number,
    centerX: number,
    centerY: number,
    radius: number,
    fillClass = "tiling-preview-fill-a",
    rotation = -Math.PI / 2,
): void {
    addPolygon(svg, regularPolygonPoints(sides, centerX, centerY, radius, rotation), fillClass);
}

function previewFill(index: number, fillClasses: readonly string[] = PREVIEW_FILL_CLASSES): string {
    return fillClasses[index % fillClasses.length] ?? PREVIEW_FILL_CLASSES[0];
}

function forEachPoint(
    points: readonly Point[],
    callback: (x: number, y: number, index: number) => void,
): void {
    points.forEach(([x, y], index) => {
        callback(x, y, index);
    });
}

function forEachPolygon(
    polygons: readonly (readonly Point[])[],
    callback: (points: readonly Point[], index: number) => void,
): void {
    polygons.forEach((points, index) => {
        callback(points, index);
    });
}

function addSquareGrid(svg: SVGSVGElement): void {
    for (let row = 0; row < 4; row += 1) {
        for (let column = 0; column < 6; column += 1) {
            addRect(
                svg,
                8 + (column * 18),
                6 + (row * 16),
                17,
                15,
                (row + column) % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-b",
            );
        }
    }
}

function addHexGrid(svg: SVGSVGElement): void {
    for (let row = 0; row < 3; row += 1) {
        for (let column = 0; column < 4; column += 1) {
            addRegularPolygon(
                svg,
                6,
                20 + (column * 27) + ((row % 2) * 13.5),
                16 + (row * 20),
                12,
                (row + column) % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-b",
                Math.PI / 6,
            );
        }
    }
}

function addTriangleGrid(svg: SVGSVGElement): void {
    const side = 17;
    const height = (Math.sqrt(3) * side) / 2;
    for (let row = 0; row < 4; row += 1) {
        for (let column = 0; column < 7; column += 1) {
            const x = 2 + (column * side);
            const y = 5 + (row * height);
            addPolygon(
                svg,
                [[x, y + height], [x + (side / 2), y], [x + side, y + height]],
                (row + column) % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-b",
            );
            addPolygon(
                svg,
                [[x + (side / 2), y], [x + side + (side / 2), y], [x + side, y + height]],
                (row + column) % 2 === 0 ? "tiling-preview-fill-c" : "tiling-preview-fill-a",
            );
        }
    }
}

function addOctagonSquare(svg: SVGSVGElement): void {
    forEachPoint([[28, 24], [64, 48], [98, 24]], (x, y, index) => {
        addRegularPolygon(svg, 8, x, y, 17, index % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-c", Math.PI / 8);
    });
    forEachPoint([[50, 14], [76, 20], [38, 48], [86, 48]], (x, y, index) => {
        addRect(svg, x - 8, y - 8, 16, 16, index % 2 === 0 ? "tiling-preview-fill-b" : "tiling-preview-fill-d");
    });
}

function addTrihexagonal(svg: SVGSVGElement): void {
    forEachPoint([[28, 36], [68, 24], [92, 46]], (x, y, index) => {
        addRegularPolygon(svg, 6, x, y, 15, index === 1 ? "tiling-preview-fill-c" : "tiling-preview-fill-a", Math.PI / 6);
    });
    forEachPolygon([
        [[42, 22], [58, 14], [56, 32]],
        [[44, 46], [58, 32], [64, 50]],
        [[78, 14], [94, 20], [80, 31]],
        [[74, 42], [88, 30], [94, 48]],
        [[14, 24], [28, 12], [30, 30]],
    ], (points, index) => {
        addPolygon(svg, points, index % 2 === 0 ? "tiling-preview-fill-b" : "tiling-preview-fill-d");
    });
}

function addDodecagonTriangle(svg: SVGSVGElement): void {
    forEachPoint([[34, 36], [86, 36]], (x, y, index) => {
        addRegularPolygon(svg, 12, x, y, 20, index === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-c", Math.PI / 12);
    });
    forEachPoint([[60, 17], [60, 55], [14, 36], [106, 36]], (x, y, index) => {
        addRegularPolygon(svg, index < 2 ? 4 : 3, x, y, 10, index % 2 === 0 ? "tiling-preview-fill-b" : "tiling-preview-fill-d", Math.PI / 4);
    });
}

function addHexSquareTriangle(svg: SVGSVGElement): void {
    addRegularPolygon(svg, 6, 60, 36, 19, "tiling-preview-fill-a", Math.PI / 6);
    forEachPoint([[22, 18], [28, 52], [92, 18], [96, 52]], (x, y, index) => {
        addRect(svg, x - 9, y - 9, 18, 18, index % 2 === 0 ? "tiling-preview-fill-b" : "tiling-preview-fill-d");
    });
    forEachPolygon([
        [[40, 16], [52, 4], [56, 23]],
        [[42, 56], [56, 49], [52, 69]],
        [[78, 14], [68, 28], [88, 28]],
        [[76, 58], [88, 45], [94, 63]],
    ], (points, index) => {
        addPolygon(svg, points, index % 2 === 0 ? "tiling-preview-fill-c" : "tiling-preview-fill-a");
    });
}

function addDodecagonHexSquare(svg: SVGSVGElement): void {
    addRegularPolygon(svg, 12, 60, 36, 20, "tiling-preview-fill-a", Math.PI / 12);
    addRegularPolygon(svg, 6, 24, 36, 14, "tiling-preview-fill-c", Math.PI / 6);
    addRegularPolygon(svg, 6, 96, 36, 14, "tiling-preview-fill-c", Math.PI / 6);
    forEachPoint([[40, 13], [80, 13], [40, 59], [80, 59]], (x, y, index) => {
        addRect(svg, x - 7, y - 7, 14, 14, index % 2 === 0 ? "tiling-preview-fill-b" : "tiling-preview-fill-d");
    });
}

function addSnubSquare(svg: SVGSVGElement): void {
    forEachPoint([[22, 18], [52, 18], [82, 18], [37, 48], [67, 48], [97, 48]], (x, y, index) => {
        addRect(svg, x - 9, y - 9, 18, 18, index % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-c");
        addPolygon(svg, [[x + 9, y - 9], [x + 24, y - 4], [x + 9, y + 9]], "tiling-preview-fill-b");
        addPolygon(svg, [[x - 9, y + 9], [x - 23, y + 4], [x - 9, y - 9]], "tiling-preview-fill-d");
    });
}

function addElongatedTriangular(svg: SVGSVGElement): void {
    for (let column = 0; column < 5; column += 1) {
        const x = 10 + (column * 22);
        addRect(svg, x, 24, 20, 18, column % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-c");
        addPolygon(svg, [[x, 24], [x + 10, 7], [x + 20, 24]], "tiling-preview-fill-b");
        addPolygon(svg, [[x, 42], [x + 10, 63], [x + 20, 42]], "tiling-preview-fill-d");
    }
}

function addSnubTrihexagonal(svg: SVGSVGElement): void {
    addRegularPolygon(svg, 6, 30, 36, 16, "tiling-preview-fill-a", Math.PI / 6);
    addRegularPolygon(svg, 6, 82, 36, 16, "tiling-preview-fill-c", Math.PI / 6);
    forEachPolygon([
        [[48, 18], [64, 10], [62, 30]],
        [[48, 54], [62, 42], [66, 62]],
        [[12, 17], [28, 8], [24, 28]],
        [[98, 20], [112, 31], [94, 36]],
        [[99, 52], [88, 38], [112, 38]],
        [[54, 36], [68, 26], [69, 48]],
    ], (points, index) => {
        addPolygon(svg, points, index % 2 === 0 ? "tiling-preview-fill-b" : "tiling-preview-fill-d");
    });
}

function addPentagonal(svg: SVGSVGElement): void {
    forEachPoint([[20, 22], [48, 18], [76, 22], [104, 18], [34, 52], [64, 50], [94, 52]], (x, y, index) => {
        addRegularPolygon(
            svg,
            5,
            x,
            y,
            13,
            previewFill(index, ["tiling-preview-fill-a", "tiling-preview-fill-b", "tiling-preview-fill-c"]),
            (Math.PI / 5) + (index % 2 === 0 ? 0 : Math.PI),
        );
    });
}

function addRhombille(svg: SVGSVGElement): void {
    for (let row = 0; row < 3; row += 1) {
        for (let column = 0; column < 4; column += 1) {
            const x = 12 + (column * 27) + ((row % 2) * 12);
            const y = 15 + (row * 19);
            addPolygon(svg, [[x, y], [x + 14, y - 8], [x + 28, y], [x + 14, y + 8]], (row + column) % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-b");
            addPolygon(svg, [[x, y], [x + 14, y + 8], [x + 14, y + 24], [x, y + 16]], "tiling-preview-fill-c");
        }
    }
}

function addDeltoid(svg: SVGSVGElement): void {
    forEachPoint([[24, 24], [56, 22], [88, 24], [38, 50], [72, 50], [104, 50]], (x, y, index) => {
        addPolygon(svg, [[x, y - 16], [x + 14, y], [x, y + 10], [x - 14, y]], index % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-c");
        addPolygon(svg, [[x + 14, y], [x + 27, y - 8], [x + 29, y + 10], [x, y + 10]], index % 2 === 0 ? "tiling-preview-fill-b" : "tiling-preview-fill-d");
    });
}

function addTetrakisSquare(svg: SVGSVGElement): void {
    forEachPoint([[15, 8], [49, 8], [83, 8], [15, 40], [49, 40], [83, 40]], (x, y, index) => {
        const center: Point = [x + 16, y + 16];
        addPolygon(svg, [[x, y], [x + 32, y], center], "tiling-preview-fill-a");
        addPolygon(svg, [[x + 32, y], [x + 32, y + 32], center], index % 2 === 0 ? "tiling-preview-fill-b" : "tiling-preview-fill-c");
        addPolygon(svg, [[x + 32, y + 32], [x, y + 32], center], "tiling-preview-fill-d");
        addPolygon(svg, [[x, y + 32], [x, y], center], "tiling-preview-fill-c");
    });
}

function addTriakisTriangular(svg: SVGSVGElement): void {
    forEachPoint([[32, 28], [72, 28], [52, 58], [94, 58]], (x, y, index) => {
        const top: Point = [x, y - 22];
        const left: Point = [x - 22, y + 14];
        const right: Point = [x + 22, y + 14];
        const center: Point = [x, y + 2];
        addPolygon(svg, [top, left, center], "tiling-preview-fill-a");
        addPolygon(svg, [left, right, center], index % 2 === 0 ? "tiling-preview-fill-b" : "tiling-preview-fill-d");
        addPolygon(svg, [right, top, center], "tiling-preview-fill-c");
    });
}

function addKiteDart(svg: SVGSVGElement): void {
    const center: Point = [60, 36];
    for (let index = 0; index < 10; index += 1) {
        const angle = (-Math.PI / 2) + ((Math.PI * 2 * index) / 10);
        const nextAngle = (-Math.PI / 2) + ((Math.PI * 2 * (index + 1)) / 10);
        const outerA: Point = [60 + (Math.cos(angle) * 30), 36 + (Math.sin(angle) * 30)];
        const outerB: Point = [60 + (Math.cos(nextAngle) * 30), 36 + (Math.sin(nextAngle) * 30)];
        const inner: Point = [60 + (Math.cos(angle + (Math.PI / 10)) * 12), 36 + (Math.sin(angle + (Math.PI / 10)) * 12)];
        addPolygon(svg, [center, outerA, inner, outerB], index % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-c");
    }
}

function addRhombStar(svg: SVGSVGElement): void {
    const center: Point = [60, 36];
    for (let index = 0; index < 8; index += 1) {
        const angle = (-Math.PI / 2) + ((Math.PI * 2 * index) / 8);
        const nextAngle = (-Math.PI / 2) + ((Math.PI * 2 * (index + 1)) / 8);
        const outerA: Point = [60 + (Math.cos(angle) * 31), 36 + (Math.sin(angle) * 31)];
        const outerB: Point = [60 + (Math.cos(nextAngle) * 31), 36 + (Math.sin(nextAngle) * 31)];
        const mid: Point = [60 + (Math.cos(angle + (Math.PI / 8)) * 18), 36 + (Math.sin(angle + (Math.PI / 8)) * 18)];
        addPolygon(svg, [center, outerA, mid, outerB], index % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-b");
    }
    addRegularPolygon(svg, 8, 60, 36, 10, "tiling-preview-fill-d", Math.PI / 8);
}

function addMonotile(svg: SVGSVGElement): void {
    const shape: Point[] = [[0, -15], [13, -9], [17, 5], [7, 16], [-8, 14], [-17, 2], [-12, -12]];
    forEachPoint([[24, 24], [58, 19], [92, 25], [40, 52], [78, 52]], (x, y, index) => {
        addPolygon(
            svg,
            shape.map(([shapeX, shapeY]) => [x + shapeX, y + shapeY] as const),
            previewFill(index),
        );
    });
}

function addTaylorSocolar(svg: SVGSVGElement): void {
    forEachPoint([[26, 24], [60, 36], [94, 24], [26, 58], [94, 58]], (x, y, index) => {
        addRegularPolygon(svg, 6, x, y, 15, index % 2 === 0 ? "tiling-preview-fill-a" : "tiling-preview-fill-c", Math.PI / 6);
        addLine(svg, [x - 13, y], [x + 13, y]);
        addLine(svg, [x - 6, y - 10], [x + 6, y + 10]);
    });
}

function addSphinx(svg: SVGSVGElement): void {
    const shape: Point[] = [[0, 0], [24, 0], [24, 14], [12, 14], [12, 28], [0, 28], [-12, 14]];
    forEachPoint([[24, 14], [62, 10], [96, 16], [42, 44], [80, 42]], (x, y, index) => {
        addPolygon(
            svg,
            shape.map(([shapeX, shapeY]) => [x + shapeX, y + shapeY] as const),
            previewFill(index, ["tiling-preview-fill-a", "tiling-preview-fill-b", "tiling-preview-fill-c"]),
        );
    });
}

function addChair(svg: SVGSVGElement): void {
    const shape: Point[] = [[0, 0], [28, 0], [28, 12], [12, 12], [12, 28], [0, 28]];
    forEachPoint([[18, 10], [54, 8], [88, 12], [34, 42], [72, 40]], (x, y, index) => {
        addPolygon(
            svg,
            shape.map(([shapeX, shapeY]) => [x + shapeX, y + shapeY] as const),
            previewFill(index),
        );
    });
}

function addTriangleFan(svg: SVGSVGElement): void {
    forEachPoint([[32, 36], [72, 34], [94, 48]], (x, y, clusterIndex) => {
        for (let index = 0; index < 6; index += 1) {
            const angle = (-Math.PI / 2) + ((Math.PI * 2 * index) / 6);
            const nextAngle = (-Math.PI / 2) + ((Math.PI * 2 * (index + 1)) / 6);
            addPolygon(
                svg,
                [
                    [x, y],
                    [x + (Math.cos(angle) * 19), y + (Math.sin(angle) * 19)],
                    [x + (Math.cos(nextAngle) * 19), y + (Math.sin(nextAngle) * 19)],
                ],
                previewFill(index + clusterIndex, ["tiling-preview-fill-a", "tiling-preview-fill-b", "tiling-preview-fill-c"]),
            );
        }
    });
}

function addPinwheel(svg: SVGSVGElement): void {
    addTriangleGrid(svg);
    const center: Point = [60, 36];
    for (let index = 0; index < 5; index += 1) {
        const angle = (-Math.PI / 2) + ((Math.PI * 2 * index) / 5);
        const nextAngle = angle + (Math.PI * 0.43);
        const far: Point = [60 + (Math.cos(angle) * 34), 36 + (Math.sin(angle) * 25)];
        const side: Point = [60 + (Math.cos(nextAngle) * 16), 36 + (Math.sin(nextAngle) * 27)];
        addPolygon(svg, [center, far, side], previewFill(index));
    }
}

const BUILDERS_BY_KEY: Readonly<Record<string, PreviewBuilder>> = {
    square: addSquareGrid,
    hex: addHexGrid,
    triangle: addTriangleGrid,
    "archimedean-4-8-8": addOctagonSquare,
    "trihexagonal-3-6-3-6": addTrihexagonal,
    "archimedean-3-12-12": addDodecagonTriangle,
    "archimedean-3-4-6-4": addHexSquareTriangle,
    "archimedean-4-6-12": addDodecagonHexSquare,
    "archimedean-3-3-4-3-4": addSnubSquare,
    "archimedean-3-3-3-4-4": addElongatedTriangular,
    "archimedean-3-3-3-3-6": addSnubTrihexagonal,
    "cairo-pentagonal": addPentagonal,
    rhombille: addRhombille,
    "deltoidal-trihexagonal": addDeltoid,
    "deltoidal-hexagonal": addDeltoid,
    "snub-square-dual": addPentagonal,
    "tetrakis-square": addTetrakisSquare,
    "triakis-triangular": addTriakisTriangular,
    "prismatic-pentagonal": addPentagonal,
    "floret-pentagonal": addPentagonal,
    "penrose-p2-kite-dart": addKiteDart,
    "penrose-p3-rhombs": addRhombStar,
    "penrose-p3-rhombs-vertex": addRhombStar,
    "ammann-beenker": addRhombStar,
    spectre: addMonotile,
    "hat-monotile": addMonotile,
    "taylor-socolar": addTaylorSocolar,
    sphinx: addSphinx,
    chair: addChair,
    "robinson-triangles": addTriangleFan,
    "tuebingen-triangle": addTriangleFan,
    "dodecagonal-square-triangle": addDodecagonTriangle,
    shield: addMonotile,
    pinwheel: addPinwheel,
};

function builderForOption(option: TopologyOption): PreviewBuilder {
    return BUILDERS_BY_KEY[option.previewKey]
        || BUILDERS_BY_KEY[option.value]
        || addRhombille;
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
    builderForOption(option)(svg);
    return svg;
}
