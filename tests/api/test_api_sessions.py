import sys
import unittest
from pathlib import Path

from backend.payload_types import SimulationStatePayload

try:
    from tests.api.support import ApiTestCase
    from tests.typed_payloads import require_simulation_state_payload
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.api.support import ApiTestCase
    from tests.typed_payloads import require_simulation_state_payload


class ApiSessionTests(ApiTestCase):
    @staticmethod
    def session_path(session_id: str, path: str) -> str:
        return f"/api/sessions/{session_id}{path}"

    def session_state(self, session_id: str) -> SimulationStatePayload:
        response = self.client.get(self.session_path(session_id, "/state"))
        self.assertEqual(response.status_code, 200)
        return require_simulation_state_payload(
            response.get_json(),
            context=f"{session_id} state response",
        )

    def test_session_scoped_cell_state_is_isolated(self) -> None:
        first = "s-test-first"
        second = "s-test-second"

        first_toggle = self.client.post(
            self.session_path(first, "/cells/toggle"),
            json={"id": "c:1:1"},
        )
        second_toggle = self.client.post(
            self.session_path(second, "/cells/toggle"),
            json={"id": "c:2:2"},
        )

        self.assertEqual(first_toggle.status_code, 200)
        self.assertEqual(second_toggle.status_code, 200)

        first_state = self.session_state(first)
        second_state = self.session_state(second)

        self.assertEqual(self.regular_cell_state(first_state, 1, 1), 1)
        self.assertEqual(self.regular_cell_state(first_state, 2, 2), 0)
        self.assertEqual(self.regular_cell_state(second_state, 1, 1), 0)
        self.assertEqual(self.regular_cell_state(second_state, 2, 2), 1)

    def test_session_state_persists_independently(self) -> None:
        first = "s-persist-first"
        second = "s-persist-second"

        self.client.post(self.session_path(first, "/cells/toggle"), json={"id": "c:1:1"})
        self.client.post(self.session_path(second, "/cells/toggle"), json={"id": "c:2:2"})

        self.recreate_app()

        first_state = self.session_state(first)
        second_state = self.session_state(second)

        self.assertEqual(self.regular_cell_state(first_state, 1, 1), 1)
        self.assertEqual(self.regular_cell_state(first_state, 2, 2), 0)
        self.assertEqual(self.regular_cell_state(second_state, 1, 1), 0)
        self.assertEqual(self.regular_cell_state(second_state, 2, 2), 1)

    def test_invalid_session_id_returns_400(self) -> None:
        response = self.client.get("/api/sessions/bad.id/state")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Session id", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
