import { FRONTEND_DEFAULTS } from "../defaults.js";
import { describeTopologySpec, resolveTopologyVariantKey } from "../topology-catalog.js";
import type { RuleSelectionOrigin } from "../types/state.js";

export const DEFAULT_CELL_SIZE = FRONTEND_DEFAULTS.ui.cell_size;
export const DEFAULT_TOPOLOGY_SPEC = Object.freeze(
    describeTopologySpec(FRONTEND_DEFAULTS.simulation.topology_spec),
);
export const DEFAULT_TOPOLOGY_VARIANT_KEY = resolveTopologyVariantKey(
    DEFAULT_TOPOLOGY_SPEC.tiling_family,
    DEFAULT_TOPOLOGY_SPEC.adjacency_mode,
);
export const MIN_CELL_SIZE = FRONTEND_DEFAULTS.ui.min_cell_size;
export const MAX_CELL_SIZE = FRONTEND_DEFAULTS.ui.max_cell_size;
export const AUTO_FIT_TARGET_CELL_SIZE = DEFAULT_CELL_SIZE;
export const MIN_RENDER_CELL_SIZE = 0.25;
export const MAX_RENDER_CELL_SIZE = 240;
export const DEFAULT_SPEED = FRONTEND_DEFAULTS.simulation.speed;
export const DEFAULT_PATCH_DEPTH = DEFAULT_TOPOLOGY_SPEC.patch_depth;
export const MIN_PATCH_DEPTH = FRONTEND_DEFAULTS.simulation.min_patch_depth;
export const MAX_PATCH_DEPTH = FRONTEND_DEFAULTS.simulation.max_patch_depth;
export const DEFAULT_DRAWER_OPEN = true;
export const RULE_SELECTION_ORIGIN_DEFAULT: RuleSelectionOrigin = "default";
export const RULE_SELECTION_ORIGIN_USER: RuleSelectionOrigin = "user";
