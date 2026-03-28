import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from collections.abc import Mapping
from typing import IO, Protocol

from backend.payload_types import ResetControlRequestPayload, SimulationStatePayload, TopologyPayload
from tests.typed_payloads import require_simulation_state_payload, require_topology_payload


class PollingProcess(Protocol):
    def poll(self) -> int | None:
        ...

class JsonApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip('/')

    def wait_until_ready(
        self,
        timeout_seconds: float = 20,
        *,
        process: PollingProcess | None = None,
    ) -> None:
        deadline = time.time() + timeout_seconds
        while True:
            try:
                with urllib.request.urlopen(f'{self.base_url}/', timeout=1):
                    return
            except Exception:
                if process is not None:
                    exit_code = process.poll()
                    if exit_code is not None:
                        raise RuntimeError(
                            f"Server exited before becoming ready (exit code {exit_code})."
                        )
                if time.time() > deadline:
                    raise RuntimeError('Server did not start in time.')
                time.sleep(0.25)

    def request_json(
        self,
        path: str,
        method: str = 'GET',
        payload: Mapping[str, object] | None = None,
    ) -> object:
        body = None if payload is None else json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            f'{self.base_url}{path}',
            data=body,
            method=method,
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read().decode('utf-8')
            return json.loads(raw) if raw else None

    def get_state(self) -> SimulationStatePayload:
        return require_simulation_state_payload(
            self.request_json("/api/state"),
            context="browser support backend state",
        )

    def get_topology(self) -> TopologyPayload:
        return require_topology_payload(
            self.request_json("/api/topology"),
            context="browser support backend topology",
        )

    def reset(self, payload: ResetControlRequestPayload) -> SimulationStatePayload:
        return require_simulation_state_payload(
            self.request_json("/api/control/reset", method="POST", payload=payload),
            context="browser support backend reset response",
        )


class AppServer:
    def __init__(self) -> None:
        self.process: subprocess.Popen[str] | None = None
        self.stdout_handle: IO[str] | None = None
        self.stderr_handle: IO[str] | None = None
        self.root = Path(__file__).resolve().parents[2]
        self.port = self._find_available_port()
        self.base_url = f'http://127.0.0.1:{self.port}'
        self.instance_dir = tempfile.TemporaryDirectory(prefix='cellular-automaton-instance-')
        self.log_dir = tempfile.TemporaryDirectory(prefix='cellular-automaton-server-logs-')
        self.stdout_path = Path(self.log_dir.name) / 'server-stdout.log'
        self.stderr_path = Path(self.log_dir.name) / 'server-stderr.log'
        self.client = JsonApiClient(self.base_url)

    def _find_available_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def start(self) -> None:
        if self.process and self.process.poll() is None:
            return
        env = os.environ.copy()
        env["PORT"] = str(self.port)
        env["APP_INSTANCE_PATH"] = self.instance_dir.name
        self.stdout_handle = self.stdout_path.open('a', encoding='utf-8')
        self.stderr_handle = self.stderr_path.open('a', encoding='utf-8')
        self.process = subprocess.Popen(
            [sys.executable, 'app.py'],
            cwd=self.root,
            stdout=self.stdout_handle,
            stderr=self.stderr_handle,
            text=True,
            env=env,
        )
        try:
            self.client.wait_until_ready(process=self.process)
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
                "Server did not become ready for browser tests.\n" + "\n".join(details)
            ) from exc

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

    def restart(self) -> None:
        self.stop()
        self.start()

    def close(self) -> None:
        self.stop()
        self.instance_dir.cleanup()
        self.log_dir.cleanup()

    def _close_log_handles(self) -> None:
        if self.stdout_handle is not None:
            self.stdout_handle.close()
            self.stdout_handle = None
        if self.stderr_handle is not None:
            self.stderr_handle.close()
            self.stderr_handle = None

    def read_stdout(self) -> str:
        if not self.stdout_path.exists():
            return ""
        return self.stdout_path.read_text(encoding='utf-8')

    def read_stderr(self) -> str:
        if not self.stderr_path.exists():
            return ""
        return self.stderr_path.read_text(encoding='utf-8')
