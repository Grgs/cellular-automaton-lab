from tools.profile_tiling_latency import benchmark_periodic_build_stages


def test_periodic_build_stage_profile_reports_each_stage() -> None:
    profile = benchmark_periodic_build_stages("trihexagonal-3-6-3-6", 3, 2, repeats=1)

    assert profile["cell_count"] == 18
    assert profile["descriptor_loading_ms"] >= 0
    assert profile["cell_realization_ms"] >= 0
    assert profile["adjacency_ms"] >= 0
    assert profile["normalization_ms"] >= 0
    assert profile["serialization_ms"] >= 0
