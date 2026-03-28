import type { CartesianSeedCell } from "../types/domain.js";

export function uniqueCells(cells: readonly CartesianSeedCell[]): CartesianSeedCell[] {
    const seen = new Set<string>();
    return cells.filter((cell) => {
        const key = `${cell.x}:${cell.y}`;
        if (seen.has(key)) {
            return false;
        }
        seen.add(key);
        return true;
    });
}

export function centerPattern(width: number, height: number, patternWidth: number, patternHeight: number): { offsetX: number; offsetY: number } {
    return {
        offsetX: Math.floor((width - patternWidth) / 2),
        offsetY: Math.floor((height - patternHeight) / 2),
    };
}

export function inBounds(x: number, y: number, width: number, height: number): boolean {
    return x >= 0 && x < width && y >= 0 && y < height;
}

export function clamp(value: number, minValue: number, maxValue: number): number {
    return Math.min(maxValue, Math.max(minValue, value));
}

export function buildAsciiSeedAt(
    width: number,
    height: number,
    rows: readonly string[],
    stateMap: Record<string, number>,
    offsetX: number,
    offsetY: number,
): CartesianSeedCell[] {
    const cells: CartesianSeedCell[] = [];

    rows.forEach((row, y) => {
        Array.from(row).forEach((token, x) => {
            const state = stateMap[token];
            if (state === undefined) {
                return;
            }
            const targetX = offsetX + x;
            const targetY = offsetY + y;
            if (!inBounds(targetX, targetY, width, height)) {
                return;
            }
            cells.push({ x: targetX, y: targetY, state });
        });
    });

    return cells;
}

export function buildCenteredAsciiSeed(
    width: number,
    height: number,
    rows: readonly string[],
    stateMap: Record<string, number>,
): CartesianSeedCell[] {
    const patternWidth = Math.max(...rows.map((row) => row.length), 0);
    const patternHeight = rows.length;
    const { offsetX, offsetY } = centerPattern(width, height, patternWidth, patternHeight);
    return buildAsciiSeedAt(width, height, rows, stateMap, offsetX, offsetY);
}

export function parseBinaryRle(patternRle: string): CartesianSeedCell[] {
    const cleanedRle = patternRle.replace(/\s+/g, "");
    const cells: CartesianSeedCell[] = [];
    let x = 0;
    let y = 0;
    let countBuffer = "";

    for (const token of cleanedRle) {
        if (token >= "0" && token <= "9") {
            countBuffer += token;
            continue;
        }

        const count = countBuffer === "" ? 1 : Number(countBuffer);
        countBuffer = "";

        if (token === "b") {
            x += count;
            continue;
        }
        if (token === "o") {
            for (let index = 0; index < count; index += 1) {
                cells.push({ x: x + index, y, state: 1 });
            }
            x += count;
            continue;
        }
        if (token === "$") {
            y += count;
            x = 0;
            continue;
        }
        if (token === "!") {
            break;
        }
    }

    return cells;
}

export function buildCenteredBinaryRleSeed(width: number, height: number, patternRle: string): CartesianSeedCell[] {
    const patternCells = parseBinaryRle(patternRle);
    if (patternCells.length === 0) {
        return [];
    }

    const patternWidth = Math.max(...patternCells.map((cell) => cell.x)) + 1;
    const patternHeight = Math.max(...patternCells.map((cell) => cell.y)) + 1;
    const { offsetX, offsetY } = centerPattern(width, height, patternWidth, patternHeight);

    return patternCells
        .map((cell) => ({
            x: cell.x + offsetX,
            y: cell.y + offsetY,
            state: cell.state,
        }))
        .filter((cell) => inBounds(cell.x, cell.y, width, height));
}
