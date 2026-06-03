import sys
import unittest
from pathlib import Path

try:
    from tests.api.support import ApiTestCase
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.api.support import ApiTestCase


class ApiTopologyPreviewTests(ApiTestCase):
    def test_preview_returns_cells_with_geometry(self) -> None:
        response = self.client.post(
            "/api/topology/preview",
            json={"geometry": "hex", "width": 6, "height": 6},
        )
        self.assertEqual(response.status_code, 200)
        preview = response.get_json()["topology_preview"]
        self.assertIn("topology_revision", preview)
        self.assertGreater(len(preview["cells"]), 0)
        cell = preview["cells"][0]
        self.assertIn("id", cell)
        self.assertIn("center", cell)
        # Geometry is enriched server-side even for regular grids.
        self.assertGreaterEqual(len(cell["vertices"]), 3)
        self.assertIn("x", cell["vertices"][0])

    def test_preview_supports_aperiodic_patch(self) -> None:
        response = self.client.post(
            "/api/topology/preview",
            json={"geometry": "sphinx", "patch_depth": 2},
        )
        self.assertEqual(response.status_code, 200)
        cells = response.get_json()["topology_preview"]["cells"]
        self.assertTrue(all(len(cell["vertices"]) >= 3 for cell in cells))

    def test_preview_does_not_disturb_running_state(self) -> None:
        before = self.get_state()["generation"]
        self.client.post(
            "/api/topology/preview", json={"geometry": "square", "width": 5, "height": 5}
        )
        self.assertEqual(self.get_state()["generation"], before)

    def test_preview_rejects_unknown_geometry(self) -> None:
        response = self.client.post("/api/topology/preview", json={"geometry": "not-a-tiling"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_preview_rejects_oversized_topology(self) -> None:
        response = self.client.post(
            "/api/topology/preview",
            json={"geometry": "floret-pentagonal", "width": 40, "height": 40},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("preview limit", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
