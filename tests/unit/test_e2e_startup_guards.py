import sys
import time
import unittest
from pathlib import Path
from unittest import mock


try:
    from tests.e2e.support_browser import BrowserAppTestCase
    from tests.e2e.support_server import JsonApiClient
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.e2e.support_browser import BrowserAppTestCase
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


if __name__ == "__main__":
    unittest.main()
