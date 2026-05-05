import type {
    AppBootstrapData,
    CellIdentifier,
    CellStateUpdate,
    PersistedSimulationSnapshotV5,
    RulesResponse,
    SimulationSnapshot,
    TopologySpec,
} from "./domain.js";

export interface ConfigTopologySpecPatch {
    width?: number;
    height?: number;
    unsafe_size_override?: boolean;
}

export interface ResetTopologySpec extends TopologySpec {
    unsafe_size_override?: boolean;
}

export interface ConfigSyncBody {
    topology_spec?: ConfigTopologySpecPatch;
    speed?: number;
    rule?: string | null;
}

export interface ResetControlBody {
    topology_spec: ResetTopologySpec;
    speed: number;
    rule: string | null;
    randomize: boolean;
}

export type CellTargetRequest = CellIdentifier;

export type CellUpdateRequest = CellStateUpdate;

export interface CellUpdatesRequest {
    cells: CellUpdateRequest[];
}

export interface ControlCommandMap {
    "/api/control/start": undefined;
    "/api/control/pause": undefined;
    "/api/control/resume": undefined;
    "/api/control/step": undefined;
    "/api/control/reset": ResetControlBody;
    "/api/config": ConfigSyncBody;
}

export type EmptyControlCommandPath = {
    [TPath in keyof ControlCommandMap]: ControlCommandMap[TPath] extends undefined ? TPath : never;
}[keyof ControlCommandMap];

export interface FetchRulesFunction {
    (): Promise<RulesResponse>;
}

export interface FetchStateFunction {
    (): Promise<SimulationSnapshot>;
}

export interface SimulationBackend {
    getState(): Promise<SimulationSnapshot>;
    getRules(): Promise<RulesResponse>;
    dispose(): void | Promise<void>;
    postControl(path: EmptyControlCommandPath): Promise<SimulationSnapshot>;
    postControl(path: "/api/control/reset", body: ResetControlBody): Promise<SimulationSnapshot>;
    postControl(path: "/api/config", body: ConfigSyncBody): Promise<SimulationSnapshot>;
    toggleCell(cell: CellTargetRequest): Promise<SimulationSnapshot>;
    setCell(cell: CellTargetRequest, state: number): Promise<SimulationSnapshot>;
    setCells(cells: CellUpdateRequest[]): Promise<SimulationSnapshot>;
}

export interface SimulationStatePersistence {
    load(): Promise<PersistedSimulationSnapshotV5 | null>;
    save(snapshot: PersistedSimulationSnapshotV5): Promise<void>;
}

export interface PostControlFunction {
    (path: EmptyControlCommandPath): Promise<SimulationSnapshot>;
    (path: "/api/control/reset", body: ResetControlBody): Promise<SimulationSnapshot>;
    (path: "/api/config", body: ConfigSyncBody): Promise<SimulationSnapshot>;
}

export interface CellMutationRequestFunction {
    (cell: CellTargetRequest, state?: number): Promise<SimulationSnapshot>;
}

export interface ToggleCellRequestFunction {
    (cell: CellTargetRequest): Promise<SimulationSnapshot>;
}

export interface SetCellRequestFunction {
    (cell: CellTargetRequest, state: number): Promise<SimulationSnapshot>;
}

export interface SetCellsRequestFunction {
    (cells: CellUpdateRequest[]): Promise<SimulationSnapshot>;
}

export interface InitAppOptions {
    backend?: SimulationBackend;
    bootstrapData?: AppBootstrapData | null;
}
