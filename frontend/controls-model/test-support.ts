export const EMPTY_SYNC_STATE = {
    pendingRuleName: null,
    syncingRuleName: null,
    pendingSpeed: null,
    syncingSpeed: null,
    isSyncing: false,
    hasPendingRuleSync: false,
    hasPendingSpeedSync: false,
    shouldLockRule: false,
    shouldLockSpeed: false,
} as const;

export async function buildControlsModelState() {
    const { createAppState, setRules, setActiveRule, setTopology } =
        await import("../state/simulation-state.js");
    const state = createAppState();
    const rule = {
        name: "signal-rule",
        display_name: "Signal Rule",
        description: "Signal states",
        default_paint_state: 2,
        supports_randomize: false,
        rule_protocol: "test",
        supports_all_topologies: true,
        states: [
            { value: 0, label: "Dead", color: "#000000", paintable: false },
            { value: 2, label: "Signal", color: "#ff0000", paintable: true },
        ],
    };
    setRules(state, [rule]);
    setActiveRule(state, rule);
    setTopology(
        state,
        {
            topology_revision: "rev-1",
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 2,
                height: 2,
                patch_depth: 0,
            },
            cells: [
                {
                    id: "cell:a",
                    kind: "square",
                    neighbors: ["cell:b", "cell:c", null, null],
                    slot: "alpha",
                    center: { x: 0, y: 0 },
                    vertices: [
                        { x: 0, y: 0 },
                        { x: 1, y: 0 },
                        { x: 1, y: 1 },
                        { x: 0, y: 1 },
                    ],
                    tile_family: "family-a",
                    orientation_token: "north",
                    chirality_token: "left",
                    decoration_tokens: ["stripe", "dot"],
                },
                {
                    id: "cell:b",
                    kind: "triangle",
                    neighbors: ["cell:a", null, null],
                    center: { x: 1.1, y: 2.2 },
                    vertices: [
                        { x: 0, y: 0 },
                        { x: 1, y: 0 },
                        { x: 0.5, y: 1 },
                    ],
                    tile_family: "family-a",
                    orientation_token: "south",
                    decoration_tokens: ["dot"],
                },
                {
                    id: "cell:c",
                    kind: "triangle",
                    neighbors: ["cell:a", "cell:b", null],
                    center: { x: 2, y: 3 },
                    vertices: [
                        { x: 0, y: 0 },
                        { x: 1, y: 0 },
                        { x: 0.5, y: 1 },
                    ],
                    tile_family: "family-b",
                    chirality_token: "right",
                },
            ],
        },
        [0, 2, 2],
    );
    return state;
}
