from __future__ import annotations

import argparse
import os
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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


def normalize_token(token: str) -> str:
    return token.replace("\\", "/")


def argv_contains_script(argv: tuple[str, ...], relative_path: str) -> bool:
    normalized_path = normalize_token(relative_path)
    return any(normalize_token(token).endswith(normalized_path) for token in argv)


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


def classify_repo_process(
    *,
    pid: int,
    cwd: Path,
    argv: tuple[str, ...],
    environ: dict[str, str],
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
            port=parse_http_server_port(argv),
        )
    if cwd == ROOT_DIR and argv_contains_script(argv, "app.py"):
        return RepoProcess(
            pid=pid,
            kind="server-host",
            command=command,
            cwd=cwd,
            port=parse_server_port(environ),
        )
    if cwd == ROOT_DIR and argv_contains_script(argv, "tools/run_browser_check.py"):
        return RepoProcess(pid=pid, kind="managed-browser-check", command=command, cwd=cwd)
    if cwd == ROOT_DIR and argv_contains_script(argv, "tools/render_canvas_review.py"):
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


def iter_repo_processes() -> tuple[RepoProcess, ...]:
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
    stat_path = PROC_DIR / str(pid) / "stat"
    try:
        stat_text = stat_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    fields = stat_text.split()
    return len(fields) >= 3 and fields[2] != "Z"


def terminate_process(process: RepoProcess, *, grace_seconds: float) -> str:
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

    try:
        os.kill(process.pid, signal.SIGKILL)
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


if __name__ == "__main__":
    raise SystemExit(main())
