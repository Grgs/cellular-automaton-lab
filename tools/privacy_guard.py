from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ALLOW_MARKER: Final[str] = "privacy-guard: allow"
TEXT_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".css",
        ".html",
        ".js",
        ".json",
        ".md",
        ".py",
        ".svg",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }
)
SKIP_PATH_PARTS: Final[frozenset[str]] = frozenset({".git", "node_modules", "static", "dist", "__pycache__"})


@dataclass(frozen=True)
class PrivacyPattern:
    code: str
    description: str
    regex: re.Pattern[str]


PRIVACY_PATTERNS: Final[tuple[PrivacyPattern, ...]] = (
    PrivacyPattern(
        code="windows-user-profile-path",
        description="Windows user-profile path",
        regex=re.compile(
            r"(?i)\b[A-Z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\r\n]+(?:[\\/][^\r\n]*)?"
        ),
    ),
    PrivacyPattern(
        code="posix-home-path",
        description="POSIX home-directory path",
        regex=re.compile(r"/(?:Users|home)/[^/\s'\"`\])]+(?:/[^\s'\"`\])]+)*"),
    ),
    PrivacyPattern(
        code="consumer-email-address",
        description="consumer webmail address",
        regex=re.compile(
            r"(?i)\b[A-Z0-9._%+-]+@(?:gmail\.com|outlook\.com|hotmail\.com|live\.com|icloud\.com|me\.com|yahoo\.com|aol\.com|proton(?:mail)?\.(?:com|me))\b"
        ),
    ),
    PrivacyPattern(
        code="consumer-cloud-link",
        description="consumer cloud-share link",
        regex=re.compile(
            r"(?i)\bhttps?://(?:drive\.google\.com|docs\.google\.com|onedrive\.live\.com|1drv\.ms|(?:www\.)?dropbox\.com)/\S+"
        ),
    ),
)


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=False,
    )
    entries = [entry.decode("utf-8") for entry in result.stdout.split(b"\x00") if entry]
    return [Path(entry) for entry in entries]


def _candidate_files(paths: list[str], all_files: bool) -> list[Path]:
    raw_paths = _tracked_files() if all_files or not paths else [Path(path) for path in paths]
    filtered: list[Path] = []
    for path in raw_paths:
        if any(part in SKIP_PATH_PARTS for part in path.parts):
            continue
        if path.suffix and path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.is_dir():
            continue
        filtered.append(path)
    return filtered


def _path_violations(path: Path) -> list[str]:
    path_text = path.as_posix()
    violations: list[str] = []
    for pattern in PRIVACY_PATTERNS:
        if pattern.regex.search(path_text):
            violations.append(f"{path}: {pattern.description} in file path")
    return violations


def _read_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw:
        return None
    return raw.decode("utf-8", errors="ignore")


def _content_violations(path: Path, text: str) -> list[str]:
    violations: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        for pattern in PRIVACY_PATTERNS:
            if pattern.regex.search(line):
                violations.append(f"{path}:{line_number}: {pattern.description}")
    return violations


def scan_paths(paths: list[str], *, all_files: bool) -> list[str]:
    violations: list[str] = []
    for path in _candidate_files(paths, all_files):
        violations.extend(_path_violations(path))
        text = _read_text(path)
        if text is None:
            continue
        violations.extend(_content_violations(path, text))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan tracked repository files for personal information leaks.")
    parser.add_argument("paths", nargs="*", help="Optional file paths supplied by pre-commit.")
    parser.add_argument("--all-files", action="store_true", help="Scan all tracked files instead of the provided list.")
    args = parser.parse_args(argv)

    violations = scan_paths(args.paths, all_files=args.all_files)
    if not violations:
        return 0

    print("Privacy guard found potentially personal information:", file=sys.stderr)
    for violation in violations:
        print(f"  {violation}", file=sys.stderr)
    print(
        f"Add '{ALLOW_MARKER}' to a line only when the flagged value is intentionally safe and public.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
