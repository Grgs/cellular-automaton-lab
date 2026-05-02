import { beforeEach, describe, expect, it, vi } from "vitest";

import { EDITOR_TOOL_BRUSH } from "./editor-tools.js";
import type { AppController } from "./types/controller-app.js";
import type { GridView } from "./types/controller-view.js";
import type { DomElements } from "./types/dom.js";
import type { RuleDefinition, SimulationSnapshot, TopologyPayload } from "./types/domain.js";
import type { RenderDiagnosticsSnapshot } from "./types/rendering.js";
import type { AppState } from "./types/state.js";
import { installFrontendGlobals } from "./test-helpers/bootstrap.js";

function buildRule(): RuleDefinition {
    return {
        name: "conway",
        display_name: "Conway",
        description: "Classic Life",
        states: [
            { value: 0, label: "Dead", color: "#000000", paintable: true },
            { value: 1, label: "Alive", color: "#ffffff", paintable: true },
        ],
        default_paint_state: 1,
        supports_randomize: true,
        rule_protocol: "universal-v1",
        supports_all_topologies: true,
    };
}

function buildTopology(topologyRevision: string = "rev-1"): TopologyPayload {
    return {
        topology_revision: topologyRevision,
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 2,
            height: 1,
            patch_depth: 0,
        },
        cells: [
            { id: "c:0:0", kind: "cell", neighbors: [null, null, null, null] },
            { id: "c:1:0", kind: "cell", neighbors: [null, null, null, null] },
        ],
    };
}

function buildSnapshot(topology: TopologyPayload, cellStates: number[] = [0, 1]): SimulationSnapshot {
    return {
        topology_spec: topology.topology_spec,
        speed: 5,
        running: false,
        generation: 7,
        rule: buildRule(),
        topology_revision: topology.topology_revision,
        topology,
        cell_states: [...cellStates],
    };
}

function buildElements(canvas: HTMLCanvasElement): DomElements {
    return {
        appFrame: null,
        topBar: null,
        mainStage: null,
        controlDrawer: null,
        drawerBackdrop: null,
        drawerToggleBtn: null,
        simulationSection: null,
        rulePaletteSection: null,
        editorSection: null,
        "rule-notes-toggle": null,
        gridPanel: null,
        gridViewport: null,
        grid: canvas,
        blockingActivityOverlay: null,
        blockingActivityMessage: null,
        blockingActivityDetail: null,
        canvasHud: null,
        canvasEditCue: null,
        canvasHudTilingText: null,
        canvasHudAdjacencyText: null,
        statusText: document.createElement("span"),
        generationText: document.createElement("span"),
        ruleText: null,
        gridSizeText: document.createElement("span"),
        gridSizePanelText: null,
        inspectorTilingText: null,
        inspectorRuleText: null,
        topologyStatus: null,
        selectionInspectorSection: null,
        selectionInspectorTitle: null,
        selectionInspectorSubtitle: null,
        selectionInspectorHint: null,
        selectionInspectorSummaryRows: null,
        selectionInspectorAdvanced: null,
        selectionInspectorAdvancedSummary: null,
        selectionInspectorAdvancedRows: null,
        quickStartHint: null,
        quickStartHintText: null,
        showcaseWhirlpoolBtn: null,
        showcaseWireworldBtn: null,
        showcasePenroseBtn: null,
        ruleSummaryText: null,
        ruleDescription: null,
        paintPalette: null,
        speedInput: null,
        speedLabel: null,
        cellSizeField: null,
        cellSizeInput: null,
        cellSizeLabel: null,
        configSyncStatus: null,
        tilingFamilySelect: null,
        tilingPickerToggle: null,
        tilingPickerMenu: null,
        tilingPickerCurrentPreview: null,
        adjacencyModeField: null,
        adjacencyModeSelect: null,
        patchDepthField: null,
        patchDepthInput: null,
        patchDepthLabel: null,
        themeToggleBtn: null,
        ruleSelect: null,
        runToggleBtn: null,
        stepBtn: null,
        resetBtn: null,
        randomBtn: null,
        resetAllSettingsBtn: null,
        presetSeedControls: null,
        presetSeedSelect: null,
        presetSeedBtn: null,
        presetHelperText: null,
        importPatternBtn: null,
        copyPatternBtn: null,
        exportPatternBtn: null,
        pastePatternBtn: null,
        shareLinkBtn: null,
        patternImportInput: null,
        patternStatus: null,
        editorTools: null,
        editorShortcutHint: null,
        unsafeSizingField: null,
        unsafeSizingToggle: null,
        brushSizeControls: null,
        undoBtn: null,
        redoBtn: null,
    };
}

function buildState(topology: TopologyPayload, cellStates: number[] = [0, 1]): AppState {
    const rule = buildRule();
    return {
        rules: [rule],
        activeRule: rule,
        editorRuleName: null,
        ruleSelectionOrigin: "default",
        selectedEditorTool: EDITOR_TOOL_BRUSH,
        brushSize: 1,
        selectedPaintState: 1,
        selectedPresetIdsByRule: {},
        undoStack: [],
        redoStack: [],
        pollTimer: null,
        isRunning: false,
        generation: 7,
        speed: 5,
        topologySpec: topology.topology_spec,
        patchDepth: 0,
        pendingPatchDepth: null,
        patchDepthByTilingFamily: {},
        unsafeSizingEnabled: false,
        width: 2,
        height: 1,
        topologyRevision: topology.topology_revision,
        topology,
        topologyIndex: null,
        cellStates,
        previewTopology: null,
        previewTopologyRevision: null,
        previewCellStatesById: null,
        cellSize: 12,
        cellSizeByTilingFamily: {},
        renderCellSize: 12,
        drawerOpen: false,
        overlaysDismissed: false,
        inspectorTemporarilyHidden: false,
        overlayRunPending: false,
        runningOverlayRestoreActive: false,
        inspectorOccludesGrid: false,
        editArmed: false,
        editCueVisible: false,
        firstRunHintDismissed: false,
        blockingActivityKind: null,
        blockingActivityMessage: "",
        blockingActivityDetail: "",
        blockingActivityVisible: false,
        blockingActivityStartedAt: null,
        patternStatus: { message: "", tone: "" },
    };
}

function buildRenderDiagnostics(): RenderDiagnosticsSnapshot {
    return {
        geometry: "square",
        adapterGeometry: "square",
        adapterFamily: "regular",
        topologyBounds: null,
        renderMetrics: {
            cellSize: 12,
            renderCellSize: 12,
            scale: 1,
            coordinateScale: 1,
            xInset: 0,
            yInset: 0,
            cssWidth: 24,
            cssHeight: 12,
            canvasWidth: 24,
            canvasHeight: 12,
        },
        sampleCells: {
            lexicographicFirst: null,
            centerNearest: null,
            boundaryFurthest: null,
        },
        metricInputs: {
            renderedTopologyCenter: null,
            renderedCellCount: 2,
            orientationTokenCounts: null,
            angularSectorCounts: null,
        },
        overlapHotspots: null,
    };
}

describe("review-api", () => {
    beforeEach(() => {
        installFrontendGlobals();
        window.__reviewApi = null;
        window.__appReady = true;
    });

    it("installs diagnostics and clears globals on dispose", async () => {
        const { installReviewApi } = await import("./review-api.js");
        const topology = buildTopology();
        const state = buildState(topology);
        const canvas = document.createElement("canvas");
        const elements = buildElements(canvas);
        elements.gridSizeText!.textContent = "2 x 1";
        elements.generationText!.textContent = "7";
        elements.statusText!.textContent = "Paused";
        const controller: Pick<AppController, "applySimulationState" | "getState"> = {
            applySimulationState: vi.fn(),
            getState: () => state,
        };
        const gridView: GridView = {
            setPreviewCells: vi.fn(),
            clearPreview: vi.fn(),
            setHoveredCell: vi.fn(),
            setSelectedCells: vi.fn(),
            getSelectedCells: vi.fn(() => []),
            setGestureOutline: vi.fn(),
            flashGestureOutline: vi.fn(),
            clearGestureOutline: vi.fn(),
            getRenderDiagnostics: () => buildRenderDiagnostics(),
            getRenderedCellCenter: () => ({ x: 1, y: 1 }),
        };

        const dispose = installReviewApi({ controller, gridView, elements });
        const diagnostics = window.__reviewApi?.getDiagnostics();

        expect(diagnostics?.tilingFamily).toBe("square");
        expect(diagnostics?.readiness.gridSizeText).toBe("2 x 1");

        dispose();
        expect(window.__reviewApi).toBeNull();
    });

    it("keeps readiness diagnostics available when render diagnostics fail", async () => {
        const { installReviewApi } = await import("./review-api.js");
        const topology = buildTopology();
        const state = buildState(topology);
        const canvas = document.createElement("canvas");
        const elements = buildElements(canvas);
        elements.gridSizeText!.textContent = "2 x 1";
        elements.generationText!.textContent = "7";
        elements.statusText!.textContent = "Paused";
        const controller: Pick<AppController, "applySimulationState" | "getState"> = {
            applySimulationState: vi.fn(),
            getState: () => state,
        };
        const gridView: GridView = {
            setPreviewCells: vi.fn(),
            clearPreview: vi.fn(),
            setHoveredCell: vi.fn(),
            setSelectedCells: vi.fn(),
            getSelectedCells: vi.fn(() => []),
            setGestureOutline: vi.fn(),
            flashGestureOutline: vi.fn(),
            clearGestureOutline: vi.fn(),
            getRenderDiagnostics: () => {
                throw new Error("diagnostics failed");
            },
            getRenderedCellCenter: () => ({ x: 1, y: 1 }),
        };

        const dispose = installReviewApi({ controller, gridView, elements });
        const diagnostics = window.__reviewApi?.getDiagnostics();

        expect(diagnostics?.transformReport).toBeNull();
        expect(diagnostics?.diagnosticErrors).toEqual(["diagnostics failed"]);
        expect(diagnostics?.readiness.gridSizeText).toBe("2 x 1");

        dispose();
    });

    it("captures a baseline for review topology changes and resets it", async () => {
        const { installReviewApi } = await import("./review-api.js");
        const topology = buildTopology();
        const baselineSnapshot = buildSnapshot(topology, [1, 0]);
        const applySimulationState = vi.fn();
        const controller: Pick<AppController, "applySimulationState" | "getState"> = {
            applySimulationState,
            getState: () => buildState(topology, baselineSnapshot.cell_states),
        };
        const gridView: GridView = {
            setPreviewCells: vi.fn(),
            clearPreview: vi.fn(),
            setHoveredCell: vi.fn(),
            setSelectedCells: vi.fn(),
            getSelectedCells: vi.fn(() => []),
            setGestureOutline: vi.fn(),
            flashGestureOutline: vi.fn(),
            clearGestureOutline: vi.fn(),
        };
        const dispose = installReviewApi({
            controller,
            gridView,
            elements: buildElements(document.createElement("canvas")),
        });

        await window.__reviewApi?.applyTopology(buildTopology("rev-2"));
        await window.__reviewApi?.resetState();

        expect(applySimulationState).toHaveBeenNthCalledWith(
            1,
            expect.objectContaining({
                generation: 0,
                running: false,
                topology_revision: "rev-2",
            }),
            { source: "review-topology" },
        );
        expect(applySimulationState).toHaveBeenNthCalledWith(2, baselineSnapshot, { source: "review-reset" });

        dispose();
    });

    it("rejects unknown cell ids and non-finite review state values", async () => {
        const { installReviewApi } = await import("./review-api.js");
        const topology = buildTopology();
        const controller: Pick<AppController, "applySimulationState" | "getState"> = {
            applySimulationState: vi.fn(),
            getState: () => buildState(topology, [0, 0]),
        };
        const gridView: GridView = {
            setPreviewCells: vi.fn(),
            clearPreview: vi.fn(),
            setHoveredCell: vi.fn(),
            setSelectedCells: vi.fn(),
            getSelectedCells: vi.fn(() => []),
            setGestureOutline: vi.fn(),
            flashGestureOutline: vi.fn(),
            clearGestureOutline: vi.fn(),
        };

        installReviewApi({
            controller,
            gridView,
            elements: buildElements(document.createElement("canvas")),
        });

        await expect(
            window.__reviewApi?.applyCellStates({ "c:9:9": 1 }) ?? Promise.resolve(),
        ).rejects.toThrow("unknown cell id");
        await expect(
            window.__reviewApi?.applyCellStates([{ id: "c:0:0", state: Number.NaN }]) ?? Promise.resolve(),
        ).rejects.toThrow("non-finite state value");
    });
});
