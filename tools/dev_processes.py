from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT_DIR = Path(__file__).resolve().parents[1]
STANDALONE_OUTPUT_DIR = ROOT_DIR / "output" / "standalone"
PROC_DIR = Path("/proc")
DEFAULT_SERVER_PORT = 5000
STALE_BROWSER_HOST_KINDS = frozenset({"server-host", "standalone-host"})


@dataclass(frozen=True)
class RepoProcess:
    pid: int
    kind: str
    command: str
    cwd: Path
    port: int | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect or clean up repo-scoped browser/server helper processes.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    subparsers.add_parser("list", help="List known repo-scoped browser/server helper processes.")

    kill_parser = subparsers.add_parser("kill", help="Kill known repo-scoped helper processes.")
    target_group = kill_parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--port", type=int, help="Kill the known repo process bound to this port."
    )
    target_group.add_argument(
        "--repo",
        action="store_true",
        help="Kill every known repo-scoped helper process.",
    )
    target_group.add_argument(
        "--stale-browser-hosts",
        action="store_true",
        help="Kill only known repo server/static-host processes.",
    )
    kill_parser.add_argument(
        "--grace-seconds",
        type=float,
        default=2.0,
        help="Seconds to wait after SIGTERM before escalating to SIGKILL.",
    )
    return parser


def build_cleanup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Clean up stale repo-owned local app/browser host processes. "
            "With no target flags, this kills stale browser/server hosts."
        ),
    )
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument("--port", type=int, help="Clean up the known repo process on a port.")
    target_group.add_argument(
        "--repo",
        action="store_true",
        help="Clean up every known repo-scoped helper process.",
    )
    target_group.add_argument(
        "--stale-browser-hosts",
        action="store_true",
        help="Clean up known repo server/static-host processes. This is the default.",
    )
    parser.add_argument(
        "--grace-seconds",
        type=float,
        default=2.0,
        help="Seconds to wait after SIGTERM before escalating when supported.",
    )
    return parser


def normalize_token(token: str) -> str:
    return token.replace("\\", "/")


def normalize_path(path: Path) -> str:
    return normalize_token(str(path)).rstrip("/").casefold()


def argv_contains_script(argv: tuple[str, ...], relative_path: str) -> bool:
    normalized_path = normalize_token(relative_path)
    return any(normalize_token(token).endswith(normalized_path) for token in argv)


def argv_contains_sequence(argv: tuple[str, ...], sequence: tuple[str, ...]) -> bool:
    if len(sequence) == 0 or len(argv) < len(sequence):
        return False
    for index in range(len(argv) - len(sequence) + 1):
        if argv[index : index + len(sequence)] == sequence:
            return True
    return False


def find_module_index(argv: tuple[str, ...], module_name: str) -> int | None:
    for index in range(len(argv) - 1):
        if argv[index] == "-m" and argv[index + 1] == module_name:
            return index
    return None


def parse_http_server_port(argv: tuple[str, ...]) -> int | None:
    module_index = find_module_index(argv, "http.server")
    if module_index is None:
        return None
    port_index = module_index + 2
    if port_index < len(argv) and argv[port_index].isdigit():
        return int(argv[port_index])
    return None


def parse_server_port(environ: dict[str, str]) -> int:
    configured = environ.get("PORT")
    return int(configured) if configured and configured.isdigit() else DEFAULT_SERVER_PORT


def first_listening_port(
    *, pid: int, listening_ports_by_pid: Mapping[int, tuple[int, ...]] | None
) -> int | None:
    if listening_ports_by_pid is None:
        return None
    ports = listening_ports_by_pid.get(pid, ())
    return ports[0] if ports else None


def classify_repo_process(
    *,
    pid: int,
    cwd: Path,
    argv: tuple[str, ...],
    environ: dict[str, str],
    listening_ports_by_pid: Mapping[int, tuple[int, ...]] | None = None,
) -> RepoProcess | None:
    if not argv:
        return None
    command = " ".join(argv)
    if cwd == STANDALONE_OUTPUT_DIR and find_module_index(argv, "http.server") is not None:
        return RepoProcess(
            pid=pid,
            kind="standalone-host",
            command=command,
            cwd=cwd,
            port=parse_http_server_port(argv)
            or first_listening_port(pid=pid, listening_ports_by_pid=listening_ports_by_pid),
        )
    if cwd == ROOT_DIR and argv_contains_script(argv, "app.py"):
        return RepoProcess(
            pid=pid,
            kind="server-host",
            command=command,
            cwd=cwd,
            port=first_listening_port(pid=pid, listening_ports_by_pid=listening_ports_by_pid)
            or parse_server_port(environ),
        )
    if cwd == ROOT_DIR and argv_contains_sequence(argv, ("-m", "tools", "browser", "check")):
        return RepoProcess(pid=pid, kind="managed-browser-check", command=command, cwd=cwd)
    if cwd == ROOT_DIR and argv_contains_sequence(argv, ("-m", "tools", "browser", "review")):
        return RepoProcess(pid=pid, kind="render-review", command=command, cwd=cwd)
    return None


def read_proc_tokens(path: Path) -> tuple[str, ...]:
    raw = path.read_bytes()
    if not raw:
        return ()
    return tuple(token.decode("utf-8", errors="replace") for token in raw.split(b"\0") if token)


def read_proc_environ(path: Path) -> dict[str, str]:
    environ: dict[str, str] = {}
    for token in read_proc_tokens(path):
        key, separator, value = token.partition("=")
        if separator:
            environ[key] = value
    return environ


def read_proc_cwd(path: Path) -> Path:
    return Path(path.resolve(strict=True))


def iter_procfs_repo_processes() -> tuple[RepoProcess, ...]:
    if not PROC_DIR.is_dir():
        raise RuntimeError(
            "tools/dev_processes.py requires a procfs-backed environment such as Linux or WSL."
        )
    processes: list[RepoProcess] = []
    current_pid = os.getpid()
    for entry in PROC_DIR.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == current_pid:
            continue
        try:
            cwd = read_proc_cwd(entry / "cwd")
            argv = read_proc_tokens(entry / "cmdline")
            environ = read_proc_environ(entry / "environ")
        except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
            continue
        process = classify_repo_process(pid=pid, cwd=cwd, argv=argv, environ=environ)
        if process is not None:
            processes.append(process)
    return tuple(sorted(processes, key=lambda item: (item.kind, item.pid)))


def find_powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def run_powershell_json(script: str) -> Any:
    executable = find_powershell()
    if executable is None:
        raise RuntimeError(
            "PowerShell is required for Windows repo process discovery but was not found."
        )
    result = subprocess.run(
        [executable, "-NoProfile", "-NonInteractive", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown PowerShell failure"
        raise RuntimeError(f"Windows process discovery failed: {detail}")
    output = result.stdout.strip()
    if not output:
        return {}
    return json.loads(output)


def as_records(value: object) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, dict):
        return (value,)
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, dict))
    return ()


def windows_command_line_to_argv(command_line: str) -> tuple[str, ...]:
    try:
        return tuple(shlex.split(command_line, posix=False))
    except ValueError:
        return tuple(command_line.split())


def windows_listening_ports_by_pid(
    listeners: Iterable[Mapping[str, Any]],
) -> dict[int, tuple[int, ...]]:
    ports_by_pid: dict[int, set[int]] = {}
    for listener in listeners:
        try:
            pid = int(listener.get("OwningProcess", 0))
            port = int(listener.get("LocalPort", 0))
        except (TypeError, ValueError):
            continue
        if pid > 0 and port > 0:
            ports_by_pid.setdefault(pid, set()).add(port)
    return {pid: tuple(sorted(ports)) for pid, ports in ports_by_pid.items()}


def infer_windows_repo_cwd(
    *, command_line: str, argv: tuple[str, ...], listening_ports: tuple[int, ...]
) -> Path | None:
    normalized_command = normalize_token(command_line).casefold()
    if normalize_path(STANDALONE_OUTPUT_DIR) in normalized_command:
        return STANDALONE_OUTPUT_DIR
    if normalize_path(ROOT_DIR) in normalized_command:
        return ROOT_DIR
    if argv_contains_script(argv, "app.py") and listening_ports:
        return ROOT_DIR
    return None


def repo_processes_from_windows_payload(payload: Mapping[str, Any]) -> tuple[RepoProcess, ...]:
    listeners = as_records(payload.get("listeners") or payload.get("Listeners"))
    processes_payload = as_records(payload.get("processes") or payload.get("Processes"))
    ports_by_pid = windows_listening_ports_by_pid(listeners)
    current_pid = os.getpid()
    process_records: list[tuple[int, int | None, str, tuple[str, ...], tuple[int, ...]]] = []
    for process_payload in processes_payload:
        try:
            pid = int(process_payload.get("ProcessId", 0))
        except (TypeError, ValueError):
            continue
        if pid <= 0 or pid == current_pid:
            continue
        try:
            parent_pid = int(process_payload.get("ParentProcessId", 0))
        except (TypeError, ValueError):
            parent_pid = None
        command_line = str(process_payload.get("CommandLine") or "").strip()
        if not command_line:
            continue
        argv = windows_command_line_to_argv(command_line)
        process_records.append((pid, parent_pid, command_line, argv, ports_by_pid.get(pid, ())))

    app_process_pids = {
        pid for pid, _, _, argv, _ in process_records if argv_contains_script(argv, "app.py")
    }
    listening_app_pids = {
        pid
        for pid, _, _, argv, listening_ports in process_records
        if pid in app_process_pids and argv_contains_script(argv, "app.py") and listening_ports
    }
    related_app_pids = set(listening_app_pids)
    for pid, parent_pid, _, _, _ in process_records:
        if pid not in app_process_pids:
            continue
        if parent_pid in listening_app_pids:
            related_app_pids.add(pid)
        if any(
            child_pid in listening_app_pids and child_parent_pid == pid
            for child_pid, child_parent_pid, _, _, _ in process_records
        ):
            related_app_pids.add(pid)

    processes: list[RepoProcess] = []
    for pid, _, command_line, argv, listening_ports in process_records:
        cwd = infer_windows_repo_cwd(
            command_line=command_line, argv=argv, listening_ports=listening_ports
        )
        if cwd is None and pid in related_app_pids:
            cwd = ROOT_DIR
        if cwd is None:
            continue
        process = classify_repo_process(
            pid=pid,
            cwd=cwd,
            argv=argv,
            environ={},
            listening_ports_by_pid=ports_by_pid,
        )
        if process is not None:
            processes.append(process)
    return tuple(sorted(processes, key=lambda item: (item.kind, item.pid)))


def iter_windows_repo_processes() -> tuple[RepoProcess, ...]:
    payload = run_powershell_json(
        """
        $ErrorActionPreference = 'Stop'
        $processes = @(Get-CimInstance Win32_Process |
            Select-Object ProcessId, ParentProcessId, CommandLine)
        $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
            Select-Object OwningProcess, LocalPort)
        [pscustomobject]@{
            processes = $processes
            listeners = $listeners
        } | ConvertTo-Json -Depth 4 -Compress
        """,
    )
    if not isinstance(payload, dict):
        return ()
    return repo_processes_from_windows_payload(payload)


def iter_repo_processes() -> tuple[RepoProcess, ...]:
    if os.name == "nt":
        return iter_windows_repo_processes()
    return iter_procfs_repo_processes()


def select_processes(
    processes: Iterable[RepoProcess],
    *,
    port: int | None = None,
    repo: bool = False,
    stale_browser_hosts: bool = False,
) -> tuple[RepoProcess, ...]:
    selected: list[RepoProcess] = []
    for process in processes:
        if port is not None and process.port == port:
            selected.append(process)
        elif repo:
            selected.append(process)
        elif stale_browser_hosts and process.kind in STALE_BROWSER_HOST_KINDS:
            selected.append(process)
    return tuple(selected)


def format_process(process: RepoProcess) -> str:
    port_fragment = f" port={process.port}" if process.port is not None else ""
    return (
        f"pid={process.pid} kind={process.kind}{port_fragment} "
        f"cwd={process.cwd} command={process.command}"
    )


def pid_is_running(pid: int) -> bool:
    if os.name == "nt":
        return windows_pid_is_running(pid)
    stat_path = PROC_DIR / str(pid) / "stat"
    try:
        stat_text = stat_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    fields = stat_text.split()
    return len(fields) >= 3 and fields[2] != "Z"


def windows_pid_is_running(pid: int) -> bool:
    executable = find_powershell()
    if executable is None:
        return False
    result = subprocess.run(
        [
            executable,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def terminate_windows_process(process: RepoProcess, *, grace_seconds: float) -> str:
    if not windows_pid_is_running(process.pid):
        return "not-running"
    executable = find_powershell()
    if executable is None:
        return "permission-denied"
    result = subprocess.run(
        [
            executable,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"Stop-Process -Id {process.pid} -ErrorAction Stop",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "permission-denied"
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not windows_pid_is_running(process.pid):
            return "killed"
        time.sleep(0.1)
    return "still-running"


def terminate_process(process: RepoProcess, *, grace_seconds: float) -> str:
    if os.name == "nt":
        return terminate_windows_process(process, grace_seconds=grace_seconds)
    if not pid_is_running(process.pid):
        return "not-running"
    try:
        os.kill(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return "not-running"
    except PermissionError:
        return "permission-denied"

    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not pid_is_running(process.pid):
            return "terminated"
        time.sleep(0.1)

    # ``signal.SIGKILL`` only exists on POSIX; this whole module is Linux-only
    # at runtime (pid_is_running above reads /proc/{pid}/stat) but mypy on
    # Windows still type-checks the source. Resolve dynamically so the
    # cross-platform type-check passes; the fallback only matters if someone
    # ever calls this on Windows, where SIGTERM is already a hard kill via
    # TerminateProcess().
    hard_kill_signal = getattr(signal, "SIGKILL", signal.SIGTERM)
    try:
        os.kill(process.pid, hard_kill_signal)
    except ProcessLookupError:
        return "terminated"
    except PermissionError:
        return "permission-denied"

    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not pid_is_running(process.pid):
            return "killed"
        time.sleep(0.1)
    return "still-running"


def list_command() -> int:
    processes = iter_repo_processes()
    if not processes:
        print("No matching repo-scoped processes found.")
        return 0
    for process in processes:
        print(format_process(process))
    return 0


def kill_command(*, selected: tuple[RepoProcess, ...], grace_seconds: float) -> int:
    if not selected:
        print("No matching repo-scoped processes found.")
        return 0
    print("Killing the following repo-scoped processes:")
    for process in selected:
        print(format_process(process))
    failures = False
    for process in selected:
        result = terminate_process(process, grace_seconds=grace_seconds)
        print(f"pid={process.pid} result={result}")
        if result in {"permission-denied", "still-running"}:
            failures = True
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.subcommand == "list":
        return list_command()

    processes = iter_repo_processes()
    selected = select_processes(
        processes,
        port=args.port,
        repo=bool(args.repo),
        stale_browser_hosts=bool(args.stale_browser_hosts),
    )
    return kill_command(selected=selected, grace_seconds=float(args.grace_seconds))


def cleanup_main(argv: list[str] | None = None) -> int:
    parser = build_cleanup_parser()
    args = parser.parse_args(argv)
    stale_browser_hosts = bool(args.stale_browser_hosts)
    if args.port is None and not args.repo:
        stale_browser_hosts = True
    saw_selection = False
    for _ in range(3):
        processes = iter_repo_processes()
        selected = select_processes(
            processes,
            port=args.port,
            repo=bool(args.repo),
            stale_browser_hosts=stale_browser_hosts,
        )
        if not selected:
            if not saw_selection:
                print("No matching repo-scoped processes found.")
            return 0
        saw_selection = True
        exit_code = kill_command(selected=selected, grace_seconds=float(args.grace_seconds))
        if exit_code != 0:
            return exit_code
        time.sleep(0.2)
    print("Cleanup stopped after 3 passes; matching repo-scoped processes may remain.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
