from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.payload_types import TopologySpecInput, TopologySpecPatch
from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.simulation.coordinator import SimulationCoordinator
from backend.simulation.models import CellMutationDelta, SimulationSnapshot
from backend.simulation.service import SimulationService


class ApplicationCommandTarget(Protocol):
    @property
    def rules(self) -> RuleRegistry: ...

    def get_state(self) -> SimulationSnapshot: ...
    def get_rule(self) -> AutomatonRule: ...
    def start(self) -> SimulationSnapshot: ...
    def pause(self) -> None: ...
    def resume(self) -> SimulationSnapshot: ...
    def step(self) -> None: ...
    def reset(
        self,
        topology_spec: TopologySpecInput | None = None,
        rule_name: str | None = None,
        speed: float | None = None,
        randomize: bool = False,
    ) -> None: ...
    def update_config(
        self,
        topology_spec: TopologySpecPatch | None = None,
        speed: float | None = None,
        rule_name: str | None = None,
    ) -> None: ...
    def toggle_cell_by_id(self, cell_id: str) -> CellMutationDelta: ...
    def set_cell_state_by_id(self, cell_id: str, state: int) -> CellMutationDelta: ...
    def set_cells_by_id(self, cells: list[tuple[str, int]]) -> CellMutationDelta: ...


@dataclass(frozen=True)
class CoordinatorCommandTarget:
    coordinator: SimulationCoordinator
    rules: RuleRegistry

    def get_state(self) -> SimulationSnapshot:
        return self.coordinator.get_state()

    def get_rule(self) -> AutomatonRule:
        return self.coordinator.get_rule()

    def start(self) -> SimulationSnapshot:
        return self.coordinator.start()

    def pause(self) -> None:
        self.coordinator.pause()

    def resume(self) -> SimulationSnapshot:
        return self.coordinator.resume()

    def step(self) -> None:
        self.coordinator.step()

    def reset(
        self,
        topology_spec: TopologySpecInput | None = None,
        rule_name: str | None = None,
        speed: float | None = None,
        randomize: bool = False,
    ) -> None:
        self.coordinator.reset(topology_spec, rule_name, speed, randomize)

    def update_config(
        self,
        topology_spec: TopologySpecPatch | None = None,
        speed: float | None = None,
        rule_name: str | None = None,
    ) -> None:
        self.coordinator.update_config(topology_spec, speed, rule_name)

    def toggle_cell_by_id(self, cell_id: str) -> CellMutationDelta:
        return self.coordinator.toggle_cell_by_id(cell_id)

    def set_cell_state_by_id(self, cell_id: str, state: int) -> CellMutationDelta:
        return self.coordinator.set_cell_state_by_id(cell_id, state)

    def set_cells_by_id(self, cells: list[tuple[str, int]]) -> CellMutationDelta:
        return self.coordinator.set_cells_by_id(cells)


@dataclass(frozen=True)
class ServiceCommandTarget:
    service: SimulationService
    rules: RuleRegistry

    def get_state(self) -> SimulationSnapshot:
        return self.service.get_state()

    def get_rule(self) -> AutomatonRule:
        return self.service.state.rule

    def start(self) -> SimulationSnapshot:
        return self.service.start()

    def pause(self) -> None:
        self.service.pause()

    def resume(self) -> SimulationSnapshot:
        return self.service.resume()

    def step(self) -> None:
        self.service.step()

    def reset(
        self,
        topology_spec: TopologySpecInput | None = None,
        rule_name: str | None = None,
        speed: float | None = None,
        randomize: bool = False,
    ) -> None:
        self.service.reset(topology_spec, rule_name, speed, randomize)

    def update_config(
        self,
        topology_spec: TopologySpecPatch | None = None,
        speed: float | None = None,
        rule_name: str | None = None,
    ) -> None:
        self.service.update_config(topology_spec, speed, rule_name)

    def toggle_cell_by_id(self, cell_id: str) -> CellMutationDelta:
        return self.service.toggle_cell_by_id(cell_id)

    def set_cell_state_by_id(self, cell_id: str, state: int) -> CellMutationDelta:
        return self.service.set_cell_state_by_id(cell_id, state)

    def set_cells_by_id(self, cells: list[tuple[str, int]]) -> CellMutationDelta:
        return self.service.set_cells_by_id(cells)
