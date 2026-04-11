import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


try:
    from tests.e2e.support_browser import BrowserAppTestCase
    from tests.e2e.support_runtime_host import StandaloneRuntimeHost
    from tests.e2e.support_server import JsonApiClient
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.support_browser import BrowserAppTestCase
    from tests.e2e.support_runtime_host import StandaloneRuntimeHost
    from tests.e2e.support_server import JsonApiClient


class DummyProcess:
    def __init__(self, exit_code: int | None) -> None:
        self._exit_code = exit_code

    def poll(self) -> int | None:
        return self._exit_code


class StartupGuardTests(unittest.TestCase):
    def test_startup_watchdog_raises_assertion_for_hung_startup(self) -> None:
        with self.assertRaisesRegex(AssertionError, "Synthetic startup did not start within"):
            with BrowserAppTestCase._startup_watchdog("Synthetic startup", timeout_seconds=0.01):
                time.sleep(0.05)

    def test_wait_until_ready_fails_fast_when_process_exits(self) -> None:
        client = JsonApiClient("http://127.0.0.1:9")
        with mock.patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            with self.assertRaisesRegex(RuntimeError, "exit code 7"):
                client.wait_until_ready(
                    timeout_seconds=0.05,
                    process=DummyProcess(7),
                )

    def test_standalone_runtime_requires_prebuilt_outputs(self) -> None:
        host = StandaloneRuntimeHost()
        with tempfile.TemporaryDirectory() as tmpdir:
            host.output_dir = Path(tmpdir)
            with self.assertRaisesRegex(
                RuntimeError,
                "Direct Python standalone browser suites now expect prebuilt standalone outputs",
            ):
                host._ensure_required_output_files()
        host.close()

    def test_standalone_runtime_does_not_auto_build_missing_outputs(self) -> None:
        host = StandaloneRuntimeHost()
        with tempfile.TemporaryDirectory() as tmpdir:
            host.output_dir = Path(tmpdir)
            with mock.patch("subprocess.run") as build_run:
                with mock.patch("subprocess.Popen") as host_process:
                    with self.assertRaisesRegex(RuntimeError, "Preferred local path"):
                        host.start()
        build_run.assert_not_called()
        host_process.assert_not_called()
        host.close()


if __name__ == "__main__":
    unittest.main()
