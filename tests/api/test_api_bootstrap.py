import sys
import unittest
from pathlib import Path

try:
    from tests.api.support import ApiTestCase
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.api.support import ApiTestCase


class ApiBootstrapTests(ApiTestCase):
    def test_bootstrap_endpoint_returns_shared_runtime_payload(self) -> None:
        response = self.client.get("/api/bootstrap")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["server_meta"]["app_name"], "cellular-automaton-lab")
        self.assertEqual(payload["snapshot_version"], 5)
        self.assertIn("app_defaults", payload)
        self.assertIn("topology_catalog", payload)
        self.assertIn("periodic_face_tilings", payload)
        self.assertIn("aperiodic_families", payload)
        self.assertTrue(
            any(entry["tiling_family"] == "square" for entry in payload["topology_catalog"])
        )
        self.assertTrue(all("render_kind" in entry for entry in payload["topology_catalog"]))
        self.assertTrue(
            any(
                entry["tiling_family"] == "penrose-p3-rhombs"
                for entry in payload["aperiodic_families"]
            )
        )
        self.assertTrue(any(entry["experimental"] for entry in payload["aperiodic_families"]))
        self.assertTrue(
            all("implementation_status" in entry for entry in payload["aperiodic_families"])
        )
        self.assertTrue(
            all("promotion_blocker" in entry for entry in payload["aperiodic_families"])
        )
        self.assertTrue(
            all("public_cell_kinds" in entry for entry in payload["aperiodic_families"])
        )


if __name__ == "__main__":
    unittest.main()
