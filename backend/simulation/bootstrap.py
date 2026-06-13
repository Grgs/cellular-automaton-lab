from __future__ import annotations

import atexit

from flask import Flask

from backend.rules import RuleRegistry
from backend.simulation.sessions import SimulationSessionRegistry


def register_simulation(app: Flask) -> SimulationSessionRegistry:
    rule_registry = RuleRegistry()
    session_registry = SimulationSessionRegistry(
        rule_registry=rule_registry,
        instance_path=app.instance_path,
    )

    app.extensions["rule_registry"] = rule_registry
    app.extensions["simulation_sessions"] = session_registry
    atexit.register(session_registry.shutdown)
    return session_registry
