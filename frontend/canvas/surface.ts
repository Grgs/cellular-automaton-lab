import type { GridMetrics } from "../types/rendering.js";

export interface CanvasSurfaceMetrics extends GridMetrics {
    pixelWidth: number;
    pixelHeight: number;
    dpr: number;
}

export interface CanvasSurface {
    context: CanvasRenderingContext2D;
    committedCanvas: HTMLCanvasElement;
    committedContext: CanvasRenderingContext2D;
    incrementalCanvas: HTMLCanvasElement;
    incrementalContext: CanvasRenderingContext2D;
    resize(metrics: GridMetrics, dpr: number, borderRadius: string): CanvasSurfaceMetrics;
    prepareIncrementalSurface(metrics: CanvasSurfaceMetrics): CanvasRenderingContext2D;
    commitIncrementalSurface(
        bounds: { minX: number; maxX: number; minY: number; maxY: number },
        metrics: CanvasSurfaceMetrics,
    ): void;
    restoreCommittedSurface(metrics: CanvasSurfaceMetrics): void;
}

export function createCanvasSurface(canvas: HTMLCanvasElement): CanvasSurface {
    const contextCandidate = canvas.getContext("2d");
    const committedCanvas = document.createElement("canvas");
    const committedContextCandidate = committedCanvas.getContext("2d");
    const incrementalCanvas = document.createElement("canvas");
    const incrementalContextCandidate = incrementalCanvas.getContext("2d");
    if (!contextCandidate || !committedContextCandidate || !incrementalContextCandidate) {
        throw new Error("Canvas 2D rendering context is unavailable.");
    }
    const context = contextCandidate;
    const committedContext = committedContextCandidate;
    const incrementalContext = incrementalContextCandidate;

    function resize(metrics: GridMetrics, dpr: number, borderRadius: string): CanvasSurfaceMetrics {
        const pixelWidth = Math.max(1, Math.round(metrics.cssWidth * dpr));
        const pixelHeight = Math.max(1, Math.round(metrics.cssHeight * dpr));

        canvas.style.width = `${metrics.cssWidth}px`;
        canvas.style.height = `${metrics.cssHeight}px`;
        canvas.style.borderRadius = borderRadius;
        if (canvas.width !== pixelWidth) {
            canvas.width = pixelWidth;
        }
        if (canvas.height !== pixelHeight) {
            canvas.height = pixelHeight;
        }
        if (committedCanvas.width !== pixelWidth) {
            committedCanvas.width = pixelWidth;
        }
        if (committedCanvas.height !== pixelHeight) {
            committedCanvas.height = pixelHeight;
        }
        if (incrementalCanvas.width !== pixelWidth) {
            incrementalCanvas.width = pixelWidth;
        }
        if (incrementalCanvas.height !== pixelHeight) {
            incrementalCanvas.height = pixelHeight;
        }
        return {
            ...metrics,
            pixelWidth: canvas.width,
            pixelHeight: canvas.height,
            dpr,
        };
    }

    function prepareIncrementalSurface(metrics: CanvasSurfaceMetrics): CanvasRenderingContext2D {
        incrementalContext.setTransform(1, 0, 0, 1, 0, 0);
        incrementalContext.clearRect(0, 0, incrementalCanvas.width, incrementalCanvas.height);
        incrementalContext.setTransform(metrics.dpr, 0, 0, metrics.dpr, 0, 0);
        return incrementalContext;
    }

    function commitIncrementalSurface(
        bounds: { minX: number; maxX: number; minY: number; maxY: number },
        metrics: CanvasSurfaceMetrics,
    ): void {
        const minX = Math.max(0, Math.floor(bounds.minX * metrics.dpr));
        const maxX = Math.min(committedCanvas.width, Math.ceil(bounds.maxX * metrics.dpr));
        const minY = Math.max(0, Math.floor(bounds.minY * metrics.dpr));
        const maxY = Math.min(committedCanvas.height, Math.ceil(bounds.maxY * metrics.dpr));
        const width = Math.max(0, maxX - minX);
        const height = Math.max(0, maxY - minY);
        if (width === 0 || height === 0) {
            return;
        }
        committedContext.setTransform(1, 0, 0, 1, 0, 0);
        committedContext.clearRect(minX, minY, width, height);
        committedContext.drawImage(
            incrementalCanvas,
            minX,
            minY,
            width,
            height,
            minX,
            minY,
            width,
            height,
        );
        committedContext.setTransform(metrics.dpr, 0, 0, metrics.dpr, 0, 0);
    }

    function restoreCommittedSurface(metrics: CanvasSurfaceMetrics): void {
        context.setTransform(1, 0, 0, 1, 0, 0);
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(committedCanvas, 0, 0);
        context.setTransform(metrics.dpr, 0, 0, metrics.dpr, 0, 0);
    }

    return {
        context,
        committedCanvas,
        committedContext,
        incrementalCanvas,
        incrementalContext,
        resize,
        prepareIncrementalSurface,
        commitIncrementalSurface,
        restoreCommittedSurface,
    };
}
