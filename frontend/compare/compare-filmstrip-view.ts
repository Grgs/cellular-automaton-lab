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
import { buildBoardThumbnailSvg, updateBoardThumbnailSvg } from "./compare-thumbnail.js";
import { FilmstripPlayer, type FilmstripPlayerState } from "./filmstrip-player.js";
import type { FilmstripTransportController } from "./compare-transport.js";
import { createTilingPreviewThumbnail } from "../controls/tiling-preview.js";

const DEFAULT_THUMB_SIZE = 180;
const MANAGEMENT_BUSY_REASON = "Wait for the wall update to finish";

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
    /** Tiling catalog used by the selected-board replacement and wall-add pickers. */
    tilingOptions?: readonly TopologyOption[];
    /** Replace the selected board from the Inspector's visual picker. */
    onReplaceBoard?: (previousGeometry: string, nextGeometry: string) => void;
    /** Add a new tiling from the wall's searchable picker. */
    onAddBoard?: (geometry: string) => void;
    /** Whether a catalog tiling supports the currently selected rule. */
    isTilingAvailable?: (geometry: string) => boolean;
    /** Whether the wall currently has capacity for another board. */
    canAddBoard?: () => boolean;
    /** Explanation shown when adding is disabled by the wall capacity policy. */
    addBoardDisabledReason?: () => string;
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
    /** Mark the board that Inspector actions target without changing speaker focus. */
    setSelectedBoard(geometry: string | null): void;
    /**
     * Toggle edit mode: board clicks paint cells (via `onPaintCell`) instead of
     * focusing; the expand glyph becomes the only zoom affordance.
     */
    setEditMode(enabled: boolean): void;
    /** Keep wall management visible but disabled while an authoritative rebuild is in flight. */
    setManagementBusy(busy: boolean): void;
    /**
     * Keep wall management visible but disabled after a failed authoritative
     * update. Pass null once a successful retry makes the wall current again.
     */
    setManagementBlocked(reason: string | null): void;
    /** Re-evaluate the add affordance after capacity inputs such as viewport width change. */
    refreshAddControl(): void;
    /** Replace one board's immutable result data and re-render its current frame. */
    updateBoardData(tiling: TopologyFilmstrip): void;
    /**
     * Drop one board's slot in place, keeping every survivor's rendering and the
     * shared clock exactly where they are (no reload, no server round-trip).
     * Returns false if the board is not on the wall. If the removed board was the
     * hero, the view returns to the gallery first.
     */
    removeBoard(geometry: string): boolean;
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
    /** Change the stable gallery/loading home used by the persistent toolbelt. */
    setHeroToolbeltHome(parent: HTMLElement): void;
    /**
     * Open the existing searchable visual picker for one selected board.
     * Returns false when that geometry is no longer on the wall.
     */
    openReplacePicker(geometry: string, anchor: HTMLElement): boolean;
    /** Close an open board tiling picker; returns whether one was open. */
    closeTilingPicker(): boolean;
    /**
     * Stop and unbind the shared clock, returning the transport to idle
     * (used when a loaded run config invalidates the current filmstrip —
     * the hidden boards must not keep playing on the old clock).
     */
    detachPlayer(): void;
    dispose(): void;
}

interface BoardEntry {
    tiling: TopologyFilmstrip;
    cell: HTMLElement;
    slot: HTMLElement;
    label: HTMLElement;
    countLabel: HTMLElement;
    expandGlyph: HTMLElement;
    preview?: TopologyPreview;
    error?: string;
    overlaid?: boolean;
    svg?: SVGSVGElement;
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

    const wallActions = el("div", "compare-filmstrip-wall-actions");
    const boardsArea = el("div", "compare-filmstrip-boards");
    boardsArea.setAttribute("role", "list");
    boardsArea.setAttribute("aria-label", "Compared tiling boards");
    root.append(wallActions, boardsArea);

    let player = new FilmstripPlayer(0, { loop: options.loop ?? false });
    let unsubscribe: (() => void) | null = null;
    let loadRevision = 0;
    let boards: BoardEntry[] = [];
    let lastRenderedIndex = -1;
    let focusedGeometry: string | null = null;
    let selectedGeometry: string | null = null;
    let heroToolbelt: HTMLElement | null = null;
    let heroToolbeltParent: HTMLElement | null = null;
    let editMode = false;
    let managementBusy = false;
    let managementBlockedReason: string | null = null;

    const managementDisabledReason = (): string | null =>
        managementBusy ? MANAGEMENT_BUSY_REASON : managementBlockedReason;
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
        } else if (heroToolbeltParent) {
            heroToolbeltParent.append(heroToolbelt);
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
            const isSelected = entry.tiling.geometry === selectedGeometry;
            entry.cell.classList.toggle("is-hero", isHero);
            entry.cell.classList.toggle("is-strip", speaker && !isHero);
            entry.cell.classList.toggle("is-selected", isSelected);
            entry.expandGlyph.hidden = isHero;
            if (isSelected) {
                entry.cell.setAttribute("aria-current", "true");
            } else {
                entry.cell.removeAttribute("aria-current");
            }
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
        if (next !== null) {
            selectedGeometry = next;
        }
        applyFocusLayout();
        options.onFocusChange?.(focusedGeometry);
    }

    function setSelectedBoard(geometry: string | null): void {
        selectedGeometry =
            geometry !== null && boards.some((entry) => entry.tiling.geometry === geometry)
                ? geometry
                : null;
        applyFocusLayout();
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
        const label = `${boardName(entry.tiling)} generation ${index}`;
        if (!entry.svg) {
            entry.svg = buildBoardThumbnailSvg(preview, cellsById, {
                size: thumbSize,
                liveColor: getLiveColor(),
                label,
            });
            entry.slot.replaceChildren(entry.svg);
        } else {
            updateBoardThumbnailSvg(entry.svg, cellsById, {
                liveColor: getLiveColor(),
                label,
            });
            if (entry.svg.parentElement !== entry.slot) {
                entry.slot.replaceChildren(entry.svg);
            }
        }
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

    function detachCurrentPlayer(): void {
        transport.detach();
        unsubscribe?.();
        unsubscribe = null;
        lastRenderedIndex = -1;
    }

    function teardownRun(): void {
        detachCurrentPlayer();
        boards = [];
        // A fresh run starts in the gallery; silent so it doesn't fire onFocusChange.
        focusedGeometry = null;
        root.classList.remove("compare-filmstrip--speaker");
        // The selected-tiling actions belong to the Inspector in gallery and
        // loading states. Return the same DOM node before old board slots are
        // replaced so it never becomes detached during a wall transition.
        placeHeroToolbelt();
    }

    function detachPlayer(): void {
        loadRevision += 1;
        detachCurrentPlayer();
    }

    function openBoardTilingPicker(anchor: HTMLElement, tiling?: TopologyFilmstrip): void {
        const pickerKey = tiling?.geometry ?? "add";
        if (openTilingPicker?.dataset.geometry === pickerKey) {
            closeTilingPicker();
            return;
        }
        closeTilingPicker();
        const adding = tiling === undefined;
        const pickerLabel = adding ? "Add tiling" : `Replace ${boardName(tiling)}`;
        const picker = element("div", {
            class: ["compare-board-tiling-picker", adding ? "is-add-picker" : ""]
                .filter(Boolean)
                .join(" "),
            role: "dialog",
            "aria-label": pickerLabel,
        });
        picker.dataset.geometry = pickerKey;
        const close = element("button", {
            class: "compare-board-tiling-picker-close",
            type: "button",
            textContent: "×",
            "aria-label": "Close tiling picker",
        });
        const header = element("div", { class: "compare-board-tiling-picker-header" }, [
            element("strong", { textContent: adding ? "Add tiling" : "Replace tiling" }),
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
                    !`${option.label} ${option.value} ${option.group}`.toLowerCase().includes(query)
                )
                    continue;
                const choice = element("button", {
                    class: "compare-board-tiling-choice",
                    type: "button",
                });
                const disabledReason = managementDisabledReason();
                const isCurrent = option.value === tiling?.geometry;
                const isDuplicate = boards.some(
                    (board) =>
                        board.tiling.geometry === option.value &&
                        board.tiling.geometry !== tiling?.geometry,
                );
                const isIncompatible = options.isTilingAvailable?.(option.value) === false;
                const isAtCapacity = adding && options.canAddBoard?.() === false;
                const unavailableReason =
                    disabledReason ??
                    (isCurrent
                        ? `${option.label} is the current tiling`
                        : isDuplicate
                          ? `${option.label} is already on the wall`
                          : isIncompatible
                            ? `${option.label} is incompatible with the selected rule`
                            : isAtCapacity
                              ? (options.addBoardDisabledReason?.() ??
                                "The wall is at its tiling limit")
                              : null);
                choice.disabled = unavailableReason !== null;
                choice.title =
                    unavailableReason ?? (adding ? `Add ${option.label}` : `Use ${option.label}`);
                choice.classList.toggle("is-current", option.value === tiling?.geometry);
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
                    if (tiling) {
                        if (option.value !== tiling.geometry) {
                            options.onReplaceBoard?.(tiling.geometry, option.value);
                        }
                    } else {
                        options.onAddBoard?.(option.value);
                    }
                    closeTilingPicker();
                });
                list.append(choice);
            }
        };
        close.addEventListener("click", closeTilingPicker);
        search.addEventListener("input", renderChoices);
        picker.append(header, search, list);
        anchor.append(picker);
        openTilingPicker = picker;
        renderChoices();
        search.focus();
    }

    function openReplacePicker(geometry: string, anchor: HTMLElement): boolean {
        const entry = entryFor(geometry);
        if (!entry || !options.tilingOptions || !options.onReplaceBoard) {
            return false;
        }
        openBoardTilingPicker(anchor, entry.tiling);
        return true;
    }

    function updateAddControlState(addButton: HTMLButtonElement): void {
        const disabledReason = managementDisabledReason();
        const hasCapacity = disabledReason === null && options.canAddBoard?.() !== false;
        const hasAvailableTiling =
            hasCapacity &&
            (options.tilingOptions ?? []).some(
                (option) =>
                    !boards.some((board) => board.tiling.geometry === option.value) &&
                    options.isTilingAvailable?.(option.value) !== false,
            );
        addButton.disabled = !hasAvailableTiling;
        addButton.title = disabledReason
            ? disabledReason
            : hasAvailableTiling
              ? "Add another tiling to the wall"
              : hasCapacity
                ? "All compatible tilings are already on the wall"
                : (options.addBoardDisabledReason?.() ?? "The wall is at its tiling limit");
    }

    function createAddControl(): void {
        if (!options.tilingOptions || !options.onAddBoard) {
            return;
        }
        const anchor = el("div", "compare-filmstrip-add-anchor");
        const addButton = element("button", {
            class: "compare-filmstrip-add",
            type: "button",
            "aria-label": "Add tiling",
        });
        addButton.append(
            element("span", {
                class: "compare-filmstrip-add-glyph",
                textContent: "+",
                "aria-hidden": "true",
            }),
            element("span", { textContent: "Add tiling" }),
        );
        updateAddControlState(addButton);
        addButton.addEventListener("click", (event) => {
            event.stopPropagation();
            openBoardTilingPicker(anchor);
        });
        anchor.append(addButton);
        wallActions.append(anchor);
    }

    function refreshManagementControls(): void {
        const addButton = wallActions.querySelector<HTMLButtonElement>(".compare-filmstrip-add");
        if (addButton) {
            updateAddControlState(addButton);
        } else {
            createAddControl();
        }
    }

    function createBoardEntry(tiling: TopologyFilmstrip): BoardEntry {
        const slot = el("div", "compare-filmstrip-slot", "…");
        const label = el("span", "compare-filmstrip-label", boardName(tiling));
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
        cell.append(slot, chrome);
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
            // A live fork owns the hero's slot: its pane handles every pointer
            // interaction there (painting, palette, its own transport), so
            // those clicks must not bubble into unfocusing. Clicking a forked
            // board's tile elsewhere (gallery or strip) still focuses it.
            if (
                focusedGeometry === tiling.geometry &&
                entryFor(tiling.geometry)?.overlaid &&
                slot.contains(target)
            ) {
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
            expandGlyph,
        };
    }

    function syncReusedBoards(filmstrip: SeedFilmstripResult): void {
        for (const [index, entry] of boards.entries()) {
            const tiling = filmstrip.tilings[index]!;
            entry.tiling = tiling;
            entry.label.textContent = boardName(tiling);
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
        const revision = ++loadRevision;
        closeTilingPicker();
        const reuseBoards = Boolean(loadOptions?.preserveBoards) && canReuseBoards(filmstrip);
        if (reuseBoards) {
            detachCurrentPlayer();
            syncReusedBoards(filmstrip);
        } else {
            teardownRun();
            boardsArea.replaceChildren();
            boards = filmstrip.tilings.map((tiling) => createBoardEntry(tiling));
        }
        wallActions.querySelector(".compare-filmstrip-add-anchor")?.remove();
        createAddControl();
        const nextPlayer = new FilmstripPlayer(filmstrip.frame_count, {
            loop: options.loop ?? false,
            ...(loadOptions?.loopStart === undefined ? {} : { loopStart: loadOptions.loopStart }),
        });
        player = nextPlayer;

        unsubscribe = nextPlayer.subscribe(onPlayerIndex);
        transport.attach(nextPlayer);
        // Prime the (still "…") board skeletons before previews load.
        onPlayerIndex(nextPlayer.state);
        applyFocusLayout();

        await Promise.all(boards.map((entry) => ensurePreview(entry)));
        if (revision !== loadRevision || player !== nextPlayer) {
            return;
        }

        // Optional post-load playback overrides (used by the featured demo).
        if (loadOptions?.speedMultiplier !== undefined) {
            transport.setSpeed(loadOptions.speedMultiplier);
        }
        if (loadOptions?.initialFrame !== undefined) {
            nextPlayer.seek(loadOptions.initialFrame);
        }
        if (loadOptions?.autoplay) {
            nextPlayer.play();
        }
    }

    return {
        element: root,
        load,
        focus,
        setSelectedBoard,
        setEditMode(enabled: boolean): void {
            if (editMode === enabled) {
                return;
            }
            editMode = enabled;
            root.classList.toggle("is-editing", editMode);
            applyFocusLayout();
        },
        setManagementBusy(busy: boolean): void {
            managementBusy = busy;
            if (busy) {
                closeTilingPicker();
            }
            refreshManagementControls();
        },
        setManagementBlocked(reason: string | null): void {
            managementBlockedReason = reason;
            if (reason) {
                closeTilingPicker();
            }
            refreshManagementControls();
        },
        refreshAddControl(): void {
            const addButton =
                wallActions.querySelector<HTMLButtonElement>(".compare-filmstrip-add");
            if (addButton) {
                updateAddControlState(addButton);
            } else {
                createAddControl();
            }
        },
        updateBoardData(tiling: TopologyFilmstrip): void {
            const entry = entryFor(tiling.geometry);
            if (entry) {
                entry.tiling = tiling;
                renderBoard(entry, player.index);
            }
        },
        removeBoard(geometry: string): boolean {
            const index = boards.findIndex((entry) => entry.tiling.geometry === geometry);
            if (index < 0) {
                return false;
            }
            const removedEntry = boards[index]!;
            const activeElement =
                document.activeElement instanceof HTMLElement ? document.activeElement : null;
            const restoreBoardFocus =
                activeElement !== null && removedEntry.cell.contains(activeElement);
            const restoreAddFocus =
                activeElement !== null && openTilingPicker?.contains(activeElement) === true;
            // Management refreshes must never leave a detached picker in the
            // controller. The stable Add anchor remains in place and can reopen
            // the picker on the very next activation.
            closeTilingPicker();
            // Dropping the hero returns to the gallery before its slot vanishes.
            if (focusedGeometry === geometry) {
                focus(null);
            }
            boards.splice(index, 1);
            removedEntry.cell.remove();
            // Survivors keep their frames and the clock keeps ticking; just
            // refresh capacity affordances and re-lay-out the stage.
            refreshManagementControls();
            applyFocusLayout();
            if (restoreBoardFocus) {
                const successor = boards[Math.min(index, boards.length - 1)];
                successor?.cell.focus();
            } else if (restoreAddFocus) {
                wallActions.querySelector<HTMLButtonElement>(".compare-filmstrip-add")?.focus();
            }
            return true;
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
                heroToolbeltParent = null;
            }
            if (!heroToolbelt && node) {
                heroToolbeltParent = node.parentElement;
            }
            heroToolbelt = node;
            placeHeroToolbelt();
        },
        setHeroToolbeltHome(parent: HTMLElement): void {
            heroToolbeltParent = parent;
            placeHeroToolbelt();
        },
        openReplacePicker,
        closeTilingPicker,
        detachPlayer,
        dispose(): void {
            closeTilingPicker();
            loadRevision += 1;
            teardownRun();
            root.remove();
        },
    };
}
