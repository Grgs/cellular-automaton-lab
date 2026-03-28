import sys
import unittest
from pathlib import Path

try:
    from backend.payload_types import ServerMetaPayload
    from backend.dev_server import APP_NAME, ListeningProcess, prepare_dev_server
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.payload_types import ServerMetaPayload
    from backend.dev_server import APP_NAME, ListeningProcess, prepare_dev_server


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


if __name__ == "__main__":
    unittest.main()
