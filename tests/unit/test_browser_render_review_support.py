from __future__ import annotations

import unittest

from tools.render_review.browser_support.render_review import (
    boundary_dominance,
    edge_density,
    gutter_score,
    normalize_readiness_snapshot,
    occupied_bounds_from_mask,
    readiness_blockers,
    readiness_tuple,
    visible_aspect_ratio,
    wait_for_patch_render_complete,
)


class _FakePage:
    def __init__(self, readiness_snapshots: list[object]) -> None:
        self._snapshots = list(readiness_snapshots)
        self.raf_calls = 0

    def evaluate(self, script: str) -> object:
        if "snapshot.readiness" in script:
            if self._snapshots:
                return self._snapshots.pop(0)
            return None
        if "requestAnimationFrame" in script:
            self.raf_calls += 1
            return None
        raise AssertionError(f"unexpected evaluate call: {script[:80]!r}")


class BrowserRenderReviewSupportTests(unittest.TestCase):
    def test_occupied_bounds_and_visible_aspect_ratio(self) -> None:
        occupied_mask = [
            False, False, False, False, False,
            False, True, True, True, False,
            False, True, True, True, False,
            False, False, False, False, False,
        ]
        bounds = occupied_bounds_from_mask(occupied_mask, width=5, height=4)
        self.assertEqual(
            bounds,
            {
                "minX": 1,
                "maxX": 3,
                "minY": 1,
                "maxY": 2,
                "width": 3,
                "height": 2,
            },
        )
        self.assertEqual(visible_aspect_ratio(bounds), 1.5)

    def test_edge_density_and_boundary_dominance(self) -> None:
        occupied_mask = [
            False, False, False, False, False,
            False, True, True, True, False,
            False, True, True, True, False,
            False, True, True, True, False,
            False, False, False, False, False,
        ]
        bounds = occupied_bounds_from_mask(occupied_mask, width=5, height=5)
        self.assertEqual(edge_density(occupied_mask, width=5, height=5), 8 / 9)
        self.assertEqual(
            boundary_dominance(occupied_mask, bounds, width=5, height=5),
            8 / 9,
        )

    def test_gutter_score_finds_enclosed_transparent_pixels(self) -> None:
        occupied_mask = [
            False, False, False, False, False,
            False, True, True, True, False,
            False, True, False, True, False,
            False, True, True, True, False,
            False, False, False, False, False,
        ]
        bounds = occupied_bounds_from_mask(occupied_mask, width=5, height=5)
        self.assertEqual(gutter_score(occupied_mask, bounds, width=5, height=5), 1 / 9)

    def test_normalize_readiness_snapshot_coerces_diagnostics_values(self) -> None:
        snapshot = normalize_readiness_snapshot(
            {
                "appReady": True,
                "blockingActivityVisible": False,
                "blockingActivityKind": "",
                "blockingActivityMessage": "",
                "blockingActivityDetail": "",
                "blockingActivityStartedAt": "123",
                "topologyRevision": "rev-1",
                "topologyCellCount": "443",
                "patchDepth": "3",
                "renderCellSize": "12.5",
                "gridSizeText": "Depth 3 • 443 tiles",
                "generationText": "0",
                "statusText": "Paused",
            }
        )
        assert snapshot is not None
        self.assertEqual(snapshot["topologyCellCount"], 443)
        self.assertEqual(snapshot["patchDepth"], 3)
        self.assertEqual(snapshot["renderCellSize"], 12.5)
        self.assertEqual(snapshot["blockingActivityStartedAt"], 123)
        self.assertEqual(
            readiness_tuple(snapshot),
            ("rev-1", 443, 3, 12.5, "Depth 3 • 443 tiles", "0", "Paused", False, None, ""),
        )

    def test_readiness_blockers_flag_active_blocking_activity(self) -> None:
        blockers = readiness_blockers(
            {
                "appReady": True,
                "blockingActivityVisible": True,
                "blockingActivityKind": "build-tiling",
                "blockingActivityMessage": "Building tiling...",
                "blockingActivityDetail": "",
                "blockingActivityStartedAt": 1,
                "topologyRevision": "rev-1",
                "topologyCellCount": 443,
                "patchDepth": 3,
                "renderCellSize": 12.5,
                "gridSizeText": "Depth 3 • 443 tiles",
                "generationText": "0",
                "statusText": "Building tiling...",
            }
        )
        self.assertIn("Blocking activity was still visible.", blockers)
        self.assertIn("Blocking activity kind was still set: build-tiling.", blockers)

    def test_readiness_blockers_flag_placeholder_grid_summary(self) -> None:
        blockers = readiness_blockers(
            {
                "appReady": True,
                "blockingActivityVisible": False,
                "blockingActivityKind": None,
                "blockingActivityMessage": "",
                "blockingActivityDetail": "",
                "blockingActivityStartedAt": None,
                "topologyRevision": "rev-1",
                "topologyCellCount": 443,
                "patchDepth": 3,
                "renderCellSize": 12.5,
                "gridSizeText": "-- x --",
                "generationText": "0",
                "statusText": "Paused",
            }
        )
        self.assertIn("Grid summary was still missing or placeholder.", blockers)

    def test_readiness_blockers_flag_missing_topology_revision(self) -> None:
        blockers = readiness_blockers(
            {
                "appReady": True,
                "blockingActivityVisible": False,
                "blockingActivityKind": None,
                "blockingActivityMessage": "",
                "blockingActivityDetail": "",
                "blockingActivityStartedAt": None,
                "topologyRevision": None,
                "topologyCellCount": 443,
                "patchDepth": 3,
                "renderCellSize": 12.5,
                "gridSizeText": "Depth 3 • 443 tiles",
                "generationText": "0",
                "statusText": "Paused",
            }
        )
        self.assertIn("Topology revision was missing.", blockers)

    def test_wait_for_patch_render_complete_accepts_stable_snapshot(self) -> None:
        stable_snapshot = {
            "appReady": True,
            "blockingActivityVisible": False,
            "blockingActivityKind": None,
            "blockingActivityMessage": "",
            "blockingActivityDetail": "",
            "blockingActivityStartedAt": None,
            "topologyRevision": "rev-1",
            "topologyCellCount": 443,
            "patchDepth": 3,
            "renderCellSize": 12.5,
            "gridSizeText": "Depth 3 • 443 tiles",
            "generationText": "0",
            "statusText": "Paused",
        }
        page = _FakePage([stable_snapshot, stable_snapshot, stable_snapshot])
        diagnostics = wait_for_patch_render_complete(
            page,
            timeout_ms=50,
            stable_poll_count=3,
            stable_poll_interval_ms=1,
        )
        self.assertTrue(diagnostics["settled"])
        self.assertEqual(diagnostics["finalSnapshot"], stable_snapshot)
        self.assertEqual(page.raf_calls, 1)

    def test_wait_for_patch_render_complete_rejects_changing_tuple(self) -> None:
        page = _FakePage(
            [
                {
                    "appReady": True,
                    "blockingActivityVisible": False,
                    "blockingActivityKind": None,
                    "blockingActivityMessage": "",
                    "blockingActivityDetail": "",
                    "blockingActivityStartedAt": None,
                    "topologyRevision": "rev-1",
                    "topologyCellCount": 443,
                    "patchDepth": 3,
                    "renderCellSize": 12.5,
                    "gridSizeText": "Depth 3 • 440 tiles",
                    "generationText": "0",
                    "statusText": "Paused",
                },
                {
                    "appReady": True,
                    "blockingActivityVisible": False,
                    "blockingActivityKind": None,
                    "blockingActivityMessage": "",
                    "blockingActivityDetail": "",
                    "blockingActivityStartedAt": None,
                    "topologyRevision": "rev-1",
                    "topologyCellCount": 443,
                    "patchDepth": 3,
                    "renderCellSize": 12.5,
                    "gridSizeText": "Depth 3 • 441 tiles",
                    "generationText": "0",
                    "statusText": "Paused",
                },
                {
                    "appReady": True,
                    "blockingActivityVisible": False,
                    "blockingActivityKind": None,
                    "blockingActivityMessage": "",
                    "blockingActivityDetail": "",
                    "blockingActivityStartedAt": None,
                    "topologyRevision": "rev-1",
                    "topologyCellCount": 443,
                    "patchDepth": 3,
                    "renderCellSize": 12.5,
                    "gridSizeText": "Depth 3 • 442 tiles",
                    "generationText": "0",
                    "statusText": "Paused",
                },
            ]
        )
        with self.assertRaisesRegex(AssertionError, "Render did not settle within"):
            wait_for_patch_render_complete(
                page,
                timeout_ms=10,
                stable_poll_count=3,
                stable_poll_interval_ms=1,
            )
