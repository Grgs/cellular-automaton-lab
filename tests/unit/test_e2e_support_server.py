import sys
import unittest
from pathlib import Path
from types import TracebackType
from unittest import mock

try:
    from tests.e2e.support_server import JsonApiClient
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.support_server import JsonApiClient


class _FakeUrlResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "_FakeUrlResponse":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class JsonApiClientTests(unittest.TestCase):
    def test_request_json_returns_none_for_empty_payloads(self) -> None:
        client = JsonApiClient("http://127.0.0.1:5000")
        with mock.patch(
            "tests.e2e.support_server.urllib.request.urlopen",
            return_value=_FakeUrlResponse(b""),
        ):
            self.assertIsNone(client.request_json("/api/state"))

    def test_get_state_rejects_non_object_json_payloads(self) -> None:
        client = JsonApiClient("http://127.0.0.1:5000")
        with mock.patch(
            "tests.e2e.support_server.urllib.request.urlopen",
            return_value=_FakeUrlResponse(b"[]"),
        ):
            with self.assertRaisesRegex(AssertionError, "JSON object"):
                client.get_state()


if __name__ == "__main__":
    unittest.main()
