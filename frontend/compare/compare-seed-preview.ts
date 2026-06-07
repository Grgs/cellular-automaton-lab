/**
 * A live strip showing where the drawn seed lands on the first few selected
 * tilings, updated as you draw. It fetches each tiling's geometry and canonical
 * cell order once (cached), then places the seed bit-string client-side — the
 * same mapping the comparison uses — and renders a begin-state thumbnail.
 */

import type { SimulationBackend } from "../types/controller.js";
import type { TopologyPreview } from "../types/domain.js";
import { buildBoardThumbnailSvg } from "./compare-thumbnail.js";
import { toBits } from "./compare-seed-pad.js";

const DEFAULT_MAX_TILINGS = 4;
const THUMB_SIZE = 96;
const REDRAW_DEBOUNCE_MS = 80;

export interface SeedPreviewTiling {
    geometry: string;
    label: string;
}

export interface SeedPreviewOptions {
    backend: SimulationBackend;
    getSeed(): string;
    getTraversal(): string;
    getGridSize(): number;
    /** Selected tilings in display order; only the first few are previewed. */
    getTilings(): SeedPreviewTiling[];
    /** Named shape for Policy-A placement, or "" for bit-string seeding. */
    getPattern?(): string;
    getPreviewHref?(entry: {
        cellsById: Record<string, number>;
        geometry: string;
        label: string;
        preview: TopologyPreview;
    }): string | null;
    maxTilings?: number;
}

export interface SeedPreviewController {
    element: HTMLElement;
    /** Re-evaluate which tilings to show and refetch geometry as needed. */
    refresh(): void;
    /** Re-render thumbnails from cached geometry for the current seed (debounced). */
    redraw(): void;
    dispose(): void;
}

/** Place a seed bit-string onto a tiling's canonical cell order. */
export function placeSeedOnOrder(order: readonly string[], bits: string): Record<string, number> {
    const cellsById: Record<string, number> = {};
    const limit = Math.min(order.length, bits.length);
    for (let index = 0; index < limit; index += 1) {
        if (bits[index] === "1") {
            const id = order[index];
            if (id !== undefined) {
                cellsById[id] = 1;
            }
        }
    }
    return cellsById;
}

function el(tag: string, className: string, text?: string): HTMLElement {
    const node = document.createElement(tag);
    node.className = className;
    if (text !== undefined) {
        node.textContent = text;
    }
    return node;
}

function thumbnailLink(href: string, label: string, thumbnail: SVGSVGElement): HTMLAnchorElement {
    const anchor = document.createElement("a");
    anchor.className = "compare-thumb-link";
    anchor.href = href;
    anchor.target = "_blank";
    anchor.rel = "noopener";
    anchor.title = `Open ${label} seed placement`;
    anchor.setAttribute("aria-label", `Open ${label} seed placement`);
    anchor.append(thumbnail);
    return anchor;
}

interface PreviewEntry {
    geometry: string;
    label: string;
    slot?: HTMLElement;
    preview?: TopologyPreview;
    error?: string;
}

export function createSeedPreview(options: SeedPreviewOptions): SeedPreviewController {
    const root = el("div", "compare-seedpreview");
    const cache = new Map<string, Promise<TopologyPreview>>();
    let entries: PreviewEntry[] = [];
    let redrawTimer: number | null = null;

    function currentPattern(): string {
        return options.getPattern?.() ?? "";
    }

    function cacheKey(geometry: string): string {
        const pattern = currentPattern();
        return pattern
            ? `${geometry}:${options.getGridSize()}:shape:${pattern}`
            : `${geometry}:${options.getGridSize()}:${options.getTraversal()}`;
    }

    function fetchPreview(geometry: string): Promise<TopologyPreview> {
        const key = cacheKey(geometry);
        let pending = cache.get(key);
        if (!pending) {
            const pattern = currentPattern();
            pending = options.backend.previewTopology({
                geometry,
                grid_size: options.getGridSize(),
                ...(pattern ? { pattern } : { traversal: options.getTraversal() }),
            });
            cache.set(key, pending);
        }
        return pending;
    }

    function renderEntry(entry: PreviewEntry): void {
        const slot = entry.slot;
        if (!slot) {
            return;
        }
        if (entry.error) {
            slot.textContent = entry.error.includes("limit") ? "too large" : "unavailable";
            return;
        }
        if (!entry.preview) {
            slot.textContent = "…";
            return;
        }
        const cellsById = currentPattern()
            ? (entry.preview.shape_cells ?? {})
            : placeSeedOnOrder(entry.preview.order ?? [], toBits(options.getSeed()));
        const thumbnail = buildBoardThumbnailSvg(entry.preview, cellsById, {
            size: THUMB_SIZE,
            liveColor: () => "var(--accent, #bf5a36)",
            label: `${entry.label} seed placement`,
        });
        const href =
            options.getPreviewHref?.({
                cellsById,
                geometry: entry.geometry,
                label: entry.label,
                preview: entry.preview,
            }) ?? null;
        slot.replaceChildren(href ? thumbnailLink(href, entry.label, thumbnail) : thumbnail);
    }

    function renderSkeleton(): void {
        root.replaceChildren();
        if (entries.length === 0) {
            root.append(
                el("div", "compare-seedpreview-empty", "Select tilings to preview the seed."),
            );
            return;
        }
        for (const entry of entries) {
            const slot = el("div", "compare-seedpreview-slot", "…");
            entry.slot = slot;
            const item = el("div", "compare-seedpreview-item");
            item.append(el("div", "compare-seedpreview-label", entry.label), slot);
            root.append(item);
        }
    }

    function refresh(): void {
        const limit = options.maxTilings ?? DEFAULT_MAX_TILINGS;
        entries = options
            .getTilings()
            .slice(0, limit)
            .map((tiling) => ({ geometry: tiling.geometry, label: tiling.label }));
        renderSkeleton();
        for (const entry of entries) {
            fetchPreview(entry.geometry).then(
                (preview) => {
                    entry.preview = preview;
                    delete entry.error;
                    renderEntry(entry);
                },
                (error: unknown) => {
                    entry.error = error instanceof Error ? error.message : String(error);
                    renderEntry(entry);
                },
            );
        }
    }

    function redraw(): void {
        if (redrawTimer !== null) {
            window.clearTimeout(redrawTimer);
        }
        redrawTimer = window.setTimeout(() => {
            redrawTimer = null;
            for (const entry of entries) {
                renderEntry(entry);
            }
        }, REDRAW_DEBOUNCE_MS);
    }

    renderSkeleton();

    return {
        element: root,
        refresh,
        redraw,
        dispose(): void {
            if (redrawTimer !== null) {
                window.clearTimeout(redrawTimer);
            }
        },
    };
}
