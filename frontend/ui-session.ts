import { FRONTEND_DEFAULTS } from "./defaults.js";
import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
} from "./editor-tools.js";
import { parseBrushSize, parseEditorTool } from "./parsers/editor.js";
import { parseUiSession } from "./parsers/session.js";
import {
    DEFAULT_CELL_SIZE,
    DEFAULT_TOPOLOGY_SPEC,
} from "./state/constants.js";
import {
    defaultCellSizeForTilingFamily,
} from "./state/sizing-state.js";
import type { DomElements } from "./types/dom.js";
import type { EditorTool } from "./editor-tools.js";
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
            return parseUiSession(JSON.parse(raw), { disclosureIds: DISCLOSURE_IDS });
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
            storage.setItem(storageKey, JSON.stringify(parseUiSession(ensureLoaded(), {
                disclosureIds: DISCLOSURE_IDS,
            })));
        } catch (error) {
            void error;
        }
    }

    function update(mutator: (session: UiSessionState) => void): UiSessionState {
        const nextSession = cloneSession(ensureLoaded());
        mutator(nextSession);
        sessionCache = parseUiSession(nextSession, { disclosureIds: DISCLOSURE_IDS });
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
                const normalizedSession = parseUiSession({
                    ...session,
                    cellSizeByTilingFamily: {
                        ...session.cellSizeByTilingFamily,
                        [String(tilingFamily)]: nextCellSize,
                    },
                }, { disclosureIds: DISCLOSURE_IDS });
                Object.assign(session, normalizedSession);
            });
        },
        getEditorTool() {
            return ensureLoaded().editorTool;
        },
        setEditorTool(editorTool: EditorTool) {
            update((session) => {
                session.editorTool = parseEditorTool(editorTool);
            });
        },
        getBrushSize() {
            return ensureLoaded().brushSize;
        },
        setBrushSize(brushSize) {
            update((session) => {
                session.brushSize = parseBrushSize(brushSize);
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
                const normalizedSession = parseUiSession({
                    ...session,
                    patchDepthByTilingFamily: {
                        ...session.patchDepthByTilingFamily,
                        [tilingFamily]: patchDepth,
                    },
                }, { disclosureIds: DISCLOSURE_IDS });
                Object.assign(session, normalizedSession);
            });
        },
        getDisclosureStates() {
            return { ...ensureLoaded().disclosures };
        },
        setDisclosureState(id, open) {
            if (!DISCLOSURE_IDS.includes(id)) {
                return;
            }
            update((session) => {
                session.disclosures[id] = Boolean(open);
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
