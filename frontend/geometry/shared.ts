import { buildRegularPreviewTopology } from "./preview-topology.js";
import type { ViewportDimensions } from "../types/controller.js";
import type { TopologyPayload } from "../types/domain.js";
import type { AppState } from "../types/state.js";
import type { GeometryViewportPreviewArgs, GridMetrics } from "../types/rendering.js";

export const DEFAULT_GEOMETRY = "square";
export const MIN_GRID_DIMENSION = 5;
export const MAX_GRID_DIMENSION = 250;
export const DEFAULT_GRID_DIMENSIONS = { width: 30, height: 20 };
export const MAX_MIXED_VIEWPORT_CELL_COUNT = 6000;
export const MIN_RENDER_CELL_SIZE = 0.25;
export const MAX_RENDER_CELL_SIZE = 240;

export function getCellGap(cellSize: number): number {
    return cellSize <= 6 ? 0 : 1;
}

export function clampGridDimension(value: number): number {
    return Math.min(MAX_GRID_DIMENSION, Math.max(MIN_GRID_DIMENSION, value));
}

export function squareGridMetrics(width: number, height: number, cellSize: number): GridMetrics {
    const gap = getCellGap(cellSize);
    const pitch = cellSize + gap;
    if (width === 0 || height === 0) {
        return {
            geometry: "square",
            width,
            height,
            cellSize,
            gap,
            pitch,
            horizontalPitch: pitch,
            verticalPitch: pitch,
            cssWidth: 0,
            cssHeight: 0,
            xInset: gap,
            yInset: gap,
        };
    }

    return {
        geometry: "square",
        width,
        height,
        cellSize,
        gap,
        pitch,
        horizontalPitch: pitch,
        verticalPitch: pitch,
        cssWidth: (width * pitch) + gap,
        cssHeight: (height * pitch) + gap,
        xInset: gap,
        yInset: gap,
    };
}

export function hexGridMetrics(width: number, height: number, cellSize: number): GridMetrics {
    const gap = getCellGap(cellSize);
    const hexHeight = cellSize;
    const radius = hexHeight / 2;
    const hexWidth = Math.sqrt(3) * radius;
    const horizontalPitch = hexWidth + gap;
    const verticalPitch = (0.75 * hexHeight) + gap;
    const oddRowOffset = height > 1 ? hexWidth / 2 : 0;
    const xInset = (hexWidth / 2) + gap;
    const yInset = radius + gap;

    if (width === 0 || height === 0) {
        return {
            geometry: "hex",
            width,
            height,
            cellSize,
            gap,
            radius,
            hexWidth,
            hexHeight,
            horizontalPitch,
            verticalPitch,
            oddRowOffset,
            xInset,
            yInset,
            cssWidth: 0,
            cssHeight: 0,
        };
    }

    return {
        geometry: "hex",
        width,
        height,
        cellSize,
        gap,
        radius,
        hexWidth,
        hexHeight,
        horizontalPitch,
        verticalPitch,
        oddRowOffset,
        xInset,
        yInset,
        cssWidth: (2 * xInset) + ((width - 1) * horizontalPitch) + oddRowOffset,
        cssHeight: (2 * yInset) + ((height - 1) * verticalPitch),
    };
}

export function triangleGridMetrics(width: number, height: number, cellSize: number): GridMetrics {
    const triangleSide = cellSize;
    const triangleHeight = (Math.sqrt(3) * triangleSide) / 2;
    const horizontalPitch = triangleSide / 2;
    const verticalPitch = triangleHeight;
    const inset = 1;

    if (width === 0 || height === 0) {
        return {
            geometry: "triangle",
            width,
            height,
            cellSize,
            gap: 0,
            triangleSide,
            triangleHeight,
            horizontalPitch,
            verticalPitch,
            xInset: inset,
            yInset: inset,
            cssWidth: 0,
            cssHeight: 0,
        };
    }

    return {
        geometry: "triangle",
        width,
        height,
        cellSize,
        gap: 0,
        triangleSide,
        triangleHeight,
        horizontalPitch,
        verticalPitch,
        xInset: inset,
        yInset: inset,
        cssWidth: (2 * inset) + triangleSide + ((width - 1) * horizontalPitch),
        cssHeight: (2 * inset) + (height * triangleHeight),
    };
}

export function fitGridDimension(
    candidate: number,
    fits: (value: number) => boolean,
    minimumDimension = MIN_GRID_DIMENSION,
): number {
    const minimum = Math.min(MAX_GRID_DIMENSION, Math.max(1, minimumDimension));
    let value = Math.min(MAX_GRID_DIMENSION, Math.max(minimum, candidate));
    while (value > minimum && !fits(value)) {
        value -= 1;
    }
    while (value < MAX_GRID_DIMENSION && fits(value + 1)) {
        value += 1;
    }
    return value;
}

function binarySearchRenderCellSize(
    low: number,
    high: number,
    fits: (value: number) => boolean,
    iterations = 14,
): number {
    let fitLow = low;
    let missHigh = high;
    for (let index = 0; index < iterations; index += 1) {
        const midpoint = (fitLow + missHigh) / 2;
        if (fits(midpoint)) {
            fitLow = midpoint;
        } else {
            missHigh = midpoint;
        }
    }
    return fitLow;
}

export function fitRenderCellSizeWithMetrics({
    viewportWidth,
    viewportHeight,
    width,
    height,
    topology = null,
    fallbackCellSize,
    buildMetrics,
}: {
    viewportWidth: number;
    viewportHeight: number;
    width: number;
    height: number;
    topology?: TopologyPayload | null;
    fallbackCellSize: number;
    buildMetrics: (args: {
        width: number;
        height: number;
        topology: TopologyPayload | null;
        cellSize: number;
    }) => GridMetrics;
}): number {
    if (viewportWidth <= 0 || viewportHeight <= 0 || typeof buildMetrics !== "function") {
        return fallbackCellSize;
    }

    const fits = (candidateCellSize: number): boolean => {
        const metrics = buildMetrics({
            width,
            height,
            topology,
            cellSize: candidateCellSize,
        });
        return metrics.cssWidth <= viewportWidth && metrics.cssHeight <= viewportHeight;
    };

    if (!fits(MIN_RENDER_CELL_SIZE)) {
        return MIN_RENDER_CELL_SIZE;
    }

    const initialHigh = Math.max(
        MIN_RENDER_CELL_SIZE,
        Math.min(MAX_RENDER_CELL_SIZE, Number(fallbackCellSize) || MIN_RENDER_CELL_SIZE),
    );

    if (!fits(initialHigh)) {
        return binarySearchRenderCellSize(MIN_RENDER_CELL_SIZE, initialHigh, fits);
    }

    let fittedLow = initialHigh;
    let candidateHigh = initialHigh;
    while (candidateHigh < MAX_RENDER_CELL_SIZE) {
        const nextHigh = Math.min(MAX_RENDER_CELL_SIZE, Math.max(candidateHigh + 1, candidateHigh * 1.5));
        if (nextHigh === candidateHigh) {
            break;
        }
        if (!fits(nextHigh)) {
            return binarySearchRenderCellSize(fittedLow, nextHigh, fits);
        }
        fittedLow = nextHigh;
        candidateHigh = nextHigh;
    }

    return fittedLow;
}

export function constrainMixedViewportDimensions(
    dimensions: ViewportDimensions,
    cellSize: number,
    countCells: (width: number, height: number) => number,
    maxCellCount = MAX_MIXED_VIEWPORT_CELL_COUNT,
    minimumDimension = MIN_GRID_DIMENSION,
): ViewportDimensions {
    void cellSize;
    const minimum = Math.min(MAX_GRID_DIMENSION, Math.max(1, minimumDimension));
    let width = Math.min(MAX_GRID_DIMENSION, Math.max(minimum, dimensions.width));
    let height = Math.min(MAX_GRID_DIMENSION, Math.max(minimum, dimensions.height));
    const initialCount = countCells(width, height);

    if (initialCount <= maxCellCount) {
        return { width, height };
    }

    const scale = Math.sqrt(maxCellCount / initialCount);
    width = clampGridDimension(Math.floor(width * scale));
    height = clampGridDimension(Math.floor(height * scale));

    while (
        countCells(width, height) > maxCellCount
        && (width > minimum || height > minimum)
    ) {
        if (width >= height && width > minimum) {
            width -= 1;
            continue;
        }
        if (height > minimum) {
            height -= 1;
            continue;
        }
        width -= 1;
    }

    return { width, height };
}

export function applyRegularViewportPreview({
    geometry,
    state,
    dimensions,
    currentTopology,
    currentCellStates,
    buildPreviewCellStatesById,
    setViewportPreview,
    clearViewportPreview,
}: GeometryViewportPreviewArgs & {
    geometry: string;
}): { applied: boolean; renderGrid: boolean } {
    const nextTopology = buildRegularPreviewTopology(geometry, {
        ...state.topologySpec,
        width: dimensions.width,
        height: dimensions.height,
    });
    if (!nextTopology) {
        if (typeof clearViewportPreview === "function") {
            clearViewportPreview(state);
        }
        return { applied: false, renderGrid: false };
    }

    if (typeof setViewportPreview === "function") {
        setViewportPreview(
            state,
            nextTopology,
            typeof buildPreviewCellStatesById === "function"
                ? buildPreviewCellStatesById(currentTopology, currentCellStates, nextTopology)
                : {},
            state.topologyRevision,
        );
    }

    return { applied: true, renderGrid: true };
}

export function applyMixedViewportPreview({
    state,
    dimensions,
}: Pick<GeometryViewportPreviewArgs, "state" | "dimensions">): { applied: boolean; renderGrid: boolean } {
    const nextState = state as AppState;
    nextState.width = dimensions.width;
    nextState.height = dimensions.height;
    return { applied: true, renderGrid: false };
}
