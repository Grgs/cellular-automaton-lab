from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import NoReturn

from tests.e2e.playwright_suite_support import (
    playwright_suite_manifest_payload,
    resolve_playwright_suite_definition,
)
from tests.e2e.support_runtime_host import standalone_build_status
from tools._common import ROOT_DIR, run_command


DEFAULT_PLAYWRIGHT_SUBSET_COUNT = 6
PLAYWRIGHT_LIB_ROOT = ROOT_DIR / "output" / "playwright-linux-libs"
PLAYWRIGHT_LIB_DEB_DIR = PLAYWRIGHT_LIB_ROOT / "debs"
PLAYWRIGHT_LIB_EXTRACT_ROOT = PLAYWRIGHT_LIB_ROOT / "root"


def suite_manifest_payload() -> list[dict[str, object]]:
    return playwright_suite_manifest_payload()


def standalone_build_status_payload() -> dict[str, object]:
    return standalone_build_status(ROOT_DIR)


def _run_capture(
    command: list[str],
    *,
    cwd: Path = ROOT_DIR,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def _find_chromium_headless_shell() -> Path | None:
    playwright_cache = Path.home() / ".cache" / "ms-playwright"
    if not playwright_cache.is_dir():
        return None
    candidates = [
        entry / "chrome-headless-shell-linux64" / "chrome-headless-shell"
        for entry in sorted(playwright_cache.iterdir())
        if entry.is_dir() and entry.name.startswith("chromium_headless_shell-")
    ]
    existing = [candidate for candidate in candidates if candidate.exists()]
    return existing[-1] if existing else None


def _linux_repair_message(
    *,
    missing_libraries: list[str],
    packages: list[str] | None = None,
    missing_tools: list[str] | None = None,
    extra_detail: str = "",
) -> str:
    resolved_packages = packages or []
    resolved_missing_tools = missing_tools or []
    lines = [
        "Playwright browser is missing shared libraries on Linux.",
        f"Missing libraries: {', '.join(missing_libraries)}",
    ]
    if resolved_packages:
        lines.append(f"Attempted repair packages: {', '.join(resolved_packages)}")
    if resolved_missing_tools:
        lines.append(f"Missing repair tools: {', '.join(resolved_missing_tools)}")
    lines.append(
        "The local self-repair path currently assumes Debian/Ubuntu-style tooling (`apt`, `apt-cache`, and `dpkg-deb`)."
    )
    lines.append(
        "Install the required runtime libraries manually or rerun in an environment with those packaging tools available."
    )
    lines.append(
        "Preferred browser entrypoints: `python -m tools test e2e`, `npm run test:e2e:playwright:server`, or `npm run test:e2e:playwright:standalone`."
    )
    lines.append("Troubleshooting reference: docs/TESTING.md (Playwright troubleshooting section).")
    if extra_detail:
        lines.append(extra_detail.strip())
    return "\n".join(lines)


def _raise_linux_repair_error(
    *,
    missing_libraries: list[str],
    packages: list[str] | None = None,
    missing_tools: list[str] | None = None,
    extra_detail: str = "",
) -> NoReturn:
    raise SystemExit(
        _linux_repair_message(
            missing_libraries=missing_libraries,
            packages=packages,
            missing_tools=missing_tools,
            extra_detail=extra_detail,
        )
    )


def _prepend_linux_library_path(env: dict[str, str], library_dir: Path) -> dict[str, str]:
    resolved_env = dict(env)
    existing = resolved_env.get("LD_LIBRARY_PATH")
    resolved_env["LD_LIBRARY_PATH"] = f"{library_dir}:{existing}" if existing else str(library_dir)
    return resolved_env


def _ldd_missing_libraries(binary_path: Path, env: dict[str, str]) -> list[str]:
    try:
        result = _run_capture(["ldd", str(binary_path)], env=env)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"`ldd` is required to inspect Playwright browser libraries: {exc}"
        ) from exc
    if result.returncode != 0:
        details = result.stderr or result.stdout or ""
        raise SystemExit(f"ldd failed for {binary_path}:\n{details}")
    missing: list[str] = []
    for line in (result.stdout or "").splitlines():
        stripped = line.strip()
        if stripped.endswith("=> not found"):
            missing.append(stripped.split(" => ", 1)[0] or stripped)
    return missing


def _choose_alsa_package(missing_libraries: list[str]) -> str:
    if shutil.which("apt-cache") is None:
        _raise_linux_repair_error(
            missing_libraries=missing_libraries,
            missing_tools=["apt-cache"],
        )
    for package_name in ("libasound2t64", "libasound2"):
        result = _run_capture(["apt-cache", "policy", package_name])
        if result.returncode == 0 and re.search(r"Candidate:\s+(?!\(none\))", result.stdout or ""):
            return package_name
    _raise_linux_repair_error(
        missing_libraries=missing_libraries,
        packages=["libasound2t64", "libasound2"],
        extra_detail="Unable to resolve an installable ALSA runtime package with `apt-cache policy`.",
    )


def _ensure_linux_playwright_runtime(env: dict[str, str]) -> dict[str, str]:
    if sys.platform != "linux":
        return env
    browser_binary = _find_chromium_headless_shell()
    if browser_binary is None:
        return env

    local_lib_dir = PLAYWRIGHT_LIB_EXTRACT_ROOT / "usr" / "lib" / "x86_64-linux-gnu"
    if local_lib_dir.exists():
        cached_env = _prepend_linux_library_path(env, local_lib_dir)
        if not _ldd_missing_libraries(browser_binary, cached_env):
            return cached_env

    current_missing = _ldd_missing_libraries(browser_binary, env)
    if not current_missing:
        return env

    missing_tools = [
        command for command in ("apt", "apt-cache", "dpkg-deb") if shutil.which(command) is None
    ]
    if missing_tools:
        _raise_linux_repair_error(
            missing_libraries=current_missing,
            missing_tools=missing_tools,
        )

    packages = ["libnspr4", "libnss3", _choose_alsa_package(current_missing)]
    PLAYWRIGHT_LIB_DEB_DIR.mkdir(parents=True, exist_ok=True)
    PLAYWRIGHT_LIB_EXTRACT_ROOT.mkdir(parents=True, exist_ok=True)

    download_result = _run_capture(
        ["apt", "download", *packages],
        cwd=PLAYWRIGHT_LIB_DEB_DIR,
        env=env,
    )
    if download_result.returncode != 0:
        _raise_linux_repair_error(
            missing_libraries=current_missing,
            packages=packages,
            extra_detail=(
                "Automatic browser-library repair failed while running `apt download`.\n"
                + (
                    download_result.stderr
                    or download_result.stdout
                    or "The `apt download` command failed."
                )
            ),
        )

    deb_files = sorted(PLAYWRIGHT_LIB_DEB_DIR.glob("*.deb"))
    for deb_file in deb_files:
        extract_result = _run_capture(
            ["dpkg-deb", "-x", str(deb_file), str(PLAYWRIGHT_LIB_EXTRACT_ROOT)],
            env=env,
        )
        if extract_result.returncode != 0:
            _raise_linux_repair_error(
                missing_libraries=current_missing,
                packages=packages,
                extra_detail=(
                    f"Failed to extract {deb_file.name} with `dpkg-deb -x`.\n"
                    + (extract_result.stderr or extract_result.stdout or "")
                ),
            )

    next_env = _prepend_linux_library_path(env, local_lib_dir)
    remaining_missing = _ldd_missing_libraries(browser_binary, next_env)
    if remaining_missing:
        _raise_linux_repair_error(
            missing_libraries=remaining_missing,
            packages=packages,
            extra_detail="Playwright browser is still missing shared libraries after the local repair attempt.",
        )
    return next_env


def build_e2e_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools test e2e",
        description=(
            "Run Playwright suites through the Python CLI or the broader local "
            "frontend-plus-playwright orchestrator."
        ),
    )
    parser.add_argument("--suite", default="all", help="Playwright suite name to run.")
    parser.add_argument(
        "--list-suites",
        action="store_true",
        help="Print the public Playwright suite manifest and exit.",
    )
    parser.add_argument(
        "--skip-standalone-build",
        action="store_true",
        help="Skip refreshing standalone output before standalone-backed suites.",
    )
    parser.add_argument(
        "--force-standalone-build",
        action="store_true",
        help="Force a standalone rebuild before running standalone-backed suites.",
    )
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        help="Additional KEY=VALUE environment overrides for the selected Playwright suite.",
    )
    parser.add_argument(
        "--orchestrated",
        action="store_true",
        help="Run the broader frontend-plus-chunked-playwright workflow.",
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="With --orchestrated, run only frontend tests and the suite integrity guard.",
    )
    parser.add_argument(
        "--playwright-only",
        action="store_true",
        help="With --orchestrated, run only chunked Playwright subsets.",
    )
    parser.add_argument(
        "--subset-count",
        type=int,
        default=DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
        help="With --orchestrated, split the server browser suite into this many chunks.",
    )
    return parser


def _parse_env_overrides(assignments: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for assignment in assignments:
        key, separator, value = assignment.partition("=")
        if not separator:
            raise SystemExit(f"Expected KEY=VALUE after --env, got {assignment!r}.")
        overrides[key] = value
    return overrides


def _run_unittest_modules(modules: list[str], env: dict[str, str]) -> int:
    result = run_command([sys.executable, "-m", "unittest", "-q", *modules], env=env)
    return result.returncode


def _ensure_current_standalone_build(
    *,
    force: bool,
    skip: bool,
    env: dict[str, str],
) -> None:
    status = standalone_build_status_payload()
    if skip:
        return
    if not force and bool(status.get("buildCurrent")):
        return
    result = run_command([sys.executable, "-m", "tools", "build", "standalone"], env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _run_playwright_suite(
    *,
    suite_name: str,
    skip_standalone_build: bool,
    force_standalone_build: bool,
    env_overrides: dict[str, str],
) -> int:
    selected_suite = resolve_playwright_suite_definition(suite_name)
    runtime_env = {
        **os.environ,
        **dict(selected_suite.env),
        **env_overrides,
    }
    runtime_env = _ensure_linux_playwright_runtime(runtime_env)
    if selected_suite.requires_standalone_build:
        _ensure_current_standalone_build(
            force=force_standalone_build,
            skip=skip_standalone_build,
            env=runtime_env,
        )
    return _run_unittest_modules([selected_suite.module], runtime_env)


def _run_orchestrated_frontend_unit_tests() -> None:
    _run_checked(["npm", "run", "test:frontend"])
    _run_checked(
        [sys.executable, "-m", "unittest", "-q", "tests.e2e.test_playwright_suite_integrity"]
    )


def _run_checked(command: list[str], *, env: dict[str, str] | None = None) -> None:
    start = time.perf_counter()
    merged_env = None if env is None else {**os.environ, **env}
    result = subprocess.run(command, cwd=ROOT_DIR, env=merged_env, check=False)
    elapsed = time.perf_counter() - start
    print(f"{elapsed:7.2f}s  {' '.join(command)}")
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _run_orchestrated_playwright_subsets(subset_count: int) -> None:
    _run_checked(["npm", "run", "build:frontend"])
    for subset_index in range(subset_count):
        _run_checked(
            [sys.executable, "-m", "tools", "test", "e2e", "--suite", "subset"],
            env={
                "PLAYWRIGHT_SUBSET_INDEX": str(subset_index),
                "PLAYWRIGHT_SUBSET_COUNT": str(subset_count),
            },
        )


def _run_orchestrated(args: argparse.Namespace) -> int:
    if args.frontend_only and args.playwright_only:
        raise SystemExit("--frontend-only and --playwright-only cannot be used together.")
    if args.subset_count <= 0:
        raise SystemExit("--subset-count must be positive.")
    if not args.playwright_only:
        _run_orchestrated_frontend_unit_tests()
    if not args.frontend_only:
        _run_orchestrated_playwright_subsets(args.subset_count)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_e2e_parser()
    args = parser.parse_args(argv)
    if args.list_suites:
        print(json.dumps(suite_manifest_payload(), indent=2))
        return 0
    if args.orchestrated:
        return _run_orchestrated(args)
    if args.skip_standalone_build and args.force_standalone_build:
        raise SystemExit(
            "--skip-standalone-build and --force-standalone-build cannot be used together."
        )
    return _run_playwright_suite(
        suite_name=str(args.suite),
        skip_standalone_build=bool(args.skip_standalone_build),
        force_standalone_build=bool(args.force_standalone_build),
        env_overrides=_parse_env_overrides(list(args.env)),
    )
