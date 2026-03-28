import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
} from "./editor-tools.js";
import { parseEditorTool } from "./parsers/editor.js";
import {
    clearPendingPatchDepth,
    rememberedCellSizeForTilingFamily,
    setPatchDepthMemoryMap,
    setCellSize,
    setCellSizeMemoryMap,
} from "./state/sizing-state.js";
import {
    setBrushSize,
    setEditorTool,
    setSelectedPaintState,
} from "./state/simulation-state.js";
import { setDrawerOpen } from "./state/overlay-state.js";
import { currentEditorRule } from "./state/selectors.js";
import { applyDisclosureState, createUiSessionStorage, DISCLOSURE_IDS } from "./ui-session.js";
import type { DomElements } from "./types/dom.js";
import type {
    CreateUiSessionStorageFunction,
    MatchMediaFunction,
    UiSessionController,
} from "./types/controller.js";
import type { AppState } from "./types/state.js";
import type { UiDisclosureId, UiSessionStorage } from "./types/session.js";
import type { EditorTool } from "./editor-tools.js";

function readStoredCellSizes(storage: UiSessionStorage, activeTilingFamily: string): Record<string, number> {
    if (typeof storage.getCellSizes === "function") {
        return storage.getCellSizes();
    }

    if (typeof storage.getCellSize !== "function") {
        return {};
    }

    return {
        [activeTilingFamily]: storage.getCellSize(activeTilingFamily),
    };
}

function readStoredPatchDepths(storage: UiSessionStorage): Record<string, number> {
    if (typeof storage.getPatchDepths === "function") {
        return storage.getPatchDepths();
    }
    return {};
}

export function createUiSessionController({
    state,
    elements,
    createUiSessionStorage: createUiSessionStorageFn = createUiSessionStorage,
    applyDisclosureStateFn = applyDisclosureState,
    currentEditorRuleFn = currentEditorRule,
    matchMediaFn = (query) => {
        if (typeof window.matchMedia === "function") {
            return window.matchMedia(query);
        }
        return { matches: true };
    },
    setBrushSizeFn = setBrushSize,
    setCellSizeFn = setCellSize,
    setCellSizeMemoryMapFn = setCellSizeMemoryMap,
    clearPendingPatchDepthFn = clearPendingPatchDepth,
    setDrawerOpenFn = setDrawerOpen,
    setEditorToolFn = setEditorTool,
    setPatchDepthMemoryMapFn = setPatchDepthMemoryMap,
    setSelectedPaintStateFn = setSelectedPaintState,
}: {
    state: AppState;
    elements: DomElements;
    createUiSessionStorage?: CreateUiSessionStorageFunction;
    applyDisclosureStateFn?: typeof applyDisclosureState;
    currentEditorRuleFn?: typeof currentEditorRule;
    matchMediaFn?: MatchMediaFunction;
    setBrushSizeFn?: typeof setBrushSize;
    setCellSizeFn?: typeof setCellSize;
    setCellSizeMemoryMapFn?: typeof setCellSizeMemoryMap;
    clearPendingPatchDepthFn?: typeof clearPendingPatchDepth;
    setDrawerOpenFn?: typeof setDrawerOpen;
    setEditorToolFn?: typeof setEditorTool;
    setPatchDepthMemoryMapFn?: typeof setPatchDepthMemoryMap;
    setSelectedPaintStateFn?: typeof setSelectedPaintState;
}): UiSessionController {
    const storage = createUiSessionStorageFn();

    function restoreInitialCellSize(): void {
        const activeTilingFamily = state.topologySpec.tiling_family;
        const rememberedCellSizes = readStoredCellSizes(storage, activeTilingFamily);
        const hasRememberedCellSizes = Object.keys(rememberedCellSizes).length > 0;
        if (hasRememberedCellSizes) {
            setCellSizeMemoryMapFn(state, rememberedCellSizes);
        } else {
            const legacyCellSize = storage.getCellSize(activeTilingFamily);
            if (legacyCellSize !== null && legacyCellSize !== undefined && activeTilingFamily) {
                setCellSizeMemoryMapFn(state, {
                    [activeTilingFamily]: legacyCellSize,
                });
            }
        }
        setCellSizeFn(
            state,
            rememberedCellSizeForTilingFamily(state, activeTilingFamily),
            activeTilingFamily,
        );
        setEditorToolFn(state, storage.getEditorTool());
        setBrushSizeFn(state, storage.getBrushSize());
        setPatchDepthMemoryMapFn(state, readStoredPatchDepths(storage));
    }

    function restoreDisclosures(): void {
        applyDisclosureStateFn(elements, storage.getDisclosureStates());
    }

    function restoreDrawerState(): void {
        const storedDrawerOpen = storage.getDrawerOpen();
        if (storedDrawerOpen === null || storedDrawerOpen === undefined) {
            setDrawerOpenFn(state, Boolean(matchMediaFn("(min-width: 861px)")?.matches));
            return;
        }
        setDrawerOpenFn(state, storedDrawerOpen);
    }

    function restorePaintStateForCurrentRule(): void {
        const rule = currentEditorRuleFn(state);
        if (!rule) {
            return;
        }

        const storedPaintState = storage.getPaintState(rule.name);
        if (storedPaintState === null || storedPaintState === undefined) {
            return;
        }

        const isValidPaintState = Array.isArray(rule.states)
            && rule.states.some(
                (cellState) => cellState.paintable && cellState.value === Number(storedPaintState),
            );
        if (isValidPaintState) {
            setSelectedPaintStateFn(state, Number(storedPaintState));
        }
    }

    function persistCellSize(tilingFamilyOrCellSize: string | number, cellSize: number | undefined = undefined): void {
        if (cellSize === undefined) {
            if (storage.setCellSize.length < 2) {
                storage.setCellSize(tilingFamilyOrCellSize);
                return;
            }
            storage.setCellSize(state.topologySpec.tiling_family, Number(tilingFamilyOrCellSize));
            return;
        }
        if (storage.setCellSize.length < 2) {
            storage.setCellSize(cellSize);
            return;
        }
        storage.setCellSize(String(tilingFamilyOrCellSize), cellSize);
    }

    function persistEditorTool(editorTool: EditorTool): void {
        storage.setEditorTool(parseEditorTool(editorTool));
    }

    function persistBrushSize(brushSize: number): void {
        storage.setBrushSize(brushSize);
    }

    function persistPaintStateForCurrentRule(): void {
        const rule = currentEditorRuleFn(state);
        if (!rule || state.selectedPaintState === null) {
            return;
        }
        storage.setPaintState(rule.name, state.selectedPaintState);
    }

    function persistPatchDepthForTilingFamily(tilingFamily: string | null | undefined, patchDepth: number): void {
        storage.setPatchDepth(tilingFamily, patchDepth);
    }

    function persistDisclosureState(id: UiDisclosureId, open: boolean): void {
        storage.setDisclosureState(id, open);
    }

    function persistDrawerState(drawerOpen: boolean): void {
        storage.setDrawerOpen(drawerOpen);
    }

    function resetSessionPreferences(): void {
        storage.clear();
        setCellSizeMemoryMapFn(state, {});
        setPatchDepthMemoryMapFn(state, {});
        clearPendingPatchDepthFn(state);
        const activeTilingFamily = state.topologySpec.tiling_family;
        setCellSizeFn(
            state,
            rememberedCellSizeForTilingFamily(state, activeTilingFamily),
            activeTilingFamily,
        );
        setEditorToolFn(state, DEFAULT_EDITOR_TOOL);
        setBrushSizeFn(state, DEFAULT_BRUSH_SIZE);
        const currentRule = currentEditorRuleFn(state);
        if (currentRule) {
            setSelectedPaintStateFn(
                state,
                currentRule.default_paint_state ?? currentRule.states.find((cellState) => cellState.paintable)?.value ?? 0,
            );
        }
        setDrawerOpenFn(state, Boolean(matchMediaFn("(min-width: 861px)")?.matches));
        DISCLOSURE_IDS.forEach((id) => {
            const disclosure = elements[id];
            if (disclosure) {
                disclosure.open = false;
            }
        });
    }

    return {
        getStorage: () => storage,
        restoreInitialCellSize,
        restoreDisclosures,
        restoreDrawerState,
        restorePaintStateForCurrentRule,
        persistCellSize,
        persistEditorTool,
        persistBrushSize,
        persistPaintStateForCurrentRule,
        persistPatchDepthForTilingFamily,
        persistDisclosureState,
        persistDrawerState,
        resetSessionPreferences,
    };
}
