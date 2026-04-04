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
    resize(metrics: GridMetrics, dpr: number, borderRadius: string): CanvasSurfaceMetrics;
    restoreCommittedSurface(metrics: CanvasSurfaceMetrics): void;
}

export function createCanvasSurface(canvas: HTMLCanvasElement): CanvasSurface {
    const contextCandidate = canvas.getContext("2d");
    const committedCanvas = document.createElement("canvas");
    const committedContextCandidate = committedCanvas.getContext("2d");
    if (!contextCandidate || !committedContextCandidate) {
        throw new Error("Canvas 2D rendering context is unavailable.");
    }
    const context = contextCandidate;
    const committedContext = committedContextCandidate;

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

        return {
            ...metrics,
            pixelWidth: canvas.width,
            pixelHeight: canvas.height,
            dpr,
        };
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
        resize,
        restoreCommittedSurface,
    };
}
