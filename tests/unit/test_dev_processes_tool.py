from __future__ import annotations

import io
import socket
import subprocess
import sys
import time
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tools import dev_processes
from tools.dev_processes import (
    RepoProcess,
    classify_repo_process,
    cleanup_main,
    main,
    select_processes,
)


def _find_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class DevProcessesToolTests(unittest.TestCase):
    def test_classify_repo_process_matches_standalone_http_server(self) -> None:
        process = classify_repo_process(
            pid=123,
            cwd=dev_processes.STANDALONE_OUTPUT_DIR,
            argv=("python", "-m", "http.server", "8123", "--bind", "127.0.0.1"),
            environ={},
        )
        self.assertIsNotNone(process)
        assert process is not None
        self.assertEqual(process.kind, "standalone-host")
        self.assertEqual(process.port, 8123)

    def test_classify_repo_process_matches_repo_app_server(self) -> None:
        process = classify_repo_process(
            pid=456,
            cwd=dev_processes.ROOT_DIR,
            argv=("python", "app.py"),
            environ={},
        )
        self.assertIsNotNone(process)
        assert process is not None
        self.assertEqual(process.kind, "server-host")
        self.assertEqual(process.port, 5000)

    def test_classify_repo_process_prefers_listening_port(self) -> None:
        process = classify_repo_process(
            pid=456,
            cwd=dev_processes.ROOT_DIR,
            argv=("python", "app.py"),
            environ={"PORT": "5000"},
            listening_ports_by_pid={456: (5017,)},
        )
        self.assertIsNotNone(process)
        assert process is not None
        self.assertEqual(process.kind, "server-host")
        self.assertEqual(process.port, 5017)

    def test_classify_repo_process_matches_helper_tools(self) -> None:
        runner = classify_repo_process(
            pid=1,
            cwd=dev_processes.ROOT_DIR,
            argv=("python", "-m", "tools", "browser", "check", "--host", "standalone"),
            environ={},
        )
        review = classify_repo_process(
            pid=2,
            cwd=dev_processes.ROOT_DIR,
            argv=("python", "-m", "tools", "browser", "review", "--profile", "pinwheel-depth-3"),
            environ={},
        )
        self.assertEqual(runner.kind if runner else None, "managed-browser-check")
        self.assertEqual(review.kind if review else None, "render-review")

    def test_select_processes_filters_by_port_and_scope(self) -> None:
        processes = (
            RepoProcess(1, "server-host", "python app.py", dev_processes.ROOT_DIR, 5000),
            RepoProcess(
                2,
                "standalone-host",
                "python -m http.server 8123",
                dev_processes.STANDALONE_OUTPUT_DIR,
                8123,
            ),
            RepoProcess(
                3,
                "managed-browser-check",
                "python -m tools browser check",
                dev_processes.ROOT_DIR,
                None,
            ),
        )
        self.assertEqual(select_processes(processes, port=8123), (processes[1],))
        self.assertEqual(select_processes(processes, repo=True), processes)
        self.assertEqual(select_processes(processes, stale_browser_hosts=True), processes[:2])

    def test_main_list_prints_processes(self) -> None:
        processes = (RepoProcess(10, "server-host", "python app.py", dev_processes.ROOT_DIR, 5000),)
        stdout = io.StringIO()
        with patch("tools.dev_processes.iter_repo_processes", side_effect=(processes, ())):
            with redirect_stdout(stdout):
                exit_code = main(["list"])
        self.assertEqual(exit_code, 0)
        self.assertIn("pid=10 kind=server-host port=5000", stdout.getvalue())

    def test_main_kill_by_port_calls_terminate_process(self) -> None:
        processes = (
            RepoProcess(10, "server-host", "python app.py", dev_processes.ROOT_DIR, 5000),
            RepoProcess(
                11,
                "standalone-host",
                "python -m http.server 8123",
                dev_processes.STANDALONE_OUTPUT_DIR,
                8123,
            ),
        )
        stdout = io.StringIO()
        with patch("tools.dev_processes.iter_repo_processes", side_effect=(processes, ())):
            with patch(
                "tools.dev_processes.terminate_process", return_value="terminated"
            ) as terminate:
                with redirect_stdout(stdout):
                    exit_code = main(["kill", "--port", "8123"])
        self.assertEqual(exit_code, 0)
        terminate.assert_called_once_with(processes[1], grace_seconds=2.0)
        self.assertIn("Killing the following repo-scoped processes:", stdout.getvalue())

    def test_cleanup_defaults_to_stale_browser_hosts(self) -> None:
        processes = (
            RepoProcess(10, "server-host", "python app.py", dev_processes.ROOT_DIR, 5000),
            RepoProcess(
                11,
                "managed-browser-check",
                "python -m tools browser check",
                dev_processes.ROOT_DIR,
                None,
            ),
        )
        stdout = io.StringIO()
        with patch("tools.dev_processes.iter_repo_processes", side_effect=(processes, ())):
            with patch(
                "tools.dev_processes.terminate_process", return_value="terminated"
            ) as terminate:
                with redirect_stdout(stdout):
                    exit_code = cleanup_main([])
        self.assertEqual(exit_code, 0)
        terminate.assert_called_once_with(processes[0], grace_seconds=2.0)
        self.assertIn("pid=10 kind=server-host port=5000", stdout.getvalue())

    def test_windows_payload_discovers_repo_app_by_listening_port(self) -> None:
        payload = {
            "processes": [
                {
                    "ProcessId": 456,
                    "ParentProcessId": 100,
                    "CommandLine": r"py -3 .\app.py",
                },
                {
                    "ProcessId": 789,
                    "ParentProcessId": 100,
                    "CommandLine": r"python -m http.server 8000",
                },
            ],
            "listeners": [
                {
                    "OwningProcess": 456,
                    "LocalPort": 5000,
                }
            ],
        }
        processes = dev_processes.repo_processes_from_windows_payload(payload)
        self.assertEqual(
            processes,
            (RepoProcess(456, "server-host", r"py -3 .\app.py", dev_processes.ROOT_DIR, 5000),),
        )

    def test_windows_payload_includes_repo_app_parent_for_reloader_cleanup(self) -> None:
        payload = {
            "processes": [
                {
                    "ProcessId": 100,
                    "ParentProcessId": 50,
                    "CommandLine": r"py -3 .\app.py",
                },
                {
                    "ProcessId": 456,
                    "ParentProcessId": 100,
                    "CommandLine": r"C:\Python\python.exe .\app.py",
                },
            ],
            "listeners": [
                {
                    "OwningProcess": 456,
                    "LocalPort": 5000,
                }
            ],
        }
        processes = dev_processes.repo_processes_from_windows_payload(payload)
        self.assertEqual(
            processes,
            (
                RepoProcess(100, "server-host", r"py -3 .\app.py", dev_processes.ROOT_DIR, 5000),
                RepoProcess(
                    456,
                    "server-host",
                    r"C:\Python\python.exe .\app.py",
                    dev_processes.ROOT_DIR,
                    5000,
                ),
            ),
        )

    @unittest.skipUnless(
        dev_processes.STANDALONE_OUTPUT_DIR.is_dir() and dev_processes.PROC_DIR.is_dir(),
        "standalone output directory and procfs-backed environment are required",
    )
    def test_main_kill_by_port_terminates_standalone_http_server_process(self) -> None:
        port = _find_available_port()
        process = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
            cwd=dev_processes.STANDALONE_OUTPUT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if any(candidate.port == port for candidate in dev_processes.iter_repo_processes()):
                    break
                time.sleep(0.1)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["kill", "--port", str(port)])
            self.assertEqual(exit_code, 0)
            process.wait(timeout=5)
            rendered = stdout.getvalue()
            self.assertIn(f"port={port}", rendered)
            self.assertRegex(rendered, r"pid=\d+ result=(terminated|killed)")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
