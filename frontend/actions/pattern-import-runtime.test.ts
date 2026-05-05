import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import type {
    ParsedPattern,
    RuleDefinition,
    SimulationSnapshot,
    TopologySpec,
} from "../types/domain.js";
import type { SimulationMutations } from "../types/controller.js";

function makeRule(name = "conway"): RuleDefinition {
    return {
        name,
        display_name: name,
        description: `${name} rule`,
        default_paint_state: 1,
        supports_randomize: true,
        states: [
            { value: 0, label: "Dead", color: "#000000", paintable: true },
            { value: 1, label: "Live", color: "#ffffff", paintable: true },
        ],
        rule_protocol: "life-like",
        supports_all_topologies: true,
    };
}

function makeTopologySpec(overrides: Partial<TopologySpec> = {}): TopologySpec {
    return {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 4,
        height: 4,
        patch_depth: 0,
        ...overrides,
    };
}

function makeParsedPattern(overrides: Partial<ParsedPattern> = {}): ParsedPattern {
    const topologySpec = makeTopologySpec(overrides.topologySpec);
    return {
        format: "cellular-automaton-lab-pattern",
        version: 5,
        topologySpec,
        rule: "conway",
        cellsById: {},
        patchDepth: topologySpec.patch_depth,
        width: topologySpec.width,
        height: topologySpec.height,
        ...overrides,
    };
}

function makeSnapshot(
    cellIds: string[],
    overrides: Partial<SimulationSnapshot> = {},
): SimulationSnapshot {
    const topologySpec = makeTopologySpec(overrides.topology_spec);
    return {
        topology_spec: topologySpec,
        speed: 5,
        running: false,
        generation: 0,
        rule: makeRule(overrides.rule?.name ?? "conway"),
        topology_revision: "rev-1",
        topology: {
            topology_revision: "rev-1",
            topology_spec: topologySpec,
            geometry: "square",
            width: topologySpec.width,
            height: topologySpec.height,
            cells: cellIds.map((id) => ({
                id,
                kind: "square",
                neighbors: [null, null, null, null],
            })),
        },
        cell_states: cellIds.map(() => 0),
        ...overrides,
    };
}

function createSimulationMutationsStub(): SimulationMutations {
    return {
        applyState: vi.fn((simulationState) => simulationState),
        applyRemoteState: vi.fn(async (simulationState) => simulationState),
        runSerialized: vi.fn(async (task, options = {}) => {
            try {
                return await task();
            } catch (error) {
                options.onError?.(error);
                if (options.onRecover) {
                    await options.onRecover(error);
                }
                throw error;
            }
        }),
        runStateMutation: vi.fn(async (task, options = {}) => {
            try {
                return await task();
            } catch (error) {
                options.onError?.(error);
                if (options.onRecover) {
                    await options.onRecover(error);
                }
                throw error;
            }
        }),
    };
}

describe("pattern-import-runtime", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("stops on cancel before mutating the backend", async () => {
        const { createAppState } = await import("../state/simulation-state.js");
        const { createPatternImportRuntime } = await import("./pattern-import-runtime.js");

        const state = createAppState();
        state.generation = 1;
        const speedInput = document.createElement("input");
        speedInput.value = "9";

        const postControlFn = vi.fn();
        const setCellsRequestFn = vi.fn();
        const confirmImportFn = vi.fn(() => false);

        const runtime = createPatternImportRuntime({
            state,
            elements: { speedInput },
            interactions: { runSerialized: vi.fn() },
            viewportController: { suppressAutoSync: vi.fn() },
            renderControlPanel: vi.fn(),
            applySimulationState: vi.fn(),
            postControlFn,
            setCellsRequestFn,
            onError: vi.fn(),
            refreshState: vi.fn(async () => {}),
            simulationMutations: createSimulationMutationsStub(),
            parsePatternTextFn: vi.fn(() => makeParsedPattern()),
            confirmImportFn,
        });

        const result = await runtime.importPatternText(async () => "pattern", {
            failurePrefix: "Import failed",
            successMessage: "Imported pattern from demo.json.",
            cancelMessage: "Import canceled.",
        });

        expect(result).toBeNull();
        expect(confirmImportFn).toHaveBeenCalled();
        expect(postControlFn).not.toHaveBeenCalled();
        expect(setCellsRequestFn).not.toHaveBeenCalled();
        expect(state.patternStatus).toEqual({
            message: "Import canceled.",
            tone: "info",
        });
    });

    it("performs only the reset when the imported pattern has no cells", async () => {
        const { createAppState } = await import("../state/simulation-state.js");
        const { createPatternImportRuntime } = await import("./pattern-import-runtime.js");

        const state = createAppState();
        state.ruleSelectionOrigin = "user";
        const speedInput = document.createElement("input");
        speedInput.value = "11";
        const resetSnapshot = makeSnapshot(["c:0:0", "c:1:0"]);
        const mutations = createSimulationMutationsStub();
        const viewportController = { suppressAutoSync: vi.fn() };
        const postControlFn = vi.fn(async () => resetSnapshot);
        const setCellsRequestFn = vi.fn();

        const runtime = createPatternImportRuntime({
            state,
            elements: { speedInput },
            interactions: { runSerialized: vi.fn() },
            viewportController,
            renderControlPanel: vi.fn(),
            applySimulationState: vi.fn(),
            postControlFn,
            setCellsRequestFn,
            onError: vi.fn(),
            refreshState: vi.fn(async () => {}),
            simulationMutations: mutations,
            parsePatternTextFn: vi.fn(() => makeParsedPattern()),
        });

        const result = await runtime.importPatternText(async () => "pattern", {
            failurePrefix: "Import failed",
            successMessage: "Imported pattern from empty.json.",
            cancelMessage: "Import canceled.",
        });

        expect(result).toBe(resetSnapshot);
        expect(postControlFn).toHaveBeenCalledWith("/api/control/reset", {
            topology_spec: {
                ...makeTopologySpec(),
                width: 4,
                height: 4,
                patch_depth: 0,
            },
            speed: 11,
            rule: "conway",
            randomize: false,
        });
        expect(setCellsRequestFn).not.toHaveBeenCalled();
        expect(viewportController.suppressAutoSync).toHaveBeenCalledTimes(2);
        expect(state.ruleSelectionOrigin).toBe("default");
        expect(state.patternStatus).toEqual({
            message: "Imported pattern from empty.json.",
            tone: "success",
        });
        expect(mutations.applyRemoteState).toHaveBeenCalledTimes(1);
    });

    it("surfaces an error when imported cells reference unknown ids", async () => {
        const { createAppState } = await import("../state/simulation-state.js");
        const { createPatternImportRuntime } = await import("./pattern-import-runtime.js");

        const state = createAppState();
        const speedInput = document.createElement("input");
        const resetSnapshot = makeSnapshot(["c:0:0"]);
        const refreshState = vi.fn(async () => {});
        const onError = vi.fn();
        const mutations = createSimulationMutationsStub();
        const setCellsRequestFn = vi.fn();

        const runtime = createPatternImportRuntime({
            state,
            elements: { speedInput },
            interactions: { runSerialized: vi.fn() },
            viewportController: { suppressAutoSync: vi.fn() },
            renderControlPanel: vi.fn(),
            applySimulationState: vi.fn(),
            postControlFn: vi.fn(async () => resetSnapshot),
            setCellsRequestFn,
            onError,
            refreshState,
            simulationMutations: mutations,
            parsePatternTextFn: vi.fn(() =>
                makeParsedPattern({
                    cellsById: {
                        missing: 1,
                    },
                }),
            ),
        });

        const result = await runtime.importPatternText(async () => "pattern", {
            failurePrefix: "Import failed",
            successMessage: "Imported pattern from broken.json.",
            cancelMessage: "Import canceled.",
        });

        expect(result).toBeNull();
        expect(setCellsRequestFn).not.toHaveBeenCalled();
        expect(refreshState).toHaveBeenCalled();
        expect(onError).toHaveBeenCalled();
        expect(state.patternStatus).toEqual({
            message: "Import failed: Pattern references an unknown cell id 'missing'.",
            tone: "error",
        });
    });

    it("resets rule origin and reports success after a successful import", async () => {
        const { createAppState } = await import("../state/simulation-state.js");
        const { createPatternImportRuntime } = await import("./pattern-import-runtime.js");

        const state = createAppState();
        state.ruleSelectionOrigin = "user";
        state.editArmed = true;
        state.editCueVisible = true;
        const speedInput = document.createElement("input");
        speedInput.value = "13";
        const resetSnapshot = makeSnapshot(["c:0:0"]);
        const finalSnapshot = makeSnapshot(["c:0:0"], {
            generation: 1,
            cell_states: [1],
        });
        const viewportController = { suppressAutoSync: vi.fn() };
        const onSuccess = vi.fn();
        const setCellsRequestFn = vi.fn(async () => finalSnapshot);

        const runtime = createPatternImportRuntime({
            state,
            elements: { speedInput },
            interactions: { runSerialized: vi.fn() },
            viewportController,
            renderControlPanel: vi.fn(),
            applySimulationState: vi.fn(),
            postControlFn: vi.fn(async () => resetSnapshot),
            setCellsRequestFn,
            onError: vi.fn(),
            refreshState: vi.fn(async () => {}),
            simulationMutations: createSimulationMutationsStub(),
            parsePatternTextFn: vi.fn(() =>
                makeParsedPattern({
                    cellsById: {
                        "c:0:0": 1,
                    },
                }),
            ),
        });

        const result = await runtime.importPatternText(async () => "pattern", {
            failurePrefix: "Import failed",
            successMessage: "Pasted pattern from clipboard.",
            cancelMessage: "Paste canceled.",
            onSuccess,
        });

        expect(result).toBe(finalSnapshot);
        expect(setCellsRequestFn).toHaveBeenCalledWith([{ id: "c:0:0", state: 1 }]);
        expect(onSuccess).toHaveBeenCalled();
        expect(viewportController.suppressAutoSync).toHaveBeenCalledTimes(2);
        expect(state.ruleSelectionOrigin).toBe("default");
        expect(state.firstRunHintDismissed).toBe(true);
        expect(state.editArmed).toBe(false);
        expect(state.editCueVisible).toBe(false);
        expect(state.patternStatus).toEqual({
            message: "Pasted pattern from clipboard.",
            tone: "success",
        });
    });
});
