/**
 * The wall's live focus pane: forking the focused board at generation N into a
 * real, editable, independently-steppable board that replaces the hero SVG. It
 * runs on its own backend session (seeded from the frame's pattern) and detaches
 * from the shared filmstrip clock — the other boards keep looping while this one
 * evolves on its own. "Discard" tears it down and restores the SVG hero.
 *
 * This module is dynamically imported on first fork so the canvas/editor pipeline
 * stays out of the landing chunk.
 */

import { EDITOR_TOOL_BRUSH } from "../editor-tools.js";
import {
    createEditablePane,
    element,
    resolvePanePaintState,
    type PaneCellSizeOptions,
    type PaneEditorCellsBuilder,
} from "../pane/pane-core.js";
import type { SimulationBackend } from "../types/controller-api.js";
import type { GridView } from "../types/controller-view.js";
import type { AppBootstrapData, PatternPayload, SimulationSnapshot } from "../types/domain.js";

export interface FocusPaneMountOptions {
    /** Friendly geometry name shown in the fork chip. */
    geometry: string;
    frameIndex: number;
    pattern: PatternPayload;
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    createGridView: (canvas: HTMLCanvasElement) => GridView;
    buildEditorToolCells: PaneEditorCellsBuilder;
    resolveCellSize?: (options: PaneCellSizeOptions) => number;
    /** Called when the user discards the fork (the pane and its session are gone). */
    onDiscard: () => void;
    onError?: (error: unknown) => void;
}

export interface FocusPaneHandle {
    element: HTMLElement;
    /** Tear down the pane and dispose its backend session. */
    dispose(): void;
}

export function mountFocusPane(options: FocusPaneMountOptions): FocusPaneHandle {
    const { geometry, frameIndex, pattern, backend, bootstrapData, createGridView } = options;
    const onError = options.onError ?? ((error) => console.error(error));
    const definitions = bootstrapData.topology_catalog;

    const root = element("div", "compare-focus-pane");
    const chip = element("div", "compare-focus-pane-chip");
    const info = element(
        "span",
        "compare-focus-pane-info",
        `⑂ Forked from ${geometry} gen ${frameIndex}`,
    );
    const badge = element("span", "compare-focus-pane-badge", "detached from the shared clock");
    const palette = element("div", "compare-focus-pane-palette");
    const actions = element("div", "compare-focus-pane-actions");
    const stepButton = element("button", "compare-focus-pane-action", "Step");
    stepButton.type = "button";
    const runButton = element("button", "compare-focus-pane-action", "Run");
    runButton.type = "button";
    const discardButton = element(
        "button",
        "compare-focus-pane-action compare-focus-pane-discard",
        "Discard",
    );
    discardButton.type = "button";
    actions.append(stepButton, runButton, discardButton);
    chip.append(info, badge, palette, actions);

    const viewport = element("div", "compare-focus-pane-viewport");
    const canvas = element("canvas", "grid-canvas compare-focus-pane-canvas");
    canvas.setAttribute("aria-label", `${geometry} forked board`);
    viewport.append(canvas);
    root.append(chip, viewport);

    const gridView = createGridView(canvas);
    let paintState = 1;
    let currentSnapshot: SimulationSnapshot | null = null;

    function renderPalette(): void {
        palette.replaceChildren();
        if (!currentSnapshot) {
            return;
        }
        paintState = resolvePanePaintState(currentSnapshot, paintState);
        for (const state of currentSnapshot.rule.states.filter(
            (candidate) => candidate.paintable !== false,
        )) {
            const button = element("button", "compare-focus-pane-swatch", state.label);
            button.type = "button";
            button.classList.toggle("is-selected", state.value === paintState);
            button.setAttribute("aria-pressed", state.value === paintState ? "true" : "false");
            const swatch = element("span", "compare-focus-pane-swatch-color");
            swatch.style.background = state.color;
            button.prepend(swatch);
            button.addEventListener("click", () => {
                paintState = state.value;
                renderPalette();
            });
            palette.append(button);
        }
    }

    const pane = createEditablePane({
        canvas,
        viewport,
        backend,
        gridView,
        bootstrapData,
        definitions,
        getTool: () => EDITOR_TOOL_BRUSH,
        getPaintState: () => paintState,
        ...(options.resolveCellSize ? { resolveCellSize: options.resolveCellSize } : {}),
        buildEditorToolCells: options.buildEditorToolCells,
        onSnapshot: (snapshot) => {
            currentSnapshot = snapshot;
            runButton.textContent = snapshot.running ? "Pause" : "Run";
            info.textContent = `⑂ Forked from ${geometry} gen ${frameIndex} · now gen ${snapshot.generation}`;
            renderPalette();
        },
        onError,
    });

    stepButton.addEventListener("click", () => void pane.step().catch(onError));
    runButton.addEventListener("click", () => void pane.runToggle().catch(onError));

    let disposed = false;
    function dispose(): void {
        if (disposed) {
            return;
        }
        disposed = true;
        pane.dispose();
        void Promise.resolve(backend.dispose()).catch(onError);
    }
    discardButton.addEventListener("click", () => {
        dispose();
        options.onDiscard();
    });

    // Reconstruct the board from the forked frame; the pane renders once seeded.
    void pane.seedFromPattern(pattern, bootstrapData.app_defaults.simulation.speed).catch(onError);

    return { element: root, dispose };
}
