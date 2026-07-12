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
import type {
    SeedFilmstripResult,
    TopologyFilmstrip,
    TopologyOption,
    TopologyPreview,
    TopologySpec,
} from "../types/domain.js";
import { buildBoardThumbnailSvg } from "./compare-thumbnail.js";
import { FilmstripPlayer, type FilmstripPlayerState } from "./filmstrip-player.js";
import type { FilmstripTransportController } from "./compare-transport.js";
import { createTilingPreviewThumbnail } from "../controls/tiling-preview.js";

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
    /** Called when the focused board changes (null = gallery), e.g. to mirror the hash. */
    onFocusChange?: (geometry: string | null) => void;
    /** Called when a board cell is clicked while edit mode is on. */
    onPaintCell?: (geometry: string, cellId: string) => void;
    /**
     * Called when a board's ✕ chrome is clicked. The affordance only renders
     * when this is provided and more than two boards are on the wall (the
     * backend needs at least two to compare).
     */
    onRemoveBoard?: (geometry: string) => void;
    /** Tiling catalog used by the per-board replacement picker. */
    tilingOptions?: readonly TopologyOption[];
    /** Replace a board's tiling from its caption picker. */
    onReplaceBoard?: (previousGeometry: string, nextGeometry: string) => void;
    /** Whether a catalog tiling supports the currently selected rule. */
    isTilingAvailable?: (geometry: string) => boolean;
    /** Called after the shared generation index changes. */
    onFrameChange?: (frameIndex: number) => void;
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
    /** Reuse existing board DOM when the incoming tiling set is unchanged. */
    preserveBoards?: boolean;
}

export interface FilmstripViewController {
    element: HTMLElement;
    /** Render a filmstrip and reset playback to the seed frame (paused). */
    load(filmstrip: SeedFilmstripResult, options?: FilmstripLoadOptions): Promise<void>;
    /** Enlarge one board (speaker view) or return to the gallery (null). */
    focus(geometry: string | null): void;
    /**
     * Toggle edit mode: board clicks paint cells (via `onPaintCell`) instead of
     * focusing; the expand glyph becomes the only zoom affordance.
     */
    setEditMode(enabled: boolean): void;
    /** Re-render one board's current frame (e.g. after an optimistic seed edit). */
    refreshBoard(geometry: string): void;
    /** The shared clock's current generation index. */
    currentFrameIndex(): number;
    /**
     * Overlay a node onto a board's slot (a live fork), or restore its SVG
     * rendering (null). Targets the board by geometry, not by focus, so a fork
     * keeps rendering in its own slot whether that board is the hero, part of
     * the speaker-view strip, or back in the gallery. Returns false if the
     * board no longer exists in the current filmstrip.
     */
    setBoardOverlay(geometry: string, node: HTMLElement | null): boolean;
    /** Persistent toolbelt overlaid on the hero in speaker view (null to clear). */
    setHeroToolbelt(node: HTMLElement | null): void;
    /** Close an open board tiling picker; returns whether one was open. */
    closeTilingPicker(): boolean;
    dispose(): void;
}

interface BoardEntry {
    tiling: TopologyFilmstrip;
    cell: HTMLElement;
    slot: HTMLElement;
    label: HTMLElement;
    countLabel: HTMLElement;
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

function element<K extends keyof HTMLElementTagNameMap>(
    tag: K,
    attrs: Record<string, string> = {},
    children: Node[] = [],
): HTMLElementTagNameMap[K] {
    const node = document.createElement(tag);
    for (const [name, value] of Object.entries(attrs)) {
        if (name === "textContent") node.textContent = value;
        else node.setAttribute(name, value);
    }
    node.append(...children);
    return node;
}

function sameTopologySpec(left: TopologySpec, right: TopologySpec): boolean {
    return (
        left.tiling_family === right.tiling_family &&
        left.adjacency_mode === right.adjacency_mode &&
        left.sizing_mode === right.sizing_mode &&
        left.width === right.width &&
        left.height === right.height &&
        left.patch_depth === right.patch_depth
    );
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
    let heroToolbelt: HTMLElement | null = null;
    let editMode = false;
    let openTilingPicker: HTMLElement | null = null;

    function closeTilingPicker(): boolean {
        if (!openTilingPicker) return false;
        openTilingPicker.remove();
        openTilingPicker = null;
        return true;
    }

    /** Move the (panel-owned) toolbelt onto the current hero, or detach it. */
    function placeHeroToolbelt(): void {
        if (!heroToolbelt) {
            return;
        }
        const hero =
            focusedGeometry !== null
                ? boards.find((entry) => entry.tiling.geometry === focusedGeometry)
                : undefined;
        if (hero) {
            hero.cell.append(heroToolbelt);
        } else {
            heroToolbelt.remove();
        }
    }

    /** Toggle gallery/speaker classes and per-board focus affordances (no re-render). */
    function applyFocusLayout(): void {
        const speaker = focusedGeometry !== null;
        root.classList.toggle("compare-filmstrip--speaker", speaker);
        for (const entry of boards) {
            const isHero = speaker && entry.tiling.geometry === focusedGeometry;
            entry.cell.classList.toggle("is-hero", isHero);
            entry.cell.classList.toggle("is-strip", speaker && !isHero);
            if (editMode) {
                entry.cell.title = "Paint cells (⤢ zooms)";
                entry.cell.setAttribute("aria-label", `${boardName(entry.tiling)}: paint cells`);
                continue;
            }
            entry.cell.title = isHero ? "Back to the wall" : "Focus this board";
            entry.cell.setAttribute(
                "aria-label",
                isHero
                    ? `${boardName(entry.tiling)}: back to the wall`
                    : `${boardName(entry.tiling)}: focus this board`,
            );
        }
        placeHeroToolbelt();
    }

    function entryFor(geometry: string): BoardEntry | undefined {
        return boards.find((entry) => entry.tiling.geometry === geometry);
    }

    function canReuseBoards(filmstrip: SeedFilmstripResult): boolean {
        if (boards.length === 0 || boards.length !== filmstrip.tilings.length) {
            return false;
        }
        return filmstrip.tilings.every((tiling, index) => {
            const current = boards[index]?.tiling;
            return (
                current !== undefined &&
                current.geometry === tiling.geometry &&
                sameTopologySpec(current.topology_spec, tiling.topology_spec)
            );
        });
    }

    /** The board's display name: friendly catalog label, geometry key fallback. */
    function boardName(tiling: TopologyFilmstrip): string {
        return tiling.label || tiling.geometry;
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
            return;
        }
        const preview = entry.preview;
        if (!preview) {
            entry.slot.textContent = "…";
            return;
        }
        const cellsById = frame;
        const svg = buildBoardThumbnailSvg(preview, cellsById, {
            size: thumbSize,
            liveColor: getLiveColor(),
            label: `${boardName(entry.tiling)} generation ${index}`,
        });
        entry.slot.replaceChildren(svg);
        const liveCells = Object.keys(cellsById).length;
        const extinct =
            entry.tiling.extinction_step !== null && index >= entry.tiling.extinction_step;
        entry.countLabel.textContent = extinct ? "extinct" : `${liveCells} live`;
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
        options.onFrameChange?.(state.index);
    }

    function teardownRun(): void {
        transport.detach();
        unsubscribe?.();
        unsubscribe = null;
        boards = [];
        lastRenderedIndex = -1;
        // A fresh run starts in the gallery; silent so it doesn't fire onFocusChange.
        focusedGeometry = null;
        root.classList.remove("compare-filmstrip--speaker");
    }

    function detachPlayer(): void {
        transport.detach();
        unsubscribe?.();
        unsubscribe = null;
        lastRenderedIndex = -1;
    }

    function createBoardEntry(tiling: TopologyFilmstrip, removable: boolean): BoardEntry {
        const slot = el("div", "compare-filmstrip-slot", "…");
        const label = el("button", "compare-filmstrip-label", boardName(tiling));
        label.setAttribute("type", "button");
        label.title = `Replace ${boardName(tiling)}`;
        label.setAttribute("aria-label", `Replace ${boardName(tiling)}`);
        const countLabel = el("div", "compare-filmstrip-count");
        const cell = el("div", "compare-filmstrip-board");
        cell.setAttribute("role", "listitem");
        cell.tabIndex = 0;
        // Board chrome (name, live count, an expand affordance) overlays the
        // board; labels stay visible so the wall explains itself at rest.
        const expandGlyph = el("span", "compare-filmstrip-expand", "⤢");
        expandGlyph.setAttribute("aria-hidden", "true");
        const chrome = el("div", "compare-filmstrip-board-chrome");
        chrome.append(label, countLabel, expandGlyph);
        if (removable) {
            // A real <button> so the cell's click handler ignores it (its
            // early-return on buttons), in edit mode included.
            const removeButton = el("button", "compare-filmstrip-remove", "✕");
            removeButton.setAttribute("type", "button");
            removeButton.title = "Remove from the wall";
            removeButton.setAttribute("aria-label", `Remove ${boardName(tiling)} from the wall`);
            removeButton.addEventListener("click", () => {
                options.onRemoveBoard?.(tiling.geometry);
            });
            chrome.append(removeButton);
        }
        cell.append(slot, chrome);
        label.addEventListener("click", (event) => {
            event.stopPropagation();
            if (!options.tilingOptions || !options.onReplaceBoard) return;
            if (openTilingPicker?.dataset.geometry === tiling.geometry) {
                closeTilingPicker();
                return;
            }
            closeTilingPicker();
            const picker = element("div", {
                class: "compare-board-tiling-picker",
                role: "dialog",
                "aria-label": `Replace ${boardName(tiling)}`,
            });
            picker.dataset.geometry = tiling.geometry;
            const close = element("button", {
                class: "compare-board-tiling-picker-close",
                type: "button",
                textContent: "×",
                "aria-label": "Close tiling picker",
            });
            const header = element("div", { class: "compare-board-tiling-picker-header" }, [
                element("strong", { textContent: "Replace tiling" }),
                close,
            ]);
            const search = element("input", {
                class: "compare-board-tiling-picker-search",
                type: "search",
                placeholder: "Search tilings",
                "aria-label": "Search tilings",
            });
            const list = element("div", { class: "compare-board-tiling-picker-list" });
            const renderChoices = (): void => {
                const query = search.value.trim().toLowerCase();
                list.replaceChildren();
                for (const option of options.tilingOptions ?? []) {
                    if (
                        query &&
                        !`${option.label} ${option.value} ${option.group}`
                            .toLowerCase()
                            .includes(query)
                    )
                        continue;
                    const choice = element("button", {
                        class: "compare-board-tiling-choice",
                        type: "button",
                    });
                    choice.disabled =
                        (option.value !== tiling.geometry &&
                            boards.some((board) => board.tiling.geometry === option.value)) ||
                        options.isTilingAvailable?.(option.value) === false;
                    choice.classList.toggle("is-current", option.value === tiling.geometry);
                    choice.append(
                        element(
                            "span",
                            { class: "compare-board-tiling-choice-thumb", "aria-hidden": "true" },
                            [createTilingPreviewThumbnail(option)],
                        ),
                        element("span", { class: "compare-board-tiling-choice-copy" }, [
                            element("span", { textContent: option.label }),
                            element("small", { textContent: option.group }),
                        ]),
                    );
                    choice.addEventListener("click", () => {
                        if (option.value !== tiling.geometry)
                            options.onReplaceBoard?.(tiling.geometry, option.value);
                        closeTilingPicker();
                    });
                    list.append(choice);
                }
            };
            close.addEventListener("click", closeTilingPicker);
            search.addEventListener("input", renderChoices);
            picker.append(header, search, list);
            cell.append(picker);
            openTilingPicker = picker;
            renderChoices();
            search.focus();
        });
        const toggleFocus = () => {
            focus(focusedGeometry === tiling.geometry ? null : tiling.geometry);
        };
        // The board tile itself behaves like a video-call participant: click
        // to focus it, click the focused hero to return to the gallery. In
        // edit mode clicks paint instead, and only the ⤢ glyph zooms.
        cell.addEventListener("click", (event) => {
            const target = event.target instanceof Element ? event.target : null;
            if (target?.closest("button")) {
                return;
            }
            if (editMode) {
                if (target?.closest(".compare-filmstrip-expand")) {
                    toggleFocus();
                    return;
                }
                const cellId = target?.closest("[data-cell-id]")?.getAttribute("data-cell-id");
                if (cellId && !entryFor(tiling.geometry)?.overlaid) {
                    options.onPaintCell?.(tiling.geometry, cellId);
                }
                return;
            }
            toggleFocus();
        });
        cell.addEventListener("keydown", (event) => {
            if (event.target !== cell) {
                return;
            }
            if (event.key === "Enter" || event.key === " " || event.key === "Spacebar") {
                event.preventDefault();
                toggleFocus();
            }
        });
        boardsArea.append(cell);
        return {
            tiling,
            cell,
            slot,
            label,
            countLabel,
        };
    }

    function syncReusedBoards(filmstrip: SeedFilmstripResult): void {
        for (const [index, entry] of boards.entries()) {
            const tiling = filmstrip.tilings[index]!;
            entry.tiling = tiling;
            entry.label.textContent = boardName(tiling);
            entry.label.title = `Replace ${boardName(tiling)}`;
            entry.label.setAttribute("aria-label", `Replace ${boardName(tiling)}`);
            entry.overlaid = false;
            if (entry.preview) {
                delete entry.error;
            }
        }
    }

    async function ensurePreview(entry: BoardEntry): Promise<void> {
        if (entry.preview && !entry.error) {
            renderBoard(entry, player.index);
            return;
        }
        const spec = entry.tiling.topology_spec;
        try {
            entry.preview = await options.backend.previewTopology({
                geometry: entry.tiling.geometry,
                width: spec.width,
                height: spec.height,
                ...(spec.patch_depth === undefined ? {} : { patch_depth: spec.patch_depth }),
            });
            delete entry.error;
        } catch (error) {
            entry.error = error instanceof Error ? error.message : String(error);
        }
        renderBoard(entry, player.index);
    }

    async function load(
        filmstrip: SeedFilmstripResult,
        loadOptions?: FilmstripLoadOptions,
    ): Promise<void> {
        const reuseBoards = Boolean(loadOptions?.preserveBoards) && canReuseBoards(filmstrip);
        if (reuseBoards) {
            detachPlayer();
            syncReusedBoards(filmstrip);
        } else {
            teardownRun();
            boardsArea.replaceChildren();
            // Removing a board only makes sense while the backend can still
            // compare what remains (two boards minimum).
            const removable = Boolean(options.onRemoveBoard) && filmstrip.tilings.length > 2;
            boards = filmstrip.tilings.map((tiling) => createBoardEntry(tiling, removable));
        }
        player = new FilmstripPlayer(filmstrip.frame_count, {
            loop: options.loop ?? false,
            ...(loadOptions?.loopStart === undefined ? {} : { loopStart: loadOptions.loopStart }),
        });

        unsubscribe = player.subscribe(onPlayerIndex);
        transport.attach(player);
        // Prime the (still "…") board skeletons before previews load.
        onPlayerIndex(player.state);
        applyFocusLayout();

        await Promise.all(boards.map((entry) => ensurePreview(entry)));

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
        setEditMode(enabled: boolean): void {
            if (editMode === enabled) {
                return;
            }
            editMode = enabled;
            root.classList.toggle("is-editing", editMode);
            applyFocusLayout();
        },
        refreshBoard(geometry: string): void {
            const entry = entryFor(geometry);
            if (entry) {
                renderBoard(entry, player.index);
            }
        },
        currentFrameIndex: () => player.index,
        setBoardOverlay(geometry: string, node: HTMLElement | null): boolean {
            const entry = entryFor(geometry);
            if (!entry) {
                return false;
            }
            if (node) {
                entry.overlaid = true;
                entry.slot.replaceChildren(node);
                return true;
            }
            if (entry.overlaid) {
                entry.overlaid = false;
                renderBoard(entry, player.index);
            }
            return true;
        },
        setHeroToolbelt(node: HTMLElement | null): void {
            if (heroToolbelt && heroToolbelt !== node) {
                heroToolbelt.remove();
            }
            heroToolbelt = node;
            placeHeroToolbelt();
        },
        closeTilingPicker,
        dispose(): void {
            closeTilingPicker();
            teardownRun();
            root.remove();
        },
    };
}
