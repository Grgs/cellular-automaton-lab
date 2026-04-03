import {
    armEditMode,
    clearEditMode,
    dismissFirstRunHint,
} from "../state/overlay-state.js";
import {
    rememberCellSizeForTilingFamily,
    setCellSize,
} from "../state/sizing-state.js";
import {
    setBrushSize,
    setEditorTool,
    setSelectedPaintState,
    setUnsafeSizingEnabled,
} from "../state/simulation-state.js";
import { setDrawerOpen } from "../state/overlay-state.js";
import {
    applyOverlayIntent,
    OVERLAY_INTENT_INSPECTOR_EMPTY_CLICK,
    OVERLAY_INTENT_MANUAL_HIDE_INSPECTOR,
    OVERLAY_INTENT_MANUAL_RESTORE,
    OVERLAY_INTENT_TOP_BAR_EMPTY_CLICK,
    OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK,
} from "../overlay-policy.js";
import { buildDrawerToggleState } from "../controls-model/shared.js";
import { topologyUsesPatchDepth } from "../topology-catalog.js";
import { toggleTheme } from "../theme.js";
import type { EditorTool } from "../editor-tools.js";
import type { UiActionOptions, UiActionSet } from "../types/actions.js";

type DrawerToggleLabel = "Hide Inspector" | "Show Inspector" | "Show Overlays" | "Show HUD";
type OverlayIntent = Parameters<typeof applyOverlayIntent>[1];

export function createUiActions({
    state,
    uiSessionController,
    renderCurrentGrid,
    renderControlPanel,
    viewportController,
    setSelectedPaintStateFn = setSelectedPaintState,
    setCellSizeFn = setCellSize,
    setDrawerOpenFn = setDrawerOpen,
    dismissFirstRunHintFn = dismissFirstRunHint,
    setEditorToolFn = setEditorTool,
    setBrushSizeFn = setBrushSize,
    toggleThemeFn = toggleTheme,
    applyOverlayIntentFn = applyOverlayIntent,
    armEditModeFn = armEditMode,
    clearEditModeFn = clearEditMode,
    setUnsafeSizingEnabledFn = setUnsafeSizingEnabled,
}: UiActionOptions & {
    setSelectedPaintStateFn?: typeof setSelectedPaintState;
    setCellSizeFn?: typeof setCellSize;
    setDrawerOpenFn?: typeof setDrawerOpen;
    dismissFirstRunHintFn?: typeof dismissFirstRunHint;
    setEditorToolFn?: typeof setEditorTool;
    setBrushSizeFn?: typeof setBrushSize;
    toggleThemeFn?: typeof toggleTheme;
    applyOverlayIntentFn?: typeof applyOverlayIntent;
    armEditModeFn?: typeof armEditMode;
    clearEditModeFn?: typeof clearEditMode;
    setUnsafeSizingEnabledFn?: typeof setUnsafeSizingEnabled;
}): UiActionSet {
    function applyPaintState(nextPaintState: number | null): void {
        setSelectedPaintStateFn(state, nextPaintState);
        uiSessionController.persistPaintStateForCurrentRule();
        if (!state.isRunning && !state.overlayRunPending) {
            if (!state.firstRunHintDismissed) {
                dismissFirstRunHintFn(state);
            }
            applyOverlayIntentFn(state, OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK);
            armEditModeFn(state, { showCue: false });
        }
        renderControlPanel();
    }

    function applyEditorTool(nextTool: EditorTool): void {
        setEditorToolFn(state, nextTool);
        uiSessionController.persistEditorTool(state.selectedEditorTool);
        renderControlPanel();
    }

    function applyBrushSize(nextBrushSize: number): void {
        setBrushSizeFn(state, nextBrushSize);
        uiSessionController.persistBrushSize(state.brushSize);
        renderControlPanel();
    }

    function applyUnsafeSizingEnabled(enabled: boolean): Promise<boolean> {
        setUnsafeSizingEnabledFn(state, enabled);
        uiSessionController.persistUnsafeSizingEnabled(Boolean(state.unsafeSizingEnabled));
        renderControlPanel();
        return Promise.resolve(Boolean(state.unsafeSizingEnabled));
    }

    function applyCellSize(
        nextCellSize: number,
        { immediate = false }: { immediate?: boolean } = {},
    ): Promise<boolean> {
        setCellSizeFn(state, nextCellSize);
        rememberCellSizeForTilingFamily(state, state.topologySpec?.tiling_family, state.cellSize);
        uiSessionController.persistCellSize(state.cellSize);
        renderControlPanel();

        if (topologyUsesPatchDepth(state.topologySpec)) {
            return Promise.resolve(false);
        }

        if (immediate) {
            const flushed = viewportController?.flush?.();
            if (flushed !== undefined) {
                return flushed;
            }
            return Promise.resolve(Boolean(viewportController?.schedule?.({ delay: 0 })));
        }

        return Promise.resolve(Boolean(viewportController?.schedule?.()));
    }

    function applyDrawerState(nextOpen: boolean): Promise<boolean> {
        const overlayChanged = applyOverlayIntentFn(
            state,
            nextOpen ? OVERLAY_INTENT_MANUAL_RESTORE : OVERLAY_INTENT_MANUAL_HIDE_INSPECTOR,
        );
        const editChanged = clearEditModeFn(state);
        setDrawerOpenFn(state, nextOpen);
        uiSessionController.persistDrawerState(state.drawerOpen);
        if (overlayChanged || editChanged || state.drawerOpen === nextOpen) {
            renderControlPanel();
        }
        return Promise.resolve(state.drawerOpen);
    }

    function applyOverlayIntentAndRender(intent: OverlayIntent): Promise<boolean> {
        const changed = applyOverlayIntentFn(state, intent);
        if (changed) {
            renderControlPanel();
            return Promise.resolve(true);
        }
        return Promise.resolve(false);
    }

    function dismissOverlays(): Promise<boolean> {
        dismissFirstRunHintFn(state);
        return applyOverlayIntentAndRender(OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK);
    }

    function applyOverlayIntentAndRenderWithEditReset(intent: OverlayIntent): Promise<boolean> {
        const overlayChanged = applyOverlayIntentFn(state, intent);
        const editChanged = clearEditModeFn(state);
        if (overlayChanged || editChanged) {
            renderControlPanel();
            return Promise.resolve(true);
        }
        return Promise.resolve(false);
    }

    return {
        setCellSize: (nextCellSize) => applyCellSize(nextCellSize),
        commitCellSize: (nextCellSize) => applyCellSize(nextCellSize, { immediate: true }),
        setUnsafeSizingEnabled: (enabled) => applyUnsafeSizingEnabled(enabled),
        setPaintState: (nextPaintState) => applyPaintState(nextPaintState),
        setEditorTool: (nextTool) => applyEditorTool(nextTool),
        setBrushSize: (nextBrushSize) => applyBrushSize(nextBrushSize),
        toggleDrawer: () => {
            const { drawerToggleLabel } = buildDrawerToggleState(state);
            if (drawerToggleLabel === "Hide Inspector") {
                return applyDrawerState(false);
            }
            if (drawerToggleLabel === "Show Inspector" || drawerToggleLabel === "Show Overlays") {
                return applyDrawerState(true);
            }
            if (drawerToggleLabel === "Show HUD") {
                return applyDrawerState(state.drawerOpen);
            }
            return state.overlaysDismissed ? applyDrawerState(state.drawerOpen) : applyDrawerState(!state.drawerOpen);
        },
        closeDrawer: () => applyDrawerState(false),
        dismissOverlays,
        handleTopBarEmptyClick: () => applyOverlayIntentAndRenderWithEditReset(OVERLAY_INTENT_TOP_BAR_EMPTY_CLICK),
        handleInspectorEmptyClick: () => applyOverlayIntentAndRenderWithEditReset(OVERLAY_INTENT_INSPECTOR_EMPTY_CLICK),
        handleWorkspaceEmptyClick: () => applyOverlayIntentAndRenderWithEditReset(OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK),
        setDisclosureState: (id, open) => uiSessionController.persistDisclosureState(id, open),
        toggleTheme: () => {
            toggleThemeFn();
            renderCurrentGrid();
            renderControlPanel();
        },
    };
}
