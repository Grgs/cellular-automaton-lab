import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../../test-helpers/bootstrap.js";
import type { RuleDefinition } from "../../types/domain.js";

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

describe("topology-selection-plan", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("returns a noop plan for an unchanged topology request", async () => {
        const { createAppState } = await import("../../state/simulation-state.js");
        const { planTopologySelection } = await import("./topology-selection-plan.js");

        const state = createAppState();
        state.width = 30;
        state.height = 20;
        state.cellSize = 12;
        state.patchDepth = 0;
        state.activeRule = makeRule("conway");
        state.topologySpec = {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 30,
            height: 20,
            patch_depth: 0,
        };

        const getViewportDimensions = vi.fn(() => ({ width: 30, height: 20 }));
        const result = planTopologySelection({
            state,
            nextTopologySpec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                width: 30,
                height: 20,
                patch_depth: 0,
            },
            preserveRuleOnTopologySelection: true,
            getViewportDimensions,
        });

        expect(result.kind).toBe("noop");
        expect(getViewportDimensions).not.toHaveBeenCalled();
    });

    it("uses remembered patch depth for patch-depth topologies", async () => {
        const { createAppState } = await import("../../state/simulation-state.js");
        const { planTopologySelection } = await import("./topology-selection-plan.js");

        const state = createAppState();
        state.activeRule = makeRule("conway");
        state.patchDepthByTilingFamily = {
            "penrose-p3-rhombs": 5,
        };

        const result = planTopologySelection({
            state,
            nextTopologySpec: {
                tiling_family: "penrose-p3-rhombs",
                adjacency_mode: "edge",
            },
            preserveRuleOnTopologySelection: false,
            getViewportDimensions: vi.fn(() => ({ width: 99, height: 99 })),
        });

        expect(result.kind).toBe("apply");
        if (result.kind !== "apply") {
            throw new Error("expected an apply plan");
        }
        expect(result.optimisticPatchDepth).toBe(5);
        expect(result.resolvedTopologySpec.patch_depth).toBe(5);
        expect(result.resetBody.topology_spec.patch_depth).toBe(5);
    });

    it("falls back to the tiling-family patch-depth default when no memory exists", async () => {
        window.APP_TOPOLOGIES = [
            ...window.APP_TOPOLOGIES,
            {
                tiling_family: "pinwheel",
                label: "Pinwheel",
                picker_group: "Experimental",
                picker_order: 340,
                sizing_mode: "patch_depth",
                family: "aperiodic",
                render_kind: "polygon_aperiodic",
                viewport_sync_mode: "presentation-only",
                supported_adjacency_modes: ["edge"],
                default_adjacency_mode: "edge",
                default_rules: { edge: "life-b2-s23" },
                geometry_keys: { edge: "pinwheel" },
                sizing_policy: { control: "patch_depth", default: 3, min: 0, max: 4 },
            },
        ];
        const { createAppState } = await import("../../state/simulation-state.js");
        const { resolveSelectedPatchDepthForTopology } =
            await import("./topology-selection-plan.js");

        const state = createAppState();
        state.activeRule = makeRule("conway");

        expect(
            resolveSelectedPatchDepthForTopology(state, {
                tiling_family: "pinwheel",
                adjacency_mode: "edge",
            }),
        ).toBe(3);
    });

    it("computes viewport dimensions for non-patch-depth selections when requested", async () => {
        const { createAppState } = await import("../../state/simulation-state.js");
        const { planTopologySelection } = await import("./topology-selection-plan.js");

        const state = createAppState();
        state.width = 30;
        state.height = 20;
        state.cellSizeByTilingFamily = {
            hex: 18,
        };

        const getViewportDimensions = vi.fn(() => ({ width: 44, height: 33 }));
        const result = planTopologySelection({
            state,
            nextTopologySpec: {
                tiling_family: "hex",
                adjacency_mode: "edge",
                width: 30,
                height: 20,
                patch_depth: 0,
            },
            preserveRuleOnTopologySelection: false,
            getViewportDimensions,
            resizeNonPatchDepthToViewport: true,
            viewportRuleName: null,
        });

        expect(getViewportDimensions).toHaveBeenCalledWith("hex", null, 18);
        expect(result.kind).toBe("apply");
        if (result.kind !== "apply") {
            throw new Error("expected an apply plan");
        }
        expect(result.resolvedTopologySpec.width).toBe(44);
        expect(result.resolvedTopologySpec.height).toBe(33);
        expect(result.resetBody.topology_spec.width).toBe(44);
        expect(result.resetBody.topology_spec.height).toBe(33);
    });

    it("builds reset payloads from the current topology, rule, and speed", async () => {
        const { createAppState } = await import("../../state/simulation-state.js");
        const { buildCurrentTopologyResetPayload } = await import("./topology-selection-plan.js");

        const state = createAppState();
        state.speed = 7;
        state.cellSize = 14;
        state.activeRule = makeRule("highlife");
        state.topologySpec = {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 30,
            height: 20,
            patch_depth: 0,
        };

        const getViewportDimensions = vi.fn(() => ({ width: 80, height: 55 }));
        const payload = buildCurrentTopologyResetPayload({
            state,
            getViewportDimensions,
            randomize: true,
        });

        expect(payload).toEqual({
            topology_spec: {
                ...state.topologySpec,
                width: 80,
                height: 55,
                patch_depth: window.APP_DEFAULTS.simulation.topology_spec.patch_depth,
            },
            speed: 7,
            rule: "highlife",
            randomize: true,
        });
        expect(getViewportDimensions).toHaveBeenCalledWith("square", "highlife", 14);
    });

    it("includes the unsafe size override flag in reset payloads when enabled", async () => {
        const { createAppState } = await import("../../state/simulation-state.js");
        const { buildCurrentTopologyResetPayload } = await import("./topology-selection-plan.js");

        const state = createAppState();
        state.unsafeSizingEnabled = true;
        state.speed = 7;
        state.patchDepth = 9;
        state.activeRule = makeRule("life-b2-s23");
        state.topologySpec = {
            tiling_family: "penrose-p3-rhombs",
            adjacency_mode: "edge",
            sizing_mode: "patch_depth",
            width: 0,
            height: 0,
            patch_depth: 9,
        };

        const payload = buildCurrentTopologyResetPayload({
            state,
            getViewportDimensions: vi.fn(() => ({ width: 99, height: 99 })),
            randomize: false,
        });

        expect(payload.topology_spec).toEqual({
            ...state.topologySpec,
            patch_depth: 9,
            unsafe_size_override: true,
        });
    });
});
