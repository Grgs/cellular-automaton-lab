from __future__ import annotations

from tools.profile_standalone_runtime import (
    ForkSample,
    RuntimeSample,
    render_summary,
    summarize_samples,
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
