import type {
    CellMutationDelta,
    PersistedSimulationSnapshotV5,
    RuleDefinition,
    RulesResponse,
    SeedComparisonResult,
    SeedFilmstripResult,
    SimulationSnapshot,
    TopologyPayload,
    TopologyPreview,
    TopologySpec,
} from "../types/domain.js";
import type { PlainObject } from "../runtime-validation.js";
import { isPlainObject } from "../runtime-validation.js";

export interface RuntimeErrorDetails {
    error?: string;
    code?: string;
    limit?: number;
    estimated_cells?: number;
    actual_cells?: number;
}

export interface DecodedInitResponse {
    snapshot?: SimulationSnapshot;
    persistedSnapshot: PersistedSimulationSnapshotV5 | null;
}

export interface DecodedRequestResponse extends RuntimeErrorDetails {
    ok: boolean;
    snapshot?: SimulationSnapshot;
    rules?: RulesResponse["rules"];
    comparison?: SeedComparisonResult;
    filmstrip?: SeedFilmstripResult;
    topologyPreview?: TopologyPreview;
    cellDelta?: CellMutationDelta;
    persistedSnapshot?: PersistedSimulationSnapshotV5;
}

export interface DecodedTickResponse extends RuntimeErrorDetails {
    ok: boolean;
    stepped: boolean;
    snapshot?: SimulationSnapshot;
    persistedSnapshot?: PersistedSimulationSnapshotV5;
}

function invalid(context: string, detail: string): never {
    throw new Error(`${context} returned invalid ${detail}.`);
}

function object(value: unknown, context: string, detail: string): PlainObject {
    return isPlainObject(value) ? value : invalid(context, detail);
}

function string(value: unknown, context: string, detail: string): string {
    return typeof value === "string" ? value : invalid(context, detail);
}

function number(value: unknown, context: string, detail: string): number {
    return typeof value === "number" && Number.isFinite(value) ? value : invalid(context, detail);
}

function integer(value: unknown, context: string, detail: string): number {
    const result = number(value, context, detail);
    return Number.isInteger(result) ? result : invalid(context, detail);
}

function boolean(value: unknown, context: string, detail: string): boolean {
    return typeof value === "boolean" ? value : invalid(context, detail);
}

function array(value: unknown, context: string, detail: string): unknown[] {
    return Array.isArray(value) ? value : invalid(context, detail);
}

function optionalString(value: unknown, context: string, detail: string): string | undefined {
    return value === undefined ? undefined : string(value, context, detail);
}

function optionalNumber(value: unknown, context: string, detail: string): number | undefined {
    return value === undefined ? undefined : number(value, context, detail);
}

function numberRecord(value: unknown, context: string, detail: string): Record<string, number> {
    const record = object(value, context, detail);
    for (const [key, entry] of Object.entries(record)) {
        number(entry, context, `${detail}.${key}`);
    }
    return record as Record<string, number>;
}

function nullableNumber(value: unknown, context: string, detail: string): number | null {
    return value === null ? null : number(value, context, detail);
}

function nullableString(value: unknown, context: string, detail: string): string | null {
    return value === null ? null : string(value, context, detail);
}

function point(value: unknown, context: string, detail: string): { x: number; y: number } {
    const payload = object(value, context, detail);
    return {
        x: number(payload.x, context, `${detail}.x`),
        y: number(payload.y, context, `${detail}.y`),
    };
}

function topologyCell(
    value: unknown,
    context: string,
    detail: string,
): TopologyPayload["cells"][number] {
    const payload = object(value, context, detail);
    const center =
        payload.center === undefined
            ? undefined
            : point(payload.center, context, `${detail}.center`);
    const vertices =
        payload.vertices === undefined
            ? undefined
            : array(payload.vertices, context, `${detail}.vertices`).map((entry) =>
                  point(entry, context, `${detail}.vertex`),
              );
    const decorations =
        payload.decoration_tokens === undefined
            ? undefined
            : array(payload.decoration_tokens, context, `${detail}.decoration_tokens`).map(
                  (entry) => string(entry, context, `${detail}.decoration_token`),
              );
    return {
        id: string(payload.id, context, `${detail}.id`),
        kind: string(payload.kind, context, `${detail}.kind`),
        neighbors: array(payload.neighbors, context, `${detail}.neighbors`).map((entry) =>
            entry === null ? null : string(entry, context, `${detail}.neighbor`),
        ),
        ...(payload.slot === undefined
            ? {}
            : { slot: string(payload.slot, context, `${detail}.slot`) }),
        ...(center === undefined ? {} : { center }),
        ...(vertices === undefined ? {} : { vertices }),
        ...(payload.tile_family === undefined
            ? {}
            : { tile_family: string(payload.tile_family, context, `${detail}.tile_family`) }),
        ...(payload.orientation_token === undefined
            ? {}
            : {
                  orientation_token: string(
                      payload.orientation_token,
                      context,
                      `${detail}.orientation_token`,
                  ),
              }),
        ...(payload.chirality_token === undefined
            ? {}
            : {
                  chirality_token: string(
                      payload.chirality_token,
                      context,
                      `${detail}.chirality_token`,
                  ),
              }),
        ...(decorations === undefined ? {} : { decoration_tokens: decorations }),
    };
}

function runtimeJson(raw: string, context: string): PlainObject {
    return object(JSON.parse(raw) as unknown, context, "payload");
}

function topologySpec(value: unknown, context: string): TopologySpec {
    const payload = object(value, context, "topology spec");
    return {
        tiling_family: string(payload.tiling_family, context, "topology spec.tiling_family"),
        adjacency_mode: string(payload.adjacency_mode, context, "topology spec.adjacency_mode"),
        sizing_mode: string(payload.sizing_mode, context, "topology spec.sizing_mode"),
        width: number(payload.width, context, "topology spec.width"),
        height: number(payload.height, context, "topology spec.height"),
        patch_depth: number(payload.patch_depth, context, "topology spec.patch_depth"),
    };
}

function compatibleFamilies(value: unknown, context: string): string[] | null {
    if (value === null) {
        return null;
    }
    return array(value, context, "compatible tiling families").map((entry) =>
        string(entry, context, "compatible tiling family"),
    );
}

function ruleDefinition(value: unknown, context: string): RuleDefinition {
    const payload = object(value, context, "rule definition");
    const states = array(payload.states, context, "rule states").map((value) => {
        const state = object(value, context, "rule state");
        return {
            value: number(state.value, context, "rule state.value"),
            label: string(state.label, context, "rule state.label"),
            color: string(state.color, context, "rule state.color"),
            paintable: boolean(state.paintable, context, "rule state.paintable"),
        };
    });
    const label = optionalString(payload.label, context, "rule definition.label");
    return {
        name: string(payload.name, context, "rule definition.name"),
        display_name: string(payload.display_name, context, "rule definition.display_name"),
        description: string(payload.description, context, "rule definition.description"),
        default_paint_state: number(
            payload.default_paint_state,
            context,
            "rule definition.default_paint_state",
        ),
        supports_randomize: boolean(
            payload.supports_randomize,
            context,
            "rule definition.supports_randomize",
        ),
        states,
        rule_protocol: string(payload.rule_protocol, context, "rule definition.rule_protocol"),
        supports_all_topologies: boolean(
            payload.supports_all_topologies,
            context,
            "rule definition.supports_all_topologies",
        ),
        compatible_tiling_families: compatibleFamilies(payload.compatible_tiling_families, context),
        ...(label === undefined ? {} : { label }),
    };
}

function topology(value: unknown, context: string): TopologyPayload {
    const payload = object(value, context, "topology payload");
    const cells = array(payload.cells, context, "topology cells").map((entry) =>
        topologyCell(entry, context, "topology cell"),
    );
    return {
        topology_revision: string(
            payload.topology_revision,
            context,
            "topology payload.topology_revision",
        ),
        topology_spec: topologySpec(payload.topology_spec, context),
        cells,
        ...(payload.geometry === undefined
            ? {}
            : { geometry: string(payload.geometry, context, "topology payload.geometry") }),
        ...(typeof payload.width === "number" ? { width: payload.width } : {}),
        ...(typeof payload.height === "number" ? { height: payload.height } : {}),
    };
}

function optionalSnapshot(value: unknown, context: string): SimulationSnapshot | undefined {
    if (value === undefined) {
        return undefined;
    }
    const payload = object(value, context, "simulation snapshot");
    const cellStates = array(payload.cell_states, context, "simulation snapshot.cell_states").map(
        (entry) => number(entry, context, "simulation cell state"),
    );
    return {
        topology_spec: topologySpec(payload.topology_spec, context),
        speed: number(payload.speed, context, "simulation snapshot.speed"),
        running: boolean(payload.running, context, "simulation snapshot.running"),
        generation: number(payload.generation, context, "simulation snapshot.generation"),
        state_revision: number(
            payload.state_revision,
            context,
            "simulation snapshot.state_revision",
        ),
        rule: ruleDefinition(payload.rule, context),
        topology_revision: string(
            payload.topology_revision,
            context,
            "simulation snapshot.topology_revision",
        ),
        topology: topology(payload.topology, context),
        cell_states: cellStates,
    };
}

function optionalPersistedSnapshot(
    value: unknown,
    context: string,
): PersistedSimulationSnapshotV5 | undefined {
    if (value === undefined || value === null) {
        return undefined;
    }
    const payload = object(value, context, "persisted snapshot");
    if (payload.version !== 5) {
        invalid(context, "persisted snapshot.version");
    }
    return {
        version: 5,
        topology_spec: topologySpec(payload.topology_spec, context),
        speed: number(payload.speed, context, "persisted snapshot.speed"),
        running: boolean(payload.running, context, "persisted snapshot.running"),
        generation: number(payload.generation, context, "persisted snapshot.generation"),
        rule: string(payload.rule, context, "persisted snapshot.rule"),
        cells_by_id: numberRecord(payload.cells_by_id, context, "persisted snapshot.cells_by_id"),
    };
}

function optionalRules(value: unknown, context: string): RulesResponse["rules"] | undefined {
    return value === undefined
        ? undefined
        : array(value, context, "rules").map((entry) => ruleDefinition(entry, context));
}

function optionalTopologyPreview(value: unknown, context: string): TopologyPreview | undefined {
    if (value === undefined) {
        return undefined;
    }
    const payload = object(value, context, "topology preview");
    const cells = array(payload.cells, context, "topology preview.cells").map((entry) => {
        const cell = object(entry, context, "topology preview cell");
        return {
            id: string(cell.id, context, "topology preview cell.id"),
            kind: string(cell.kind, context, "topology preview cell.kind"),
            center: point(cell.center, context, "topology preview cell.center"),
            vertices: array(cell.vertices, context, "topology preview cell.vertices").map(
                (vertex) => point(vertex, context, "topology preview cell.vertex"),
            ),
        };
    });
    const revision = string(
        payload.topology_revision,
        context,
        "topology preview.topology_revision",
    );
    const order =
        payload.order === undefined
            ? undefined
            : array(payload.order, context, "topology preview.order").map((entry) =>
                  string(entry, context, "topology preview order entry"),
              );
    const shapeCells =
        payload.shape_cells === undefined
            ? undefined
            : numberRecord(payload.shape_cells, context, "topology preview.shape_cells");
    return {
        topology_revision: revision,
        topology_spec: topologySpec(payload.topology_spec, context),
        cells,
        ...(order === undefined ? {} : { order }),
        ...(shapeCells === undefined ? {} : { shape_cells: shapeCells }),
    };
}

function optionalFilmstrip(value: unknown, context: string): SeedFilmstripResult | undefined {
    if (value === undefined) {
        return undefined;
    }
    const payload = object(value, context, "filmstrip payload");
    const tilings = array(payload.tilings, context, "filmstrip tilings").map((entry) => {
        const tiling = object(entry, context, "filmstrip tiling");
        const label = optionalString(tiling.label, context, "filmstrip tiling.label");
        const seedOrder =
            tiling.seed_order === undefined
                ? undefined
                : array(tiling.seed_order, context, "filmstrip tiling.seed_order").map((cellId) =>
                      string(cellId, context, "filmstrip tiling seed cell"),
                  );
        return {
            geometry: string(tiling.geometry, context, "filmstrip tiling.geometry"),
            tiling_family: string(tiling.tiling_family, context, "filmstrip tiling.tiling_family"),
            family: string(tiling.family, context, "filmstrip tiling.family"),
            ...(label === undefined ? {} : { label }),
            cell_count: number(tiling.cell_count, context, "filmstrip tiling.cell_count"),
            topology: topology(tiling.topology, context),
            topology_spec: topologySpec(tiling.topology_spec, context),
            frames: array(tiling.frames, context, "filmstrip tiling.frames").map((frame) =>
                numberRecord(frame, context, "filmstrip frame"),
            ),
            extinction_step: nullableNumber(
                tiling.extinction_step,
                context,
                "filmstrip tiling.extinction_step",
            ),
            period: nullableNumber(tiling.period, context, "filmstrip tiling.period"),
            note: nullableString(tiling.note, context, "filmstrip tiling.note"),
            ...(seedOrder === undefined ? {} : { seed_order: seedOrder }),
        };
    });
    return {
        rule_name: string(payload.rule_name, context, "filmstrip.rule_name"),
        seed: string(payload.seed, context, "filmstrip.seed"),
        traversal: string(payload.traversal, context, "filmstrip.traversal"),
        frame_count: number(payload.frame_count, context, "filmstrip.frame_count"),
        grid_size: number(payload.grid_size, context, "filmstrip.grid_size"),
        tilings,
    };
}

function optionalComparison(value: unknown, context: string): SeedComparisonResult | undefined {
    if (value === undefined) {
        return undefined;
    }
    const payload = object(value, context, "comparison payload");
    const results = array(payload.results, context, "comparison results").map((entry) => {
        const result = object(entry, context, "comparison result");
        const resultTopologySpec =
            result.topology_spec === undefined
                ? undefined
                : topologySpec(result.topology_spec, context);
        const initialCells =
            result.initial_cells_by_id === undefined
                ? undefined
                : numberRecord(
                      result.initial_cells_by_id,
                      context,
                      "comparison result.initial_cells_by_id",
                  );
        const finalCells =
            result.final_cells_by_id === undefined
                ? undefined
                : numberRecord(
                      result.final_cells_by_id,
                      context,
                      "comparison result.final_cells_by_id",
                  );
        return {
            geometry: string(result.geometry, context, "comparison result.geometry"),
            tiling_family: string(result.tiling_family, context, "comparison result.tiling_family"),
            family: string(result.family, context, "comparison result.family"),
            cell_count: number(result.cell_count, context, "comparison result.cell_count"),
            seed_bits: number(result.seed_bits, context, "comparison result.seed_bits"),
            seed_cells: number(result.seed_cells, context, "comparison result.seed_cells"),
            initial_population: number(
                result.initial_population,
                context,
                "comparison result.initial_population",
            ),
            final_population: number(
                result.final_population,
                context,
                "comparison result.final_population",
            ),
            normalized_population: number(
                result.normalized_population,
                context,
                "comparison result.normalized_population",
            ),
            classification: string(
                result.classification,
                context,
                "comparison result.classification",
            ),
            period: nullableNumber(result.period, context, "comparison result.period"),
            steps_run: number(result.steps_run, context, "comparison result.steps_run"),
            extinction_step: nullableNumber(
                result.extinction_step,
                context,
                "comparison result.extinction_step",
            ),
            note: nullableString(result.note, context, "comparison result.note"),
            population: array(result.population, context, "comparison result.population").map(
                (count) => number(count, context, "comparison population entry"),
            ),
            change_rate: array(result.change_rate, context, "comparison result.change_rate").map(
                (rate) => number(rate, context, "comparison change-rate entry"),
            ),
            ...(resultTopologySpec === undefined ? {} : { topology_spec: resultTopologySpec }),
            ...(initialCells === undefined ? {} : { initial_cells_by_id: initialCells }),
            ...(finalCells === undefined ? {} : { final_cells_by_id: finalCells }),
        };
    });
    return {
        rule_name: string(payload.rule_name, context, "comparison.rule_name"),
        seed: string(payload.seed, context, "comparison.seed"),
        seed_bits: number(payload.seed_bits, context, "comparison.seed_bits"),
        traversal: string(payload.traversal, context, "comparison.traversal"),
        steps: number(payload.steps, context, "comparison.steps"),
        grid_size: number(payload.grid_size, context, "comparison.grid_size"),
        degenerate: boolean(payload.degenerate, context, "comparison.degenerate"),
        results,
    };
}

export function decodeCellMutationDelta(value: unknown, context = "Runtime"): CellMutationDelta {
    const payload = object(value, context, "cell delta");
    return {
        base_state_revision: integer(
            payload.base_state_revision,
            context,
            "cell delta.base_state_revision",
        ),
        state_revision: integer(payload.state_revision, context, "cell delta.state_revision"),
        topology_revision: string(
            payload.topology_revision,
            context,
            "cell delta.topology_revision",
        ),
        generation: integer(payload.generation, context, "cell delta.generation"),
        cell_updates: array(payload.cell_updates, context, "cell delta.cell_updates").map(
            (entry) => {
                const update = object(entry, context, "cell delta update");
                return {
                    id: string(update.id, context, "cell delta update.id"),
                    state: integer(update.state, context, "cell delta update.state"),
                };
            },
        ),
    };
}

function optionalCellDelta(payload: PlainObject, context: string): CellMutationDelta | undefined {
    return payload.base_state_revision === undefined
        ? undefined
        : decodeCellMutationDelta(payload, context);
}

function errorDetails(payload: PlainObject, context: string): RuntimeErrorDetails {
    return {
        ...(payload.error === undefined ? {} : { error: string(payload.error, context, "error") }),
        ...(payload.code === undefined
            ? {}
            : { code: string(payload.code, context, "error code") }),
        ...(payload.limit === undefined
            ? {}
            : { limit: number(payload.limit, context, "error limit") }),
        ...(payload.estimated_cells === undefined
            ? {}
            : {
                  estimated_cells: number(payload.estimated_cells, context, "estimated cell count"),
              }),
        ...(payload.actual_cells === undefined
            ? {}
            : { actual_cells: number(payload.actual_cells, context, "actual cell count") }),
    };
}

export function decodeInitResponse(raw: string): DecodedInitResponse {
    const context = "Standalone init";
    const payload = runtimeJson(raw, context);
    const snapshot = optionalSnapshot(payload.snapshot, context);
    return {
        ...(snapshot === undefined ? {} : { snapshot }),
        persistedSnapshot: optionalPersistedSnapshot(payload.persisted_snapshot, context) ?? null,
    };
}

export function decodeRequestResponse(raw: string): DecodedRequestResponse {
    const context = "Standalone request";
    const payload = runtimeJson(raw, context);
    const snapshot = optionalSnapshot(payload.snapshot, context);
    const rules = optionalRules(payload.rules, context);
    const comparison = optionalComparison(payload.comparison, context);
    const filmstrip = optionalFilmstrip(payload.filmstrip, context);
    const topologyPreview = optionalTopologyPreview(payload.topology_preview, context);
    const cellDelta = optionalCellDelta(payload, context);
    const persistedSnapshot = optionalPersistedSnapshot(payload.persisted_snapshot, context);
    return {
        ok: boolean(payload.ok, context, "ok"),
        ...errorDetails(payload, context),
        ...(snapshot === undefined ? {} : { snapshot }),
        ...(rules === undefined ? {} : { rules }),
        ...(comparison === undefined ? {} : { comparison }),
        ...(filmstrip === undefined ? {} : { filmstrip }),
        ...(topologyPreview === undefined ? {} : { topologyPreview }),
        ...(cellDelta === undefined ? {} : { cellDelta }),
        ...(persistedSnapshot === undefined ? {} : { persistedSnapshot }),
    };
}

export function decodeTickResponse(raw: string): DecodedTickResponse {
    const context = "Standalone tick";
    const payload = runtimeJson(raw, context);
    const snapshot = optionalSnapshot(payload.snapshot, context);
    const persistedSnapshot = optionalPersistedSnapshot(payload.persisted_snapshot, context);
    return {
        ok: boolean(payload.ok, context, "ok"),
        stepped: boolean(payload.stepped, context, "stepped"),
        ...errorDetails(payload, context),
        ...(snapshot === undefined ? {} : { snapshot }),
        ...(persistedSnapshot === undefined ? {} : { persistedSnapshot }),
    };
}
