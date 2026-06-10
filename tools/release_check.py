from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

ROOT_DIR = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")
Phase = Literal["pre-publish", "post-publish"]


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout or result.stderr or "").strip()


def _git_output(*args: str) -> str | None:
    result = _run_command(["git", *args])
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _gh_json(*args: str) -> dict[str, Any] | None:
    result = _run_command(["gh", *args])
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _check_version_shape(version: str) -> CheckResult:
    return CheckResult(
        "version format",
        VERSION_PATTERN.fullmatch(version) is not None,
        "expected semantic tag form like v0.4.0",
    )


def _check_release_notes(version: str) -> CheckResult:
    path = ROOT_DIR / "docs" / "releases" / f"{version}.md"
    return CheckResult(
        "release notes",
        path.exists(),
        str(path.relative_to(ROOT_DIR))
        if path.exists()
        else f"missing {path.relative_to(ROOT_DIR)}",
    )


def _check_release_docs(version: str) -> CheckResult:
    docs = {
        "README.md": ROOT_DIR / "README.md",
        "CHANGELOG.md": ROOT_DIR / "CHANGELOG.md",
        "docs/MAINTENANCE.md": ROOT_DIR / "docs" / "MAINTENANCE.md",
    }
    missing = [
        name
        for name, path in docs.items()
        if version not in path.read_text(encoding="utf-8", errors="ignore")
    ]
    return CheckResult(
        "release-facing docs",
        not missing,
        "version appears in README, changelog, and maintenance docs"
        if not missing
        else "missing version in " + ", ".join(missing),
    )


def _check_clean_tree(phase: Phase) -> CheckResult:
    status = _git_output("status", "--porcelain")
    if status is None:
        return CheckResult("git tree clean", False, "could not read git status")
    if not status:
        return CheckResult("git tree clean", True, "working tree is clean")
    if phase == "post-publish":
        return CheckResult("git tree clean", False, "release verification should run clean")
    return CheckResult("git tree clean", False, "commit or stash changes before publishing")


def _check_on_target_branch(target_branch: str) -> CheckResult:
    branch = _git_output("branch", "--show-current")
    ok = branch == target_branch
    return CheckResult(
        "target branch",
        ok,
        f"on {branch or 'detached HEAD'}, expected {target_branch}",
    )


def _check_synced_with_origin(target_branch: str) -> CheckResult:
    head = _git_output("rev-parse", "HEAD")
    upstream = _git_output("rev-parse", f"origin/{target_branch}")
    if head is None or upstream is None:
        return CheckResult(
            "origin sync",
            False,
            f"could not compare HEAD with origin/{target_branch}; run git fetch first",
        )
    return CheckResult(
        "origin sync",
        head == upstream,
        f"HEAD {'matches' if head == upstream else 'differs from'} origin/{target_branch}",
    )


def _check_local_tag(version: str, *, should_exist: bool) -> CheckResult:
    tag = _git_output("tag", "--list", version)
    exists = tag == version
    return CheckResult(
        "local tag",
        exists is should_exist,
        f"{version} {'exists' if exists else 'is missing'} locally",
    )


def _check_remote_tag(version: str, *, should_exist: bool) -> CheckResult:
    result = _run_command(["git", "ls-remote", "--tags", "origin", f"refs/tags/{version}"])
    exists = result.returncode == 0 and bool(result.stdout.strip())
    return CheckResult(
        "remote tag",
        exists is should_exist,
        f"{version} {'exists' if exists else 'is missing'} on origin",
    )


def _check_tag_target(version: str, target_branch: str) -> CheckResult:
    tag_target = _git_output("rev-list", "-n", "1", version)
    upstream = _git_output("rev-parse", f"origin/{target_branch}")
    if tag_target is None or upstream is None:
        return CheckResult(
            "tag target",
            False,
            f"could not compare {version} with origin/{target_branch}",
        )
    return CheckResult(
        "tag target",
        tag_target == upstream,
        f"{version} {'points at' if tag_target == upstream else 'does not point at'} origin/{target_branch}",
    )


def _check_github_release(version: str, *, should_exist: bool) -> CheckResult:
    release = _gh_json(
        "release",
        "view",
        version,
        "--json",
        "tagName,name,isDraft,isPrerelease,url,publishedAt",
    )
    if release is None:
        return CheckResult(
            "GitHub Release",
            should_exist is False,
            f"{version} is missing on GitHub",
        )
    ok = should_exist and not bool(release.get("isDraft"))
    detail = str(release.get("url") or f"{version} exists on GitHub")
    if release.get("isDraft"):
        detail += " (draft)"
    return CheckResult("GitHub Release", ok, detail)


def _check_latest_release(version: str) -> CheckResult:
    release = _gh_json("release", "view", "--json", "tagName,url")
    tag = str(release.get("tagName")) if release is not None else ""
    return CheckResult(
        "latest release",
        tag == version,
        f"latest is {tag or 'unknown'}, expected {version}",
    )


def collect_checks(version: str, *, phase: Phase, target_branch: str) -> list[CheckResult]:
    should_be_published = phase == "post-publish"
    checks = [
        _check_version_shape(version),
        _check_release_notes(version),
        _check_release_docs(version),
        _check_clean_tree(phase),
        _check_on_target_branch(target_branch),
        _check_synced_with_origin(target_branch),
        _check_local_tag(version, should_exist=should_be_published),
        _check_remote_tag(version, should_exist=should_be_published),
        _check_github_release(version, should_exist=should_be_published),
    ]
    if should_be_published:
        checks.extend(
            (
                _check_tag_target(version, target_branch),
                _check_latest_release(version),
            )
        )
    return checks


def _render_text(checks: list[CheckResult], *, version: str, phase: Phase) -> str:
    lines = [f"release check: {version} ({phase})"]
    for check in checks:
        marker = "PASS" if check.ok else "FAIL"
        lines.append(f"[{marker}] {check.name}: {check.detail}")
    if all(check.ok for check in checks):
        if phase == "pre-publish":
            lines.append(
                "Ready to tag and publish. After publishing, rerun with --phase post-publish."
            )
        else:
            lines.append("Release publication verified.")
    else:
        lines.append("Release process is incomplete; resolve FAIL checks before continuing.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check release prerequisites before publishing and verify tag/release state after publishing.",
    )
    parser.add_argument("--version", required=True, help="Release tag, for example v0.4.0.")
    parser.add_argument(
        "--phase",
        choices=("pre-publish", "post-publish"),
        default="pre-publish",
        help="Check either pre-publication readiness or post-publication completeness.",
    )
    parser.add_argument(
        "--target-branch",
        default="main",
        help="Branch expected to contain the release commit. Default: main.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    phase = cast(Phase, args.phase)
    checks = collect_checks(
        str(args.version),
        phase=phase,
        target_branch=str(args.target_branch),
    )
    if args.format == "json":
        print(
            json.dumps(
                {
                    "version": args.version,
                    "phase": phase,
                    "ok": all(check.ok for check in checks),
                    "checks": [check.__dict__ for check in checks],
                },
                indent=2,
            )
        )
    else:
        print(_render_text(checks, version=str(args.version), phase=phase))
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
