import { indexTopology } from "./topology-index.js";
import type {
    CellMutationDelta,
    PersistedSimulationSnapshotV5,
    SimulationSnapshot,
} from "./types/domain.js";

export function applyCellMutationDelta(
    snapshot: SimulationSnapshot,
    delta: CellMutationDelta,
): SimulationSnapshot | null {
    if (
        delta.state_epoch !== snapshot.state_epoch ||
        delta.base_state_revision !== snapshot.state_revision ||
        delta.topology_revision !== snapshot.topology_revision ||
        delta.generation !== snapshot.generation
    ) {
        return null;
    }
    const expectedRevision =
        delta.cell_updates.length === 0 ? delta.base_state_revision : delta.base_state_revision + 1;
    if (delta.state_revision !== expectedRevision) {
        return null;
    }

    const topologyIndex = indexTopology(snapshot.topology);
    const nextCellStates = [...snapshot.cell_states];
    const updatedCellIds = new Set<string>();
    for (const update of delta.cell_updates) {
        const cell = topologyIndex.byId.get(update.id);
        if (!cell || updatedCellIds.has(update.id) || !Number.isInteger(update.state)) {
            return null;
        }
        updatedCellIds.add(update.id);
        nextCellStates[cell.index] = update.state;
    }
    return {
        ...snapshot,
        state_revision: delta.state_revision,
        cell_states: nextCellStates,
    };
}

export class SimulationSnapshotCache {
    private snapshot: SimulationSnapshot | null = null;

    current(): SimulationSnapshot | null {
        return this.snapshot;
    }

    install(
        nextSnapshot: SimulationSnapshot,
        requestBase: SimulationSnapshot | null,
    ): SimulationSnapshot {
        // When another response landed while this request was in flight, keep
        // the cached snapshot unless the arriving one is genuinely newer.
        // Epochs order runtime lifetimes (restore/replace resets revisions but
        // always mints a larger epoch), revisions order within a lifetime.
        if (this.snapshot !== requestBase && this.snapshot !== null) {
            const cached = this.snapshot;
            const stale =
                nextSnapshot.state_epoch < cached.state_epoch ||
                (nextSnapshot.state_epoch === cached.state_epoch &&
                    nextSnapshot.state_revision < cached.state_revision);
            if (stale) {
                return cached;
            }
        }
        this.snapshot = nextSnapshot;
        return nextSnapshot;
    }

    async reconcileDelta(
        delta: CellMutationDelta,
        refresh: () => Promise<SimulationSnapshot>,
    ): Promise<SimulationSnapshot> {
        const current = this.snapshot;
        if (current !== null) {
            const applied = applyCellMutationDelta(current, delta);
            if (applied !== null) {
                this.snapshot = applied;
                return applied;
            }
        }

        const refreshBase = this.snapshot;
        const refreshed = await refresh();
        return this.install(refreshed, refreshBase);
    }
}

export function persistedSnapshotFrom(snapshot: SimulationSnapshot): PersistedSimulationSnapshotV5 {
    const cellsById: Record<string, number> = {};
    snapshot.topology.cells.forEach((cell, index) => {
        const state = Number(snapshot.cell_states[index] ?? 0);
        if (state !== 0) {
            cellsById[cell.id] = state;
        }
    });
    return {
        version: 5,
        topology_spec: snapshot.topology_spec,
        speed: snapshot.speed,
        running: snapshot.running,
        generation: snapshot.generation,
        rule: snapshot.rule.name,
        cells_by_id: cellsById,
    };
}
