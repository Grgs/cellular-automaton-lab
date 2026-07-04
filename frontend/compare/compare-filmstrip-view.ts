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
    /** Called when the focused board changes (null = gallery), e.g. to mirror the hash. */
    onFocusChange?: (geometry: string | null) => void;
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
    /** Enlarge one board (speaker view) or return to the gallery (null). */
    focus(geometry: string | null): void;
    /** The shared clock's current generation index. */
    currentFrameIndex(): number;
    /** Overlay a node onto the focused board's slot (live fork), or restore its SVG (null). */
    setHeroOverlay(node: HTMLElement | null): boolean;
    dispose(): void;
}

interface BoardEntry {
    tiling: TopologyFilmstrip;
    cell: HTMLElement;
    slot: HTMLElement;
    countLabel: HTMLElement;
    focusButton: HTMLButtonElement;
    openButton?: HTMLButtonElement;
    preview?: TopologyPreview;
    error?: string;
    overlaid?: boolean;
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

function iconButton(label: string, title: string, onClick: () => void): HTMLButtonElement {
    const node = document.createElement("button");
    node.type = "button";
    node.className = "compare-filmstrip-focus";
    node.textContent = label;
    node.title = title;
    node.setAttribute("aria-label", title);
    node.setAttribute("aria-pressed", "false");
    node.addEventListener("click", (event) => {
        event.stopPropagation();
        onClick();
    });
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
    let focusedGeometry: string | null = null;
    let overlayEntry: BoardEntry | null = null;

    /** Toggle gallery/speaker classes and per-board focus affordances (no re-render). */
    function applyFocusLayout(): void {
        const speaker = focusedGeometry !== null;
        root.classList.toggle("compare-filmstrip--speaker", speaker);
        for (const entry of boards) {
            const isHero = speaker && entry.tiling.geometry === focusedGeometry;
            entry.cell.classList.toggle("is-hero", isHero);
            entry.cell.classList.toggle("is-strip", speaker && !isHero);
            entry.focusButton.setAttribute("aria-pressed", isHero ? "true" : "false");
            entry.focusButton.title = isHero ? "Back to the gallery" : "Focus this board";
            entry.focusButton.setAttribute(
                "aria-label",
                isHero ? "Back to the gallery" : `Focus ${entry.tiling.geometry}`,
            );
        }
    }

    function focus(geometry: string | null): void {
        const next =
            geometry !== null && boards.some((entry) => entry.tiling.geometry === geometry)
                ? geometry
                : null;
        if (next === focusedGeometry) {
            return;
        }
        focusedGeometry = next;
        applyFocusLayout();
        options.onFocusChange?.(focusedGeometry);
    }

    function renderBoard(entry: BoardEntry, index: number): void {
        // A live fork owns this board's slot; leave its canvas untouched.
        if (entry.overlaid) {
            return;
        }
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
            entry.openButton.textContent = `Fork gen ${index} →`;
            entry.openButton.title = `Fork ${entry.tiling.geometry} generation ${index} into the Lab as an editable board`;
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
        overlayEntry = null;
        // A fresh run starts in the gallery; silent so it doesn't fire onFocusChange.
        focusedGeometry = null;
        root.classList.remove("compare-filmstrip--speaker");
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
            const focusButton = iconButton("⤢", `Focus ${tiling.geometry}`, () => {
                focus(focusedGeometry === tiling.geometry ? null : tiling.geometry);
            });
            const openButton = options.onOpenFrame
                ? linkButton(
                      "Fork gen 0 →",
                      `Fork ${tiling.geometry} generation 0 into the Lab as an editable board`,
                      () => options.onOpenFrame?.(tiling, player.index),
                  )
                : undefined;
            const header = el("div", "compare-filmstrip-board-head");
            header.append(label, focusButton);
            cell.append(header, slot, countLabel);
            if (openButton) {
                cell.append(openButton);
            }
            // In speaker view a strip thumbnail is a click target to swap focus;
            // clicks on its buttons are handled by those buttons (stopPropagation).
            cell.addEventListener("click", (event) => {
                if (event.target instanceof Element && event.target.closest("button")) {
                    return;
                }
                if (focusedGeometry !== null && focusedGeometry !== tiling.geometry) {
                    focus(tiling.geometry);
                }
            });
            boardsArea.append(cell);
            return {
                tiling,
                cell,
                slot,
                countLabel,
                focusButton,
                ...(openButton ? { openButton } : {}),
            };
        });

        unsubscribe = player.subscribe(onPlayerIndex);
        transport.attach(player);
        // Prime the (still "…") board skeletons before previews load.
        onPlayerIndex(player.state);
        applyFocusLayout();

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
        focus,
        currentFrameIndex: () => player.index,
        setHeroOverlay(node: HTMLElement | null): boolean {
            if (node) {
                const entry = boards.find(
                    (candidate) => candidate.tiling.geometry === focusedGeometry,
                );
                if (!entry) {
                    return false;
                }
                overlayEntry = entry;
                entry.overlaid = true;
                entry.slot.replaceChildren(node);
                return true;
            }
            if (overlayEntry) {
                overlayEntry.overlaid = false;
                renderBoard(overlayEntry, player.index);
                overlayEntry = null;
            }
            return true;
        },
        dispose(): void {
            teardownRun();
            root.remove();
        },
    };
}
