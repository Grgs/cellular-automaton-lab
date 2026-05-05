import { centerPattern, clamp, inBounds } from "./core.js";
import type { CartesianSeedCell } from "../types/domain.js";

function createSquareCellWriter(width: number, height: number): {
    setCell(x: number, y: number, state: number): void;
    drawHorizontal(x1: number, x2: number, y: number, state: number): void;
    drawVertical(x: number, y1: number, y2: number, state: number): void;
    drawStairLine(startX: number, startY: number, endX: number, endY: number, state: number): void;
    toCells(): CartesianSeedCell[];
} {
    const cellMap = new Map<string, CartesianSeedCell>();

    function setCell(x: number, y: number, state: number): void {
        if (!inBounds(x, y, width, height)) {
            return;
        }
        cellMap.set(`${x}:${y}`, { x, y, state });
    }

    function drawHorizontal(x1: number, x2: number, y: number, state: number): void {
        const start = Math.min(x1, x2);
        const end = Math.max(x1, x2);
        for (let x = start; x <= end; x += 1) {
            setCell(x, y, state);
        }
    }

    function drawVertical(x: number, y1: number, y2: number, state: number): void {
        const start = Math.min(y1, y2);
        const end = Math.max(y1, y2);
        for (let y = start; y <= end; y += 1) {
            setCell(x, y, state);
        }
    }

    function drawStairLine(startX: number, startY: number, endX: number, endY: number, state: number): void {
        let currentX = startX;
        let currentY = startY;
        setCell(currentX, currentY, state);

        while (currentX !== endX || currentY !== endY) {
            if (currentX < endX) {
                currentX += 1;
            } else if (currentX > endX) {
                currentX -= 1;
            }
            setCell(currentX, currentY, state);

            if (currentY < endY) {
                currentY += 1;
            } else if (currentY > endY) {
                currentY -= 1;
            }
            setCell(currentX, currentY, state);
        }
    }

    return {
        setCell,
        drawHorizontal,
        drawVertical,
        drawStairLine,
        toCells() {
            return Array.from(cellMap.values());
        },
    };
}

export function buildWireworldSignalLoop(width: number, height: number): CartesianSeedCell[] {
    const margin = 2;
    const loopWidth = clamp(Math.floor(width * 0.56), 11, Math.max(11, width - (margin * 2)));
    const loopHeight = clamp(Math.floor(height * 0.52), 8, Math.max(8, height - (margin * 2)));
    const { offsetX: left, offsetY: top } = centerPattern(width, height, loopWidth, loopHeight);
    const right = left + loopWidth - 1;
    const bottom = top + loopHeight - 1;
    const midY = top + Math.floor(loopHeight / 2);
    const spurX = left + Math.max(3, Math.floor(loopWidth * 0.68));
    const writer = createSquareCellWriter(width, height);

    writer.drawHorizontal(left + 1, right - 1, top, 3);
    writer.drawHorizontal(left + 1, right - 1, bottom, 3);
    writer.drawVertical(left, top + 1, bottom - 1, 3);
    writer.drawVertical(right, top + 1, bottom - 1, 3);

    writer.drawHorizontal(left, right, midY, 3);
    writer.drawVertical(spurX, top + 2, bottom - 2, 3);
    writer.drawHorizontal(left + 2, spurX - 1, bottom - 2, 3);

    writer.setCell(left, midY + 1, 1);
    writer.setCell(left, midY + 2, 2);

    return writer.toCells();
}

export function buildWireworldDiodeDemo(width: number, height: number): CartesianSeedCell[] {
    const margin = 2;
    const patternWidth = clamp(Math.floor(width * 0.64), 15, Math.max(15, width - (margin * 2)));
    const patternHeight = clamp(Math.floor(height * 0.58), 10, Math.max(10, height - (margin * 2)));
    const { offsetX: left, offsetY: top } = centerPattern(width, height, patternWidth, patternHeight);
    const right = left + patternWidth - 1;
    const gateCenterX = left + Math.floor(patternWidth * 0.58);
    const gateCenterY = top + Math.floor(patternHeight / 2);
    const inputY = gateCenterY;
    const outputX = right - 2;
    const arm = Math.max(2, Math.floor(Math.min(patternWidth, patternHeight) / 4));
    const branchY = gateCenterY + arm;
    const writer = createSquareCellWriter(width, height);

    writer.drawHorizontal(left + 1, gateCenterX - arm - 1, inputY, 3);
    writer.drawHorizontal(gateCenterX + arm + 1, outputX, inputY, 3);

    writer.drawStairLine(gateCenterX - arm, gateCenterY, gateCenterX, gateCenterY - arm, 3);
    writer.drawStairLine(gateCenterX - arm, gateCenterY, gateCenterX, gateCenterY + arm, 3);
    writer.drawStairLine(gateCenterX, gateCenterY - arm, gateCenterX + arm, gateCenterY, 3);
    writer.drawStairLine(gateCenterX, gateCenterY + arm, gateCenterX + arm, gateCenterY, 3);

    writer.drawHorizontal(
        gateCenterX - Math.max(1, Math.floor(arm / 2)),
        gateCenterX + Math.max(1, Math.floor(arm / 2)),
        gateCenterY,
        3,
    );
    writer.drawVertical(gateCenterX + Math.max(1, Math.floor(arm / 2)), gateCenterY, branchY, 3);
    writer.drawHorizontal(gateCenterX - arm, gateCenterX + arm - 1, branchY, 3);

    writer.setCell(left + 1, inputY, 2);
    writer.setCell(left + 2, inputY, 1);

    return writer.toCells();
}
