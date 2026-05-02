"""Run pip-audit and npm audit and emit a unified findings summary.

Default behaviour fails the run when either ecosystem reports a finding at or
above the configured severity threshold. The intent is to be wired into a
nightly cron workflow so transitive CVE drift surfaces before release, and to
be runnable locally for one-off checks.

Examples:

    py -3 tools/run_supply_chain_audit.py
    py -3 tools/run_supply_chain_audit.py --ecosystem python
    py -3 tools/run_supply_chain_audit.py --format json
    py -3 tools/run_supply_chain_audit.py --severity moderate
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
PIP_REQUIREMENTS: Final[tuple[str, ...]] = ("requirements.txt", "requirements-dev.txt")
SEVERITY_ORDER: Final[tuple[str, ...]] = ("info", "low", "moderate", "high", "critical")


@dataclass(frozen=True)
class Finding:
    ecosystem: str
    package: str
    installed_version: str
    vuln_id: str
    severity: str
    fix_versions: tuple[str, ...]
    aliases: tuple[str, ...]
    description: str


@dataclass
class EcosystemResult:
    ecosystem: str
    findings: list[Finding] = field(default_factory=list)
    error: str | None = None
    skipped_reason: str | None = None


def _severity_at_or_above(severity: str, threshold: str) -> bool:
    threshold_index = SEVERITY_ORDER.index(threshold)
    try:
        actual_index = SEVERITY_ORDER.index(severity.lower())
    except ValueError:
        # Unknown severities (e.g., pip-audit findings without CVSS data) are
        # treated as "high" so they are not silently dropped.
        actual_index = SEVERITY_ORDER.index("high")
    return actual_index >= threshold_index


def _run_pip_audit(ignore_ids: frozenset[str]) -> EcosystemResult:
    result = EcosystemResult(ecosystem="python")
    try:
        import pip_audit  # type: ignore[import-untyped]  # noqa: F401
    except ImportError:
        result.skipped_reason = "pip-audit is not installed; add pip-audit to requirements-dev.in"
        return result

    cmd: list[str] = [
        sys.executable,
        "-m",
        "pip_audit",
        "--format",
        "json",
        "--progress-spinner",
        "off",
    ]
    for requirement in PIP_REQUIREMENTS:
        cmd.extend(["--requirement", str(ROOT_DIR / requirement)])
    for ignore in sorted(ignore_ids):
        cmd.extend(["--ignore-vuln", ignore])

    completed = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, check=False)

    if completed.returncode not in (0, 1):
        # pip-audit exits 1 when vulnerabilities are found, anything else is an error.
        result.error = (
            f"pip-audit exited with code {completed.returncode}: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
        return result

    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        result.error = f"pip-audit produced unparseable JSON: {exc}"
        return result

    dependencies = payload.get("dependencies", payload) if isinstance(payload, dict) else payload
    if not isinstance(dependencies, list):
        result.error = f"pip-audit JSON had unexpected shape: {type(payload).__name__}"
        return result

    for entry in dependencies:
        if not isinstance(entry, dict):
            continue
        package = str(entry.get("name", ""))
        installed_version = str(entry.get("version", ""))
        for vuln in entry.get("vulns", []) or []:
            if not isinstance(vuln, dict):
                continue
            vuln_id = str(vuln.get("id", ""))
            if vuln_id in ignore_ids:
                continue
            fix_versions = tuple(str(v) for v in vuln.get("fix_versions", []) or [])
            aliases = tuple(str(a) for a in vuln.get("aliases", []) or [])
            description = str(vuln.get("description", "")).strip()
            result.findings.append(
                Finding(
                    ecosystem="python",
                    package=package,
                    installed_version=installed_version,
                    vuln_id=vuln_id,
                    # PyPI advisory data does not carry CVSS severity reliably,
                    # so unrated findings escalate to "high" via the lookup.
                    severity=str(vuln.get("severity", "")).lower() or "unrated",
                    fix_versions=fix_versions,
                    aliases=aliases,
                    description=description,
                )
            )
    return result


def _run_npm_audit() -> EcosystemResult:
    result = EcosystemResult(ecosystem="npm")
    npm_executable = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_executable is None:
        result.skipped_reason = "npm is not on PATH; install Node.js to enable npm audit"
        return result
    if not (ROOT_DIR / "package-lock.json").exists():
        result.skipped_reason = "no package-lock.json; run 'npm install' first"
        return result

    completed = subprocess.run(
        [npm_executable, "audit", "--json"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    if not completed.stdout.strip():
        result.error = (
            f"npm audit produced no output (exit {completed.returncode}): "
            f"{completed.stderr.strip()}"
        )
        return result

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        result.error = f"npm audit produced unparseable JSON: {exc}"
        return result

    if not isinstance(payload, dict):
        result.error = f"npm audit JSON had unexpected shape: {type(payload).__name__}"
        return result

    if payload.get("error"):
        result.error = f"npm audit reported an error: {payload['error']}"
        return result

    vulnerabilities = payload.get("vulnerabilities", {})
    if not isinstance(vulnerabilities, dict):
        return result

    for package, entry in vulnerabilities.items():
        if not isinstance(entry, dict):
            continue
        severity = str(entry.get("severity", "")).lower()
        installed_version = ""
        via_entries = entry.get("via", [])
        aliases: list[str] = []
        descriptions: list[str] = []
        if isinstance(via_entries, list):
            for via in via_entries:
                if isinstance(via, dict):
                    title = str(via.get("title", "")).strip()
                    if title:
                        descriptions.append(title)
                    url = str(via.get("url", "")).strip()
                    if url:
                        aliases.append(url)
                    range_value = str(via.get("range", "")).strip()
                    if range_value and not installed_version:
                        installed_version = range_value
        fix_available = entry.get("fixAvailable", False)
        fix_versions: tuple[str, ...] = ()
        if isinstance(fix_available, dict):
            fix_versions = (str(fix_available.get("version", "")),)
        elif fix_available is True:
            fix_versions = ("available",)
        result.findings.append(
            Finding(
                ecosystem="npm",
                package=str(package),
                installed_version=installed_version,
                vuln_id="; ".join(aliases) or "n/a",
                severity=severity or "unrated",
                fix_versions=fix_versions,
                aliases=tuple(aliases),
                description="; ".join(descriptions),
            )
        )
    return result


def _format_summary(results: list[EcosystemResult], threshold: str) -> str:
    lines: list[str] = []
    blocking_total = 0
    informational_total = 0
    for result in results:
        if result.skipped_reason is not None:
            lines.append(f"[{result.ecosystem}] skipped: {result.skipped_reason}")
            continue
        if result.error is not None:
            lines.append(f"[{result.ecosystem}] error: {result.error}")
            continue
        if not result.findings:
            lines.append(f"[{result.ecosystem}] no findings")
            continue
        blocking = [f for f in result.findings if _severity_at_or_above(f.severity, threshold)]
        informational = [f for f in result.findings if f not in blocking]
        blocking_total += len(blocking)
        informational_total += len(informational)
        lines.append(
            f"[{result.ecosystem}] {len(blocking)} blocking, {len(informational)} informational"
        )
        for finding in blocking + informational:
            tag = "BLOCK" if finding in blocking else "info "
            fix = ", ".join(finding.fix_versions) if finding.fix_versions else "no fix listed"
            lines.append(
                f"  {tag} {finding.severity:>8s}  {finding.package}=={finding.installed_version}"
                f"  {finding.vuln_id}  fix: {fix}"
            )
    lines.append("")
    lines.append(
        f"Totals: {blocking_total} blocking (severity >= {threshold}), "
        f"{informational_total} informational"
    )
    return "\n".join(lines)


def _to_serializable(results: list[EcosystemResult], threshold: str) -> dict[str, object]:
    payload: dict[str, object] = {"threshold": threshold, "ecosystems": []}
    ecosystems_field = payload["ecosystems"]
    assert isinstance(ecosystems_field, list)
    for result in results:
        ecosystems_field.append(
            {
                "ecosystem": result.ecosystem,
                "skipped_reason": result.skipped_reason,
                "error": result.error,
                "findings": [
                    {
                        "package": f.package,
                        "installed_version": f.installed_version,
                        "vuln_id": f.vuln_id,
                        "severity": f.severity,
                        "fix_versions": list(f.fix_versions),
                        "aliases": list(f.aliases),
                        "description": f.description,
                        "blocking": _severity_at_or_above(f.severity, threshold),
                    }
                    for f in result.findings
                ],
            }
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--ecosystem",
        choices=("all", "python", "npm"),
        default="all",
        help="which ecosystem to audit (default: all)",
    )
    parser.add_argument(
        "--severity",
        choices=SEVERITY_ORDER,
        default="high",
        help="minimum severity that fails the run (default: high)",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="output format (default: summary)",
    )
    parser.add_argument(
        "--ignore-pip-vuln",
        action="append",
        default=[],
        help="pip-audit vulnerability ID to ignore; may be passed multiple times",
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="always exit 0 even when blocking findings are present",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="write the formatted output to this file as well as stdout",
    )
    args = parser.parse_args(argv)

    ignore_ids = frozenset(args.ignore_pip_vuln)
    results: list[EcosystemResult] = []
    if args.ecosystem in ("all", "python"):
        results.append(_run_pip_audit(ignore_ids))
    if args.ecosystem in ("all", "npm"):
        results.append(_run_npm_audit())

    if args.format == "json":
        rendered = json.dumps(_to_serializable(results, args.severity), indent=2, sort_keys=True)
    else:
        rendered = _format_summary(results, args.severity)

    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    has_error = any(r.error is not None for r in results)
    has_blocking = any(
        any(_severity_at_or_above(f.severity, args.severity) for f in r.findings) for r in results
    )

    if args.no_fail:
        return 0
    if has_error:
        return 2
    if has_blocking:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
