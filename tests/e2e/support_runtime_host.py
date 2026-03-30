from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path

from playwright.sync_api import Page

from tests.e2e.support_server import AppServer, JsonApiClient


_STANDALONE_BUILD_LOCK = threading.Lock()
_STANDALONE_BUILD_READY = False
_STANDALONE_REQUIRED_OUTPUTS = (
    "index.html",
    "standalone-bootstrap.json",
    "standalone-python-manifest.json",
)


def _find_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(base_url: str, *, timeout_seconds: float = 20, process: subprocess.Popen[str] | None = None) -> None:
    deadline = time.time() + timeout_seconds
    while True:
        try:
            with urllib.request.urlopen(f"{base_url}/", timeout=1):
                return
        except Exception:
            if process is not None:
                exit_code = process.poll()
                if exit_code is not None:
                    raise RuntimeError(
                        f"Host exited before becoming ready (exit code {exit_code})."
                    )
            if time.time() > deadline:
                raise RuntimeError("Host did not start in time.")
            time.sleep(0.25)


class BrowserRuntimeHost(ABC):
    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parents[2]

    @property
    @abstractmethod
    def base_url(self) -> str:
        raise NotImplementedError

    def client(self) -> JsonApiClient | None:
        return None

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    def before_test(self) -> None:
        return None

    def restart(self) -> None:
        raise RuntimeError(f"{self.__class__.__name__} does not support restart().")

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def capture_failure_artifacts(self, artifact_dir: Path, page: Page | None) -> None:
        raise NotImplementedError


class ServerRuntimeHost(BrowserRuntimeHost):
    def __init__(self) -> None:
        super().__init__()
        self.server = AppServer()

    @property
    def base_url(self) -> str:
        return self.server.base_url

    def client(self) -> JsonApiClient:
        return self.server.client

    def start(self) -> None:
        self.server.start()

    def stop(self) -> None:
        self.server.stop()

    def before_test(self) -> None:
        self.server.close()
        self.server = AppServer()
        self.server.start()

    def restart(self) -> None:
        self.server.restart()

    def close(self) -> None:
        self.server.close()

    def capture_failure_artifacts(self, artifact_dir: Path, page: Page | None) -> None:
        del page
        try:
            backend_state = self.server.client.get_state()
            (artifact_dir / "backend-state.json").write_text(
                json.dumps(backend_state, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            (artifact_dir / "backend-state-error.txt").write_text(str(exc), encoding="utf-8")

        try:
            backend_topology = self.server.client.get_topology()
            (artifact_dir / "backend-topology.json").write_text(
                json.dumps(backend_topology, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            (artifact_dir / "backend-topology-error.txt").write_text(str(exc), encoding="utf-8")

        stdout_text = self.server.read_stdout()
        stderr_text = self.server.read_stderr()
        if stdout_text:
            (artifact_dir / "server-stdout.log").write_text(stdout_text, encoding="utf-8")
        if stderr_text:
            (artifact_dir / "server-stderr.log").write_text(stderr_text, encoding="utf-8")
        (artifact_dir / "server-log-paths.txt").write_text(
            f"stdout={self.server.stdout_path}\nstderr={self.server.stderr_path}\n",
            encoding="utf-8",
        )


def ensure_standalone_build(root: Path) -> None:
    global _STANDALONE_BUILD_READY
    if _STANDALONE_BUILD_READY:
        return
    with _STANDALONE_BUILD_LOCK:
        if _STANDALONE_BUILD_READY:
            return
        npm_executable = shutil.which("npm.cmd") or shutil.which("npm")
        if npm_executable is None:
            raise RuntimeError("npm is required to build the standalone frontend for browser tests.")
        subprocess.run(
            [npm_executable, "run", "build:frontend:standalone"],
            cwd=root,
            check=True,
            env=os.environ.copy(),
        )
        _STANDALONE_BUILD_READY = True


class StandaloneRuntimeHost(BrowserRuntimeHost):
    def __init__(self) -> None:
        super().__init__()
        self.output_dir = self.root / "output" / "standalone"
        self.process: subprocess.Popen[str] | None = None
        self.port = _find_available_port()
        self._base_url = f"http://127.0.0.1:{self.port}"
        self.log_dir = tempfile.TemporaryDirectory(prefix="cellular-automaton-standalone-logs-")
        self.stdout_path = Path(self.log_dir.name) / "standalone-stdout.log"
        self.stderr_path = Path(self.log_dir.name) / "standalone-stderr.log"
        self.stdout_handle = None
        self.stderr_handle = None

    @property
    def base_url(self) -> str:
        return self._base_url

    def _close_log_handles(self) -> None:
        if self.stdout_handle is not None:
            self.stdout_handle.close()
            self.stdout_handle = None
        if self.stderr_handle is not None:
            self.stderr_handle.close()
            self.stderr_handle = None

    def _ensure_required_output_files(self) -> None:
        missing_outputs = [
            relative_path
            for relative_path in _STANDALONE_REQUIRED_OUTPUTS
            if not (self.output_dir / relative_path).exists()
        ]
        if missing_outputs:
            formatted_outputs = "\n".join(
                f"- output/standalone/{relative_path}"
                for relative_path in missing_outputs
            )
            raise RuntimeError(
                "Standalone build is missing required packaging outputs before the static host can start.\n"
                f"{formatted_outputs}\n"
                "Run `npm run build:frontend:standalone` and verify the standalone packager completed successfully."
            )

    def _start_process(self) -> None:
        ensure_standalone_build(self.root)
        self._ensure_required_output_files()
        self.port = _find_available_port()
        self._base_url = f"http://127.0.0.1:{self.port}"
        self.stdout_handle = self.stdout_path.open("a", encoding="utf-8")
        self.stderr_handle = self.stderr_path.open("a", encoding="utf-8")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(self.port), "--bind", "127.0.0.1"],
            cwd=self.output_dir,
            stdout=self.stdout_handle,
            stderr=self.stderr_handle,
            text=True,
        )
        try:
            _wait_until_ready(self.base_url, process=self.process)
        except Exception as exc:
            stdout_tail = self.read_stdout().splitlines()[-20:]
            stderr_tail = self.read_stderr().splitlines()[-20:]
            details = [
                f"stdout_log={self.stdout_path}",
                f"stderr_log={self.stderr_path}",
            ]
            if stdout_tail:
                details.append("stdout_tail:\n" + "\n".join(stdout_tail))
            if stderr_tail:
                details.append("stderr_tail:\n" + "\n".join(stderr_tail))
            raise RuntimeError(
                "Standalone static host did not become ready for browser tests.\n" + "\n".join(details)
            ) from exc

    def start(self) -> None:
        if self.process and self.process.poll() is None:
            return
        self._start_process()

    def stop(self) -> None:
        if not self.process:
            self._close_log_handles()
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except Exception:
            self.process.kill()
            self.process.wait(timeout=5)
        self.process = None
        self._close_log_handles()

    def before_test(self) -> None:
        self.restart()

    def restart(self) -> None:
        self.stop()
        self._start_process()

    def close(self) -> None:
        self.stop()
        self.log_dir.cleanup()

    def read_stdout(self) -> str:
        if not self.stdout_path.exists():
            return ""
        return self.stdout_path.read_text(encoding="utf-8")

    def read_stderr(self) -> str:
        if not self.stderr_path.exists():
            return ""
        return self.stderr_path.read_text(encoding="utf-8")

    def capture_failure_artifacts(self, artifact_dir: Path, page: Page | None) -> None:
        if page is not None and not page.is_closed():
            try:
                storage = page.evaluate(
                    """async ({ databaseName, objectStoreName, snapshotKey, localStorageKey }) => {
                        const localStorageValue = window.localStorage.getItem(localStorageKey);
                        const indexedDbValue = await new Promise((resolve) => {
                            if (typeof window.indexedDB === "undefined") {
                                resolve(null);
                                return;
                            }
                            const openRequest = window.indexedDB.open(databaseName, 1);
                            openRequest.onerror = () => resolve({ error: String(openRequest.error) });
                            openRequest.onsuccess = () => {
                                const database = openRequest.result;
                                if (!database.objectStoreNames.contains(objectStoreName)) {
                                    resolve(null);
                                    return;
                                }
                                const transaction = database.transaction(objectStoreName, "readonly");
                                const store = transaction.objectStore(objectStoreName);
                                const getRequest = store.get(snapshotKey);
                                getRequest.onerror = () => resolve({ error: String(getRequest.error) });
                                getRequest.onsuccess = () => resolve(getRequest.result ?? null);
                            };
                        });
                        return {
                            localStorageValue,
                            indexedDbValue,
                            appReady: window.__appReady === true,
                        };
                    }""",
                    {
                        "databaseName": "cellular-automaton-lab-standalone",
                        "objectStoreName": "runtime",
                        "snapshotKey": "snapshot-v5",
                        "localStorageKey": "cellular-automaton-lab-standalone-state-v5",
                    },
                )
                (artifact_dir / "standalone-storage.json").write_text(
                    json.dumps(storage, indent=2),
                    encoding="utf-8",
                )
            except Exception as exc:
                (artifact_dir / "standalone-storage-error.txt").write_text(str(exc), encoding="utf-8")

        stdout_text = self.read_stdout()
        stderr_text = self.read_stderr()
        if stdout_text:
            (artifact_dir / "standalone-stdout.log").write_text(stdout_text, encoding="utf-8")
        if stderr_text:
            (artifact_dir / "standalone-stderr.log").write_text(stderr_text, encoding="utf-8")
        (artifact_dir / "standalone-log-paths.txt").write_text(
            f"stdout={self.stdout_path}\nstderr={self.stderr_path}\n",
            encoding="utf-8",
        )


def create_runtime_host(kind: str) -> BrowserRuntimeHost:
    if kind == "server":
        return ServerRuntimeHost()
    if kind == "standalone":
        return StandaloneRuntimeHost()
    raise ValueError(f"Unknown browser runtime host kind '{kind}'.")
