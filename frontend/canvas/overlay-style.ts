import {
    DARK_HOVER_PALETTE_LUMINANCE_THRESHOLD,
    DARK_HOVER_STROKE_ALPHA,
    DARK_HOVER_TINT_ALPHA,
    DARK_SELECTION_TINT_ALPHA,
    LIGHT_SELECTION_TINT_ALPHA,
} from "./render-constants.js";
import { parseColorChannels, relativeLuminance, withAlpha } from "./theme-colors.js";
import type { CanvasColors, CanvasRenderStyle } from "../types/rendering.js";

type CanvasOverlayStyle = Pick<
    CanvasRenderStyle,
    | "hoverTintColor"
    | "hoverStrokeColor"
    | "selectionTintColor"
    | "selectionStrokeColor"
    | "gesturePaintStrokeColor"
    | "gestureEraseStrokeColor"
>;

function isDarkThemeHoverPalette(canvasColors: CanvasColors): boolean {
    const parsed = parseColorChannels(canvasColors.lineStrong);
    return parsed ? relativeLuminance(parsed) > DARK_HOVER_PALETTE_LUMINANCE_THRESHOLD : false;
}

export function resolveCanvasOverlayStyle(canvasColors: CanvasColors): CanvasOverlayStyle {
    const useDarkHoverPalette = isDarkThemeHoverPalette(canvasColors);
    return {
        hoverTintColor: useDarkHoverPalette
            ? withAlpha(
                  canvasColors.lineAperiodic || canvasColors.line || canvasColors.live,
                  DARK_HOVER_TINT_ALPHA,
              )
            : canvasColors.lineStrong,
        hoverStrokeColor: useDarkHoverPalette
            ? withAlpha(
                  canvasColors.lineAperiodic || canvasColors.line || canvasColors.live,
                  DARK_HOVER_STROKE_ALPHA,
              )
            : canvasColors.live,
        selectionTintColor: withAlpha(
            canvasColors.accent,
            useDarkHoverPalette ? DARK_SELECTION_TINT_ALPHA : LIGHT_SELECTION_TINT_ALPHA,
        ),
        selectionStrokeColor: canvasColors.accentStrong || canvasColors.accent,
        gesturePaintStrokeColor: canvasColors.accentStrong || canvasColors.accent,
        gestureEraseStrokeColor:
            canvasColors.lineAperiodic || canvasColors.lineStrong || canvasColors.line,
    };
}
