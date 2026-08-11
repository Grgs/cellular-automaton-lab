from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from tools._common import ROOT_DIR

VULTURE_FINDINGS_EXIT_CODE = 3
VULTURE_FINDING_PATTERN = re.compile(
    r"^(?P<path>.+):(?P<line>\d+): unused (?P<kind>\w+) "
    r"'(?P<name>[^']+)' \((?P<confidence>\d+)% confidence\)$"
)
PYTHON_TARGETS = (
    ROOT_DIR / "app.py",
    ROOT_DIR / "backend",
    ROOT_DIR / "examples",
    ROOT_DIR / "tests",
    ROOT_DIR / "tools",
)

# These assignments are consumed by their owning frameworks or by dataclass
# serialization, so a read of the Python attribute is neither expected nor
# desirable. Keep this list narrow and path-qualified.
KNOWN_DYNAMIC_ASSIGNMENTS: dict[tuple[str, str, str], str] = {
    (
        "tools/cli_support.py",
        "attribute",
        "prog",
    ): "argparse reads the parser program name while formatting errors and help",
    (
        "tools/profile_standalone_runtime.py",
        "attribute",
        "daemon_threads",
    ): "ThreadingHTTPServer reads this class-controlled server setting",
    (
        "tools/profile_standalone_runtime.py",
        "variable",
        "after_dispose_browser_memory_bytes",
    ): "RuntimeSample is serialized with dataclasses.asdict for the profiler report",
}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    name: str
    raw: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.path, self.kind, self.name)


@dataclass(frozen=True)
class SourceFacts:
    typed_dict_members: frozenset[tuple[str, int]]
    protocol_parameters: frozenset[tuple[str, int]]
    string_literals: frozenset[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find actionable dead Python code while accounting for repo dynamic contracts."
    )
    parser.add_argument(
        "--show-suppressed",
        action="store_true",
        help="also print findings suppressed as known dynamic Python usage",
    )
    return parser


def _iter_python_paths() -> list[Path]:
    paths: list[Path] = []
    for target in PYTHON_TARGETS:
        if target.is_file():
            paths.append(target)
        elif target.is_dir():
            paths.extend(path for path in target.rglob("*.py") if "__pycache__" not in path.parts)
    return sorted(paths)


def _base_name(expression: ast.expr) -> str | None:
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        return expression.attr
    if isinstance(expression, ast.Subscript):
        return _base_name(expression.value)
    return None


def collect_source_facts(paths: list[Path]) -> SourceFacts:
    typed_dict_members: set[tuple[str, int]] = set()
    protocol_parameters: set[tuple[str, int]] = set()
    string_literals: set[str] = set()

    for path in paths:
        relative_path = path.relative_to(ROOT_DIR).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                string_literals.add(node.value)
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = {_base_name(base) for base in node.bases}
            if "TypedDict" in base_names:
                typed_dict_members.update(
                    (relative_path, statement.lineno)
                    for statement in node.body
                    if isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                )
            if "Protocol" in base_names:
                for statement in node.body:
                    if not isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
                        continue
                    arguments = (
                        *statement.args.posonlyargs,
                        *statement.args.args,
                        *statement.args.kwonlyargs,
                    )
                    protocol_parameters.update(
                        (relative_path, argument.lineno) for argument in arguments
                    )
                    if statement.args.vararg is not None:
                        protocol_parameters.add((relative_path, statement.args.vararg.lineno))
                    if statement.args.kwarg is not None:
                        protocol_parameters.add((relative_path, statement.args.kwarg.lineno))

    return SourceFacts(
        typed_dict_members=frozenset(typed_dict_members),
        protocol_parameters=frozenset(protocol_parameters),
        string_literals=frozenset(string_literals),
    )


def parse_vulture_output(output: str) -> list[Finding]:
    findings: list[Finding] = []
    for raw_line in output.splitlines():
        match = VULTURE_FINDING_PATTERN.fullmatch(raw_line)
        if match is None:
            continue
        findings.append(
            Finding(
                path=Path(match.group("path")).as_posix(),
                line=int(match.group("line")),
                kind=match.group("kind"),
                name=match.group("name"),
                raw=raw_line,
            )
        )
    return findings


def suppression_reason(finding: Finding, facts: SourceFacts) -> str | None:
    if (finding.path, finding.line) in facts.typed_dict_members:
        return "TypedDict member is consumed as a runtime dictionary key"
    if (
        finding.kind == "variable"
        and (
            finding.path,
            finding.line,
        )
        in facts.protocol_parameters
    ):
        return "Protocol method parameter defines a callable interface"
    if finding.name in facts.string_literals and (
        finding.kind == "class" or finding.name.isupper()
    ):
        return "definition is resolved by an exact string-based repository contract"
    return KNOWN_DYNAMIC_ASSIGNMENTS.get(finding.key)


def classify_findings(
    findings: list[Finding], facts: SourceFacts
) -> tuple[list[Finding], list[tuple[Finding, str]]]:
    actionable: list[Finding] = []
    suppressed: list[tuple[Finding, str]] = []
    for finding in findings:
        reason = suppression_reason(finding, facts)
        if reason is None:
            actionable.append(finding)
        else:
            suppressed.append((finding, reason))
    return actionable, suppressed


def _vulture_command() -> list[str] | None:
    executable = shutil.which("vulture")
    if executable is None:
        return None
    return [executable, "--config", str(ROOT_DIR / "pyproject.toml")]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = _vulture_command()
    if command is None:
        print("vulture is not installed; install the pinned development requirements")
        return 2

    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in {0, VULTURE_FINDINGS_EXIT_CODE}:
        print(result.stderr or result.stdout, end="")
        return result.returncode

    findings = parse_vulture_output(result.stdout)
    actionable, suppressed = classify_findings(findings, collect_source_facts(_iter_python_paths()))
    for finding in actionable:
        print(finding.raw)
    if args.show_suppressed:
        for finding, reason in suppressed:
            print(f"suppressed: {finding.raw} -- {reason}")

    if actionable:
        print(
            f"dead-code audit: {len(actionable)} actionable finding(s); "
            f"{len(suppressed)} dynamic finding(s) suppressed"
        )
        return 1
    print(f"dead-code audit: clean; {len(suppressed)} dynamic finding(s) suppressed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
