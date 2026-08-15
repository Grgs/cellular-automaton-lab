"""Check and update the repository's npm and Python dependency surfaces."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import venv
from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

from tools._common import ROOT_DIR

PYTHON_SOURCE_PATHS: Final[tuple[Path, ...]] = (
    ROOT_DIR / "requirements.in",
    ROOT_DIR / "requirements-dev.in",
    ROOT_DIR / "requirements-lock.in",
)
PYTHON_LOCK_PATHS: Final[tuple[Path, ...]] = (
    ROOT_DIR / "requirements.txt",
    ROOT_DIR / "requirements-dev.txt",
    ROOT_DIR / "requirements-lock.txt",
)
LOCK_TOOL_REQUIREMENTS: Final[Path] = ROOT_DIR / "requirements-lock.txt"
RUNTIME_REQUIREMENTS: Final[Path] = ROOT_DIR / "requirements.txt"
LOCK_TOOL_ENV: Final[Path] = ROOT_DIR / "output" / "dependency-tools"
NODE_VERSION_PATH: Final[Path] = ROOT_DIR / ".node-version"
NVMRC_PATH: Final[Path] = ROOT_DIR / ".nvmrc"
PYTHON_VERSION_PATH: Final[Path] = ROOT_DIR / ".python-version"
PACKAGE_PATH: Final[Path] = ROOT_DIR / "package.json"
PACKAGE_LOCK_PATH: Final[Path] = ROOT_DIR / "package-lock.json"
PIN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[^\s;\\]+)(?:\s+\\)?\s*$",
    re.MULTILINE,
)


class MaintenanceError(RuntimeError):
    """A dependency workflow invariant failed."""


@dataclass(frozen=True)
class DependencyPin:
    ecosystem: str
    name: str
    current: str
    source: str
    latest: str | None = None

    @property
    def is_current(self) -> bool:
        return self.latest is None or self.current == self.latest


def _canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _is_wsl_environment(environment: Mapping[str, str] | None = None) -> bool:
    values = os.environ if environment is None else environment
    return bool(values.get("WSL_DISTRO_NAME") or values.get("WSL_INTEROP"))


def ensure_native_wsl_python(
    *, platform: str | None = None, environment: Mapping[str, str] | None = None
) -> None:
    active_platform = sys.platform if platform is None else platform
    if active_platform == "win32" and _is_wsl_environment(environment):
        raise MaintenanceError(
            "Dependency maintenance was started with Windows Python from WSL. "
            "Create `.venv` with WSL Python 3.13 and rerun through "
            "`python -m tools dependencies ...`."
        )


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MaintenanceError(f"{path.relative_to(ROOT_DIR)} must contain a JSON object")
    return payload


def read_python_source_pins() -> dict[str, DependencyPin]:
    pins: dict[str, DependencyPin] = {}
    for path in PYTHON_SOURCE_PATHS:
        text = path.read_text(encoding="utf-8")
        for match in PIN_PATTERN.finditer(text):
            name = match.group("name")
            key = _canonical_name(name)
            if key in pins:
                raise MaintenanceError(f"duplicate Python direct dependency: {name}")
            pins[key] = DependencyPin(
                ecosystem="python",
                name=name,
                current=match.group("version"),
                source=path.name,
            )
    return pins


def read_npm_source_pins() -> dict[str, DependencyPin]:
    package = _load_json(PACKAGE_PATH)
    pins: dict[str, DependencyPin] = {}
    for section in ("devDependencies", "overrides"):
        values = package.get(section, {})
        if not isinstance(values, dict):
            raise MaintenanceError(f"package.json {section} must be an object")
        for name, raw_version in values.items():
            if not isinstance(name, str) or not isinstance(raw_version, str):
                raise MaintenanceError(f"package.json {section} must contain string pins")
            pins[f"{section}:{name}"] = DependencyPin(
                ecosystem="npm",
                name=name,
                current=raw_version.lstrip("^~"),
                source=f"package.json#{section}",
            )
    return pins


def _python_latest(name: str) -> str:
    url = f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - fixed registry
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise MaintenanceError(f"could not query PyPI for {name}: {exc}") from exc
    info = payload.get("info") if isinstance(payload, dict) else None
    version = info.get("version") if isinstance(info, dict) else None
    if not isinstance(version, str) or not version:
        raise MaintenanceError(f"PyPI returned no latest version for {name}")
    return version


def _npm_latest(name: str) -> str:
    encoded_name = urllib.parse.quote(name, safe="")
    url = f"https://registry.npmjs.org/{encoded_name}/latest"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - fixed registry
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise MaintenanceError(f"could not query npm for {name}: {exc}") from exc
    version = payload.get("version") if isinstance(payload, dict) else None
    if not isinstance(version, str) or not version:
        raise MaintenanceError(f"npm returned no latest version for {name}")
    return version


def resolve_latest_versions(
    pins: Iterable[DependencyPin],
    *,
    python_resolver: Callable[[str], str] = _python_latest,
    npm_resolver: Callable[[str], str] = _npm_latest,
) -> list[DependencyPin]:
    ordered = sorted(pins, key=lambda pin: (pin.ecosystem, pin.name.lower(), pin.source))

    def resolve(pin: DependencyPin) -> DependencyPin:
        resolver = python_resolver if pin.ecosystem == "python" else npm_resolver
        return DependencyPin(**{**asdict(pin), "latest": resolver(pin.name)})

    with ThreadPoolExecutor(max_workers=min(8, max(1, len(ordered)))) as executor:
        return list(executor.map(resolve, ordered))


def _expected_node_version() -> str:
    return NODE_VERSION_PATH.read_text(encoding="utf-8").strip()


def validate_runtime_pin_files() -> None:
    expected = _expected_node_version()
    nvm_version = NVMRC_PATH.read_text(encoding="utf-8").strip()
    if nvm_version != expected:
        raise MaintenanceError(f".nvmrc pins Node {nvm_version}, but .node-version pins {expected}")
    package = _load_json(PACKAGE_PATH)
    engines = package.get("engines")
    package_version = engines.get("node") if isinstance(engines, dict) else None
    if package_version != expected:
        raise MaintenanceError(
            f"package.json engines.node is {package_version!r}, expected {expected!r}"
        )


def check_node_version() -> None:
    expected = _expected_node_version()
    result = subprocess.run(
        ["node", "--version"], check=False, capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        raise MaintenanceError("Node.js is unavailable; install the version in .node-version")
    actual = result.stdout.strip().lstrip("v")
    if actual != expected:
        raise MaintenanceError(
            f"Node {actual} is active, but this repo requires {expected}. "
            "Select `.node-version` with your Node version manager."
        )


def check_python_version() -> None:
    expected = PYTHON_VERSION_PATH.read_text(encoding="utf-8").strip()
    actual = ".".join(str(part) for part in sys.version_info[:3])
    if actual != expected:
        raise MaintenanceError(
            f"Python {actual} is active, but this repo requires {expected}. "
            "Install/select `.python-version`, then rebuild the native `.venv`."
        )


def _locked_versions(path: Path) -> dict[str, str]:
    return {
        _canonical_name(match.group("name")): match.group("version")
        for match in PIN_PATTERN.finditer(path.read_text(encoding="utf-8"))
    }


def validate_lock_surfaces(
    python_pins: dict[str, DependencyPin], npm_pins: dict[str, DependencyPin]
) -> None:
    locks_by_source = {
        source.name: _locked_versions(lock)
        for source, lock in zip(PYTHON_SOURCE_PATHS, PYTHON_LOCK_PATHS, strict=True)
    }
    for key, pin in python_pins.items():
        locked = locks_by_source.get(pin.source)
        if locked is None:
            raise MaintenanceError(f"no Python lock is configured for {pin.source}")
        if locked.get(key) != pin.current:
            raise MaintenanceError(
                f"{pin.name}=={pin.current} from {pin.source} is not present in its lock"
            )

    package_lock = _load_json(PACKAGE_LOCK_PATH)
    packages = package_lock.get("packages")
    if not isinstance(packages, dict):
        raise MaintenanceError("package-lock.json is missing packages")
    root = packages.get("")
    locked_dev = root.get("devDependencies") if isinstance(root, dict) else None
    if not isinstance(locked_dev, dict):
        raise MaintenanceError("package-lock.json is missing root devDependencies")
    for key, pin in npm_pins.items():
        if key.startswith("overrides:"):
            resolved = packages.get(f"node_modules/{pin.name}")
            resolved_version = resolved.get("version") if isinstance(resolved, dict) else None
            if resolved_version != pin.current:
                raise MaintenanceError(f"package-lock.json override is stale for {pin.name}")
            continue
        if not key.startswith("devDependencies:"):
            continue
        declared = locked_dev.get(pin.name)
        package_declared = _load_json(PACKAGE_PATH)["devDependencies"]
        expected = package_declared.get(pin.name) if isinstance(package_declared, dict) else None
        if declared != expected:
            raise MaintenanceError(f"package-lock.json is stale for {pin.name}")
        resolved = packages.get(f"node_modules/{pin.name}")
        resolved_version = resolved.get("version") if isinstance(resolved, dict) else None
        if resolved_version != pin.current:
            raise MaintenanceError(
                f"package-lock.json resolves {pin.name} to {resolved_version}, "
                f"expected {pin.current}"
            )


def validate_mirrored_pins(python_pins: dict[str, DependencyPin]) -> None:
    mirrors = {
        "ruff": (
            ROOT_DIR / ".pre-commit-config.yaml",
            re.compile(r"ruff==(?P<version>[0-9][^\s]+)"),
        ),
        "coverage": (
            ROOT_DIR / ".github" / "workflows" / "ci.yml",
            re.compile(r"coverage==(?P<version>[0-9][^\s]+)"),
        ),
    }
    for name, (path, pattern) in mirrors.items():
        expected = python_pins[name].current
        versions = {match.group("version") for match in pattern.finditer(path.read_text())}
        if versions != {expected}:
            relative = path.relative_to(ROOT_DIR)
            raise MaintenanceError(
                f"{relative} mirrors {name} as {sorted(versions)}, expected {expected}"
            )


def _replace_python_pin(text: str, name: str, version: str) -> str:
    pattern = re.compile(rf"^{re.escape(name)}==[^\s;\\]+\s*$", re.MULTILINE | re.IGNORECASE)
    updated, count = pattern.subn(f"{name}=={version}", text)
    if count != 1:
        raise MaintenanceError(f"expected one direct pin for {name}, found {count}")
    return updated


def _write_updates(resolved: list[DependencyPin]) -> None:
    package = _load_json(PACKAGE_PATH)
    python_text = {path: path.read_text(encoding="utf-8") for path in PYTHON_SOURCE_PATHS}
    updated_python: dict[str, str] = {}

    for pin in resolved:
        if pin.latest is None or pin.latest == pin.current:
            continue
        if pin.ecosystem == "python":
            path = ROOT_DIR / pin.source
            python_text[path] = _replace_python_pin(python_text[path], pin.name, pin.latest)
            updated_python[_canonical_name(pin.name)] = pin.latest
            continue
        section = pin.source.split("#", maxsplit=1)[1]
        values = package.get(section)
        if not isinstance(values, dict):
            raise MaintenanceError(f"package.json {section} must be an object")
        prior = values[pin.name]
        prefix = prior[0] if isinstance(prior, str) and prior[:1] in {"^", "~"} else ""
        values[pin.name] = prefix + pin.latest

    for path, text in python_text.items():
        path.write_text(text, encoding="utf-8")
    PACKAGE_PATH.write_text(json.dumps(package, indent=4) + "\n", encoding="utf-8")
    _sync_mirrors(updated_python)


def _sync_mirrors(updated_python: dict[str, str]) -> None:
    replacements = (
        ("ruff", ROOT_DIR / ".pre-commit-config.yaml", re.compile(r"ruff==[^\s]+")),
        (
            "coverage",
            ROOT_DIR / ".github" / "workflows" / "ci.yml",
            re.compile(r"coverage==[^\s]+"),
        ),
    )
    for name, path, pattern in replacements:
        version = updated_python.get(name)
        if version is None:
            continue
        text = path.read_text(encoding="utf-8")
        path.write_text(pattern.sub(f"{name}=={version}", text), encoding="utf-8")


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT_DIR, check=False)
    if completed.returncode != 0:
        raise MaintenanceError(f"command failed ({completed.returncode}): {' '.join(command)}")


def _lock_tool_python() -> Path:
    if os.name == "nt":
        return LOCK_TOOL_ENV / "Scripts" / "python.exe"
    return LOCK_TOOL_ENV / "bin" / "python"


def bootstrap_lock_tool() -> Path:
    if not LOCK_TOOL_REQUIREMENTS.exists():
        raise MaintenanceError("requirements-lock.txt is missing; regenerate the lock-tool lock")
    if not RUNTIME_REQUIREMENTS.exists():
        raise MaintenanceError("requirements.txt is missing; regenerate the runtime lock")
    python = _lock_tool_python()
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(LOCK_TOOL_ENV)
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "-r",
            str(RUNTIME_REQUIREMENTS),
            "-r",
            str(LOCK_TOOL_REQUIREMENTS),
        ]
    )
    return python


def compile_python_locks(python: Path) -> None:
    for source, output in zip(PYTHON_SOURCE_PATHS, PYTHON_LOCK_PATHS, strict=True):
        _run(
            [
                str(python),
                "-m",
                "piptools",
                "compile",
                "--upgrade",
                "--strip-extras",
                "--generate-hashes",
                "--allow-unsafe",
                f"--output-file={output}",
                str(source),
            ]
        )


def run_audits() -> None:
    _run(["npm", "audit", "--audit-level=low"])
    command = [sys.executable, "-m", "pip_audit"]
    for path in PYTHON_LOCK_PATHS:
        command.extend(("-r", str(path)))
    _run(command)


def _render(pins: list[DependencyPin]) -> str:
    lines = []
    for pin in pins:
        latest = pin.latest or "not queried"
        status = "current" if pin.is_current else "UPDATE"
        lines.append(
            f"{pin.ecosystem:<6} {pin.name:<28} {pin.current:<12} latest {latest:<12} {status}"
        )
    return "\n".join(lines)


def build_check_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check dependency pins and lock surfaces.")
    parser.add_argument("--offline", action="store_true", help="skip npm and PyPI queries")
    parser.add_argument("--audit", action="store_true", help="run npm audit and pip-audit")
    parser.add_argument(
        "--skip-node-check", action="store_true", help="allow a non-pinned local Node version"
    )
    parser.add_argument(
        "--skip-python-check",
        action="store_true",
        help="allow a non-pinned local Python version",
    )
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser


def check_main(argv: list[str] | None = None) -> int:
    args = build_check_parser().parse_args(argv)
    try:
        ensure_native_wsl_python()
        validate_runtime_pin_files()
        if not args.skip_python_check:
            check_python_version()
        if not args.skip_node_check:
            check_node_version()
        python_pins = read_python_source_pins()
        npm_pins = read_npm_source_pins()
        validate_lock_surfaces(python_pins, npm_pins)
        validate_mirrored_pins(python_pins)
        pins = list(python_pins.values()) + list(npm_pins.values())
        resolved = pins if args.offline else resolve_latest_versions(pins)
        stale = [pin for pin in resolved if not pin.is_current]
        if args.audit:
            run_audits()
        if args.format == "json":
            print(json.dumps({"dependencies": [asdict(pin) for pin in resolved]}, indent=2))
        else:
            print(_render(resolved))
            print(f"\n{len(resolved)} direct dependency surfaces checked; {len(stale)} stale.")
        return 1 if stale else 0
    except MaintenanceError as exc:
        print(f"dependency check failed: {exc}", file=sys.stderr)
        return 2


def build_update_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update all direct pins and regenerate locks.")
    parser.add_argument("--dry-run", action="store_true", help="report updates without writing")
    parser.add_argument("--skip-audit", action="store_true", help="skip npm audit and pip-audit")
    parser.add_argument(
        "--skip-node-check", action="store_true", help="allow a non-pinned local Node version"
    )
    parser.add_argument(
        "--skip-python-check",
        action="store_true",
        help="allow a non-pinned local Python version",
    )
    return parser


def update_main(argv: list[str] | None = None) -> int:
    args = build_update_parser().parse_args(argv)
    try:
        ensure_native_wsl_python()
        validate_runtime_pin_files()
        if not args.skip_python_check:
            check_python_version()
        if not args.skip_node_check:
            check_node_version()
        before = resolve_latest_versions(
            list(read_python_source_pins().values()) + list(read_npm_source_pins().values())
        )
        print(_render(before))
        stale = [pin for pin in before if not pin.is_current]
        if args.dry_run:
            print(f"\nDry run: {len(stale)} direct dependency updates available.")
            return 1 if stale else 0
        _write_updates(before)
        _run(["npm", "install"])
        compile_python_locks(bootstrap_lock_tool())
        python_pins = read_python_source_pins()
        npm_pins = read_npm_source_pins()
        validate_lock_surfaces(python_pins, npm_pins)
        validate_mirrored_pins(python_pins)
        if not args.skip_audit:
            run_audits()
        print(f"\nUpdated {len(stale)} direct dependencies and regenerated all locks.")
        return 0
    except MaintenanceError as exc:
        print(f"dependency update failed: {exc}", file=sys.stderr)
        return 2
