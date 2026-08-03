from __future__ import annotations

import json
from pathlib import Path

from tools.profile_standalone_runtime import (
    ForkSample,
    RuntimeSample,
    render_summary,
    summarize_samples,
)
from tools.standalone_runtime_budget import (
    StandaloneRuntimeBudget,
    evaluate_runtime_report,
    load_runtime_budget,
)


def _budget() -> StandaloneRuntimeBudget:
    return StandaloneRuntimeBudget(
        profile_name="emulated-lower-end-desktop",
        cpu_throttle_rate=4,
        minimum_repeats=3,
        forks_per_run=1,
        observed_cold_start_ms=1200,
        cold_start_margin_ms=800,
        cold_start_limit_ms=2000,
    )


def _sample(
    *, cold_start_ms: float, first_startup_ms: float, first_memory_bytes: int
) -> RuntimeSample:
    return RuntimeSample(
        cold_start_ms=cold_start_ms,
        browser_baseline_memory_bytes=50,
        main_runtime_memory_bytes=100,
        forks=[
            ForkSample(
                fork_id="profile-1",
                startup_ms=first_startup_ms,
                memory_bytes=100 + first_memory_bytes,
                incremental_memory_bytes=first_memory_bytes,
            )
        ],
        peak_browser_memory_bytes=150 + first_memory_bytes,
        after_dispose_browser_memory_bytes=140,
    )


def test_summarize_samples_reports_medians_and_maxima() -> None:
    summary = summarize_samples(
        [
            _sample(cold_start_ms=1000, first_startup_ms=500, first_memory_bytes=20),
            _sample(cold_start_ms=1200, first_startup_ms=700, first_memory_bytes=30),
            _sample(cold_start_ms=1100, first_startup_ms=600, first_memory_bytes=25),
        ],
        forks_per_run=1,
    )

    assert summary["coldStartMsMedian"] == 1100
    assert summary["coldStartMsMax"] == 1200
    forks = summary["forks"]
    assert isinstance(forks, list)
    assert forks[0]["startupMsMedian"] == 600
    assert forks[0]["incrementalMemoryBytesMedian"] == 25


def test_render_summary_names_profile_and_fork_measurements() -> None:
    samples = [_sample(cold_start_ms=1000, first_startup_ms=500, first_memory_bytes=20)]
    report: dict[str, object] = {
        "profile": {
            "name": "emulated-lower-end-desktop",
            "cpuThrottleRate": 4,
            "repeats": 1,
            "forksPerRun": 1,
        },
        "summary": summarize_samples(samples, forks_per_run=1),
    }

    rendered = render_summary(report)

    assert "emulated-lower-end-desktop" in rendered
    assert "cold start: median 1000.0 ms" in rendered
    assert "fork 1: startup median 500.0 ms" in rendered


def test_load_runtime_budget_requires_an_explicit_additive_margin(tmp_path: Path) -> None:
    budget_path = tmp_path / "budget.json"
    budget_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "profile": {
                    "name": "emulated-lower-end-desktop",
                    "cpuThrottleRate": 4,
                    "minimumRepeats": 3,
                    "forksPerRun": 2,
                },
                "coldStartMs": {
                    "observedBaseline": 3690,
                    "regressionMargin": 4310,
                    "limit": 8000,
                },
            }
        ),
        encoding="utf-8",
    )

    budget = load_runtime_budget(budget_path)

    assert budget.cold_start_limit_ms == 8000
    assert budget.minimum_repeats == 3

    payload = json.loads(budget_path.read_text(encoding="utf-8"))
    payload["coldStartMs"]["limit"] = 7999
    budget_path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        load_runtime_budget(budget_path)
    except ValueError as error:
        assert "observedBaseline + regressionMargin" in str(error)
    else:
        raise AssertionError("inconsistent cold-start budget was accepted")


def test_evaluate_runtime_report_checks_profile_shape_and_maximum() -> None:
    report: dict[str, object] = {
        "profile": {
            "name": "emulated-lower-end-desktop",
            "cpuThrottleRate": 4,
            "repeats": 3,
            "forksPerRun": 1,
        },
        "summary": {"coldStartMsMax": 1900},
    }

    assert evaluate_runtime_report(report, _budget()) == ()

    report["summary"] = {"coldStartMsMax": 2100}
    assert evaluate_runtime_report(report, _budget()) == (
        "cold-start maximum 2100.0 ms exceeds 2000.0 ms",
    )


def test_render_summary_reports_budget_status() -> None:
    samples = [_sample(cold_start_ms=1000, first_startup_ms=500, first_memory_bytes=20)]
    report: dict[str, object] = {
        "profile": {
            "name": "emulated-lower-end-desktop",
            "cpuThrottleRate": 4,
            "repeats": 3,
            "forksPerRun": 1,
        },
        "summary": summarize_samples(samples, forks_per_run=1),
        "budgetEvaluation": {
            "coldStartLimitMs": 2000,
            "passed": True,
            "violations": [],
        },
    }

    assert "cold-start budget: PASS | limit 2000.0 ms" in render_summary(report)
