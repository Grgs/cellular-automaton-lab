import type { PeriodicFaceTilingDescriptor } from "./rendering.js";

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

export type BootstrappedFrontendDefaults = FrontendDefaults;

export interface ServerMetaPayload {
    app_name: string;
}

export type AperiodicImplementationStatus =
    | "true_substitution"
    | "exact_affine"
    | "canonical_patch"
    | "known_deviation";

export interface BootstrappedAperiodicFamilyDefinition {
    tiling_family: string;
    label: string;
    experimental: boolean;
    implementation_status: AperiodicImplementationStatus;
    promotion_blocker: string | null;
    public_cell_kinds: readonly string[];
}

export interface AppBootstrapData {
    app_defaults: BootstrappedFrontendDefaults;
    topology_catalog: ReadonlyArray<BootstrappedTopologyDefinition>;
    periodic_face_tilings: ReadonlyArray<PeriodicFaceTilingDescriptor>;
    aperiodic_families: ReadonlyArray<BootstrappedAperiodicFamilyDefinition>;
    server_meta: ServerMetaPayload;
    snapshot_version: number;
}

export interface SizingPolicy {
    control: SizingControl;
    default: number;
    min: number;
    max: number;
    unsafe_max?: number;
}

export interface BootstrappedTopologyDefinition {
    tiling_family: string;
    label: string;
    picker_group: string;
    picker_order: number;
    sizing_mode: string;
    family: string;
    render_kind: string;
    viewport_sync_mode: string;
    supported_adjacency_modes: readonly string[];
    default_adjacency_mode: string;
    default_rules: Readonly<Record<string, string>>;
    geometry_keys: Readonly<Record<string, string>>;
    sizing_policy: Readonly<SizingPolicy>;
}

export type TopologyDefinition = BootstrappedTopologyDefinition;

export interface TopologyOption {
    value: string;
    label: string;
    group: string;
    order: number;
    family: string;
    previewKey: string;
    renderKind: string;
    sizingMode: string;
    searchAliases: readonly string[];
}

export interface AdjacencyModeOption {
    value: string;
    label: string;
}

export interface PointPayload {
    x: number;
    y: number;
}

export interface ApiTopologyCellPayload {
    id: string;
    kind: string;
    neighbors: Array<string | null>;
    slot?: string;
    center?: PointPayload;
    vertices?: PointPayload[];
    tile_family?: string;
    orientation_token?: string;
    chirality_token?: string;
    decoration_tokens?: string[];
}

export type TopologyCell = ApiTopologyCellPayload;

export interface IndexedTopologyCell extends TopologyCell {
    index: number;
}

export interface TopologyIndex {
    byId: Map<string, IndexedTopologyCell>;
}

export interface ApiTopologyPayload {
    topology_revision: string;
    topology_spec: TopologySpec;
    cells: TopologyCell[];
}

export interface TopologyPayload extends ApiTopologyPayload {
    geometry?: string;
    width?: number;
    height?: number;
}

export interface CellStateDefinition {
    value: number;
    label: string;
    color: string;
    paintable: boolean;
}

export interface ApiRuleDefinition {
    name: string;
    display_name: string;
    description: string;
    default_paint_state: number;
    supports_randomize: boolean;
    states: CellStateDefinition[];
    rule_protocol: string;
    supports_all_topologies: boolean;
}

export interface RuleDefinition extends ApiRuleDefinition {
    label?: string;
}

export interface RulesResponse {
    rules: RuleDefinition[];
}

export interface CompareRequest {
    seed: string;
    rule?: string;
    traversal?: string;
    steps?: number;
    grid_size?: number;
    geometries?: readonly string[];
    include_states?: boolean;
    /** When set, seed each tiling with this named shape (Policy A) instead of the bit seed. */
    pattern?: string;
}

export interface TopologyComparisonResultPayload {
    geometry: string;
    tiling_family: string;
    family: string;
    cell_count: number;
    seed_bits: number;
    seed_cells: number;
    initial_population: number;
    final_population: number;
    normalized_population: number;
    classification: string;
    period: number | null;
    steps_run: number;
    extinction_step: number | null;
    note: string | null;
    population: number[];
    change_rate: number[];
    // Present only when the request set include_states: true. Together they
    // reconstruct the begin/end board for an "open in board" / share link.
    topology_spec?: TopologySpec;
    initial_cells_by_id?: Record<string, number>;
    final_cells_by_id?: Record<string, number>;
}

export interface SeedComparisonResult {
    rule_name: string;
    seed: string;
    seed_bits: number;
    traversal: string;
    steps: number;
    grid_size: number;
    degenerate: boolean;
    results: TopologyComparisonResultPayload[];
}

export interface TopologyPreviewRequest {
    geometry: string;
    width?: number;
    height?: number;
    patch_depth?: number;
    /** When set, the tiling is built at the size a comparison sweep would use. */
    grid_size?: number;
    traversal?: string;
    /** When set, the named shape's geometric placement is returned as shape_cells. */
    pattern?: string;
}

export interface TopologyPreviewCell {
    id: string;
    kind: string;
    center: PointPayload;
    vertices: PointPayload[];
}

export interface TopologyPreview {
    topology_revision: string;
    topology_spec: TopologySpec;
    cells: TopologyPreviewCell[];
    /** Cell ids in canonical traversal order; present only when a traversal was requested. */
    order?: string[];
    /** Live cell ids for a named shape's placement; present only when a pattern was requested. */
    shape_cells?: Record<string, number>;
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
    description: string | null;
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

export interface ApiSimulationSnapshot {
    topology_spec: TopologySpec;
    speed: number;
    running: boolean;
    generation: number;
    rule: RuleDefinition;
    topology_revision: string;
    topology: TopologyPayload;
    cell_states: number[];
}

export type SimulationSnapshot = ApiSimulationSnapshot;

export interface PersistedSimulationSnapshotV5 {
    version: 5;
    topology_spec: TopologySpec;
    speed: number;
    running: boolean;
    generation: number;
    rule: string;
    cells_by_id: Record<string, number>;
}
