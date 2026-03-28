export type SizingControl = "cell_size" | "patch_depth";

export interface TopologySpec {
    tiling_family: string;
    adjacency_mode: string;
    sizing_mode: string;
    width: number;
    height: number;
    patch_depth: number;
}

export interface SimulationDefaults {
    topology_spec: TopologySpec;
    speed: number;
    rule: string;
    min_grid_size: number;
    max_grid_size: number;
    min_patch_depth: number;
    max_patch_depth: number;
    min_speed: number;
    max_speed: number;
}

export interface UiDefaults {
    cell_size: number;
    min_cell_size: number;
    max_cell_size: number;
    storage_key: string;
}

export interface ThemeDefaults {
    default: string;
    storage_key: string;
}

export interface FrontendDefaults {
    simulation: SimulationDefaults;
    ui: UiDefaults;
    theme: ThemeDefaults;
}

export interface BootstrappedFrontendDefaults {
    simulation?: Partial<SimulationDefaults> & {
        topology_spec?: Partial<TopologySpec>;
    };
    ui?: Partial<UiDefaults>;
    theme?: Partial<ThemeDefaults>;
}

export interface SizingPolicy {
    control: SizingControl;
    default: number;
    min: number;
    max: number;
}

export interface BootstrappedTopologyDefinition {
    tiling_family?: unknown;
    label?: unknown;
    picker_group?: unknown;
    picker_order?: unknown;
    sizing_mode?: unknown;
    family?: unknown;
    viewport_sync_mode?: unknown;
    supported_adjacency_modes?: unknown;
    default_adjacency_mode?: unknown;
    default_rules?: Record<string, string>;
    geometry_keys?: Record<string, string>;
    sizing_policy?: Partial<SizingPolicy>;
    [key: string]: unknown;
}

export interface TopologyDefinition {
    tiling_family: string;
    label: string;
    picker_group: string;
    picker_order: number;
    sizing_mode: string;
    family: string;
    viewport_sync_mode: string;
    supported_adjacency_modes: readonly string[];
    default_adjacency_mode: string;
    default_rules: Readonly<Record<string, string>>;
    variant_keys: Readonly<Record<string, string>>;
    sizing_policy: Readonly<SizingPolicy>;
}

export interface TopologyOption {
    value: string;
    label: string;
    group: string;
    order: number;
}

export interface AdjacencyModeOption {
    value: string;
    label: string;
}

export interface TopologyCell {
    id: string;
    [key: string]: unknown;
}

export interface IndexedTopologyCell extends TopologyCell {
    index: number;
}

export interface TopologyIndex {
    byId: Map<string, IndexedTopologyCell>;
}

export interface TopologyPayload {
    topology_revision?: string | null;
    topology_spec?: Partial<TopologySpec>;
    cells?: TopologyCell[];
    [key: string]: unknown;
}

export interface CellStateDefinition {
    value: number;
    label?: string;
    color?: string;
    paintable?: boolean;
    [key: string]: unknown;
}

export interface RuleDefinition {
    name: string;
    display_name?: string;
    label?: string;
    description?: string;
    default_paint_state?: number | null;
    supports_randomize?: boolean;
    states?: CellStateDefinition[];
    [key: string]: unknown;
}

export interface RulesResponse {
    rules: RuleDefinition[];
}

export interface CellIdentifier {
    id: string;
}

export interface CellStateUpdate extends CellIdentifier {
    state: number;
}

export interface CartesianSeedCell {
    x: number;
    y: number;
    state: number;
}

export interface PatternPayload {
    format: string;
    version: number;
    topology_spec: TopologySpec;
    rule: string;
    cells_by_id: Record<string, number>;
}

export interface ParsedPattern {
    format: string;
    version: number;
    topologySpec: TopologySpec;
    rule: string;
    cellsById: Record<string, number>;
    patchDepth: number;
    width: number;
    height: number;
}

export interface PresetMetadata {
    id: string;
    label: string;
    description?: string;
}

export interface PresetBuildContext {
    width: number;
    height: number;
    geometry: string;
    presetId: string;
}

export interface ResolvedPresetSelection {
    rule: RuleDefinition | null;
    ruleName: string;
    geometry: string;
    width: number;
    height: number;
    presetOptions: PresetMetadata[];
    defaultPresetId: string | null;
    selectedPresetId: string | null;
    presetId: string | null;
}

export interface SimulationSnapshot {
    topology_spec?: Partial<TopologySpec>;
    speed?: number;
    running?: boolean;
    generation?: number;
    rule?: RuleDefinition | null;
    topology_revision?: string | null;
    topology?: TopologyPayload | null;
    cell_states?: number[];
    [key: string]: unknown;
}
