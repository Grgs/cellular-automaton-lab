"""Test package root."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, settings
from hypothesis.configuration import set_hypothesis_home_dir


set_hypothesis_home_dir(Path(tempfile.gettempdir()) / "cellular-automaton-lab-hypothesis")

settings.register_profile(
    "cellular-automaton-lab",
    max_examples=20,
    deadline=None,
    derandomize=True,
    database=None,
    suppress_health_check=(HealthCheck.too_slow,),
)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "cellular-automaton-lab"))
