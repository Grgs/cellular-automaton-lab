import { drawGestureOutlineLayer, drawHoverLayer, drawPreviewLayer, drawSelectionLayer } from "./render-layers.js";
import type { CanvasCommittedRenderSnapshot } from "./committed-renderer.js";
import { resolveRenderedCellColor } from "./render-style.js";
import type { TransientOverlaySnapshot } from "./transient-overlays.js";

export function drawTransientOverlaySnapshot(
    renderState: CanvasCommittedRenderSnapshot,
    overlaySnapshot: TransientOverlaySnapshot,
): void {
    const shared = {
        geometry: renderState.geometry,
        topology: renderState.topology,
        metrics: renderState.metrics,
        geometryCache: renderState.geometryCache,
        canvasColors: renderState.canvasColors,
        renderStyle: renderState.renderStyle,
        colorLookup: renderState.colorLookup,
    };

    if (overlaySnapshot.hoveredCell) {
        drawHoverLayer({
            context: renderState.context,
            ...shared,
            resolveRenderedCellColor,
            hoveredCell: overlaySnapshot.hoveredCell,
            cellStates: renderState.cellStates,
        });
    }

    if (overlaySnapshot.selectedCells.length > 0) {
        drawSelectionLayer({
            context: renderState.context,
            ...shared,
            resolveRenderedCellColor,
            selectedCells: overlaySnapshot.selectedCells,
            cellStates: renderState.cellStates,
        });
    }

    if (overlaySnapshot.previewCells.size > 0) {
        drawPreviewLayer({
            context: renderState.context,
            ...shared,
            resolveRenderedCellColor,
            previewCells: overlaySnapshot.previewCells,
        });
    }

    if (overlaySnapshot.gestureOutlineTone !== null && overlaySnapshot.gestureOutlineCells.length > 0) {
        drawGestureOutlineLayer({
            context: renderState.context,
            ...shared,
            resolveRenderedCellColor,
            outlinedCells: overlaySnapshot.gestureOutlineCells,
            tone: overlaySnapshot.gestureOutlineTone,
            cellStates: renderState.cellStates,
        });
    }
}
