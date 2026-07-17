from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.profile_refactor_baseline import _bundle_baseline, _median_payload, render_summary


class RefactorBaselineProfileTests(unittest.TestCase):
    def test_median_payload_returns_the_latest_payload_and_median(self) -> None:
        calls: list[int] = []

        def payload() -> dict[str, int]:
            calls.append(len(calls) + 1)
            return {"call": calls[-1]}

        result, elapsed_ms = _median_payload(payload, repeats=3)

        self.assertEqual(result, {"call": 3})
        self.assertGreaterEqual(elapsed_ms, 0)

    def test_missing_bundle_is_reported_without_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing"
            self.assertEqual(
                _bundle_baseline(missing),
                {"available": False, "build_dir": str(missing)},
            )

    def test_summary_includes_all_baseline_surfaces(self) -> None:
        summary = render_summary(
            {
                "topology_and_mutation": [
                    {
                        "geometry": "square",
                        "cell_count": 4,
                        "cold_build_median_ms": 1.25,
                        "single_toggle_ms": 2.5,
                        "single_toggle_bytes": 512,
                    }
                ],
                "comparison": {"median_ms": 3.0, "payload_bytes": 1024},
                "filmstrip": {"median_ms": 4.0, "payload_bytes": 2048},
                "bundle": {"available": True, "raw_bytes": 4096, "gzip_bytes": 1024},
            }
        )

        self.assertIn("square", summary)
        self.assertIn("toggle=", summary)
        self.assertIn("comparison", summary)
        self.assertIn("filmstrip", summary)
        self.assertIn("bundle", summary)


if __name__ == "__main__":
    unittest.main()
