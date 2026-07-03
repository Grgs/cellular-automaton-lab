/**
 * The live, synchronized side-by-side view. It takes a `SeedFilmstripResult`
 * (one board state per generation for each tiling, all sharing one frame count)
 * and renders every tiling in lockstep off a single {@link FilmstripPlayer}.
 *
 * The player owns the shared frame index; the {@link FilmstripTransportController}
 * (pinned below the stage) owns the clock and playback controls. This view owns
 * only the rendering: per tiling it fetches the board geometry once, then redraws
 * `frames[index]` with {@link buildBoardThumbnailSvg} whenever the index moves.
 * On `load` it hands the fresh player to the transport via `transport.attach`.
 */

import type { SimulationBackend } from "../types/controller.js";
import type { SeedFilmstripResult, TopologyFilmstrip, TopologyPreview } from "../types/domain.js";
import { buildBoardThumbnailSvg } from "./compare-thumbnail.js";
import { FilmstripPlayer, type FilmstripPlayerState } from "./filmstrip-player.js";
import type { FilmstripTransportController } from "./compare-transport.js";

const DEFAULT_THUMB_SIZE = 180;

export interface FilmstripViewOptions {
    backend: SimulationBackend;
    /** The shared transport bar; `load` attaches each run's player to it. */
    transport: FilmstripTransportController;
    /** Resolver for the live-cell colour (tracks the selected rule's palette). */
    getLiveColor?: () => (state: number) => string;
    /** Rendered board size in px. */
    thumbSize?: number;
    /** Loop back to the seed frame after the last instead of stopping. */
    loop?: boolean;
    /** Called when the user wants to load one board's current generation into build mode. */
    onOpenFrame?: (tiling: TopologyFilmstrip, frameIndex: number) => void;
}

/** Optional playback overrides applied right after a filmstrip is loaded. */
export interface FilmstripLoadOptions {
    /** Start playing immediately instead of waiting on the seed frame. */
    autoplay?: boolean;
    /** Seek to this generation after loading (e.g. a lively frame when paused). */
    initialFrame?: number;
    /** Frame the loop wraps back to, so playback replays only a lively sub-window. */
    loopStart?: number;
    /** Transport speed multiplier to apply (must match a speed-selector option). */
    speedMultiplier?: number;
}

export interface FilmstripViewController {
    element: HTMLElement;
    /** Render a filmstrip and reset playback to the seed frame (paused). */
    load(filmstrip: SeedFilmstripResult, options?: FilmstripLoadOptions): Promise<void>;
    dispose(): void;
}

interface BoardEntry {
    tiling: TopologyFilmstrip;
    slot: HTMLElement;
    countLabel: HTMLElement;
    openButton?: HTMLButtonElement;
    preview?: TopologyPreview;
    error?: string;
}

function el(tag: string, className: string, text?: string): HTMLElement {
    const node = document.createElement(tag);
    node.className = className;
    if (text !== undefined) {
        node.textContent = text;
    }
    return node;
}

function linkButton(label: string, title: string, onClick: () => void): HTMLButtonElement {
    const node = document.createElement("button");
    node.type = "button";
    node.className = "compare-link compare-filmstrip-open";
    node.textContent = label;
    node.title = title;
    node.setAttribute("aria-label", title);
    node.addEventListener("click", onClick);
    return node;
}

export function createFilmstripView(options: FilmstripViewOptions): FilmstripViewController {
    const thumbSize = options.thumbSize ?? DEFAULT_THUMB_SIZE;
    const getLiveColor = options.getLiveColor ?? (() => () => "var(--live, #1f2430)");
    const transport = options.transport;

    const root = el("div", "compare-filmstrip");
    root.setAttribute("role", "region");
    root.setAttribute("aria-label", "Synchronized side-by-side filmstrip");

    const boardsArea = el("div", "compare-filmstrip-boards");
    boardsArea.setAttribute("role", "list");
    boardsArea.setAttribute("aria-label", "Compared tiling boards");
    root.append(boardsArea);

    let player = new FilmstripPlayer(0, { loop: options.loop ?? false });
    let unsubscribe: (() => void) | null = null;
    let boards: BoardEntry[] = [];
    let lastRenderedIndex = -1;

    function renderBoard(entry: BoardEntry, index: number): void {
        const frame = entry.tiling.frames[index] ?? {};
        if (entry.error) {
            entry.slot.textContent = entry.error.includes("limit") ? "too large" : "unavailable";
            entry.countLabel.textContent = "";
            if (entry.openButton) {
                entry.openButton.disabled = true;
                entry.openButton.title = "This board is unavailable.";
            }
            return;
        }
        const preview = entry.preview;
        if (!preview) {
            entry.slot.textContent = "…";
            if (entry.openButton) {
                entry.openButton.disabled = true;
                entry.openButton.title = "Load the board preview before opening this generation.";
            }
            return;
        }
        const cellsById = frame;
        const svg = buildBoardThumbnailSvg(preview, cellsById, {
            size: thumbSize,
            liveColor: getLiveColor(),
            label: `${entry.tiling.geometry} generation ${index}`,
        });
        entry.slot.replaceChildren(svg);
        const liveCells = Object.keys(cellsById).length;
        const extinct =
            entry.tiling.extinction_step !== null && index >= entry.tiling.extinction_step;
        entry.countLabel.textContent = extinct ? "extinct" : `${liveCells} live`;
        if (entry.openButton) {
            entry.openButton.disabled = false;
            entry.openButton.textContent = `Open gen ${index}`;
            entry.openButton.title = `Load ${entry.tiling.geometry} generation ${index} into build mode`;
        }
    }

    function renderAllBoards(index: number): void {
        for (const entry of boards) {
            renderBoard(entry, index);
        }
        lastRenderedIndex = index;
    }

    // The view subscribes to the player only for rendering; the transport owns the
    // controls and the clock, subscribing to the same player independently.
    function onPlayerIndex(state: FilmstripPlayerState): void {
        if (state.index !== lastRenderedIndex) {
            renderAllBoards(state.index);
        }
    }

    function teardownRun(): void {
        transport.detach();
        unsubscribe?.();
        unsubscribe = null;
        boards = [];
        lastRenderedIndex = -1;
    }

    async function load(
        filmstrip: SeedFilmstripResult,
        loadOptions?: FilmstripLoadOptions,
    ): Promise<void> {
        teardownRun();
        player = new FilmstripPlayer(filmstrip.frame_count, {
            loop: options.loop ?? false,
            ...(loadOptions?.loopStart === undefined ? {} : { loopStart: loadOptions.loopStart }),
        });

        boardsArea.replaceChildren();
        boards = filmstrip.tilings.map((tiling) => {
            const slot = el("div", "compare-filmstrip-slot", "…");
            const label = el("div", "compare-filmstrip-label", tiling.geometry);
            const countLabel = el("div", "compare-filmstrip-count");
            const cell = el("div", "compare-filmstrip-board");
            cell.setAttribute("role", "listitem");
            const openButton = options.onOpenFrame
                ? linkButton(
                      "Open gen 0",
                      `Load ${tiling.geometry} generation 0 into build mode`,
                      () => options.onOpenFrame?.(tiling, player.index),
                  )
                : undefined;
            cell.append(label, slot, countLabel);
            if (openButton) {
                cell.append(openButton);
            }
            boardsArea.append(cell);
            return { tiling, slot, countLabel, ...(openButton ? { openButton } : {}) };
        });

        unsubscribe = player.subscribe(onPlayerIndex);
        transport.attach(player);
        // Prime the (still "…") board skeletons before previews load.
        onPlayerIndex(player.state);

        await Promise.all(
            boards.map(async (entry) => {
                const spec = entry.tiling.topology_spec;
                try {
                    entry.preview = await options.backend.previewTopology({
                        geometry: entry.tiling.geometry,
                        width: spec.width,
                        height: spec.height,
                        ...(spec.patch_depth === undefined
                            ? {}
                            : { patch_depth: spec.patch_depth }),
                    });
                    delete entry.error;
                } catch (error) {
                    entry.error = error instanceof Error ? error.message : String(error);
                }
                renderBoard(entry, player.index);
            }),
        );

        // Optional post-load playback overrides (used by the featured demo).
        if (loadOptions?.speedMultiplier !== undefined) {
            transport.setSpeed(loadOptions.speedMultiplier);
        }
        if (loadOptions?.initialFrame !== undefined) {
            player.seek(loadOptions.initialFrame);
        }
        if (loadOptions?.autoplay) {
            player.play();
        }
    }

    return {
        element: root,
        load,
        dispose(): void {
            teardownRun();
            root.remove();
        },
    };
}
