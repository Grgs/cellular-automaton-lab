"""Load and evaluate the checked-in standalone runtime performance policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_BUDGET_PATH: Final[Path] = ROOT_DIR / "tools" / "standalone_runtime_budget.json"


@dataclass(frozen=True)
class StandaloneRuntimeBudget:
    profile_name: str
    cpu_throttle_rate: float
    minimum_repeats: int
    forks_per_run: int
    observed_cold_start_ms: float
    cold_start_margin_ms: float
    cold_start_limit_ms: float

    def to_report_payload(self) -> dict[str, object]:
        return {
            "profileName": self.profile_name,
            "cpuThrottleRate": self.cpu_throttle_rate,
            "minimumRepeats": self.minimum_repeats,
            "forksPerRun": self.forks_per_run,
            "observedColdStartMs": self.observed_cold_start_ms,
            "coldStartMarginMs": self.cold_start_margin_ms,
            "coldStartLimitMs": self.cold_start_limit_ms,
        }


def _positive_number(value: object, *, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{field} must be a positive number")
    return float(value)


def _positive_integer(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def load_runtime_budget(path: Path = DEFAULT_RUNTIME_BUDGET_PATH) -> StandaloneRuntimeBudget:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schemaVersion") != 1:
        raise ValueError(f"{path}: unsupported or missing schemaVersion")
    profile = payload.get("profile")
    cold_start = payload.get("coldStartMs")
    if not isinstance(profile, dict) or not isinstance(cold_start, dict):
        raise ValueError(f"{path}: profile and coldStartMs must be objects")
    profile_name = profile.get("name")
    if not isinstance(profile_name, str) or not profile_name:
        raise ValueError(f"{path}: profile.name must be a non-empty string")
    observed = _positive_number(
        cold_start.get("observedBaseline"), field="coldStartMs.observedBaseline"
    )
    margin = _positive_number(
        cold_start.get("regressionMargin"), field="coldStartMs.regressionMargin"
    )
    limit = _positive_number(cold_start.get("limit"), field="coldStartMs.limit")
    if observed + margin != limit:
        raise ValueError(
            f"{path}: coldStartMs.limit must equal observedBaseline + regressionMargin"
        )
    return StandaloneRuntimeBudget(
        profile_name=profile_name,
        cpu_throttle_rate=_positive_number(
            profile.get("cpuThrottleRate"), field="profile.cpuThrottleRate"
        ),
        minimum_repeats=_positive_integer(
            profile.get("minimumRepeats"), field="profile.minimumRepeats"
        ),
        forks_per_run=_positive_integer(profile.get("forksPerRun"), field="profile.forksPerRun"),
        observed_cold_start_ms=observed,
        cold_start_margin_ms=margin,
        cold_start_limit_ms=limit,
    )


def evaluate_runtime_report(
    report: dict[str, object], budget: StandaloneRuntimeBudget
) -> tuple[str, ...]:
    violations: list[str] = []
    profile = report.get("profile")
    summary = report.get("summary")
    if not isinstance(profile, dict) or not isinstance(summary, dict):
        return ("profile report is missing profile or summary metadata",)
    if profile.get("name") != budget.profile_name:
        violations.append(
            f"profile name {profile.get('name')!r} does not match {budget.profile_name!r}"
        )
    throttle = profile.get("cpuThrottleRate")
    if not isinstance(throttle, (int, float)) or float(throttle) != budget.cpu_throttle_rate:
        violations.append(f"CPU throttle {throttle!r} does not match {budget.cpu_throttle_rate:g}x")
    repeats = profile.get("repeats")
    if not isinstance(repeats, int) or repeats < budget.minimum_repeats:
        violations.append(
            f"profile repeats {repeats!r} is below the required {budget.minimum_repeats}"
        )
    forks = profile.get("forksPerRun")
    if forks != budget.forks_per_run:
        violations.append(f"forks per run {forks!r} does not match {budget.forks_per_run}")
    cold_start_max = summary.get("coldStartMsMax")
    if not isinstance(cold_start_max, (int, float)):
        violations.append("profile summary is missing coldStartMsMax")
    elif float(cold_start_max) > budget.cold_start_limit_ms:
        violations.append(
            f"cold-start maximum {float(cold_start_max):.1f} ms exceeds "
            f"{budget.cold_start_limit_ms:.1f} ms"
        )
    return tuple(violations)
