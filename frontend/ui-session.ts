import { FRONTEND_DEFAULTS } from "./defaults.js";
import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
    normalizeBrushSize,
    normalizeEditorTool,
} from "./editor-tools.js";
import {
    DEFAULT_CELL_SIZE,
    DEFAULT_TOPOLOGY_SPEC,
} from "./state/constants.js";
import {
    defaultCellSizeForTilingFamily,
    normalizeCellSizeForTilingFamily,
    normalizePatchDepthForTilingFamily,
} from "./state/sizing-state.js";
import type { DomElements } from "./types/dom.js";
import type {
    MatchMediaResult,
    UiDisclosureId,
    UiSessionState,
    UiSessionStorage,
} from "./types/session.js";

export const UI_SESSION_STORAGE_KEY = FRONTEND_DEFAULTS.ui.storage_key;
export const DISCLOSURE_IDS: readonly UiDisclosureId[] = Object.freeze([
    "rule-notes-toggle",
]);

function emptySession(): UiSessionState {
    return {
        cellSize: DEFAULT_CELL_SIZE,
        cellSizeByTilingFamily: {},
        editorTool: DEFAULT_EDITOR_TOOL,
        brushSize: DEFAULT_BRUSH_SIZE,
        drawerOpen: null,
        paintStatesByRule: {},
        patchDepthByTilingFamily: {},
        disclosures: {},
    };
}

function normalizePaintStatesByRule(value: unknown): Record<string, number> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return {};
    }

    return Object.fromEntries(
        Object.entries(value)
            .filter(([ruleName]) => typeof ruleName === "string" && ruleName.length > 0)
            .map(([ruleName, state]) => [ruleName, Number(state)])
            .filter(([, state]) => Number.isInteger(state)),
    );
}

function normalizeCellSizeByTilingFamily(value: unknown): Record<string, number> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return {};
    }

    return Object.fromEntries(
        Object.entries(value)
            .filter(([tilingFamily]) => typeof tilingFamily === "string" && tilingFamily.length > 0)
            .map(([tilingFamily, cellSize]) => [
                tilingFamily,
                normalizeCellSizeForTilingFamily(tilingFamily, cellSize),
            ])
            .filter(([, cellSize]) => Number.isInteger(cellSize)),
    );
}

function normalizeDisclosures(value: unknown): Partial<Record<UiDisclosureId, boolean>> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return {};
    }

    return Object.fromEntries(
        DISCLOSURE_IDS.map((id) => [id, Boolean((value as Record<string, unknown>)[id])]),
    ) as Partial<Record<UiDisclosureId, boolean>>;
}

function normalizePatchDepthByTilingFamily(value: unknown): Record<string, number> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return {};
    }

    return Object.fromEntries(
        Object.entries(value)
            .filter(([tilingFamily]) => typeof tilingFamily === "string" && tilingFamily.length > 0)
            .map(([tilingFamily, patchDepth]) => [
                tilingFamily,
                normalizePatchDepthForTilingFamily(tilingFamily, patchDepth),
            ])
            .filter(([, patchDepth]) => Number.isInteger(patchDepth)),
    );
}

export function normalizeUiSession(value: unknown): UiSessionState {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return emptySession();
    }

    const rawValue = value as Record<string, unknown>;
    const session = emptySession();
    if (rawValue.cellSizeByTilingFamily && typeof rawValue.cellSizeByTilingFamily === "object") {
        session.cellSizeByTilingFamily = normalizeCellSizeByTilingFamily(rawValue.cellSizeByTilingFamily);
    } else if (rawValue.cellSize !== null && rawValue.cellSize !== undefined) {
        session.cellSizeByTilingFamily = {
            [DEFAULT_TOPOLOGY_SPEC.tiling_family]: normalizeCellSizeForTilingFamily(
                DEFAULT_TOPOLOGY_SPEC.tiling_family,
                rawValue.cellSize,
            ),
        };
    }
    if (rawValue.editorTool !== null && rawValue.editorTool !== undefined) {
        session.editorTool = normalizeEditorTool(rawValue.editorTool);
    }
    if (rawValue.brushSize !== null && rawValue.brushSize !== undefined) {
        session.brushSize = normalizeBrushSize(rawValue.brushSize);
    }
    if (rawValue.drawerOpen !== null && rawValue.drawerOpen !== undefined) {
        session.drawerOpen = Boolean(rawValue.drawerOpen);
    }
    session.paintStatesByRule = normalizePaintStatesByRule(rawValue.paintStatesByRule);
    session.patchDepthByTilingFamily = normalizePatchDepthByTilingFamily(rawValue.patchDepthByTilingFamily);
    session.disclosures = normalizeDisclosures(rawValue.disclosures);
    session.cellSize = session.cellSizeByTilingFamily[DEFAULT_TOPOLOGY_SPEC.tiling_family]
        ?? defaultCellSizeForTilingFamily(DEFAULT_TOPOLOGY_SPEC.tiling_family);
    return session;
}

function cloneSession(session: UiSessionState): UiSessionState {
    return {
        cellSize: session.cellSize,
        cellSizeByTilingFamily: { ...session.cellSizeByTilingFamily },
        editorTool: session.editorTool,
        brushSize: session.brushSize,
        drawerOpen: session.drawerOpen,
        paintStatesByRule: { ...session.paintStatesByRule },
        patchDepthByTilingFamily: { ...session.patchDepthByTilingFamily },
        disclosures: { ...session.disclosures },
    };
}

export function createUiSessionStorage({
    storage = window.localStorage,
    storageKey = UI_SESSION_STORAGE_KEY,
}: {
    storage?: Storage;
    storageKey?: string;
} = {}): UiSessionStorage {
    let sessionCache: UiSessionState | null = null;

    function readStorage(): UiSessionState {
        try {
            const raw = storage.getItem(storageKey);
            if (!raw) {
                return emptySession();
            }
            return normalizeUiSession(JSON.parse(raw));
        } catch (error) {
            void error;
            return emptySession();
        }
    }

    function ensureLoaded(): UiSessionState {
        if (sessionCache === null) {
            sessionCache = readStorage();
        }
        return sessionCache;
    }

    function flush(): void {
        try {
            storage.setItem(storageKey, JSON.stringify(normalizeUiSession(ensureLoaded())));
        } catch (error) {
            void error;
        }
    }

    function update(mutator: (session: UiSessionState) => void): UiSessionState {
        const nextSession = cloneSession(ensureLoaded());
        mutator(nextSession);
        sessionCache = normalizeUiSession(nextSession);
        flush();
        return cloneSession(sessionCache);
    }

    function load(): UiSessionState {
        return cloneSession(ensureLoaded());
    }

    return {
        load,
        clear() {
            sessionCache = emptySession();
            try {
                storage.removeItem(storageKey);
            } catch (error) {
                void error;
            }
            return cloneSession(sessionCache);
        },
        getCellSizes() {
            return { ...ensureLoaded().cellSizeByTilingFamily };
        },
        getCellSize(tilingFamily = DEFAULT_TOPOLOGY_SPEC.tiling_family) {
            return ensureLoaded().cellSizeByTilingFamily[String(tilingFamily)]
                ?? defaultCellSizeForTilingFamily(tilingFamily);
        },
        setCellSize(tilingFamilyOrCellSize, cellSize = undefined) {
            const tilingFamily = cellSize === undefined
                ? DEFAULT_TOPOLOGY_SPEC.tiling_family
                : String(tilingFamilyOrCellSize);
            const nextCellSize = cellSize === undefined ? tilingFamilyOrCellSize : cellSize;
            return update((session) => {
                session.cellSizeByTilingFamily[String(tilingFamily)] = normalizeCellSizeForTilingFamily(
                    tilingFamily,
                    nextCellSize,
                );
                session.cellSize = session.cellSizeByTilingFamily[DEFAULT_TOPOLOGY_SPEC.tiling_family]
                    ?? defaultCellSizeForTilingFamily(DEFAULT_TOPOLOGY_SPEC.tiling_family);
            });
        },
        getEditorTool() {
            return ensureLoaded().editorTool;
        },
        setEditorTool(editorTool) {
            update((session) => {
                session.editorTool = normalizeEditorTool(editorTool);
            });
        },
        getBrushSize() {
            return ensureLoaded().brushSize;
        },
        setBrushSize(brushSize) {
            update((session) => {
                session.brushSize = normalizeBrushSize(brushSize);
            });
        },
        getDrawerOpen() {
            return ensureLoaded().drawerOpen;
        },
        setDrawerOpen(drawerOpen) {
            update((session) => {
                session.drawerOpen = Boolean(drawerOpen);
            });
        },
        getPaintState(ruleName) {
            if (!ruleName) {
                return null;
            }
            return ensureLoaded().paintStatesByRule[ruleName] ?? null;
        },
        setPaintState(ruleName, paintState) {
            if (!ruleName) {
                return;
            }
            update((session) => {
                session.paintStatesByRule[ruleName] = Number(paintState);
            });
        },
        getPatchDepths() {
            return { ...ensureLoaded().patchDepthByTilingFamily };
        },
        getPatchDepth(tilingFamily) {
            if (!tilingFamily) {
                return null;
            }
            return ensureLoaded().patchDepthByTilingFamily[tilingFamily] ?? null;
        },
        setPatchDepth(tilingFamily, patchDepth) {
            if (!tilingFamily) {
                return;
            }
            update((session) => {
                session.patchDepthByTilingFamily[tilingFamily] = normalizePatchDepthForTilingFamily(
                    tilingFamily,
                    patchDepth,
                );
            });
        },
        getDisclosureStates() {
            return { ...ensureLoaded().disclosures };
        },
        setDisclosureState(id, open) {
            if (!DISCLOSURE_IDS.includes(id as UiDisclosureId)) {
                return;
            }
            update((session) => {
                session.disclosures[id as UiDisclosureId] = Boolean(open);
            });
        },
    };
}

export function applyDisclosureState(
    elements: DomElements,
    disclosureStates: Partial<Record<UiDisclosureId, boolean>> = {},
): void {
    for (const id of DISCLOSURE_IDS) {
        const element = elements[id];
        if (!element) {
            continue;
        }
        if (Object.prototype.hasOwnProperty.call(disclosureStates, id)) {
            element.open = Boolean(disclosureStates[id]);
        }
    }
}
