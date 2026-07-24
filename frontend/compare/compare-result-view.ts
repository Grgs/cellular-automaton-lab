import type { SimulationBackend } from "../types/controller.js";
import type {
    PatternPayload,
    SeedComparisonResult,
    TopologyComparisonResultPayload,
    TopologyPreview,
} from "../types/domain.js";
import { buildShareUrl } from "../share-link.js";
import { buildComparisonStatePattern } from "./compare-patterns.js";
import {
    buildClassificationGrid,
    buildPhasePortraitSvg,
    buildPortraitLegend,
} from "./compare-charts.js";
import { element as el } from "./compare-dom.js";
import { buildBoardThumbnailSvg } from "./compare-thumbnail.js";

// Matches _MAX_PREVIEW_CELLS in backend/simulation/topology_preview.py; larger
// patches are not offered a thumbnail (the backend would reject them anyway).
const MAX_PREVIEW_CELLS = 10000;

interface ActionMenuItem {
    label: string;
    title: string;
    onClick(): void;
}

export type CompareResultViewController = readonly [
    element: HTMLElement,
    render: (comparison: SeedComparisonResult) => void,
    open: (pattern: PatternPayload) => Promise<void>,
    closeMenu: () => boolean,
    dispose: () => void,
];

export function createCompareResultView(
    backend: Pick<SimulationBackend, "previewTopology">,
    labels: ReadonlyMap<string, string>,
    getLiveColor: (ruleName: string) => (state: number) => string,
    onHighlight: (geometry: string | null) => void,
    status: HTMLElement,
    onOpenPattern: ((pattern: PatternPayload) => void | Promise<void>) | undefined,
    onRequestClose: (() => void) | undefined,
): CompareResultViewController {
    const element = el("div", { class: "compare-results" });
    const previewCache = new Map<string, Promise<TopologyPreview>>();

    function render(comparison: SeedComparisonResult): void {
        element.replaceChildren();
        if (comparison.degenerate) {
            element.append(
                el("div", {
                    class: "compare-warning",
                    textContent:
                        "This seed extincts quickly on most selected tilings — not a meaningful comparison. Try a larger seed, different rule, or more steps.",
                }),
            );
        }
        const legend = buildPortraitLegend(comparison);
        element.append(
            el("div", {
                class: "compare-section-title",
                textContent: "Phase portrait — live(t) / live(0)",
            }),
            buildPhasePortraitSvg(comparison),
            ...(legend ? [legend] : []),
            el("div", { class: "compare-section-title", textContent: "End-state classification" }),
            el("div", { class: "compare-grid-scroll" }, [
                buildClassificationGrid(comparison, {
                    onRowHover: onHighlight,
                    renderRowActions: (result) => renderRowActions(comparison, result),
                    labelForGeometry: (geometry) => labels.get(geometry),
                }),
            ]),
        );
    }

    function renderRowActions(
        comparison: SeedComparisonResult,
        result: TopologyComparisonResultPayload,
    ): Node | null {
        const begin = buildComparisonStatePattern(comparison, result, "begin");
        if (!begin) {
            return null;
        }
        const end = buildComparisonStatePattern(comparison, result, "end");
        const wrap = el("div", { class: "compare-row-actions" });
        const beginTitle = onOpenPattern
            ? "Load the seed on this tiling into the board"
            : "Open the seed on this tiling in a new tab";
        const openItems: ActionMenuItem[] = [
            {
                label: "Begin",
                title: beginTitle,
                onClick: () => void openPattern(begin),
            },
        ];
        if (end) {
            const endTitle = onOpenPattern
                ? "Load the final state on this tiling into the board"
                : "Open the final state on this tiling in a new tab";
            openItems.push({
                label: "End",
                title: endTitle,
                onClick: () => void openPattern(end),
            });
        }
        wrap.append(actionMenu("Open", "Open state", openItems));
        if (end) {
            // Symmetric with the open buttons: a shareable link for either state.
            wrap.append(
                actionMenu("Copy", "Copy share link", [
                    copyLinkMenuItem(begin, "Begin", "Copy a shareable link to the seed state"),
                    copyLinkMenuItem(end, "End", "Copy a shareable link to the final state"),
                ]),
            );
        } else {
            wrap.append(
                actionMenu("Copy", "Copy share link", [
                    copyLinkMenuItem(begin, "Link", "Copy a shareable link to this state"),
                ]),
            );
        }
        if (result.topology_spec && result.cell_count > 0) {
            if (result.cell_count <= MAX_PREVIEW_CELLS) {
                const previewButton = el(
                    "button",
                    {
                        class: "compare-link",
                        type: "button",
                        title: "Show begin/end thumbnails",
                    },
                    ["▸ preview"],
                );
                previewButton.addEventListener("click", () =>
                    togglePreview(comparison, result, previewButton),
                );
                wrap.append(previewButton);
            } else {
                // Too dense for a useful 132 px thumbnail; say so rather than
                // silently dropping the preview affordance.
                wrap.append(
                    el("span", {
                        class: "compare-row-note",
                        textContent: "preview too large",
                        title: `${result.cell_count.toLocaleString()} cells exceeds the ${MAX_PREVIEW_CELLS.toLocaleString()}-cell preview limit`,
                    }),
                );
            }
        }
        return wrap;
    }

    function patternShareUrl(pattern: PatternPayload): string {
        return buildShareUrl(pattern, location.href);
    }

    async function openPattern(pattern: PatternPayload): Promise<void> {
        if (onOpenPattern) {
            await onOpenPattern(pattern);
            onRequestClose?.();
            return;
        }
        open(patternShareUrl(pattern), "_blank", "noopener");
    }

    function fetchPreview(result: TopologyComparisonResultPayload): Promise<TopologyPreview> {
        const spec = result.topology_spec;
        const key = `${result.geometry}:${spec?.width}x${spec?.height}:${spec?.patch_depth}`;
        let pending = previewCache.get(key);
        if (!pending) {
            pending = backend.previewTopology({
                geometry: result.geometry,
                width: spec?.width ?? 16,
                height: spec?.height ?? 16,
                ...(spec?.patch_depth === undefined ? {} : { patch_depth: spec.patch_depth }),
            });
            previewCache.set(key, pending);
        }
        return pending;
    }

    function thumbnailBlock(
        label: string,
        preview: TopologyPreview,
        cellsById: Record<string, number>,
        liveColor: (state: number) => string,
        pattern: PatternPayload | null,
    ): HTMLElement {
        const thumbnail = buildBoardThumbnailSvg(preview, cellsById, {
            liveColor,
            label: `${label} state`,
        });
        const media = pattern
            ? el(
                  "a",
                  {
                      class: "compare-thumb-link",
                      href: patternShareUrl(pattern),
                      target: "_blank",
                      rel: "noopener",
                      title: `Open ${label.toLowerCase()} state in a new tab`,
                      "aria-label": `Open ${label.toLowerCase()} state in a new tab`,
                  },
                  [thumbnail],
              )
            : thumbnail;
        return el("div", { class: "compare-thumb-block" }, [
            el("div", { class: "compare-thumb-label", textContent: label }),
            media,
        ]);
    }

    function togglePreview(
        comparison: SeedComparisonResult,
        result: TopologyComparisonResultPayload,
        button: HTMLButtonElement,
    ): void {
        const row = button.closest("tr");
        if (!row) {
            return;
        }
        const sibling = row.nextElementSibling;
        if (sibling instanceof HTMLElement && sibling.classList.contains("compare-detail")) {
            sibling.remove();
            button.textContent = "▸ preview";
            return;
        }
        button.textContent = "▾ preview";
        const cell = el("td", { class: "compare-detail-cell" });
        cell.colSpan = row.children.length;
        cell.append(el("div", { class: "compare-detail-status", textContent: "Loading preview…" }));
        const detail = el("tr", { class: "compare-detail" }, [cell]);
        row.after(detail);
        void renderPreviewInto(comparison, result, cell);
    }

    async function renderPreviewInto(
        comparison: SeedComparisonResult,
        result: TopologyComparisonResultPayload,
        cell: HTMLTableCellElement,
    ): Promise<void> {
        try {
            const preview = await fetchPreview(result);
            const liveColor = getLiveColor(comparison.rule_name);
            cell.replaceChildren(
                el("div", { class: "compare-detail-grid" }, [
                    thumbnailBlock(
                        "Begin",
                        preview,
                        result.initial_cells_by_id ?? {},
                        liveColor,
                        buildComparisonStatePattern(comparison, result, "begin"),
                    ),
                    thumbnailBlock(
                        "End",
                        preview,
                        result.final_cells_by_id ?? {},
                        liveColor,
                        buildComparisonStatePattern(comparison, result, "end"),
                    ),
                ]),
            );
        } catch (error) {
            cell.replaceChildren(
                el("div", {
                    class: "compare-detail-status",
                    textContent: `Preview failed: ${error instanceof Error ? error.message : String(error)}`,
                }),
            );
        }
    }

    function actionMenu(label: string, title: string, items: ActionMenuItem[]): HTMLElement {
        const details = el("details", { class: "compare-action-menu" });
        const summary = el("summary", { class: "compare-link", title, textContent: label });
        const panel = el(
            "div",
            { class: "compare-action-menu-panel" },
            items.map((item) => {
                const button = el("button", {
                    class: "compare-action-menu-item",
                    type: "button",
                    title: item.title,
                    textContent: item.label,
                });
                button.addEventListener("click", () => {
                    details.removeAttribute("open");
                    item.onClick();
                });
                return button;
            }),
        );
        details.append(summary, panel);
        return details;
    }

    function copyLinkMenuItem(
        pattern: PatternPayload,
        label: string,
        title: string,
    ): ActionMenuItem {
        return {
            label,
            title,
            onClick: () => copyPatternLink(pattern, label),
        };
    }

    function copyPatternLink(pattern: PatternPayload, copiedLabel: string): void {
        const url = patternShareUrl(pattern);
        const clipboard = navigator.clipboard;
        if (!clipboard) {
            prompt("Copy this share link:", url);
            return;
        }
        void clipboard.writeText(url).then(
            () => {
                status.textContent = `Copied ${copiedLabel.toLowerCase()} share link.`;
            },
            () => prompt("Copy this share link:", url),
        );
    }

    // Native <details> menus stay open until re-clicked; close any open one when
    // the click lands outside it so only one menu is ever open at a time.
    function onDocumentPointerDown(event: Event): void {
        const target = event.target;
        for (const menu of element.querySelectorAll(".compare-action-menu[open]")) {
            if (!(target instanceof Node) || !menu.contains(target)) {
                menu.removeAttribute("open");
            }
        }
    }

    function closeMenu(): boolean {
        const openMenu = element.querySelector(".compare-action-menu[open]");
        if (!openMenu) {
            return false;
        }
        openMenu.removeAttribute("open");
        return true;
    }

    document.addEventListener("pointerdown", onDocumentPointerDown);

    return [
        element,
        render,
        openPattern,
        closeMenu,
        (): void => {
            document.removeEventListener("pointerdown", onDocumentPointerDown);
        },
    ];
}
