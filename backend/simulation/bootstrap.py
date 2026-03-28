from __future__ import annotations

import atexit
from pathlib import Path

from flask import Flask

from backend.rules import RuleRegistry
from backend.simulation.coordinator import SimulationCoordinator
from backend.simulation.persistence import SimulationStateStore


def register_simulation(app: Flask) -> SimulationCoordinator:
    rule_registry = RuleRegistry()
    state_store = SimulationStateStore(Path(app.instance_path) / "simulation_state.json")
    simulation = SimulationCoordinator(rule_registry=rule_registry, state_store=state_store)
    simulation.start_background_loop()

    app.extensions["rule_registry"] = rule_registry
    app.extensions["simulation_coordinator"] = simulation
    atexit.register(simulation.shutdown)
    return simulation
