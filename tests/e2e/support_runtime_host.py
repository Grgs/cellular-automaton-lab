from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Any, TextIO

from playwright.sync_api import Page

from tests.e2e.support_server import AppServer, JsonApiClient

_EXTERNAL_RUNTIME_HOST_KIND_ENV = "E2E_EXTERNAL_RUNTIME_HOST_KIND"
_EXTERNAL_RUNTIME_BASE_URL_ENV = "E2E_EXTERNAL_RUNTIME_BASE_URL"
_EXTERNAL_RUNTIME_STDOUT_PATH_ENV = "E2E_EXTERNAL_RUNTIME_STDOUT_PATH"
_EXTERNAL_RUNTIME_STDERR_PATH_ENV = "E2E_EXTERNAL_RUNTIME_STDERR_PATH"

_STANDALONE_REQUIRED_OUTPUTS = (
    "index.html",
    "standalone-bootstrap.json",
    "standalone-python-bundle.json",
)
_STANDALONE_BUILD_MANIFEST_NAME = "build-manifest.json"
_SOURCE_FINGERPRINT_DIRS = ("frontend",)
_SOURCE_FINGERPRINT_FILES = (
    "tools/build-standalone.mjs",
    "package.json",
    "package-lock.json",
)


def _run_git_output(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _iter_source_fingerprint_paths(root: Path) -> tuple[str, ...]:
    relative_paths: list[str] = []
    for relative_dir in _SOURCE_FINGERPRINT_DIRS:
        absolute_dir = root / relative_dir
        if not absolute_dir.exists():
            continue
        for absolute_path in sorted(path for path in absolute_dir.rglob("*") if path.is_file()):
            relative_paths.append(absolute_path.relative_to(root).as_posix())
    for relative_file in _SOURCE_FINGERPRINT_FILES:
        absolute_file = root / relative_file
        if absolute_file.exists():
            relative_paths.append(absolute_file.relative_to(root).as_posix())
    return tuple(sorted(dict.fromkeys(relative_paths)))


def compute_source_fingerprint(root: Path) -> tuple[str, tuple[str, ...]]:
    hash_object = hashlib.sha256()
    relative_paths = _iter_source_fingerprint_paths(root)
    for relative_path in relative_paths:
        absolute_path = root / relative_path
        hash_object.update(relative_path.encode("utf-8"))
        hash_object.update(b"\0")
        hash_object.update(absolute_path.read_bytes())
        hash_object.update(b"\0")
    return hash_object.hexdigest(), relative_paths


@lru_cache(maxsize=4)
def current_repo_provenance(root_path: str) -> dict[str, Any]:
    root = Path(root_path)
    source_fingerprint, source_files = compute_source_fingerprint(root)
    git_head = _run_git_output(root, "rev-parse", "HEAD")
    git_status = _run_git_output(root, "status", "--porcelain")
    git_dirty = None if git_status is None else bool(git_status)
    return {
        "gitHead": git_head,
        "gitDirty": git_dirty,
        "sourceFingerprint": source_fingerprint,
        "sourceFileCount": len(source_files),
    }


def load_standalone_build_manifest(output_dir: Path) -> dict[str, Any] | None:
    manifest_path = output_dir / _STANDALONE_BUILD_MANIFEST_NAME
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_files = payload.get("sourceFiles")
    return {
        "manifestPath": str(manifest_path),
        "builtAt": payload.get("builtAt"),
        "gitHead": payload.get("gitHead"),
        "gitDirty": payload.get("gitDirty"),
        "sourceFingerprint": payload.get("sourceFingerprint"),
        "sourceFileCount": len(source_files) if isinstance(source_files, list) else None,
    }


def build_runtime_provenance_report(
    *,
    host_kind: str,
    current_repo: dict[str, Any],
    standalone_build: dict[str, Any] | None,
) -> dict[str, Any]:
    warnings: list[str] = []
    current_git_head = current_repo.get("gitHead")
    current_source_fingerprint = current_repo.get("sourceFingerprint")
    if current_git_head is None:
        warnings.append("Current checkout git HEAD is unavailable.")
    if current_repo.get("gitDirty") is None:
        warnings.append("Current checkout dirty-state provenance is unavailable.")

    comparison: dict[str, bool | None] = {
        "gitHeadMatches": None,
        "fingerprintMatches": None,
    }
    if host_kind == "standalone":
        if standalone_build is None:
            warnings.append("Standalone build manifest is missing.")
        else:
            standalone_git_head = standalone_build.get("gitHead")
            standalone_source_fingerprint = standalone_build.get("sourceFingerprint")
            if standalone_build.get("gitDirty") is True:
                warnings.append("Standalone bundle was built from a dirty checkout.")
            if standalone_git_head is None:
                warnings.append("Standalone build git HEAD is unavailable.")
            if standalone_source_fingerprint is None:
                warnings.append("Standalone build source fingerprint is unavailable.")
            if current_git_head is not None and standalone_git_head is not None:
                comparison["gitHeadMatches"] = current_git_head == standalone_git_head
                if comparison["gitHeadMatches"] is False:
                    warnings.append(
                        f"Standalone build git HEAD {standalone_git_head} does not match current checkout HEAD {current_git_head}."
                    )
            if current_source_fingerprint is not None and standalone_source_fingerprint is not None:
                comparison["fingerprintMatches"] = current_source_fingerprint == standalone_source_fingerprint
                if comparison["fingerprintMatches"] is False:
                    warnings.append("Standalone build source fingerprint does not match the current checkout.")

    return {
        "hostKind": host_kind,
        "currentRepo": current_repo,
        "standaloneBuild": standalone_build,
        "comparison": comparison,
        "warnings": warnings,
    }


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


def _standalone_output_dir(root: Path) -> Path:
    return root / "output" / "standalone"


def missing_standalone_output_files(output_dir: Path) -> list[str]:
    return [
        relative_path
        for relative_path in _STANDALONE_REQUIRED_OUTPUTS
        if not (output_dir / relative_path).exists()
    ]


def standalone_build_status(root: Path) -> dict[str, Any]:
    output_dir = _standalone_output_dir(root)
    missing_outputs = missing_standalone_output_files(output_dir)
    standalone_build = load_standalone_build_manifest(output_dir)
    current_repo = current_repo_provenance(str(root))
    provenance = build_runtime_provenance_report(
        host_kind="standalone",
        current_repo=current_repo,
        standalone_build=standalone_build,
    )
    fingerprint_matches = provenance["comparison"].get("fingerprintMatches")
    build_current = (
        len(missing_outputs) == 0
        and standalone_build is not None
        and fingerprint_matches is True
    )
    if missing_outputs:
        reason = "required outputs are missing"
    elif standalone_build is None:
        reason = "build manifest is missing"
    elif fingerprint_matches is False:
        reason = "source fingerprint differs from current checkout"
    elif fingerprint_matches is None:
        reason = "build provenance is incomplete"
    else:
        reason = "standalone build outputs are current"
    return {
        "outputDir": str(output_dir),
        "requiredOutputsPresent": len(missing_outputs) == 0,
        "missingOutputs": missing_outputs,
        "manifestPresent": standalone_build is not None,
        "buildCurrent": build_current,
        "reason": reason,
        "recommendedBuildCommand": "npm run build:frontend:standalone",
        "preferredStandaloneCommand": "npm run test:e2e:playwright:standalone",
        "runtimeProvenance": provenance,
    }


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
    def runtime_provenance(self) -> dict[str, Any]:
        raise NotImplementedError

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

    def runtime_provenance(self) -> dict[str, Any]:
        return build_runtime_provenance_report(
            host_kind="server",
            current_repo=current_repo_provenance(str(self.root)),
            standalone_build=None,
        )

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
        self.stdout_handle: TextIO | None = None
        self.stderr_handle: TextIO | None = None

    @property
    def base_url(self) -> str:
        return self._base_url

    def runtime_provenance(self) -> dict[str, Any]:
        return build_runtime_provenance_report(
            host_kind="standalone",
            current_repo=current_repo_provenance(str(self.root)),
            standalone_build=load_standalone_build_manifest(self.output_dir),
        )

    def _close_log_handles(self) -> None:
        if self.stdout_handle is not None:
            self.stdout_handle.close()
            self.stdout_handle = None
        if self.stderr_handle is not None:
            self.stderr_handle.close()
            self.stderr_handle = None

    def _ensure_required_output_files(self) -> None:
        missing_outputs = missing_standalone_output_files(self.output_dir)
        if missing_outputs:
            formatted_outputs = "\n".join(
                f"- output/standalone/{relative_path}"
                for relative_path in missing_outputs
            )
            raise RuntimeError(
                "Standalone build outputs are missing before the static host can start.\n"
                f"{formatted_outputs}\n"
                "Direct Python standalone browser suites now expect prebuilt standalone outputs.\n"
                "Preferred local path: `npm run test:e2e:playwright:standalone`\n"
                "Build only: `npm run build:frontend:standalone`"
            )

    def _start_process(self) -> None:
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


class ExternalRuntimeHost(BrowserRuntimeHost):
    def __init__(
        self,
        *,
        kind: str,
        base_url: str,
        stdout_path: str | None = None,
        stderr_path: str | None = None,
    ) -> None:
        super().__init__()
        self.kind = kind
        self._base_url = base_url.rstrip("/")
        self.stdout_path = Path(stdout_path) if stdout_path else None
        self.stderr_path = Path(stderr_path) if stderr_path else None

    @property
    def base_url(self) -> str:
        return self._base_url

    def runtime_provenance(self) -> dict[str, Any]:
        return build_runtime_provenance_report(
            host_kind="standalone",
            current_repo=current_repo_provenance(str(self.root)),
            standalone_build=load_standalone_build_manifest(self.output_dir),
        )

    def client(self) -> JsonApiClient | None:
        if self.kind == "server":
            return JsonApiClient(self.base_url)
        return None

    def runtime_provenance(self) -> dict[str, Any]:
        return build_runtime_provenance_report(
            host_kind=self.kind,
            current_repo=current_repo_provenance(str(self.root)),
            standalone_build=(
                load_standalone_build_manifest(_standalone_output_dir(self.root))
                if self.kind == "standalone"
                else None
            ),
        )

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def before_test(self) -> None:
        return None

    def close(self) -> None:
        return None

    def _copy_log_file(self, artifact_dir: Path, source: Path | None, target_name: str) -> None:
        if source is None or not source.exists():
            return
        shutil.copyfile(source, artifact_dir / target_name)

    def capture_failure_artifacts(self, artifact_dir: Path, page: Page | None) -> None:
        if self.kind == "server":
            client = JsonApiClient(self.base_url)
            try:
                backend_state = client.get_state()
                (artifact_dir / "backend-state.json").write_text(
                    json.dumps(backend_state, indent=2),
                    encoding="utf-8",
                )
            except Exception as exc:
                (artifact_dir / "backend-state-error.txt").write_text(str(exc), encoding="utf-8")
            try:
                backend_topology = client.get_topology()
                (artifact_dir / "backend-topology.json").write_text(
                    json.dumps(backend_topology, indent=2),
                    encoding="utf-8",
                )
            except Exception as exc:
                (artifact_dir / "backend-topology-error.txt").write_text(str(exc), encoding="utf-8")
            self._copy_log_file(artifact_dir, self.stdout_path, "server-stdout.log")
            self._copy_log_file(artifact_dir, self.stderr_path, "server-stderr.log")
            (artifact_dir / "server-log-paths.txt").write_text(
                f"stdout={self.stdout_path}\nstderr={self.stderr_path}\n",
                encoding="utf-8",
            )
            return

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
        self._copy_log_file(artifact_dir, self.stdout_path, "standalone-stdout.log")
        self._copy_log_file(artifact_dir, self.stderr_path, "standalone-stderr.log")
        (artifact_dir / "standalone-log-paths.txt").write_text(
            f"stdout={self.stdout_path}\nstderr={self.stderr_path}\n",
            encoding="utf-8",
        )


def create_runtime_host(kind: str) -> BrowserRuntimeHost:
    external_kind = os.environ.get(_EXTERNAL_RUNTIME_HOST_KIND_ENV)
    external_base_url = os.environ.get(_EXTERNAL_RUNTIME_BASE_URL_ENV)
    if external_kind == kind and external_base_url:
        return ExternalRuntimeHost(
            kind=kind,
            base_url=external_base_url,
            stdout_path=os.environ.get(_EXTERNAL_RUNTIME_STDOUT_PATH_ENV),
            stderr_path=os.environ.get(_EXTERNAL_RUNTIME_STDERR_PATH_ENV),
        )
    if kind == "server":
        return ServerRuntimeHost()
    if kind == "standalone":
        return StandaloneRuntimeHost()
    raise ValueError(f"Unknown browser runtime host kind '{kind}'.")
