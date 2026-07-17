import type { GridView, ViewportDimensions } from "../types/controller-view.js";
import type {
    BootstrappedTopologyDefinition,
    SimulationSnapshot,
    TopologySpec,
} from "../types/domain.js";

export interface PaneViewportDimensionsOptions {
    viewportWidth: number;
    viewportHeight: number;
    geometry: string;
    cellSize: number;
    fallbackDimensions: ViewportDimensions;
    maxCellCount?: number;
}

export interface PaneCellSizeOptions {
    viewportWidth: number;
    viewportHeight: number;
    width: number;
    height: number;
    topology: SimulationSnapshot["topology"];
    geometry: string;
    fallbackCellSize: number;
}

export function geometryForSpec(
    definitions: readonly BootstrappedTopologyDefinition[],
    spec: TopologySpec,
): string {
    const definition = definitions.find(
        (candidate) => candidate.tiling_family === spec.tiling_family,
    );
    return definition?.geometry_keys[spec.adjacency_mode] ?? spec.tiling_family;
}

function cssPixelValue(value: string): number {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : 0;
}

export function fitCanvasElementToViewport(canvas: HTMLCanvasElement, viewport: HTMLElement): void {
    const canvasWidth = Number.parseFloat(canvas.style.width) || canvas.width;
    const canvasHeight = Number.parseFloat(canvas.style.height) || canvas.height;
    if (canvasWidth <= 0 || canvasHeight <= 0) {
        return;
    }
    const viewportStyle = window.getComputedStyle(viewport);
    const availableWidth = Math.max(
        1,
        viewport.clientWidth -
            cssPixelValue(viewportStyle.paddingLeft) -
            cssPixelValue(viewportStyle.paddingRight),
    );
    const availableHeight = Math.max(
        1,
        viewport.clientHeight -
            cssPixelValue(viewportStyle.paddingTop) -
            cssPixelValue(viewportStyle.paddingBottom),
    );
    const scale = Math.min(1, availableWidth / canvasWidth, availableHeight / canvasHeight);
    canvas.style.width = `${canvasWidth * scale}px`;
    canvas.style.height = `${canvasHeight * scale}px`;
}

export interface PaneRenderer {
    render(snapshot: SimulationSnapshot | null): void;
}

interface PaneRendererOptions {
    canvas: HTMLCanvasElement;
    viewport: HTMLElement;
    gridView: GridView;
    definitions: readonly BootstrappedTopologyDefinition[];
    fallbackCellSize: number;
    resolveCellSize?: ((options: PaneCellSizeOptions) => number) | undefined;
}

export function createPaneRenderer(options: PaneRendererOptions): PaneRenderer {
    const { canvas, viewport, gridView, definitions, fallbackCellSize, resolveCellSize } = options;

    return {
        render(snapshot): void {
            if (!snapshot) {
                return;
            }
            const geometry = geometryForSpec(definitions, snapshot.topology_spec);
            const viewportWidth = viewport.clientWidth;
            const viewportHeight = viewport.clientHeight;
            const cellSize =
                viewportWidth > 0 && viewportHeight > 0
                    ? (resolveCellSize?.({
                          viewportWidth,
                          viewportHeight,
                          width: snapshot.topology.width ?? snapshot.topology_spec.width,
                          height: snapshot.topology.height ?? snapshot.topology_spec.height,
                          topology: snapshot.topology,
                          geometry,
                          fallbackCellSize,
                      }) ?? fallbackCellSize)
                    : fallbackCellSize;
            gridView.render?.(
                {
                    topology: snapshot.topology,
                    cellStates: snapshot.cell_states,
                    previewCellStatesById: null,
                    tileColorsEnabled: true,
                },
                cellSize,
                snapshot.rule.states,
                geometry,
            );
            fitCanvasElementToViewport(canvas, viewport);
        },
    };
}
