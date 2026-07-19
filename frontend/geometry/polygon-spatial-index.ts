import type {
    PolygonGeometryCell,
    PolygonIntersectionBounds,
    PolygonSpatialIndex,
} from "../types/rendering.js";

const MIN_INDEXED_CELLS = 32;
const TARGET_CELLS_PER_BUCKET = 8;
// Avoid an adversarial overlap pattern multiplying one cell into most buckets.
// Those unusual fields keep the existing linear hit-test behavior instead.
const MAX_BUCKETS_PER_CELL = 64;

function clampBucketIndex(value: number, minimum: number, size: number, count: number): number {
    return Math.min(count - 1, Math.max(0, Math.floor((value - minimum) / size)));
}

export function buildPolygonSpatialIndex(
    cells: readonly PolygonGeometryCell[],
): PolygonSpatialIndex | null {
    if (cells.length < MIN_INDEXED_CELLS) {
        return null;
    }

    let minX = Number.POSITIVE_INFINITY;
    let maxX = Number.NEGATIVE_INFINITY;
    let minY = Number.POSITIVE_INFINITY;
    let maxY = Number.NEGATIVE_INFINITY;
    for (const cell of cells) {
        minX = Math.min(minX, cell.minX);
        maxX = Math.max(maxX, cell.maxX);
        minY = Math.min(minY, cell.minY);
        maxY = Math.max(maxY, cell.maxY);
    }

    const width = maxX - minX;
    const height = maxY - minY;
    if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
        return null;
    }

    const targetBucketCount = Math.max(1, Math.ceil(cells.length / TARGET_CELLS_PER_BUCKET));
    const aspectRatio = width / height;
    const columnCount = Math.min(
        targetBucketCount,
        Math.max(1, Math.round(Math.sqrt(targetBucketCount * aspectRatio))),
    );
    const rowCount = Math.max(1, Math.ceil(targetBucketCount / columnCount));
    const bucketWidth = width / columnCount;
    const bucketHeight = height / rowCount;
    const bucketRanges: Array<{
        minColumn: number;
        maxColumn: number;
        minRow: number;
        maxRow: number;
    }> = [];

    for (const cell of cells) {
        const minColumn = clampBucketIndex(cell.minX, minX, bucketWidth, columnCount);
        const maxColumn = clampBucketIndex(cell.maxX, minX, bucketWidth, columnCount);
        const minRow = clampBucketIndex(cell.minY, minY, bucketHeight, rowCount);
        const maxRow = clampBucketIndex(cell.maxY, minY, bucketHeight, rowCount);
        if ((maxColumn - minColumn + 1) * (maxRow - minRow + 1) > MAX_BUCKETS_PER_CELL) {
            return null;
        }
        bucketRanges.push({ minColumn, maxColumn, minRow, maxRow });
    }

    const buckets: PolygonGeometryCell[][] = Array.from(
        { length: columnCount * rowCount },
        () => [],
    );
    cells.forEach((cell, index) => {
        const range = bucketRanges[index];
        if (!range) {
            return;
        }
        for (let row = range.minRow; row <= range.maxRow; row += 1) {
            for (let column = range.minColumn; column <= range.maxColumn; column += 1) {
                buckets[row * columnCount + column]?.push(cell);
            }
        }
    });

    return {
        minX,
        maxX,
        minY,
        maxY,
        columnCount,
        rowCount,
        bucketWidth,
        bucketHeight,
        buckets,
        sourceIndexes: new Map(cells.map((cell, sourceIndex) => [cell, sourceIndex])),
    };
}

export function polygonSpatialIndexCandidates(
    index: PolygonSpatialIndex,
    x: number,
    y: number,
): readonly PolygonGeometryCell[] {
    if (x < index.minX || x > index.maxX || y < index.minY || y > index.maxY) {
        return [];
    }
    const column = clampBucketIndex(x, index.minX, index.bucketWidth, index.columnCount);
    const row = clampBucketIndex(y, index.minY, index.bucketHeight, index.rowCount);
    return index.buckets[row * index.columnCount + column] ?? [];
}

export function polygonSpatialIndexIntersectionCandidates(
    index: PolygonSpatialIndex,
    bounds: PolygonIntersectionBounds,
): readonly PolygonGeometryCell[] {
    if (
        !Number.isFinite(bounds.minX) ||
        !Number.isFinite(bounds.maxX) ||
        !Number.isFinite(bounds.minY) ||
        !Number.isFinite(bounds.maxY) ||
        bounds.minX > bounds.maxX ||
        bounds.minY > bounds.maxY ||
        bounds.maxX < index.minX ||
        bounds.minX > index.maxX ||
        bounds.maxY < index.minY ||
        bounds.minY > index.maxY
    ) {
        return [];
    }

    const minColumn = clampBucketIndex(
        Math.max(bounds.minX, index.minX),
        index.minX,
        index.bucketWidth,
        index.columnCount,
    );
    const maxColumn = clampBucketIndex(
        Math.min(bounds.maxX, index.maxX),
        index.minX,
        index.bucketWidth,
        index.columnCount,
    );
    const minRow = clampBucketIndex(
        Math.max(bounds.minY, index.minY),
        index.minY,
        index.bucketHeight,
        index.rowCount,
    );
    const maxRow = clampBucketIndex(
        Math.min(bounds.maxY, index.maxY),
        index.minY,
        index.bucketHeight,
        index.rowCount,
    );
    const candidates = new Set<PolygonGeometryCell>();
    for (let row = minRow; row <= maxRow; row += 1) {
        for (let column = minColumn; column <= maxColumn; column += 1) {
            for (const cell of index.buckets[row * index.columnCount + column] ?? []) {
                if (
                    cell.maxX >= bounds.minX &&
                    cell.minX <= bounds.maxX &&
                    cell.maxY >= bounds.minY &&
                    cell.minY <= bounds.maxY
                ) {
                    candidates.add(cell);
                }
            }
        }
    }

    return [...candidates].sort(
        (left, right) =>
            (index.sourceIndexes.get(left) ?? Number.MAX_SAFE_INTEGER) -
            (index.sourceIndexes.get(right) ?? Number.MAX_SAFE_INTEGER),
    );
}
