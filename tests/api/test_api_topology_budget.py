from __future__ import annotations

from tests.api.support import ApiTestCase


class ApiTopologyBudgetTests(ApiTestCase):
    def test_reset_rejects_oversized_topology_without_mutating_session(self) -> None:
        before = self.get_state()
        payload = self.build_reset_payload(width=201, height=100)
        payload["topology_spec"]["unsafe_size_override"] = True

        response = self.client.post("/api/control/reset", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {
                "error": (
                    "Topology exceeds the interactive 20,000-cell limit "
                    "(estimated cell count: 20,100)."
                ),
                "code": "topology_cell_budget_exceeded",
                "limit": 20_000,
                "estimated_cells": 20_100,
            },
        )
        after = self.get_state()
        self.assertEqual(
            after["topology"]["topology_revision"], before["topology"]["topology_revision"]
        )
        self.assertEqual(after["cell_states"], before["cell_states"])
