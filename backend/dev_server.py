from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypedDict, cast
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from backend.payload_types import ServerMetaPayload


APP_NAME = "cellular-automaton-lab"


class _WindowsProcessPayload(TypedDict, total=False):
    pid: int
    command_line: str
    executable_path: str


@dataclass(frozen=True)
class ListeningProcess:
    pid: int | None
    command_line: str = ""
    executable_path: str | None = None


def resolve_replace_existing(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def resolve_query_host(host: str) -> str:
    return "127.0.0.1" if host in {"0.0.0.0", "::", ""} else host


def port_is_available(host: str, port: int) -> bool:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def wait_for_port(host: str, port: int, *, should_be_available: bool, timeout_seconds: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if port_is_available(host, port) == should_be_available:
            return True
        time.sleep(0.05)
    return port_is_available(host, port) == should_be_available


def _windows_listener_pid(port: int) -> int | None:
    result = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    suffix = f":{port}"
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line or not line.startswith("TCP"):
            continue
        parts = line.split()
        if len(parts) < 5 or parts[3] != "LISTENING":
            continue
        local_address = parts[1]
        if local_address.endswith(suffix):
            try:
                return int(parts[4])
            except ValueError:
                return None
    return None


def _windows_process_details(pid: int) -> ListeningProcess:
    powershell = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            f"$process = Get-CimInstance Win32_Process -Filter \"ProcessId = {pid}\"; "
            "if ($null -eq $process) { exit 1 }; "
            "$payload = @{ "
            "  pid = $process.ProcessId; "
            "  command_line = $process.CommandLine; "
            "  executable_path = $process.ExecutablePath "
            "} | ConvertTo-Json -Compress; "
            "Write-Output $payload"
        ),
    ]
    result = subprocess.run(powershell, check=False, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return ListeningProcess(pid=pid)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return ListeningProcess(pid=pid)
    if not isinstance(payload, dict):
        return ListeningProcess(pid=pid)
    process_payload = cast(_WindowsProcessPayload, payload)
    return ListeningProcess(
        pid=pid,
        command_line=str(process_payload.get("command_line") or ""),
        executable_path=process_payload.get("executable_path"),
    )


def _posix_listener_pid(port: int) -> int | None:
    for command in (
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
        ["ss", "-ltnp"],
    ):
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            continue
        if command[0] == "lsof":
            for line in result.stdout.splitlines():
                line = line.strip()
                if line:
                    try:
                        return int(line)
                    except ValueError:
                        continue
            continue

        for raw_line in result.stdout.splitlines():
            if f":{port} " not in raw_line:
                continue
            marker = "pid="
            if marker not in raw_line:
                continue
            pid_fragment = raw_line.split(marker, 1)[1].split(",", 1)[0].split(")", 1)[0]
            try:
                return int(pid_fragment)
            except ValueError:
                continue
    return None


def _posix_process_details(pid: int) -> ListeningProcess:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "args="],
        check=False,
        capture_output=True,
        text=True,
    )
    command_line = result.stdout.strip() if result.returncode == 0 else ""
    executable_path = None
    exe_link = Path(f"/proc/{pid}/exe")
    if exe_link.exists():
        try:
            executable_path = str(exe_link.resolve())
        except OSError:
            executable_path = None
    return ListeningProcess(pid=pid, command_line=command_line, executable_path=executable_path)


def find_listening_process(port: int) -> ListeningProcess:
    if os.name == "nt":
        pid = _windows_listener_pid(port)
        return _windows_process_details(pid) if pid is not None else ListeningProcess(pid=None)

    pid = _posix_listener_pid(port)
    return _posix_process_details(pid) if pid is not None else ListeningProcess(pid=None)


def fetch_server_meta(host: str, port: int, *, timeout_seconds: float = 1.0) -> ServerMetaPayload | None:
    query_host = resolve_query_host(host)
    url = f"http://{query_host}:{port}/api/meta"
    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            if response.status != 200:
                return None
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    app_name = payload.get("app_name")
    if not isinstance(app_name, str) or not app_name:
        return None
    return {"app_name": app_name}


def looks_like_this_app(
    listener: ListeningProcess,
    meta: ServerMetaPayload | None,
    *,
    app_entrypoint: Path,
) -> bool:
    if meta and meta.get("app_name") == APP_NAME:
        return True

    command_line = listener.command_line.lower()
    if not command_line:
        return False
    return app_entrypoint.name.lower() in command_line and "python" in command_line


def terminate_process(pid: int) -> None:
    os.kill(pid, signal.SIGTERM)


def format_listener(listener: ListeningProcess, meta: ServerMetaPayload | None) -> str:
    _ = meta
    pieces = []
    if listener.pid is not None:
        pieces.append(f"pid {listener.pid}")
    if listener.command_line:
        pieces.append(listener.command_line)
    return " | ".join(pieces) if pieces else "unknown listener"


def prepare_dev_server(
    *,
    host: str,
    port: int,
    app_entrypoint: Path,
    replace_existing: bool,
    port_is_available_fn: Callable[[str, int], bool] = port_is_available,
    find_listening_process_fn: Callable[[int], ListeningProcess] = find_listening_process,
    fetch_server_meta_fn: Callable[[str, int], ServerMetaPayload | None] = fetch_server_meta,
    terminate_process_fn: Callable[[int], None] = terminate_process,
    wait_for_port_fn: Callable[[str, int], bool] | None = None,
) -> ListeningProcess | None:
    if port_is_available_fn(host, port):
        return None

    listener = find_listening_process_fn(port)
    meta = fetch_server_meta_fn(host, port)
    listener_summary = format_listener(listener, meta)

    if not replace_existing:
        raise RuntimeError(
            f"Port {port} is already in use by {listener_summary}. "
            "Stop that process or restart with DEV_REPLACE_SERVER=1 to replace a stale dev server."
        )

    if listener.pid is None:
        raise RuntimeError(
            f"Port {port} is already in use, but the listening process could not be identified. "
            "Stop the existing listener and try again."
        )

    if not looks_like_this_app(listener, meta, app_entrypoint=app_entrypoint):
        raise RuntimeError(
            f"Refusing to replace the listener on port {port} because it does not look like this app: "
            f"{listener_summary}"
        )

    terminate_process_fn(listener.pid)
    waiter = wait_for_port_fn or (lambda wait_host, wait_port: wait_for_port(
        wait_host,
        wait_port,
        should_be_available=True,
    ))
    if not waiter(host, port):
        raise RuntimeError(
            f"Stopped pid {listener.pid}, but port {port} did not become available in time."
        )
    return listener
