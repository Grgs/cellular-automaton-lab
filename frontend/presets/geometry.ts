import type { CoordinateCell } from "../types/editor.js";

const HEX_HEIGHT = 1.0;
const HEX_RADIUS = HEX_HEIGHT / 2;
const HEX_WIDTH = Math.sqrt(3) * HEX_RADIUS;
const HEX_ROW_PITCH = 0.75;

const HEX_NEIGHBOR_OFFSETS_EVEN_ROW: readonly (readonly [number, number])[] = Object.freeze([
    [-1, -1],
    [0, -1],
    [1, 0],
    [0, 1],
    [-1, 1],
    [-1, 0],
]);

const HEX_NEIGHBOR_OFFSETS_ODD_ROW: readonly (readonly [number, number])[] = Object.freeze([
    [0, -1],
    [1, -1],
    [1, 0],
    [1, 1],
    [0, 1],
    [-1, 0],
]);

function oddRNeighborOffsets(y: number): readonly (readonly [number, number])[] {
    return y % 2 === 1 ? HEX_NEIGHBOR_OFFSETS_ODD_ROW : HEX_NEIGHBOR_OFFSETS_EVEN_ROW;
}

function keyForCell(cell: CoordinateCell): string {
    return `${cell.x}:${cell.y}`;
}

export function pointyHexCellCenter(x: number, y: number): { x: number; y: number } {
    return {
        x: x * HEX_WIDTH + (y % 2) * (HEX_WIDTH / 2),
        y: y * HEX_ROW_PITCH,
    };
}

export function pointyHexGridCenter(width: number, height: number): { x: number; y: number } {
    if (width <= 0 || height <= 0) {
        return { x: 0, y: 0 };
    }

    const maxCenterX = (width - 1) * HEX_WIDTH + (height > 1 ? HEX_WIDTH / 2 : 0);
    const maxCenterY = (height - 1) * HEX_ROW_PITCH;
    return {
        x: maxCenterX / 2,
        y: maxCenterY / 2,
    };
}

export function pointyHexMaxRadius(width: number, height: number): number {
    if (width <= 0 || height <= 0) {
        return 1;
    }

    const gridCenter = pointyHexGridCenter(width, height);
    const corners = [
        pointyHexCellCenter(0, 0),
        pointyHexCellCenter(width - 1, 0),
        pointyHexCellCenter(0, height - 1),
        pointyHexCellCenter(width - 1, height - 1),
    ];

    return Math.max(
        ...corners.map((corner) => Math.hypot(corner.x - gridCenter.x, corner.y - gridCenter.y)),
        1,
    );
}

export function squareCellCenter(x: number, y: number): { x: number; y: number } {
    return { x, y };
}

export function squareGridCenter(width: number, height: number): { x: number; y: number } {
    return {
        x: (width - 1) / 2,
        y: (height - 1) / 2,
    };
}

export function squareMaxRadius(width: number, height: number): number {
    if (width <= 0 || height <= 0) {
        return 1;
    }
    const gridCenter = squareGridCenter(width, height);
    const corners = [
        squareCellCenter(0, 0),
        squareCellCenter(width - 1, 0),
        squareCellCenter(0, height - 1),
        squareCellCenter(width - 1, height - 1),
    ];
    return Math.max(
        ...corners.map((corner) => Math.hypot(corner.x - gridCenter.x, corner.y - gridCenter.y)),
        1,
    );
}

export function oddRNeighbors(x: number, y: number): CoordinateCell[] {
    return oddRNeighborOffsets(y).map(([dx, dy]) => ({ x: x + dx, y: y + dy }));
}

export function hexCellsAtDistance(
    centerX: number,
    centerY: number,
    distance: number,
): CoordinateCell[] {
    const origin = { x: centerX, y: centerY };
    let frontier: CoordinateCell[] = [origin];
    const visited = new Set([keyForCell(origin)]);

    for (let step = 0; step < distance; step += 1) {
        const nextFrontier: CoordinateCell[] = [];
        frontier.forEach((cell) => {
            oddRNeighbors(cell.x, cell.y).forEach((neighbor) => {
                const key = keyForCell(neighbor);
                if (visited.has(key)) {
                    return;
                }
                visited.add(key);
                nextFrontier.push(neighbor);
            });
        });
        frontier = nextFrontier;
    }

    return frontier;
}
