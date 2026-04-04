import sys
import unittest
from pathlib import Path
from types import TracebackType
from unittest import mock

try:
    from backend.payload_types import ServerMetaPayload
    from backend.dev_server import (
        APP_NAME,
        ListeningProcess,
        _windows_process_details,
        fetch_server_meta,
        prepare_dev_server,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.payload_types import ServerMetaPayload
    from backend.dev_server import (
        APP_NAME,
        ListeningProcess,
        _windows_process_details,
        fetch_server_meta,
        prepare_dev_server,
    )


class _FakeUrlResponse:
    def __init__(self, body: bytes, *, status: int = 200) -> None:
        self.body = body
        self.status = status

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
        return self.body


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


class DevServerGuardTests(unittest.TestCase):
    @staticmethod
    def app_meta(*_: object) -> ServerMetaPayload:
        return {"app_name": APP_NAME}

    def test_prepare_dev_server_returns_none_when_port_is_available(self) -> None:
        result = prepare_dev_server(
            host="127.0.0.1",
            port=5000,
            app_entrypoint=Path("app.py"),
            replace_existing=False,
            port_is_available_fn=lambda *_: True,
        )

        self.assertIsNone(result)

    def test_prepare_dev_server_raises_clear_error_when_port_is_busy(self) -> None:
        listener = ListeningProcess(pid=42, command_line="python app.py")

        with self.assertRaisesRegex(RuntimeError, r"Port 5000 is already in use by pid 42"):
            prepare_dev_server(
                host="127.0.0.1",
                port=5000,
                app_entrypoint=Path("app.py"),
                replace_existing=False,
                port_is_available_fn=lambda *_: False,
                find_listening_process_fn=lambda _: listener,
                fetch_server_meta_fn=self.app_meta,
            )

    def test_prepare_dev_server_replaces_recognized_listener_when_requested(self) -> None:
        listener = ListeningProcess(pid=99, command_line="python app.py")
        terminated: list[int] = []
        waited: list[tuple[str, int]] = []

        def record_wait(wait_host: str, wait_port: int) -> bool:
            waited.append((wait_host, wait_port))
            return True

        result = prepare_dev_server(
            host="127.0.0.1",
            port=5000,
            app_entrypoint=Path("app.py"),
            replace_existing=True,
            port_is_available_fn=lambda *_: False,
            find_listening_process_fn=lambda _: listener,
            fetch_server_meta_fn=self.app_meta,
            terminate_process_fn=terminated.append,
            wait_for_port_fn=record_wait,
        )

        self.assertEqual(result, listener)
        self.assertEqual(terminated, [99])
        self.assertEqual(waited, [("127.0.0.1", 5000)])

    def test_prepare_dev_server_refuses_to_replace_unrecognized_listener(self) -> None:
        listener = ListeningProcess(pid=77, command_line="node dev-server.js")

        with self.assertRaisesRegex(RuntimeError, r"Refusing to replace the listener on port 5000"):
            prepare_dev_server(
                host="127.0.0.1",
                port=5000,
                app_entrypoint=Path("app.py"),
                replace_existing=True,
                port_is_available_fn=lambda *_: False,
                find_listening_process_fn=lambda _: listener,
                fetch_server_meta_fn=lambda *_: None,
            )

    def test_fetch_server_meta_rejects_non_object_payloads(self) -> None:
        with mock.patch(
            "backend.dev_server.urlopen",
            return_value=_FakeUrlResponse(b"[]"),
        ):
            self.assertIsNone(fetch_server_meta("127.0.0.1", 5000))

        with mock.patch(
            "backend.dev_server.urlopen",
            return_value=_FakeUrlResponse(b'{"app_name": ""}'),
        ):
            self.assertIsNone(fetch_server_meta("127.0.0.1", 5000))

    def test_windows_process_details_ignores_invalid_payload_objects(self) -> None:
        with mock.patch(
            "backend.dev_server.subprocess.run",
            return_value=_FakeCompletedProcess(stdout="[]"),
        ):
            self.assertEqual(_windows_process_details(42), ListeningProcess(pid=42))


if __name__ == "__main__":
    unittest.main()
