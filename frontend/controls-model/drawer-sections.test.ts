import { beforeEach, describe, expect, it, vi } from "vitest";

import { installFrontendGlobals } from "../test-helpers/bootstrap.js";
import { buildControlsModelState, EMPTY_SYNC_STATE } from "./test-support.js";

describe("controls-model drawer sections", () => {
    beforeEach(() => {
        installFrontendGlobals();
        vi.resetModules();
    });

    it("builds topology sizing state from a patch-depth family", async () => {
        const { buildDrawerTopologyViewModel } = await import("./drawer-topology.js");
        const state = await buildControlsModelState();
        state.topologySpec = {
            ...state.topologySpec,
            tiling_family: "penrose-p3-rhombs",
            sizing_mode: "patch_depth",
            patch_depth: 3,
        };
        state.patchDepth = 3;

        const viewModel = buildDrawerTopologyViewModel({
            state,
            syncState: EMPTY_SYNC_STATE,
        });

        expect(viewModel.tilingFamilyValue).toBe("penrose-p3-rhombs");
        expect(viewModel.patchDepthVisible).toBe(true);
        expect(viewModel.patchDepthLabel).toBe("Depth 3");
        expect(viewModel.cellSizeVisible).toBe(false);
    });

    it("builds rule and palette state independently from the broader drawer builder", async () => {
        const { buildDrawerRulePaletteViewModel } = await import("./drawer-rule-palette.js");
        const state = await buildControlsModelState();

        const viewModel = buildDrawerRulePaletteViewModel({
            state,
            paletteRule: state.activeRule,
        });

        expect(viewModel.ruleSelectValue).toBe("signal-rule");
        expect(viewModel.ruleOptions).toEqual([
            { name: "signal-rule", displayName: "Signal Rule" },
        ]);
        expect(viewModel.paletteStates).toEqual([
            { value: 2, label: "Signal", color: "#ff0000" },
        ]);
    });

    it("builds pattern controls independently from preset selection and topology availability", async () => {
        const { buildPresetSelection } = await import("../preset-selection.js");
        const { buildDrawerPatternViewModel } = await import("./drawer-patterns.js");
        const state = await buildControlsModelState();
        state.topology = null;

        const viewModel = buildDrawerPatternViewModel({
            state,
            activeRule: state.activeRule,
            paletteRule: state.activeRule,
            presetSelection: buildPresetSelection(state),
        });

        expect(viewModel.presetSeedDisabled).toBe(true);
        expect(viewModel.presetHelperText).toContain("No curated preset");
        expect(viewModel.copyPatternDisabled).toBe(true);
        expect(viewModel.exportPatternDisabled).toBe(true);
    });
});
