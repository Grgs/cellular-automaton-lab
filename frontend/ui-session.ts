import { FRONTEND_DEFAULTS } from "./defaults.js";
import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
} from "./editor-tools.js";
import { parseBrushSize, parseEditorTool } from "./parsers/editor.js";
import { parseUiSession } from "./parsers/session.js";
import { parseStoredUiSession, serializeUiSession } from "./parsers/session-storage.js";
import {
    DEFAULT_CELL_SIZE,
    DEFAULT_TOPOLOGY_SPEC,
} from "./state/constants.js";
import {
    defaultCellSizeForTilingFamily,
} from "./state/sizing-state.js";
import { cloneUiSession, createEmptyUiSession } from "./ui-session-state.js";
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

export function createUiSessionStorage({
    storage = window.localStorage,
    storageKey = UI_SESSION_STORAGE_KEY,
}: {
    storage?: Storage;
    storageKey?: string;
} = {}): UiSessionStorage {
    let sessionCache: UiSessionState | null = null;
    const defaultTilingFamily = DEFAULT_TOPOLOGY_SPEC.tiling_family;

    function readStorage(): UiSessionState {
        try {
            const raw = storage.getItem(storageKey);
            if (!raw) {
                return createEmptyUiSession(defaultTilingFamily);
            }
            return parseStoredUiSession(JSON.parse(raw), {
                disclosureIds: DISCLOSURE_IDS,
                defaultTilingFamily,
            });
        } catch (error) {
            void error;
            return createEmptyUiSession(defaultTilingFamily);
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
            storage.setItem(storageKey, JSON.stringify(serializeUiSession(ensureLoaded(), {
                disclosureIds: DISCLOSURE_IDS,
                defaultTilingFamily,
            })));
        } catch (error) {
            void error;
        }
    }

    function update(mutator: (session: UiSessionState) => void): UiSessionState {
        const nextSession = cloneUiSession(ensureLoaded());
        mutator(nextSession);
        sessionCache = parseUiSession(nextSession, {
            disclosureIds: DISCLOSURE_IDS,
            defaultTilingFamily,
        });
        flush();
        return cloneUiSession(sessionCache);
    }

    function load(): UiSessionState {
        return cloneUiSession(ensureLoaded());
    }

    return {
        load,
        clear() {
            sessionCache = createEmptyUiSession(defaultTilingFamily);
            try {
                storage.removeItem(storageKey);
            } catch (error) {
                void error;
            }
            return cloneUiSession(sessionCache);
        },
        getCellSizes() {
            return { ...ensureLoaded().cellSizeByTilingFamily };
        },
        getCellSize(tilingFamily = DEFAULT_TOPOLOGY_SPEC.tiling_family) {
            return ensureLoaded().cellSizeByTilingFamily[String(tilingFamily)]
                ?? defaultCellSizeForTilingFamily(tilingFamily);
        },
        getUnsafeSizingEnabled() {
            return Boolean(ensureLoaded().unsafeSizingEnabled);
        },
        getTileColorsEnabled() {
            return ensureLoaded().tileColorsEnabled !== false;
        },
        setDefaultCellSize(cellSize) {
            return update((session) => {
                const normalizedSession = parseUiSession({
                    ...session,
                    cellSizeByTilingFamily: {
                        ...session.cellSizeByTilingFamily,
                        [DEFAULT_TOPOLOGY_SPEC.tiling_family]: cellSize,
                    },
                }, {
                    disclosureIds: DISCLOSURE_IDS,
                    defaultTilingFamily,
                });
                Object.assign(session, normalizedSession);
            });
        },
        setCellSizeForTilingFamily(tilingFamily, cellSize) {
            return update((session) => {
                const normalizedSession = parseUiSession({
                    ...session,
                    cellSizeByTilingFamily: {
                        ...session.cellSizeByTilingFamily,
                        [String(tilingFamily)]: cellSize,
                    },
                }, {
                    disclosureIds: DISCLOSURE_IDS,
                    defaultTilingFamily,
                });
                Object.assign(session, normalizedSession);
            });
        },
        setUnsafeSizingEnabled(enabled) {
            return update((session) => {
                const normalizedSession = parseUiSession({
                    ...session,
                    unsafeSizingEnabled: Boolean(enabled),
                }, {
                    disclosureIds: DISCLOSURE_IDS,
                    defaultTilingFamily,
                });
                Object.assign(session, normalizedSession);
            });
        },
        setTileColorsEnabled(enabled) {
            return update((session) => {
                const normalizedSession = parseUiSession({
                    ...session,
                    tileColorsEnabled: enabled !== false,
                }, {
                    disclosureIds: DISCLOSURE_IDS,
                    defaultTilingFamily,
                });
                Object.assign(session, normalizedSession);
            });
        },
        getEditorTool() {
            return ensureLoaded().editorTool;
        },
        setEditorTool(editorTool: EditorTool) {
            return update((session) => {
                session.editorTool = parseEditorTool(editorTool);
            });
        },
        getBrushSize() {
            return ensureLoaded().brushSize;
        },
        setBrushSize(brushSize) {
            return update((session) => {
                session.brushSize = parseBrushSize(brushSize);
            });
        },
        getDrawerOpen() {
            return ensureLoaded().drawerOpen;
        },
        setDrawerOpen(drawerOpen) {
            return update((session) => {
                session.drawerOpen = Boolean(drawerOpen);
            });
        },
        getPaintState(ruleName) {
            if (!ruleName) {
                return null;
            }
            return ensureLoaded().paintStatesByRule[ruleName] ?? null;
        },
        setPaintStateForRule(ruleName, paintState) {
            return update((session) => {
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
        setPatchDepthForTilingFamily(tilingFamily, patchDepth) {
            return update((session) => {
                const normalizedSession = parseUiSession({
                    ...session,
                    patchDepthByTilingFamily: {
                        ...session.patchDepthByTilingFamily,
                        [tilingFamily]: patchDepth,
                    },
                }, {
                    disclosureIds: DISCLOSURE_IDS,
                    defaultTilingFamily,
                });
                Object.assign(session, normalizedSession);
            });
        },
        getDisclosureStates() {
            return { ...ensureLoaded().disclosures };
        },
        setDisclosureState(id, open) {
            return update((session) => {
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
